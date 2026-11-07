#include <GLES3/gl3.h>
#include "oa_stream.h"
#include <android/asset_manager.h>
#include <android/log.h>
#include <math.h>
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO,"OpemAmalurScene",__VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR,"OpemAmalurScene",__VA_ARGS__)
enum{LODS=6,GRASS=3,TREE_LEAF=4,REGION=5,MAX_DRAWS=128,STATE_NONE=0,STATE_QUEUED,STATE_CPU,STATE_GPU,MAX_JOBS=4096,UPLOAD_BUDGET=6*1024*1024,TEXTURE_BUDGET=2,VERTEX_BYTES=28};
#define HYSTERESIS 3200.0f
#define TEXTURE_LINGER 5.0f
typedef struct draw_rec{uint32_t texture,first,count;}draw_rec;
typedef struct region_range{draw_rec draw;uint32_t flags;float sphere[4],min_sq,max_sq;uint32_t source;float distance_scale;}region_range;
typedef struct lod_data{region_range *ranges;int state;uint8_t *bytes;size_t size;GLuint array,vertex,index;int geometry_kind;uint32_t draw_count;draw_rec draws[MAX_DRAWS];size_t gpu_bytes;uint32_t triangles;}lod_data;
static const draw_rec *lod_draw(const lod_data *q,unsigned d){return q->ranges?&q->ranges[d].draw:q->draws+d;}
typedef struct cell{int ix,iy;float lo[3],hi[3],base_lo[3],base_hi[3],distance;lod_data lod[LODS];int shown;}cell;
typedef struct texture_slot{int state;uint8_t *bytes;size_t size;uint32_t w,h;GLuint id;float idle;size_t gpu_bytes;}texture_slot;
typedef struct material{uint32_t flags,t[6],native_family;float native_color[4],native_specular[4];uint32_t native_t[8];float native_uv[4];int terrain_set;uint32_t terrain_t[8];float terrain_uv[4],terrain_levels[4],terrain_powers[4];}material;
typedef struct job{int kind,index,lod;}job;
struct oa_stream{
 AAssetManager *assets;pthread_t thread;pthread_mutex_t lock;pthread_cond_t wake,done;int stop,started;
 float cell_size;unsigned cell_count,texture_count,material_count;cell *cells;texture_slot *textures;material *materials;float *water;GLuint flat_normal,flat_black;
 job jobs[MAX_JOBS];unsigned job_count;
 /* Collision requests are latest-wins: only the current player cell matters. */
 int want_x,want_y,want_pending,have_x,have_y,built_x,built_y;opem_collision_world *built;int building;char error[192];
 float far_range,last_eye[3];int64_t last_update;
 size_t cpu_bytes;size_t gpu_bytes;
 float upload_ms,upload_worst;unsigned drawn_cells,drawn_draws,drawn_tris,drawn_native;
 unsigned char *leaf_materials;unsigned leaf_index_cells,native_leaf_cells;
 unsigned region_index_cells,region_cells,region_draws,region_lod_culled;float region_distance_scale;
 int native_post_ready;float native_post[4];
 int native_lighting_ready;float native_sky[4],native_ambient[2],terrain_height_blend;
 unsigned terrain_sets,drawn_terrain,forced_leaf_cells;int terrain_maps_attempted;GLuint terrain_paint,terrain_selector;size_t terrain_gpu_bytes;
};
static int64_t now_ns(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return (int64_t)t.tv_sec*1000000000+t.tv_nsec;}
static uint8_t *asset_read(AAssetManager *m,const char *name,size_t *size){AAsset *a=AAssetManager_open(m,name,AASSET_MODE_STREAMING);uint8_t *b;off64_t n;size_t got=0;if(!a)return NULL;n=AAsset_getLength64(a);b=(uint8_t*)malloc((size_t)n?(size_t)n:1);if(!b){AAsset_close(a);return NULL;}
 while(got<(size_t)n){int r=AAsset_read(a,b+got,(size_t)n-got);if(r<=0)break;got+=(size_t)r;}AAsset_close(a);if(got!=(size_t)n){free(b);return NULL;}*size=got;return b;}
static opem_collision_world *build_collision(oa_stream *s,int cx,int cy,char *error,size_t cap){
 float *soup=NULL;size_t floats=0,used=0;int dx,dy;opem_collision_world *w=NULL;
 for(dy=-1;dy<=1;dy++)for(dx=-1;dx<=1;dx++){char name[64];size_t size;uint8_t *b;uint32_t n;snprintf(name,sizeof(name),"world/k%d_%d.bin",cx+dx,cy+dy);b=asset_read(s->assets,name,&size);if(!b)continue;
  if(size>=4){memcpy(&n,b,4);if(size==4+(size_t)n*36u&&n){float *grown=(float*)realloc(soup,(floats+(size_t)n*9u)*sizeof(float));if(grown){soup=grown;memcpy(soup+floats,b+4,(size_t)n*36u);floats+=(size_t)n*9u;used++;}}}free(b);}
 if(!floats){snprintf(error,cap,"no collision cells near %d %d",cx,cy);free(soup);return NULL;}
 if(!opem_collision_create(&w,soup,(uint32_t)(floats/3),3,error,cap))w=NULL;free(soup);return w;}
static void *worker(void *arg){oa_stream *s=(oa_stream*)arg;pthread_mutex_lock(&s->lock);
 for(;;){unsigned i,best=MAX_JOBS;float near=1e30f;job j;
  if(s->stop)break;
  if(s->want_pending){int cx=s->want_x,cy=s->want_y;char error[192]="";opem_collision_world *w;s->want_pending=0;s->building=1;pthread_mutex_unlock(&s->lock);w=build_collision(s,cx,cy,error,sizeof(error));pthread_mutex_lock(&s->lock);s->building=0;if(!w)snprintf(s->error,sizeof(s->error),"%s",error);if(s->built)opem_collision_destroy(s->built);s->built=w;s->built_x=cx;s->built_y=cy;pthread_cond_broadcast(&s->done);continue;}
  for(i=0;i<s->job_count;i++){float d=s->jobs[i].kind==0?s->cells[s->jobs[i].index].distance:0;if(d<near){near=d;best=i;}}
  if(best==MAX_JOBS){pthread_cond_wait(&s->wake,&s->lock);continue;}
  j=s->jobs[best];s->jobs[best]=s->jobs[--s->job_count];pthread_mutex_unlock(&s->lock);
  {char name[64];size_t size=0;uint8_t *b;
   if(j.kind==0&&j.lod==GRASS)snprintf(name,sizeof(name),"world/g%d_%d.bin",s->cells[j.index].ix,s->cells[j.index].iy);else if(j.kind==0&&j.lod==TREE_LEAF)snprintf(name,sizeof(name),"world/l%d_%d.bin",s->cells[j.index].ix,s->cells[j.index].iy);else if(j.kind==0&&j.lod==REGION)snprintf(name,sizeof(name),"world/r%d_%d.bin",s->cells[j.index].ix,s->cells[j.index].iy);else if(j.kind==0)snprintf(name,sizeof(name),"world/c%d_%d_%d.bin",s->cells[j.index].ix,s->cells[j.index].iy,j.lod);else snprintf(name,sizeof(name),"world/t%d.bin",j.index);
   b=asset_read(s->assets,name,&size);
   pthread_mutex_lock(&s->lock);
   if(j.kind==0){lod_data *l=s->cells[j.index].lod+j.lod;if(l->state==STATE_QUEUED){l->bytes=b;l->size=size;l->state=b?STATE_CPU:STATE_NONE;if(b)s->cpu_bytes+=size;else LOGE("Stream cell missing %s",name);}else free(b);}
   else{texture_slot *t=s->textures+j.index;if(t->state==STATE_QUEUED){t->bytes=b;t->size=size;t->state=b?STATE_CPU:STATE_NONE;if(b)s->cpu_bytes+=size;else LOGE("Stream texture missing %s",name);}else free(b);}}
 }
 pthread_mutex_unlock(&s->lock);return NULL;}
oa_stream *oa_stream_open(AAssetManager *m){
 size_t size=0;uint8_t *b=asset_read(m,"world/index.bin",&size);oa_stream *s;uint32_t cells,textures,unused;float cell_size;unsigned i;
 if(!b)return NULL;
 if(size<20||memcmp(b,"OAWI",4)){free(b);LOGE("Stream index invalid");return NULL;}
 memcpy(&cell_size,b+4,4);memcpy(&cells,b+8,4);memcpy(&textures,b+12,4);memcpy(&unused,b+16,4);
 if(cells>65536||size!=20+(size_t)cells*48u||!(cell_size>0)){free(b);LOGE("Stream index shape invalid");return NULL;}
 s=(oa_stream*)calloc(1,sizeof(*s));if(!s){free(b);return NULL;}
 s->assets=m;s->far_range=OA_STREAM_FAR;s->cell_size=cell_size;s->cell_count=cells;s->cells=(cell*)calloc(cells,sizeof(cell));
 {size_t ws=0;uint8_t *wb=asset_read(m,"world/water.bin",&ws);uint32_t wc=0;if(wb&&ws>=4)memcpy(&wc,wb,4);if(wb&&ws==4+(size_t)wc*44u&&(s->water=(float*)malloc((size_t)wc*44u))!=NULL)memcpy(s->water,wb+4,(size_t)wc*44u);free(wb);}
 {size_t ms=0;uint8_t *mb=asset_read(m,"world/materials.bin",&ms);uint32_t mc=0,k,top=0;if(mb&&ms>=4)memcpy(&mc,mb,4);if(!mb||ms!=4+(size_t)mc*28u){free(mb);free(b);free(s->cells);free(s);LOGE("Stream materials invalid");return NULL;}
  s->materials=(material*)calloc(mc?mc:1,sizeof(material));s->material_count=mc;if(!s->materials){free(mb);free(b);free(s->cells);free(s);return NULL;}for(k=0;k<mc;k++){memcpy(&s->materials[k].flags,mb+4+(size_t)k*28u,28u);s->materials[k].terrain_set=(s->materials[k].flags&0x40000000u)?-2:-1;}free(mb);for(k=0;k<mc;k++){int q;for(q=0;q<6;q++)if(s->materials[k].t[q]!=0xffffffffu&&s->materials[k].t[q]+1>top)top=s->materials[k].t[q]+1;}textures=top;}
 /* Optional evidence-backed material profile. Legacy packs keep their original path. */
 {size_t ns=0;uint8_t *nb=asset_read(m,"world/lighting.bin",&ns);if(nb){
   if((ns==32||ns==36)&&!memcmp(nb,"OALG001",8)){unsigned q;int valid=1;float vals[6];memcpy(vals,nb+8,24);for(q=0;q<6;q++)if(!isfinite(vals[q])||vals[q]<0||vals[q]>100)valid=0;
    if(valid){memcpy(s->native_sky,vals,16);memcpy(s->native_ambient,vals+4,8);s->native_lighting_ready=1;if(ns==36){float f;memcpy(&f,nb+32,4);if(isfinite(f)&&f>0&&f<=1)s->terrain_height_blend=f;}}}
   if(!s->native_lighting_ready)LOGE("Native global lighting profile invalid");free(nb);}}
 {size_t ns=0;uint8_t *nb=asset_read(m,"world/material-lighting.bin",&ns);if(nb){uint32_t n=0,k,accepted=0;
   if(ns>=12&&!memcmp(nb,"OAML001",8))memcpy(&n,nb+8,4);
   if(n<=s->material_count&&ns==12+(size_t)n*36u){for(k=0;k<n;k++){const uint8_t *p=nb+12+(size_t)k*36u;uint32_t family;float vals[8];unsigned q;int valid=1;memcpy(&family,p,4);memcpy(vals,p+4,32);
     if(family==0)continue;if(family!=1)valid=0;for(q=0;q<8;q++)if(!isfinite(vals[q])||vals[q]<0||vals[q]>1024)valid=0;
     if(valid){s->materials[k].native_family=family;memcpy(s->materials[k].native_color,vals,16);memcpy(s->materials[k].native_specular,vals+4,16);accepted++;}
     else LOGE("Native material lighting row invalid index=%u",k);}
    LOGI("Native material lighting profile rows=%u globals=%d sky=(%.3f %.3f %.3f %.3f) ambient=(%.3f %.3f)",accepted,s->native_lighting_ready,s->native_sky[0],s->native_sky[1],s->native_sky[2],s->native_sky[3],s->native_ambient[0],s->native_ambient[1]);}
   else LOGE("Native material lighting profile shape invalid");free(nb);}}
 {size_t ts=0;uint8_t *tb=asset_read(m,"world/terrain_materials.bin",&ts);if(tb){uint32_t version=0,n=0,k,stride=56;unsigned top=textures;
   if(ts>=12&&!memcmp(tb,"OATP",4)){memcpy(&version,tb+4,4);memcpy(&n,tb+8,4);}
   stride=version==2?88u:56u;if((version==1||version==2)&&n<=64&&ts==12+(size_t)n*stride){for(k=0;k<n;k++){const uint8_t *p=tb+12+(size_t)k*stride;uint32_t index,set,t[8];float uv[4];unsigned j;int valid=1;
    memcpy(&index,p,4);memcpy(&set,p+4,4);memcpy(t,p+8,32);memcpy(uv,p+40,16);
    if(index>=s->material_count||set>=5)valid=0;for(j=0;j<8;j++)if(t[j]>=16384)valid=0;for(j=0;j<4;j++)if(!isfinite(uv[j])||uv[j]<=0||uv[j]>16)valid=0;
    if(valid){material *row=s->materials+index;if(!(row->flags&0x40000000u))continue;row->terrain_set=(int)set;memcpy(row->terrain_t,t,32);memcpy(row->terrain_uv,uv,16);if(version==2){memcpy(row->terrain_levels,p+56,16);memcpy(row->terrain_powers,p+72,16);}s->terrain_sets|=1u<<set;for(j=0;j<8;j++)if(t[j]+1>top)top=t[j]+1;}
    else LOGE("Native terrain row invalid row=%u",k);}
    textures=top;LOGI("Native terrain profiles=%u supported_mask=%u height_blend=%.6f",n,s->terrain_sets,s->terrain_height_blend);}
   else LOGE("Native terrain profile shape invalid");free(tb);}}
 {size_t n=0;uint8_t *b=asset_read(m,"world/post.bin",&n);if(b){if(n==24&&!memcmp(b,"OAPO001",8)){unsigned i;int valid=1;float f[4];memcpy(f,b+8,16);for(i=0;i<4;i++)if(!isfinite(f[i])||f[i]<0||f[i]>128)valid=0;if(f[1]<=0)valid=0;if(valid){memcpy(s->native_post,f,16);s->native_post_ready=1;LOGI("Native post profile ready exposure=%.7f min_luminance=%.7f inverse_range=%.7f bloom_merge=%.7f",f[0],f[1],f[2],f[3]);}}if(!s->native_post_ready)LOGE("Native post profile invalid");free(b);}}
 {size_t ns=0;uint8_t *nb=asset_read(m,"world/native-materials.bin",&ns);if(nb){uint32_t n=0,k,accepted=0;if(ns>=12&&!memcmp(nb,"OANM001",8))memcpy(&n,nb+8,4);
 if(n<=s->material_count&&ns==12+(size_t)n*84u){for(k=0;k<n;k++){const uint8_t *p=nb+12+(size_t)k*84u;uint32_t family,t[8];float f[12];unsigned j;int valid=1;memcpy(&family,p,4);memcpy(t,p+4,32);memcpy(f,p+36,48);if((family<1||family>6)&&family!=8)continue;for(j=0;j<12;j++)if(!isfinite(f[j])||fabsf(f[j])>100000.f)valid=0;for(j=0;j<8;j++)if(t[j]!=0xffffffffu&&t[j]>16383)valid=0;if(!valid)continue;material *row=s->materials+k;row->native_family=family;memcpy(row->native_t,t,32);memcpy(row->native_color,f,16);memcpy(row->native_specular,f+4,16);memcpy(row->native_uv,f+8,16);for(j=0;j<8;j++)if(t[j]!=0xffffffffu&&t[j]+1>textures)textures=t[j]+1;accepted++;}}
 LOGI("Native material contracts rows=%u accepted=%u",n,accepted);free(nb);}}
 s->texture_count=textures;s->textures=(texture_slot*)calloc(textures?textures:1,sizeof(texture_slot));
 if(!s->cells||!s->textures||!s->materials){free(b);free(s->cells);free(s->textures);free(s->leaf_materials);free(s->materials);free(s);return NULL;}
 for(i=0;i<cells;i++){const uint8_t *r=b+20+i*48u;int32_t ix,iy;uint32_t t[4];cell *c=s->cells+i;memcpy(&ix,r,4);memcpy(&iy,r+4,4);memcpy(c->lo,r+8,12);memcpy(c->hi,r+20,12);memcpy(c->base_lo,c->lo,12);memcpy(c->base_hi,c->hi,12);memcpy(t,r+32,16);c->lod[GRASS].triangles=t[3];c->ix=ix;c->iy=iy;c->shown=-1;c->distance=1e30f;c->lod[0].triangles=t[0];c->lod[1].triangles=t[1];c->lod[2].triangles=t[2];}
 free(b);
 s->have_x=s->have_y=s->want_x=s->want_y=0x7fffffff;
 pthread_mutex_init(&s->lock,NULL);pthread_cond_init(&s->wake,NULL);pthread_cond_init(&s->done,NULL);
 if(pthread_create(&s->thread,NULL,worker,s)){LOGE("Stream thread failed");free(s->cells);free(s->textures);free(s);return NULL;}
 /* Optional source-proven leaf-only cells keep foliage attributes independent of coarse body meshes. */
 {size_t z=0;uint8_t *q=asset_read(m,"world/leaf-index.bin",&z);uint32_t n=0,nm=0,mc=0,k;if(q&&z>=20&&!memcmp(q,"OALF001",8)){memcpy(&n,q+8,4);memcpy(&nm,q+12,4);memcpy(&mc,q+16,4);if(n<=cells&&nm<=s->material_count&&mc==s->material_count&&z==20+(size_t)nm*8+(size_t)n*12){int valid=1;for(k=0;k<nm;k++){uint32_t x,y;memcpy(&x,q+20+k*8,4);memcpy(&y,q+24+k*8,4);if(x>=mc||y>=mc||s->materials[y].native_family!=6)valid=0;}if(valid&&(s->leaf_materials=(unsigned char*)calloc(mc,1))!=NULL){for(k=0;k<nm;k++){uint32_t x,y;memcpy(&x,q+20+k*8,4);memcpy(&y,q+24+k*8,4);s->leaf_materials[x]=s->leaf_materials[y]=1;}for(k=0;k<n;k++){const uint8_t *r=q+20+nm*8+k*12;int32_t x,y;uint32_t nt,j;memcpy(&x,r,4);memcpy(&y,r+4,4);memcpy(&nt,r+8,4);for(j=0;j<cells;j++)if(s->cells[j].ix==x&&s->cells[j].iy==y){s->cells[j].lod[TREE_LEAF].triangles=nt;s->leaf_index_cells++;break;}}}}}free(q);if(s->leaf_index_cells)LOGI("Native leaf index cells=%u source_owned=1",s->leaf_index_cells);}
 /* Optional authored Region/actor visuals can also own cells absent from the old scene-only index. */
 {size_t z=0;uint8_t *q=asset_read(m,"world/region-index.bin",&z);uint32_t n=0,mc=0,k;float scale=0;
  if(q&&z>=24&&!memcmp(q,"OARGIDX1",8)){memcpy(&n,q+8,4);memcpy(&mc,q+12,4);memcpy(&scale,q+16,4);
   if(n<=65536&&mc==s->material_count&&isfinite(scale)&&scale>0&&scale<=16&&z==24+(size_t)n*40){int valid=1;unsigned extra=0;
    for(k=0;k<n;k++){const uint8_t *r=q+24+k*40;float bounds[6];uint32_t runs,j;int32_t x,y;memcpy(&x,r,4);memcpy(&y,r+4,4);memcpy(&runs,r+12,4);memcpy(bounds,r+16,24);if(runs>4096)valid=0;for(j=0;j<6;j++)if(!isfinite(bounds[j]))valid=0;for(j=0;j<3;j++)if(bounds[j]>bounds[j+3])valid=0;for(j=0;j<cells;j++)if(s->cells[j].ix==x&&s->cells[j].iy==y)break;if(j==cells)extra++;for(j=0;j<k;j++){int32_t ax,ay;memcpy(&ax,q+24+j*40,4);memcpy(&ay,q+28+j*40,4);if(ax==x&&ay==y)valid=0;}}
    if(cells+extra>65536)valid=0;
    if(valid){cell *grown;pthread_mutex_lock(&s->lock);grown=(cell*)realloc(s->cells,(size_t)(cells+extra)*sizeof(cell));if(grown){unsigned old_cells=cells;memset(grown+cells,0,(size_t)extra*sizeof(cell));s->cells=grown;s->region_distance_scale=scale;
      for(k=0;k<n;k++){const uint8_t *r=q+24+k*40;float bounds[6];uint32_t tris,j;int32_t x,y;memcpy(&x,r,4);memcpy(&y,r+4,4);memcpy(&tris,r+8,4);memcpy(bounds,r+16,24);for(j=0;j<cells;j++)if(s->cells[j].ix==x&&s->cells[j].iy==y)break;
       if(j==cells){cell *c=s->cells+cells++;c->ix=x;c->iy=y;c->shown=-1;c->distance=1e30f;memcpy(c->lo,bounds,12);memcpy(c->hi,bounds+3,12);memcpy(c->base_lo,c->lo,12);memcpy(c->base_hi,c->hi,12);}
       {cell *c=s->cells+j;unsigned a;c->lod[REGION].triangles=tris;for(a=0;a<3;a++){c->lo[a]=fminf(c->lo[a],bounds[a]);c->hi[a]=fmaxf(c->hi[a],bounds[a+3]);}s->region_index_cells++;}}
      s->cell_count=cells;LOGI("Authored region index cells=%u new_cells=%u lod_distance_scale=%.6f",s->region_index_cells,cells-old_cells,scale);
     }pthread_mutex_unlock(&s->lock);}
   }
   if(!s->region_index_cells)LOGE("Authored region index invalid");
  }free(q);}
 s->started=1;LOGI("Stream opened cells=%u textures=%u cell_size=%.0f",cells,textures,cell_size);return s;}
void oa_stream_set_far(oa_stream *s,float range){s->far_range=range;}
void oa_stream_close(oa_stream *s){unsigned i;int l;if(!s)return;pthread_mutex_lock(&s->lock);s->stop=1;pthread_cond_broadcast(&s->wake);pthread_mutex_unlock(&s->lock);if(s->started)pthread_join(s->thread,NULL);
 if(s->built)opem_collision_destroy(s->built);for(i=0;i<s->cell_count;i++)for(l=0;l<LODS;l++){free(s->cells[i].lod[l].bytes);free(s->cells[i].lod[l].ranges);}for(i=0;i<s->texture_count;i++)free(s->textures[i].bytes);
 pthread_mutex_destroy(&s->lock);pthread_cond_destroy(&s->wake);pthread_cond_destroy(&s->done);free(s->water);free(s->cells);free(s->textures);free(s->leaf_materials);free(s->materials);free(s);}
void oa_stream_bounds(const oa_stream *s,float center[3],float *radius){float lo[3]={1e30f,1e30f,1e30f},hi[3]={-1e30f,-1e30f,-1e30f};unsigned i;int k;double r=0;for(i=0;i<s->cell_count;i++)for(k=0;k<3;k++){if(s->cells[i].lo[k]<lo[k])lo[k]=s->cells[i].lo[k];if(s->cells[i].hi[k]>hi[k])hi[k]=s->cells[i].hi[k];}
 for(k=0;k<3;k++){double d=(double)hi[k]-lo[k];center[k]=(lo[k]+hi[k])*.5f;r+=d*d;}*radius=(float)(sqrt(r)*.5);}
opem_collision_world *oa_stream_collision_now(oa_stream *s,const float feet[3],char *error,size_t cap){int cx=(int)floorf(feet[0]/s->cell_size),cy=(int)floorf(feet[1]/s->cell_size);opem_collision_world *w=build_collision(s,cx,cy,error,cap);if(w){s->have_x=cx;s->have_y=cy;}return w;}
opem_collision_world *oa_stream_collision_poll(oa_stream *s,const float feet[3]){int cx=(int)floorf(feet[0]/s->cell_size),cy=(int)floorf(feet[1]/s->cell_size);opem_collision_world *w=NULL;pthread_mutex_lock(&s->lock);
 if(s->built){w=s->built;s->built=NULL;s->have_x=s->built_x;s->have_y=s->built_y;}
 else if(s->error[0]){LOGE("Stream collision: %s",s->error);s->error[0]=0;s->have_x=cx;s->have_y=cy;}
 if((cx!=s->have_x||cy!=s->have_y)&&!s->building&&(!s->want_pending||s->want_x!=cx||s->want_y!=cy)){s->want_x=cx;s->want_y=cy;s->want_pending=1;pthread_cond_broadcast(&s->wake);}
 pthread_mutex_unlock(&s->lock);return w;}
static void push_job(oa_stream *s,int kind,int index,int lod){if(s->job_count<MAX_JOBS){job j;j.kind=kind;j.index=index;j.lod=lod;s->jobs[s->job_count++]=j;pthread_cond_signal(&s->wake);}}
static void free_gpu(oa_stream *s,lod_data *l){if(l->array)glDeleteVertexArrays(1,&l->array);if(l->vertex)glDeleteBuffers(1,&l->vertex);if(l->index)glDeleteBuffers(1,&l->index);l->array=l->vertex=l->index=0;s->gpu_bytes-=l->gpu_bytes;l->gpu_bytes=0;l->draw_count=0;free(l->ranges);l->ranges=NULL;}
/* Builds GL objects from a loaded cell. A cell becomes drawable once its textures are ready. */
static int upload_cell(oa_stream *s,cell *c,lod_data *l){uint32_t v,i,d,k,stride,head=16,run_stride=12;const uint8_t *b=l->bytes;int region=l->size>=28&&!memcmp(b,"OARGEO1",8);
 free(l->ranges);l->ranges=NULL;l->draw_count=0;
 if(region){uint32_t vs,rs;memcpy(&v,b+8,4);memcpy(&i,b+12,4);memcpy(&d,b+16,4);memcpy(&vs,b+20,4);memcpy(&rs,b+24,4);if(vs!=76||rs!=48||sizeof(region_range)!=48)return 0;head=28;run_stride=48;l->geometry_kind=2;stride=76;}
 else{if(l->size<16||(memcmp(b,"OAWC",4)&&memcmp(b,"OAWF",4)&&memcmp(b,"OAWE",4))){LOGE("Stream cell invalid");return 0;}l->geometry_kind=!memcmp(b,"OAWF",4)?1:!memcmp(b,"OAWE",4)?2:0;stride=l->geometry_kind==1?40:l->geometry_kind==2?76:VERTEX_BYTES;memcpy(&v,b+4,4);memcpy(&i,b+8,4);memcpy(&d,b+12,4);}
 if(d>(region?4096u:MAX_DRAWS)||l->size!=head+(size_t)d*run_stride+(size_t)v*stride+(size_t)i*4u){LOGE("Stream cell shape invalid %d %d",c->ix,c->iy);return 0;}
 if(region){l->ranges=(region_range*)malloc((size_t)d*sizeof(region_range));if(d&&!l->ranges)return 0;memcpy(l->ranges,b+head,(size_t)d*48);for(k=0;k<d;k++){region_range *r=l->ranges+k;unsigned a;if(r->draw.texture>=s->material_count||r->draw.first>i||r->draw.count>i-r->draw.first||r->draw.count%3||!isfinite(r->min_sq)||!isfinite(r->max_sq)||r->min_sq<0||r->max_sq<r->min_sq||!isfinite(r->distance_scale)||r->distance_scale<0||r->distance_scale>16){free(l->ranges);l->ranges=NULL;return 0;}for(a=0;a<4;a++)if(!isfinite(r->sphere[a])){free(l->ranges);l->ranges=NULL;return 0;}}}
 else{memcpy(l->draws,b+head,d*12u);for(k=0;k<d;k++)if(l->draws[k].texture>=s->material_count)return 0;}
 l->draw_count=d;
 glGenVertexArrays(1,&l->array);glGenBuffers(1,&l->vertex);glGenBuffers(1,&l->index);glBindVertexArray(l->array);
 glBindBuffer(GL_ARRAY_BUFFER,l->vertex);glBufferData(GL_ARRAY_BUFFER,(GLsizeiptr)((size_t)v*stride),b+head+(size_t)d*run_stride,GL_STATIC_DRAW);
 glBindBuffer(GL_ELEMENT_ARRAY_BUFFER,l->index);glBufferData(GL_ELEMENT_ARRAY_BUFFER,(GLsizeiptr)((size_t)i*4u),b+head+(size_t)d*run_stride+(size_t)v*stride,GL_STATIC_DRAW);
 glEnableVertexAttribArray(0);glVertexAttribPointer(0,3,GL_FLOAT,GL_FALSE,stride,(void*)0);
 if(l->geometry_kind==1){glEnableVertexAttribArray(1);glVertexAttribPointer(1,3,GL_FLOAT,GL_FALSE,stride,(void*)24);glEnableVertexAttribArray(2);glVertexAttribPointer(2,4,GL_UNSIGNED_BYTE,GL_TRUE,stride,(void*)36);glEnableVertexAttribArray(3);glVertexAttribPointer(3,2,GL_FLOAT,GL_FALSE,stride,(void*)16);glEnableVertexAttribArray(7);glVertexAttribIPointer(7,1,GL_UNSIGNED_INT,stride,(void*)12);}
 else if(l->geometry_kind==2){glEnableVertexAttribArray(1);glVertexAttribPointer(1,3,GL_FLOAT,GL_FALSE,stride,(void*)12);glEnableVertexAttribArray(2);glVertexAttribPointer(2,4,GL_UNSIGNED_BYTE,GL_TRUE,stride,(void*)64);glEnableVertexAttribArray(3);glVertexAttribPointer(3,2,GL_FLOAT,GL_FALSE,stride,(void*)48);glEnableVertexAttribArray(4);glVertexAttribPointer(4,3,GL_FLOAT,GL_FALSE,stride,(void*)24);glEnableVertexAttribArray(5);glVertexAttribPointer(5,3,GL_FLOAT,GL_FALSE,stride,(void*)36);glEnableVertexAttribArray(6);glVertexAttribPointer(6,2,GL_FLOAT,GL_FALSE,stride,(void*)56);glDisableVertexAttribArray(7);glEnableVertexAttribArray(8);glVertexAttribPointer(8,1,GL_FLOAT,GL_FALSE,stride,(void*)72);}
 else{glEnableVertexAttribArray(1);glVertexAttribPointer(1,4,GL_SHORT,GL_TRUE,stride,(void*)12);glDisableVertexAttribArray(2);glEnableVertexAttribArray(3);glVertexAttribPointer(3,2,GL_FLOAT,GL_FALSE,stride,(void*)20);glDisableVertexAttribArray(7);}
 glVertexAttrib4f(2,1,1,1,1);glVertexAttribI4ui(7,0,0,0,0);
 glBindVertexArray(0);glBindBuffer(GL_ARRAY_BUFFER,0);glBindBuffer(GL_ELEMENT_ARRAY_BUFFER,0);
 l->gpu_bytes=(size_t)v*stride+(size_t)i*4u;s->gpu_bytes+=l->gpu_bytes;return 1;}
static int upload_texture(oa_stream *s,texture_slot *t){uint32_t fmt,w,h,levels,l;size_t at=20,total=0;const uint8_t *b=t->bytes;
 if(t->size<20||memcmp(b,"OATX",4))return 0;memcpy(&fmt,b+4,4);memcpy(&w,b+8,4);memcpy(&h,b+12,4);memcpy(&levels,b+16,4);if(levels>16)return 0;
 glGenTextures(1,&t->id);glActiveTexture(GL_TEXTURE0);glBindTexture(GL_TEXTURE_2D,t->id);
 glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,GL_REPEAT);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,GL_REPEAT);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_LINEAR_MIPMAP_LINEAR);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_LINEAR);{size_t slot=(size_t)(t-s->textures);glTexParameterf(GL_TEXTURE_2D,0x84FE,(slot>=655&&slot<=660)||(slot>=666&&slot<=669)||(slot>=676&&slot<=696)?1.0f:4.0f);}glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAX_LEVEL,(GLint)levels-1);
 for(l=0;l<levels;l++){uint32_t n,lw=w>>l?w>>l:1,lh=h>>l?h>>l:1;if(at+4>t->size)return 0;memcpy(&n,b+at,4);at+=4;if(at+n>t->size)return 0;if(fmt==GL_RGBA8||fmt==GL_SRGB8_ALPHA8){if(n!=(size_t)lw*lh*4u)return 0;glTexImage2D(GL_TEXTURE_2D,(GLint)l,fmt,(GLsizei)lw,(GLsizei)lh,0,GL_RGBA,GL_UNSIGNED_BYTE,b+at);}else glCompressedTexImage2D(GL_TEXTURE_2D,(GLint)l,fmt,(GLsizei)lw,(GLsizei)lh,0,(GLsizei)n,b+at);at+=n;total+=n;}
 glBindTexture(GL_TEXTURE_2D,0);if(glGetError()!=GL_NO_ERROR){LOGE("Stream texture upload error");return 0;}
 t->w=w;t->h=h;t->gpu_bytes=total;s->gpu_bytes+=total;return 1;}
static GLuint one_pixel(const uint8_t *rgba){GLuint t;glGenTextures(1,&t);glBindTexture(GL_TEXTURE_2D,t);glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA8,1,1,0,GL_RGBA,GL_UNSIGNED_BYTE,rgba);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST);glBindTexture(GL_TEXTURE_2D,0);return t;}
void oa_stream_update(oa_stream *s,const float eye[3]){
 unsigned i;int l;size_t budget=UPLOAD_BUDGET;int tex_budget=TEXTURE_BUDGET;int64_t t0=now_ns(),now=t0;float dt=s->last_update?(float)(now-s->last_update)*1e-9f:0;float ms;s->last_update=now;
 pthread_mutex_lock(&s->lock);memcpy(s->last_eye,eye,12);
 for(i=0;i<s->texture_count;i++)if(s->textures[i].state==STATE_GPU)s->textures[i].idle+=dt;
 /* Requests */
 for(i=0;i<s->cell_count;i++){cell *c=s->cells+i;float dx=eye[0]<c->base_lo[0]?c->base_lo[0]-eye[0]:eye[0]>c->base_hi[0]?eye[0]-c->base_hi[0]:0,dy=eye[1]<c->base_lo[1]?c->base_lo[1]-eye[1]:eye[1]>c->base_hi[1]?eye[1]-c->base_hi[1]:0,d=sqrtf(dx*dx+dy*dy);int want=oa_stream_want(d,s->far_range);c->distance=d;
  {lod_data *g=c->lod+GRASS;if(g->triangles&&d<OA_STREAM_GRASS){if(g->state==STATE_NONE){g->state=STATE_QUEUED;push_job(s,0,(int)i,GRASS);}}else if(d>OA_STREAM_GRASS+HYSTERESIS&&g->state!=STATE_NONE){if(g->state==STATE_GPU)free_gpu(s,g);else if(g->state==STATE_CPU){s->cpu_bytes-=g->size;free(g->bytes);g->bytes=NULL;g->size=0;}g->state=STATE_NONE;}}
  {lod_data *g=c->lod+TREE_LEAF;if(oa_stream_leaf_native&&g->triangles&&want>=0){if(g->state==STATE_NONE){g->state=STATE_QUEUED;push_job(s,0,(int)i,TREE_LEAF);}}else if((!oa_stream_leaf_native||d>s->far_range+HYSTERESIS)&&g->state!=STATE_NONE){if(g->state==STATE_GPU)free_gpu(s,g);else if(g->state==STATE_CPU){s->cpu_bytes-=g->size;free(g->bytes);g->bytes=NULL;g->size=0;}g->state=STATE_NONE;}}
  {lod_data *g=c->lod+REGION;if(oa_stream_region&&g->triangles&&want>=0){if(g->state==STATE_NONE){g->state=STATE_QUEUED;push_job(s,0,(int)i,REGION);}}else if((!oa_stream_region||d>s->far_range+HYSTERESIS)&&g->state!=STATE_NONE){if(g->state==STATE_GPU)free_gpu(s,g);else if(g->state==STATE_CPU){s->cpu_bytes-=g->size;free(g->bytes);g->bytes=NULL;g->size=0;}g->state=STATE_NONE;}}
  if(want>=0&&c->lod[want].state==STATE_NONE&&c->lod[want].triangles){c->lod[want].state=STATE_QUEUED;push_job(s,0,(int)i,want);}
  if(oa_stream_leaf_lod_override==0&&want>=0&&c->lod[0].state==STATE_NONE&&c->lod[0].triangles){c->lod[0].state=STATE_QUEUED;push_job(s,0,(int)i,0);}
  /* Show the wanted level when ready, else keep whatever level is ready. */
  {int show=-1;if(want>=0){if(c->lod[want].state==STATE_GPU)show=want;else{for(l=want+1;l<GRASS&&show<0;l++)if(c->lod[l].state==STATE_GPU)show=l;for(l=want-1;l>=0&&show<0;l--)if(c->lod[l].state==STATE_GPU)show=l;}}c->shown=show;}
  /* Release levels no longer needed once the wanted one shows. */
  for(l=0;l<GRASS;l++){lod_data *q=c->lod+l;int keep=(oa_stream_leaf_lod_override==0&&want>=0&&l==0)||l==want||(l==c->shown)||oa_stream_want(d>HYSTERESIS?d-HYSTERESIS:0,s->far_range)==l;if(keep||q->state==STATE_NONE)continue;
   if(q->state==STATE_GPU){free_gpu(s,q);q->state=STATE_NONE;}else if(q->state==STATE_CPU){s->cpu_bytes-=q->size;free(q->bytes);q->bytes=NULL;q->size=0;q->state=STATE_NONE;}else if(q->state==STATE_QUEUED)q->state=STATE_NONE;}
  /* Textures for anything loaded or in use stay awake. */
  for(l=0;l<LODS;l++){lod_data *q=c->lod+l;unsigned k;if(q->state!=STATE_GPU)continue;for(k=0;k<q->draw_count;k++){const material *mt=s->materials+lod_draw(q,k)->texture;int e;for(e=0;e<(mt->terrain_set>=0||mt->native_uv[0]>0?8:6);e++){uint32_t t=mt->terrain_set>=0?mt->terrain_t[e]:mt->native_uv[0]>0?mt->native_t[e]:mt->t[e];if(t==0xffffffffu)continue;s->textures[t].idle=0;if(s->textures[t].state==STATE_NONE){s->textures[t].state=STATE_QUEUED;push_job(s,1,(int)t,0);}}}}
 }
 /* Uploads, nearest first, within budget. */
 {int moved=1;while(moved&&budget>0){unsigned bi=s->cell_count;int bl=-1;float near=1e30f;moved=0;for(i=0;i<s->cell_count;i++)for(l=0;l<LODS;l++)if(s->cells[i].lod[l].state==STATE_CPU&&s->cells[i].distance<near){near=s->cells[i].distance;bi=i;bl=l;}
   if(bl>=0){lod_data *q=s->cells[bi].lod+bl;if(q->size>budget&&budget!=UPLOAD_BUDGET)break;if(upload_cell(s,s->cells+bi,q))q->state=STATE_GPU;else q->state=STATE_NONE;budget=q->size>budget?0:budget-q->size;s->cpu_bytes-=q->size;free(q->bytes);q->bytes=NULL;q->size=0;moved=1;}}}
 for(i=0;i<s->texture_count&&tex_budget>0;i++){texture_slot *t=s->textures+i;if(t->state==STATE_CPU){if(upload_texture(s,t))t->state=STATE_GPU;else{t->state=STATE_NONE;LOGE("Stream texture invalid %u",i);}s->cpu_bytes-=t->size;free(t->bytes);t->bytes=NULL;t->size=0;tex_budget--;}
  else if(t->state==STATE_GPU&&t->idle>TEXTURE_LINGER){glDeleteTextures(1,&t->id);t->id=0;s->gpu_bytes-=t->gpu_bytes;t->gpu_bytes=0;t->state=STATE_NONE;}}
 pthread_mutex_unlock(&s->lock);
 ms=(float)(now_ns()-t0)*1e-6f;s->upload_ms=ms;if(ms>s->upload_worst)s->upload_worst=ms;
}
static int cell_visible(const float p[6][4],const cell *c){int i;for(i=0;i<6;i++){float x=p[i][0]>0?c->hi[0]:c->lo[0],y=p[i][1]>0?c->hi[1]:c->lo[1],z=p[i][2]>0?c->hi[2]:c->lo[2];if(p[i][0]*x+p[i][1]*y+p[i][2]*z+p[i][3]<0)return 0;}return 1;}
static int lod_ready(const oa_stream *s,const lod_data *q){unsigned d;for(d=0;d<q->draw_count;d++){const material *mt=s->materials+lod_draw(q,d)->texture;int e;for(e=0;e<(mt->terrain_set>=0||mt->native_uv[0]>0?8:6);e++){uint32_t t=mt->terrain_set>=0?mt->terrain_t[e]:mt->native_uv[0]>0?mt->native_t[e]:mt->t[e];if(t!=0xffffffffu&&(t>=s->texture_count||s->textures[t].state!=STATE_GPU))return 0;}}return 1;}
/* Binds a material. In the shadow pass (terrain<0) only the base texture matters. */
static void bind_material(oa_stream *s,uint32_t index,int has_texture,int terrain){const material *mt=s->materials+index;int e;
 if(terrain<0){uint32_t t=mt->t[0];glUniform1i(has_texture,t!=0xffffffffu);glBindTexture(GL_TEXTURE_2D,t!=0xffffffffu?s->textures[t].id:0);return;}
 glUniform1i(terrain,(int)(mt->flags&1));
 for(e=5;e>=0;e--){uint32_t t=mt->t[e];GLuint id=t!=0xffffffffu?s->textures[t].id:((mt->flags&1)?(e>=3?s->flat_normal:s->flat_black):(e==1?s->flat_normal:s->flat_black));if(!(mt->flags&1)&&e>=3)continue;glActiveTexture(GL_TEXTURE0+(unsigned)e);glBindTexture(GL_TEXTURE_2D,id);}}
void oa_stream_draw(oa_stream *s,const float m[16],int has_texture,int terrain,const float center[3],float radius){
 float planes[6][4];unsigned i;int j,k;uint32_t bound=0xfffffffeu;unsigned cells=0,draws=0,tris=0;
 if(!s->flat_normal){const uint8_t n[4]={128,128,255,255},z[4]={0,0,0,255};s->flat_normal=one_pixel(n);s->flat_black=one_pixel(z);}
 for(j=0;j<3;j++)for(k=0;k<4;k++){planes[j*2][k]=m[k*4+3]+m[k*4+j];planes[j*2+1][k]=m[k*4+3]-m[k*4+j];}
 glActiveTexture(GL_TEXTURE0);
 for(i=0;i<s->cell_count;i++){const cell *c=s->cells+i;const lod_data *q;unsigned d;int pass;if(c->shown<0)continue;if(!cell_visible(planes,c))continue;
  if(radius>0&&(c->hi[0]<center[0]-radius||c->lo[0]>center[0]+radius||c->hi[1]<center[1]-radius||c->lo[1]>center[1]+radius))continue;
  cells++;
  for(pass=0;pass<2;pass++){q=c->lod+(pass?GRASS:c->shown);if(q->state!=STATE_GPU||(pass&&(radius>0||c->distance>OA_STREAM_GRASS))||!lod_ready(s,q))continue;
   glBindVertexArray(q->array);
   for(d=0;d<q->draw_count;d++){const draw_rec *r=lod_draw(q,d);if(s->materials[r->texture].flags&(56u|0x40000000u))continue;if(r->texture!=bound){bind_material(s,r->texture,has_texture,terrain);bound=r->texture;}glDrawElements(GL_TRIANGLES,(GLsizei)r->count,GL_UNSIGNED_INT,(void*)(uintptr_t)((size_t)r->first*4u));draws++;tris+=r->count/3;}}}
 glBindVertexArray(0);glActiveTexture(GL_TEXTURE0);glBindTexture(GL_TEXTURE_2D,0);if(has_texture>=0)glUniform1i(has_texture,0);
 if(radius<=0){s->drawn_cells=cells;s->drawn_draws=draws;s->drawn_tris=tris;}
}
/* The world in the order the tiler wants: nearest first, solid buildings before the costly ground, and cutouts last so they cannot switch off early depth for what is solid. */
typedef struct visible_cell{float distance;unsigned index;}visible_cell;
static int visible_order(const void *a,const void *b){float x=((const visible_cell*)a)->distance,y=((const visible_cell*)b)->distance;return x<y?-1:x>y;}
static void bind_world(oa_stream *s,uint32_t index,int phase){const material *mt=s->materials+index;int e,native=mt->native_uv[0]>0&&phase!=1&&phase<4,top=native?7:phase==1||phase==4||phase==5?5:phase==3||phase==6?0:2;for(e=top;e>=0;e--){uint32_t t=native?mt->native_t[e]:mt->t[e];GLuint id=t!=0xffffffffu?s->textures[t].id:(phase==1?(e>=3?s->flat_normal:s->flat_black):(e==1?s->flat_normal:s->flat_black));glActiveTexture(GL_TEXTURE0+(unsigned)e);glBindTexture(GL_TEXTURE_2D,id);}}
int oa_stream_hide;int oa_stream_leaf_lod_override=-1;int oa_stream_leaf_native=1;int oa_stream_region=1;
static int terrain_maps(oa_stream *s){
 if(s->terrain_paint&&s->terrain_selector)return 1;if(s->terrain_maps_attempted||!s->terrain_sets||s->terrain_height_blend<=0)return 0;s->terrain_maps_attempted=1;
 {size_t n=0;uint8_t *b=asset_read(s->assets,"world/terrain_paint.bin",&n);uint32_t fmt=0,w=0,h=0,levels=0,bytes=0;
  if(b&&n>=24){memcpy(&fmt,b+4,4);memcpy(&w,b+8,4);memcpy(&h,b+12,4);memcpy(&levels,b+16,4);memcpy(&bytes,b+20,4);}
  if(!b||n<24||memcmp(b,"OATX",4)||fmt!=GL_RGBA8||w!=4097||h!=4097||levels!=1||bytes!=4097u*4097u*4u||n!=24+(size_t)bytes){free(b);LOGE("Native terrain paint atlas invalid");return 0;}
  glGenTextures(1,&s->terrain_paint);glBindTexture(GL_TEXTURE_2D,s->terrain_paint);glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA8,(GLsizei)w,(GLsizei)h,0,GL_RGBA,GL_UNSIGNED_BYTE,b+24);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_LINEAR);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_LINEAR);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,GL_CLAMP_TO_EDGE);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,GL_CLAMP_TO_EDGE);s->terrain_gpu_bytes=bytes;free(b);}
 {size_t n=0;uint8_t *b=asset_read(s->assets,"world/terrain_selector.bin",&n);if(!b||n!=4096u*4096u){free(b);glDeleteTextures(1,&s->terrain_paint);s->terrain_paint=0;s->terrain_gpu_bytes=0;LOGE("Native terrain selector invalid");return 0;}
  glGenTextures(1,&s->terrain_selector);glBindTexture(GL_TEXTURE_2D,s->terrain_selector);glPixelStorei(GL_UNPACK_ALIGNMENT,1);glTexImage2D(GL_TEXTURE_2D,0,GL_R8UI,4096,4096,0,GL_RED_INTEGER,GL_UNSIGNED_BYTE,b);glPixelStorei(GL_UNPACK_ALIGNMENT,4);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,GL_CLAMP_TO_EDGE);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,GL_CLAMP_TO_EDGE);s->terrain_gpu_bytes+=n;free(b);}
 s->gpu_bytes+=s->terrain_gpu_bytes;glBindTexture(GL_TEXTURE_2D,0);LOGI("Native terrain atlas ready paint=4097 selector=4096 mask=%u height_blend=%.6f gpu_mb=%.1f",s->terrain_sets,s->terrain_height_blend,(float)s->terrain_gpu_bytes/1048576.f);return 1;
}
void oa_stream_draw_world_range(oa_stream *s,const float m[16],const GLuint program[7],unsigned features,int first_phase,int last_phase,int reset_stats){
 float planes[6][4];unsigned i,count=0,draws=0,tris=0,native_draws=0,terrain_draws=0,forced_leaf_cells=0,native_leaf_cells=0,region_cells=0,region_draws=0,region_lod_culled=0;int j,k,phase;GLint old_front=GL_CCW;GLboolean cull_default=glIsEnabled(GL_CULL_FACE);visible_cell *vis=(visible_cell*)malloc(sizeof(visible_cell)*s->cell_count);
 if(!vis)return;glGetIntegerv(GL_FRONT_FACE,&old_front);if(m[3]*m[3]+m[7]*m[7]+m[11]*m[11]>1e-12f){float hand=(m[4]*m[9]-m[8]*m[5])*m[3]+(m[8]*m[1]-m[0]*m[9])*m[7]+(m[0]*m[5]-m[4]*m[1])*m[11];glFrontFace(hand>0?GL_CW:GL_CCW);}glCullFace(GL_BACK);
 if(!s->flat_normal){const uint8_t n[4]={128,128,255,255},z[4]={0,0,0,255};s->flat_normal=one_pixel(n);s->flat_black=one_pixel(z);}
 for(j=0;j<3;j++)for(k=0;k<4;k++){planes[j*2][k]=m[k*4+3]+m[k*4+j];planes[j*2+1][k]=m[k*4+3]-m[k*4+j];}
 for(i=0;i<s->cell_count;i++){const cell *c=s->cells+i;if((c->shown>=0||(oa_stream_region&&c->lod[REGION].state==STATE_GPU))&&cell_visible(planes,c)){vis[count].distance=c->distance;vis[count].index=i;count++;}}
 qsort(vis,count,sizeof(visible_cell),visible_order);
 for(phase=first_phase;phase<=last_phase;phase++){uint32_t bound=0xfffffffeu;if(oa_stream_hide&(1<<phase)){if(phase==4){glEnable(GL_BLEND);glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA);glDepthMask(GL_FALSE);}continue;}GLint cut=glGetUniformLocation(program[phase],"alpha_cut"),water=phase==4||phase==5?glGetUniformLocation(program[phase],"water[0]"):-1;glUseProgram(program[phase]);
  {GLint sky=glGetUniformLocation(program[phase],"sky_light"),amb=glGetUniformLocation(program[phase],"ambient_scales");if(sky>=0)glUniform4fv(sky,1,s->native_sky);if(amb>=0)glUniform2fv(amb,1,s->native_ambient);}
  if(phase==1){int ready=(features&32u)?terrain_maps(s):0;glUniform1i(glGetUniformLocation(program[phase],"terrain_map_ready"),ready);glUniform1i(glGetUniformLocation(program[phase],"terrain_supported_sets"),(int)s->terrain_sets);glUniform1f(glGetUniformLocation(program[phase],"terrain_height_blend"),s->terrain_height_blend);glUniform1i(glGetUniformLocation(program[phase],"terrain_paint"),11);glUniform1i(glGetUniformLocation(program[phase],"terrain_selector"),12);glActiveTexture(GL_TEXTURE11);glBindTexture(GL_TEXTURE_2D,s->terrain_paint);glActiveTexture(GL_TEXTURE12);glBindTexture(GL_TEXTURE_2D,s->terrain_selector);}
  /* Blended surfaces go last, farthest first, and leave depth alone. */
  if(phase==4){glEnable(GL_BLEND);glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA);glDepthMask(GL_FALSE);}
  for(i=0;i<count;i++){const cell *c=s->cells+vis[phase>=4?count-1-i:i].index;int leaf_pass,leaf_ready=phase==2&&oa_stream_leaf_native&&(features&128u)&&s->leaf_materials&&c->lod[TREE_LEAF].state==STATE_GPU&&lod_ready(s,c->lod+TREE_LEAF);for(leaf_pass=0;leaf_pass<3;leaf_pass++){int region_pass=leaf_pass==2;const lod_data *q;unsigned d;int bound_array=0;if((leaf_pass==0&&c->shown<0)||(leaf_pass==1&&!leaf_ready)||(region_pass&&(!oa_stream_region||!s->region_index_cells)))continue;q=c->lod+(region_pass?REGION:leaf_pass==1?TREE_LEAF:phase==3?GRASS:c->shown);if(leaf_pass==1)native_leaf_cells++;else if(!region_pass&&phase==2&&oa_stream_leaf_lod_override==0&&c->lod[0].state==STATE_GPU&&lod_ready(s,c->lod)){q=c->lod;forced_leaf_cells++;}if(q->state!=STATE_GPU||(!region_pass&&phase==3&&c->distance>OA_STREAM_GRASS)||!lod_ready(s,q))continue;if(region_pass&&phase==0)region_cells++;
   for(d=0;d<q->draw_count;d++){const draw_rec *r=lod_draw(q,d);if(leaf_pass==0&&leaf_ready&&s->leaf_materials[r->texture])continue;if(region_pass&&q->ranges){const region_range *rr=q->ranges+d;float dx=s->last_eye[0]-rr->sphere[0],dy=s->last_eye[1]-rr->sphere[1],dz=s->last_eye[2]-rr->sphere[2],scale=rr->distance_scale>0?rr->distance_scale:s->region_distance_scale,dist2=(dx*dx+dy*dy+dz*dz)*scale*scale;if(dist2<rr->min_sq||dist2>=rr->max_sq){region_lod_culled++;continue;}}unsigned f=s->materials[r->texture].flags;int kind=phase==3?3:(f&8)?4:(f&16)?5:(f&32)?6:(f&1)?1:(f&2)?2:0;if(kind!=phase)continue;if((f&0x40000000u)&&(!(features&32u)||!s->terrain_paint||!s->terrain_selector))continue;if(!bound_array){glBindVertexArray(q->array);glUniform1i(glGetUniformLocation(program[phase],"geometry_kind"),q->geometry_kind);if(phase==1){unsigned td,mask=0;for(td=0;td<q->draw_count;td++){int set=s->materials[lod_draw(q,td)->texture].terrain_set;if(set>=0&&set<5)mask|=1u<<set;}glUniform1i(glGetUniformLocation(program[phase],"terrain_supported_sets"),(int)mask);}bound_array=1;}/* Native MATS bits:0x20000000 alphaMap6.GREEN,0x10000000 BACK,0x08000000 NONE. */if(phase==3||(f&0x08000000u)||s->materials[r->texture].native_family==6)glDisable(GL_CULL_FACE);else if((f&0x10000000u)||cull_default)glEnable(GL_CULL_FACE);else glDisable(GL_CULL_FACE);if(r->texture!=bound){material *native=s->materials+r->texture;GLint family=glGetUniformLocation(program[phase],"material_family"),color=glGetUniformLocation(program[phase],"material_color"),spec=glGetUniformLocation(program[phase],"material_specular");
    if(phase==1){GLint set=glGetUniformLocation(program[phase],"terrain_draw_set"),uv=glGetUniformLocation(program[phase],"terrain_uv_scales");glUniform1i(set,native->terrain_set);glUniform4fv(glGetUniformLocation(program[phase],"terrain_specular_levels"),1,native->terrain_levels);glUniform4fv(glGetUniformLocation(program[phase],"terrain_specular_powers"),1,native->terrain_powers);if(uv>=0)glUniform4fv(uv,1,native->terrain_uv);}
    glUniform1i(glGetUniformLocation(program[phase],"native_alpha_slot"),(f&0x20000000u)?6:0);if(family>=0)glUniform1i(family,phase==1&&native->terrain_set>=0?7:s->native_lighting_ready?(int)native->native_family:0);if(color>=0)glUniform4fv(color,1,native->native_color);glUniform4fv(glGetUniformLocation(program[phase],"material_tiling"),1,native->native_uv);if(spec>=0){if(phase==1&&native->terrain_set>=0)glUniform4f(spec,1,1,0,0);else glUniform4fv(spec,1,native->native_specular);}bind_world(s,r->texture,phase);if(phase==1&&native->terrain_set>=0){unsigned j;for(j=0;j<8;j++){uint32_t tid=native->terrain_t[j];glActiveTexture(GL_TEXTURE0+j);glBindTexture(GL_TEXTURE_2D,tid<s->texture_count?s->textures[tid].id:0);}}if(cut>=0)glUniform1f(cut,(float)(f>>8&255u)/255.f);if(water>=0&&s->water)glUniform1fv(water,11,s->water+(size_t)r->texture*11u);bound=r->texture;}glDrawElements(GL_TRIANGLES,(GLsizei)r->count,GL_UNSIGNED_INT,(void*)(uintptr_t)((size_t)r->first*4u));draws++;tris+=r->count/3;if(region_pass)region_draws++;if((features&16u)&&s->native_lighting_ready&&s->materials[r->texture].native_family>0&&phase<=3)native_draws++;if(phase==1&&s->materials[r->texture].terrain_set>=0)terrain_draws++;}}}}
 glDisable(GL_BLEND);glDepthMask(GL_TRUE);glBindVertexArray(0);glActiveTexture(GL_TEXTURE0);glBindTexture(GL_TEXTURE_2D,0);s->drawn_cells=count;s->drawn_draws=draws+(reset_stats?0:s->drawn_draws);s->drawn_tris=tris+(reset_stats?0:s->drawn_tris);s->drawn_native=native_draws+(reset_stats?0:s->drawn_native);s->drawn_terrain=terrain_draws+(reset_stats?0:s->drawn_terrain);s->forced_leaf_cells=forced_leaf_cells+(reset_stats?0:s->forced_leaf_cells);s->native_leaf_cells=native_leaf_cells+(reset_stats?0:s->native_leaf_cells);s->region_cells=region_cells;s->region_draws=region_draws+(reset_stats?0:s->region_draws);s->region_lod_culled=region_lod_culled+(reset_stats?0:s->region_lod_culled);glFrontFace((GLenum)old_front);if(cull_default)glEnable(GL_CULL_FACE);else glDisable(GL_CULL_FACE);free(vis);
}
void oa_stream_gpu_close(oa_stream *s){unsigned i;int l;if(!s)return;pthread_mutex_lock(&s->lock);if(s->terrain_paint)glDeleteTextures(1,&s->terrain_paint);if(s->terrain_selector)glDeleteTextures(1,&s->terrain_selector);s->terrain_paint=s->terrain_selector=0;s->terrain_maps_attempted=0;s->gpu_bytes-=s->terrain_gpu_bytes;s->terrain_gpu_bytes=0;if(s->flat_normal){glDeleteTextures(1,&s->flat_normal);glDeleteTextures(1,&s->flat_black);s->flat_normal=s->flat_black=0;}for(i=0;i<s->cell_count;i++){s->cells[i].shown=-1;for(l=0;l<LODS;l++){lod_data *q=s->cells[i].lod+l;if(q->state==STATE_GPU){free_gpu(s,q);q->state=STATE_NONE;}}}for(i=0;i<s->texture_count;i++){texture_slot *t=s->textures+i;if(t->state==STATE_GPU){glDeleteTextures(1,&t->id);t->id=0;s->gpu_bytes-=t->gpu_bytes;t->gpu_bytes=0;t->state=STATE_NONE;}}pthread_mutex_unlock(&s->lock);}
void oa_stream_get_stats(oa_stream *s,oa_stream_stats *o){unsigned i;pthread_mutex_lock(&s->lock);o->cells=s->cell_count;o->queued=s->job_count;o->cells_drawn=s->drawn_cells;o->draws=s->drawn_draws;o->triangles=s->drawn_tris;o->native_material_draws=s->drawn_native;o->native_terrain_draws=s->drawn_terrain;o->forced_leaf_cells=s->forced_leaf_cells;o->native_leaf_cells=s->native_leaf_cells;o->region_cells=s->region_cells;o->region_draws=s->region_draws;o->region_lod_culled=s->region_lod_culled;o->gpu_mb=(float)s->gpu_bytes/1048576.f;o->cpu_mb=(float)s->cpu_bytes/1048576.f;o->upload_ms=s->upload_ms;o->upload_worst_ms=s->upload_worst;s->upload_worst=0;o->textures=0;for(i=0;i<s->texture_count;i++)if(s->textures[i].state==STATE_GPU)o->textures++;pthread_mutex_unlock(&s->lock);}

int oa_stream_native_post(const oa_stream *s,float out[4]){if(!s||!s->native_post_ready)return 0;memcpy(out,s->native_post,16);return 1;}

void oa_stream_draw_world(oa_stream *s,const float m[16],const GLuint programs[7],unsigned f){oa_stream_draw_world_range(s,m,programs,f,0,6,1);}
