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
enum{LODS=4,GRASS=3,MAX_DRAWS=128,STATE_NONE=0,STATE_QUEUED,STATE_CPU,STATE_GPU,MAX_JOBS=4096,UPLOAD_BUDGET=6*1024*1024,TEXTURE_BUDGET=2,VERTEX_BYTES=28};
#define HYSTERESIS 3200.0f
#define TEXTURE_LINGER 5.0f
typedef struct draw_rec{uint32_t texture,first,count;}draw_rec;
typedef struct lod_data{int state;uint8_t *bytes;size_t size;GLuint array,vertex,index;uint32_t draw_count;draw_rec draws[MAX_DRAWS];size_t gpu_bytes;uint32_t triangles;}lod_data;
typedef struct cell{int ix,iy;float lo[3],hi[3],distance;lod_data lod[LODS];int shown;}cell;
typedef struct texture_slot{int state;uint8_t *bytes;size_t size;uint32_t w,h;GLuint id;float idle;size_t gpu_bytes;}texture_slot;
typedef struct material{uint32_t flags,t[6];}material;
typedef struct job{int kind,index,lod;}job;
struct oa_stream{
 AAssetManager *assets;pthread_t thread;pthread_mutex_t lock;pthread_cond_t wake,done;int stop,started;
 float cell_size;unsigned cell_count,texture_count,material_count;cell *cells;texture_slot *textures;material *materials;float *water;GLuint flat_normal,flat_black;
 job jobs[MAX_JOBS];unsigned job_count;
 /* Collision requests are latest-wins: only the current player cell matters. */
 int want_x,want_y,want_pending,have_x,have_y,built_x,built_y;opem_collision_world *built;int building;char error[192];
 float far_range,last_eye[3];int64_t last_update;
 size_t cpu_bytes;size_t gpu_bytes;
 float upload_ms,upload_worst;unsigned drawn_cells,drawn_draws,drawn_tris;
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
   if(j.kind==0&&j.lod==GRASS)snprintf(name,sizeof(name),"world/g%d_%d.bin",s->cells[j.index].ix,s->cells[j.index].iy);else if(j.kind==0)snprintf(name,sizeof(name),"world/c%d_%d_%d.bin",s->cells[j.index].ix,s->cells[j.index].iy,j.lod);else snprintf(name,sizeof(name),"world/t%d.bin",j.index);
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
  s->materials=(material*)malloc(sizeof(material)*(mc?mc:1));s->material_count=mc;memcpy(s->materials,mb+4,(size_t)mc*28u);free(mb);for(k=0;k<mc;k++){int q;for(q=0;q<6;q++)if(s->materials[k].t[q]!=0xffffffffu&&s->materials[k].t[q]+1>top)top=s->materials[k].t[q]+1;}textures=top;}
 s->texture_count=textures;s->textures=(texture_slot*)calloc(textures?textures:1,sizeof(texture_slot));
 if(!s->cells||!s->textures||!s->materials){free(b);free(s->cells);free(s->textures);free(s->materials);free(s);return NULL;}
 for(i=0;i<cells;i++){const uint8_t *r=b+20+i*48u;int32_t ix,iy;uint32_t t[4];cell *c=s->cells+i;memcpy(&ix,r,4);memcpy(&iy,r+4,4);memcpy(c->lo,r+8,12);memcpy(c->hi,r+20,12);memcpy(t,r+32,16);c->lod[GRASS].triangles=t[3];c->ix=ix;c->iy=iy;c->shown=-1;c->distance=1e30f;c->lod[0].triangles=t[0];c->lod[1].triangles=t[1];c->lod[2].triangles=t[2];}
 free(b);
 s->have_x=s->have_y=s->want_x=s->want_y=0x7fffffff;
 pthread_mutex_init(&s->lock,NULL);pthread_cond_init(&s->wake,NULL);pthread_cond_init(&s->done,NULL);
 if(pthread_create(&s->thread,NULL,worker,s)){LOGE("Stream thread failed");free(s->cells);free(s->textures);free(s);return NULL;}
 s->started=1;LOGI("Stream opened cells=%u textures=%u cell_size=%.0f",cells,textures,cell_size);return s;}
void oa_stream_set_far(oa_stream *s,float range){s->far_range=range;}
void oa_stream_close(oa_stream *s){unsigned i;int l;if(!s)return;pthread_mutex_lock(&s->lock);s->stop=1;pthread_cond_broadcast(&s->wake);pthread_mutex_unlock(&s->lock);if(s->started)pthread_join(s->thread,NULL);
 if(s->built)opem_collision_destroy(s->built);for(i=0;i<s->cell_count;i++)for(l=0;l<LODS;l++)free(s->cells[i].lod[l].bytes);for(i=0;i<s->texture_count;i++)free(s->textures[i].bytes);
 pthread_mutex_destroy(&s->lock);pthread_cond_destroy(&s->wake);pthread_cond_destroy(&s->done);free(s->water);free(s->cells);free(s->textures);free(s->materials);free(s);}
void oa_stream_bounds(const oa_stream *s,float center[3],float *radius){float lo[3]={1e30f,1e30f,1e30f},hi[3]={-1e30f,-1e30f,-1e30f};unsigned i;int k;double r=0;for(i=0;i<s->cell_count;i++)for(k=0;k<3;k++){if(s->cells[i].lo[k]<lo[k])lo[k]=s->cells[i].lo[k];if(s->cells[i].hi[k]>hi[k])hi[k]=s->cells[i].hi[k];}
 for(k=0;k<3;k++){double d=(double)hi[k]-lo[k];center[k]=(lo[k]+hi[k])*.5f;r+=d*d;}*radius=(float)(sqrt(r)*.5);}
opem_collision_world *oa_stream_collision_now(oa_stream *s,const float feet[3],char *error,size_t cap){int cx=(int)floorf(feet[0]/s->cell_size),cy=(int)floorf(feet[1]/s->cell_size);opem_collision_world *w=build_collision(s,cx,cy,error,cap);if(w){s->have_x=cx;s->have_y=cy;}return w;}
opem_collision_world *oa_stream_collision_poll(oa_stream *s,const float feet[3]){int cx=(int)floorf(feet[0]/s->cell_size),cy=(int)floorf(feet[1]/s->cell_size);opem_collision_world *w=NULL;pthread_mutex_lock(&s->lock);
 if(s->built){w=s->built;s->built=NULL;s->have_x=s->built_x;s->have_y=s->built_y;}
 else if(s->error[0]){LOGE("Stream collision: %s",s->error);s->error[0]=0;s->have_x=cx;s->have_y=cy;}
 if((cx!=s->have_x||cy!=s->have_y)&&!s->building&&(!s->want_pending||s->want_x!=cx||s->want_y!=cy)){s->want_x=cx;s->want_y=cy;s->want_pending=1;pthread_cond_broadcast(&s->wake);}
 pthread_mutex_unlock(&s->lock);return w;}
static void push_job(oa_stream *s,int kind,int index,int lod){if(s->job_count<MAX_JOBS){job j;j.kind=kind;j.index=index;j.lod=lod;s->jobs[s->job_count++]=j;pthread_cond_signal(&s->wake);}}
static void free_gpu(oa_stream *s,lod_data *l){if(l->array)glDeleteVertexArrays(1,&l->array);if(l->vertex)glDeleteBuffers(1,&l->vertex);if(l->index)glDeleteBuffers(1,&l->index);l->array=l->vertex=l->index=0;s->gpu_bytes-=l->gpu_bytes;l->gpu_bytes=0;l->draw_count=0;}
/* Builds GL objects from a loaded cell. A cell becomes drawable once its textures are ready. */
static int upload_cell(oa_stream *s,cell *c,lod_data *l){uint32_t v,i,d,k;const uint8_t *b=l->bytes;
 if(l->size<16||memcmp(b,"OAWC",4)){LOGE("Stream cell invalid");return 0;}memcpy(&v,b+4,4);memcpy(&i,b+8,4);memcpy(&d,b+12,4);
 if(d>MAX_DRAWS||l->size!=16+(size_t)d*12u+(size_t)v*VERTEX_BYTES+(size_t)i*4u){LOGE("Stream cell shape invalid %d %d",c->ix,c->iy);return 0;}
 memcpy(l->draws,b+16,d*12u);l->draw_count=d;
 for(k=0;k<d;k++)if(l->draws[k].texture>=s->material_count)return 0;
 glGenVertexArrays(1,&l->array);glGenBuffers(1,&l->vertex);glGenBuffers(1,&l->index);glBindVertexArray(l->array);
 glBindBuffer(GL_ARRAY_BUFFER,l->vertex);glBufferData(GL_ARRAY_BUFFER,(GLsizeiptr)((size_t)v*VERTEX_BYTES),b+16+d*12u,GL_STATIC_DRAW);
 glBindBuffer(GL_ELEMENT_ARRAY_BUFFER,l->index);glBufferData(GL_ELEMENT_ARRAY_BUFFER,(GLsizeiptr)((size_t)i*4u),b+16+d*12u+(size_t)v*VERTEX_BYTES,GL_STATIC_DRAW);
 glEnableVertexAttribArray(0);glVertexAttribPointer(0,3,GL_FLOAT,GL_FALSE,VERTEX_BYTES,(void*)0);
 glEnableVertexAttribArray(1);glVertexAttribPointer(1,4,GL_SHORT,GL_TRUE,VERTEX_BYTES,(void*)12);
 glDisableVertexAttribArray(2);glVertexAttrib3f(2,.8f,.8f,.8f);
 glEnableVertexAttribArray(3);glVertexAttribPointer(3,2,GL_FLOAT,GL_FALSE,VERTEX_BYTES,(void*)20);
 glBindVertexArray(0);glBindBuffer(GL_ARRAY_BUFFER,0);glBindBuffer(GL_ELEMENT_ARRAY_BUFFER,0);
 l->gpu_bytes=(size_t)v*VERTEX_BYTES+(size_t)i*4u;s->gpu_bytes+=l->gpu_bytes;return 1;}
static int upload_texture(oa_stream *s,texture_slot *t){uint32_t fmt,w,h,levels,l;size_t at=20,total=0;const uint8_t *b=t->bytes;
 if(t->size<20||memcmp(b,"OATX",4))return 0;memcpy(&fmt,b+4,4);memcpy(&w,b+8,4);memcpy(&h,b+12,4);memcpy(&levels,b+16,4);if(levels>16)return 0;
 glGenTextures(1,&t->id);glActiveTexture(GL_TEXTURE0);glBindTexture(GL_TEXTURE_2D,t->id);
 glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,GL_REPEAT);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,GL_REPEAT);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_LINEAR_MIPMAP_LINEAR);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_LINEAR);glTexParameterf(GL_TEXTURE_2D,0x84FE,4.0f);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAX_LEVEL,(GLint)levels-1);
 for(l=0;l<levels;l++){uint32_t n,lw=w>>l?w>>l:1,lh=h>>l?h>>l:1;if(at+4>t->size)return 0;memcpy(&n,b+at,4);at+=4;if(at+n>t->size)return 0;if(fmt==GL_RGBA8||fmt==GL_SRGB8_ALPHA8){if(n!=(size_t)lw*lh*4u)return 0;glTexImage2D(GL_TEXTURE_2D,(GLint)l,fmt,(GLsizei)lw,(GLsizei)lh,0,GL_RGBA,GL_UNSIGNED_BYTE,b+at);}else glCompressedTexImage2D(GL_TEXTURE_2D,(GLint)l,fmt,(GLsizei)lw,(GLsizei)lh,0,(GLsizei)n,b+at);at+=n;total+=n;}
 glBindTexture(GL_TEXTURE_2D,0);if(glGetError()!=GL_NO_ERROR){LOGE("Stream texture upload error");return 0;}
 t->w=w;t->h=h;t->gpu_bytes=total;s->gpu_bytes+=total;return 1;}
static GLuint one_pixel(const uint8_t *rgba){GLuint t;glGenTextures(1,&t);glBindTexture(GL_TEXTURE_2D,t);glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA8,1,1,0,GL_RGBA,GL_UNSIGNED_BYTE,rgba);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST);glBindTexture(GL_TEXTURE_2D,0);return t;}
void oa_stream_update(oa_stream *s,const float eye[3]){
 unsigned i;int l;size_t budget=UPLOAD_BUDGET;int tex_budget=TEXTURE_BUDGET;int64_t t0=now_ns(),now=t0;float dt=s->last_update?(float)(now-s->last_update)*1e-9f:0;float ms;s->last_update=now;
 pthread_mutex_lock(&s->lock);
 for(i=0;i<s->texture_count;i++)if(s->textures[i].state==STATE_GPU)s->textures[i].idle+=dt;
 /* Requests */
 for(i=0;i<s->cell_count;i++){cell *c=s->cells+i;float dx=eye[0]<c->lo[0]?c->lo[0]-eye[0]:eye[0]>c->hi[0]?eye[0]-c->hi[0]:0,dy=eye[1]<c->lo[1]?c->lo[1]-eye[1]:eye[1]>c->hi[1]?eye[1]-c->hi[1]:0,d=sqrtf(dx*dx+dy*dy);int want=oa_stream_want(d,s->far_range);c->distance=d;
  {lod_data *g=c->lod+GRASS;if(g->triangles&&d<OA_STREAM_GRASS){if(g->state==STATE_NONE){g->state=STATE_QUEUED;push_job(s,0,(int)i,GRASS);}}else if(d>OA_STREAM_GRASS+HYSTERESIS&&g->state!=STATE_NONE){if(g->state==STATE_GPU)free_gpu(s,g);else if(g->state==STATE_CPU){s->cpu_bytes-=g->size;free(g->bytes);g->bytes=NULL;g->size=0;}g->state=STATE_NONE;}}
  if(want>=0&&c->lod[want].state==STATE_NONE&&c->lod[want].triangles){c->lod[want].state=STATE_QUEUED;push_job(s,0,(int)i,want);}
  /* Show the wanted level when ready, else keep whatever level is ready. */
  {int show=-1;if(want>=0){if(c->lod[want].state==STATE_GPU)show=want;else{for(l=want+1;l<GRASS&&show<0;l++)if(c->lod[l].state==STATE_GPU)show=l;for(l=want-1;l>=0&&show<0;l--)if(c->lod[l].state==STATE_GPU)show=l;}}c->shown=show;}
  /* Release levels no longer needed once the wanted one shows. */
  for(l=0;l<GRASS;l++){lod_data *q=c->lod+l;int keep=l==want||(l==c->shown)||oa_stream_want(d>HYSTERESIS?d-HYSTERESIS:0,s->far_range)==l;if(keep||q->state==STATE_NONE)continue;
   if(q->state==STATE_GPU){free_gpu(s,q);q->state=STATE_NONE;}else if(q->state==STATE_CPU){s->cpu_bytes-=q->size;free(q->bytes);q->bytes=NULL;q->size=0;q->state=STATE_NONE;}else if(q->state==STATE_QUEUED)q->state=STATE_NONE;}
  /* Textures for anything loaded or in use stay awake. */
  for(l=0;l<LODS;l++){lod_data *q=c->lod+l;unsigned k;if(q->state!=STATE_GPU)continue;for(k=0;k<q->draw_count;k++){const material *mt=s->materials+q->draws[k].texture;int e;for(e=0;e<6;e++){uint32_t t=mt->t[e];if(t==0xffffffffu)continue;s->textures[t].idle=0;if(s->textures[t].state==STATE_NONE){s->textures[t].state=STATE_QUEUED;push_job(s,1,(int)t,0);}}}}
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
static int lod_ready(const oa_stream *s,const lod_data *q){unsigned d;for(d=0;d<q->draw_count;d++){const material *mt=s->materials+q->draws[d].texture;int e;for(e=0;e<6;e++)if(mt->t[e]!=0xffffffffu&&s->textures[mt->t[e]].state!=STATE_GPU)return 0;}return 1;}
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
   for(d=0;d<q->draw_count;d++){const draw_rec *r=q->draws+d;if(s->materials[r->texture].flags&56u)continue;if(r->texture!=bound){bind_material(s,r->texture,has_texture,terrain);bound=r->texture;}glDrawElements(GL_TRIANGLES,(GLsizei)r->count,GL_UNSIGNED_INT,(void*)(uintptr_t)((size_t)r->first*4u));draws++;tris+=r->count/3;}}}
 glBindVertexArray(0);glActiveTexture(GL_TEXTURE0);glBindTexture(GL_TEXTURE_2D,0);if(has_texture>=0)glUniform1i(has_texture,0);
 if(radius<=0){s->drawn_cells=cells;s->drawn_draws=draws;s->drawn_tris=tris;}
}
/* The world in the order the tiler wants: nearest first, solid buildings before the costly ground, and cutouts last so they cannot switch off early depth for what is solid. */
typedef struct visible_cell{float distance;unsigned index;}visible_cell;
static int visible_order(const void *a,const void *b){float x=((const visible_cell*)a)->distance,y=((const visible_cell*)b)->distance;return x<y?-1:x>y;}
static void bind_world(oa_stream *s,uint32_t index,int phase){const material *mt=s->materials+index;int e,top=phase==1||phase==4||phase==5?5:phase==3||phase==6?0:2;for(e=top;e>=0;e--){uint32_t t=mt->t[e];GLuint id=t!=0xffffffffu?s->textures[t].id:(phase==1?(e>=3?s->flat_normal:s->flat_black):(e==1?s->flat_normal:s->flat_black));glActiveTexture(GL_TEXTURE0+(unsigned)e);glBindTexture(GL_TEXTURE_2D,id);}}
int oa_stream_hide;
void oa_stream_draw_world(oa_stream *s,const float m[16],const GLuint program[7]){
 float planes[6][4];unsigned i,count=0,draws=0,tris=0;int j,k,phase;visible_cell *vis=(visible_cell*)malloc(sizeof(visible_cell)*s->cell_count);
 if(!vis)return;
 if(!s->flat_normal){const uint8_t n[4]={128,128,255,255},z[4]={0,0,0,255};s->flat_normal=one_pixel(n);s->flat_black=one_pixel(z);}
 for(j=0;j<3;j++)for(k=0;k<4;k++){planes[j*2][k]=m[k*4+3]+m[k*4+j];planes[j*2+1][k]=m[k*4+3]-m[k*4+j];}
 for(i=0;i<s->cell_count;i++){const cell *c=s->cells+i;if(c->shown>=0&&cell_visible(planes,c)){vis[count].distance=c->distance;vis[count].index=i;count++;}}
 qsort(vis,count,sizeof(visible_cell),visible_order);
 for(phase=0;phase<7;phase++){uint32_t bound=0xfffffffeu;if(oa_stream_hide&(1<<phase)){if(phase==4){glEnable(GL_BLEND);glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA);glDepthMask(GL_FALSE);}continue;}GLint cut=glGetUniformLocation(program[phase],"alpha_cut"),water=phase==4||phase==5?glGetUniformLocation(program[phase],"water[0]"):-1;glUseProgram(program[phase]);
  /* Blended surfaces go last, farthest first, and leave depth alone. */
  if(phase==4){glEnable(GL_BLEND);glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA);glDepthMask(GL_FALSE);}
  for(i=0;i<count;i++){const cell *c=s->cells+vis[phase>=4?count-1-i:i].index;const lod_data *q=c->lod+(phase==3?GRASS:c->shown);unsigned d;int bound_array=0;if(q->state!=STATE_GPU||(phase==3&&c->distance>OA_STREAM_GRASS)||!lod_ready(s,q))continue;
   for(d=0;d<q->draw_count;d++){const draw_rec *r=q->draws+d;unsigned f=s->materials[r->texture].flags;int kind=phase==3?3:(f&8)?4:(f&16)?5:(f&32)?6:(f&1)?1:(f&2)?2:0;if(kind!=phase)continue;if(!bound_array){glBindVertexArray(q->array);bound_array=1;}if(r->texture!=bound){bind_world(s,r->texture,phase);if(cut>=0)glUniform1f(cut,(float)(f>>8&255u)/255.f);if(water>=0&&s->water)glUniform1fv(water,11,s->water+(size_t)r->texture*11u);bound=r->texture;}glDrawElements(GL_TRIANGLES,(GLsizei)r->count,GL_UNSIGNED_INT,(void*)(uintptr_t)((size_t)r->first*4u));draws++;tris+=r->count/3;}}}
 glDisable(GL_BLEND);glDepthMask(GL_TRUE);glBindVertexArray(0);glActiveTexture(GL_TEXTURE0);glBindTexture(GL_TEXTURE_2D,0);s->drawn_cells=count;s->drawn_draws=draws;s->drawn_tris=tris;free(vis);
}
void oa_stream_gpu_close(oa_stream *s){unsigned i;int l;if(!s)return;pthread_mutex_lock(&s->lock);if(s->flat_normal){glDeleteTextures(1,&s->flat_normal);glDeleteTextures(1,&s->flat_black);s->flat_normal=s->flat_black=0;}for(i=0;i<s->cell_count;i++){s->cells[i].shown=-1;for(l=0;l<LODS;l++){lod_data *q=s->cells[i].lod+l;if(q->state==STATE_GPU){free_gpu(s,q);q->state=STATE_NONE;}}}for(i=0;i<s->texture_count;i++){texture_slot *t=s->textures+i;if(t->state==STATE_GPU){glDeleteTextures(1,&t->id);t->id=0;s->gpu_bytes-=t->gpu_bytes;t->gpu_bytes=0;t->state=STATE_NONE;}}pthread_mutex_unlock(&s->lock);}
void oa_stream_get_stats(oa_stream *s,oa_stream_stats *o){unsigned i;pthread_mutex_lock(&s->lock);o->cells=s->cell_count;o->queued=s->job_count;o->cells_drawn=s->drawn_cells;o->draws=s->drawn_draws;o->triangles=s->drawn_tris;o->gpu_mb=(float)s->gpu_bytes/1048576.f;o->cpu_mb=(float)s->cpu_bytes/1048576.f;o->upload_ms=s->upload_ms;o->upload_worst_ms=s->upload_worst;s->upload_worst=0;o->textures=0;for(i=0;i<s->texture_count;i++)if(s->textures[i].state==STATE_GPU)o->textures++;pthread_mutex_unlock(&s->lock);}
