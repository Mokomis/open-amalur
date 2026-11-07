#include "oa_character_appearance.h"
#include "oa_appearance.h"
#include "oa_cosmetic_material.h"
#include "oa_cosmetic_texture_bank.h"
#include <string.h>
#include "opening_sha256.h"
#include "oa_render_cache.h"
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <math.h>
#include <android/log.h>
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR,"OpemAmalurScene",__VA_ARGS__)
#define CA_MODELS 224
#define CA_SURFACES 128
typedef struct {uint32_t fab;unsigned char *bytes;size_t size;oa_am_model model;} ca_model;
typedef struct {unsigned component,assembly;oa_cm_surface gpu;oa_cm_material material;int beard;} ca_surface;
struct oa_ca_renderer {
 AAssetManager *manager;unsigned model_count;ca_model models[CA_MODELS];
 oa_cm_texture_bank textures;oa_cm_context material;GLuint character_cube,world_cube,black_cube,scene_character_cube,scene_world_cube,scene_probe;
 int gpu_ready;
};
struct oa_ca_actor {
 oa_ca_renderer *renderer;oa_creation_state profile;oa_cm_instance instance;
 oa_ap_plan plan;unsigned count;ca_surface surfaces[CA_SURFACES];
 float component_world[32*64*12];unsigned char *idle;size_t idle_size;
 unsigned idle_bones,idle_frames;float idle_fps;int posed;
};
typedef struct {const char *name;size_t size;const char *sha;} ca_asset;
#include "oa_character_appearance_assets.inc"
static uint32_t u32(const unsigned char *p){return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;}
static int error(char *e,size_t n,const char *s){if(e&&n)snprintf(e,n,"%s",s);return 0;}
static int asset_hash(const unsigned char *p,size_t n,const char *hex){
 unsigned char b[32];unsigned i;sha256(p,n,b);
 for(i=0;i<32;i++){unsigned v;if(sscanf(hex+2*i,"%2x",&v)!=1||v!=b[i])return 0;}return 1;
}
static int read_file(void *user,const char *name,unsigned char **out,size_t *size){
 oa_ca_renderer *r=(oa_ca_renderer*)user;AAsset *a;unsigned char *b;size_t n,at=0,i;const ca_asset *pin=NULL;
 *out=NULL;*size=0;if(!r||!r->manager||!name)return 0;
 a=AAssetManager_open(r->manager,name,AASSET_MODE_BUFFER);if(!a)return 0;n=(size_t)AAsset_getLength64(a);
 if(!n||n>64u*1024u*1024u){AAsset_close(a);return 0;}
 for(i=0;i<sizeof(ca_assets)/sizeof(*ca_assets);i++)if(!strcmp(ca_assets[i].name,name)){pin=ca_assets+i;break;}
 /* Texture-bank resources have their own generated source hashes. */
 if(!pin&&strncmp(name,"creator-bank/textures/",22)){AAsset_close(a);return 0;}
 if(pin&&n!=pin->size){AAsset_close(a);return 0;}
 b=(unsigned char*)malloc(n);if(!b){AAsset_close(a);return 0;}
 while(at<n){size_t want=n-at;int got;if(want>1048576u)want=1048576u;got=AAsset_read(a,b+at,want);if(got<=0)break;at+=(size_t)got;}
 AAsset_close(a);if(at!=n||(pin&&!asset_hash(b,n,pin->sha))){free(b);return 0;}*out=b;*size=n;return 1;
}
static int model_lookup(void *user,uint32_t fab,oa_am_model *out){
 oa_ca_renderer *r=(oa_ca_renderer*)user;unsigned i;ca_model x;char path[128];
 for(i=0;i<r->model_count;i++)if(r->models[i].fab==fab){*out=r->models[i].model;return 1;}
 if(r->model_count>=CA_MODELS)return 0;memset(&x,0,sizeof(x));
 snprintf(path,sizeof(path),"creator-bank/models/%u.oaam",fab);
 if(!read_file(r,path,&x.bytes,&x.size))return 0;
 if(!oa_am_open(&x.model,x.bytes,x.size)||x.model.fab!=fab){free(x.bytes);return 0;}
 x.fab=fab;r->models[r->model_count++]=x;*out=x.model;return 1;
}
oa_ca_renderer *oa_ca_renderer_create(AAssetManager *m){
 oa_ca_renderer *r;if(!m)return NULL;r=(oa_ca_renderer*)calloc(1,sizeof(*r));if(r)r->manager=m;return r;
}
static GLuint load_cube(oa_ca_renderer *r,const char *name){
 unsigned char *b=NULL;size_t n=0;GLuint tex=0;unsigned f;
 if(!read_file(r,name,&b,&n)||n!=1536){free(b);return 0;}
 glGenTextures(1,&tex);glBindTexture(GL_TEXTURE_CUBE_MAP,tex);
 for(f=0;f<6;f++)glTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X+f,0,GL_RGBA8,8,8,0,GL_RGBA,GL_UNSIGNED_BYTE,b+f*256);
 glTexParameteri(GL_TEXTURE_CUBE_MAP,GL_TEXTURE_MIN_FILTER,GL_LINEAR);glTexParameteri(GL_TEXTURE_CUBE_MAP,GL_TEXTURE_MAG_FILTER,GL_LINEAR);
 glTexParameteri(GL_TEXTURE_CUBE_MAP,GL_TEXTURE_WRAP_S,GL_CLAMP_TO_EDGE);glTexParameteri(GL_TEXTURE_CUBE_MAP,GL_TEXTURE_WRAP_T,GL_CLAMP_TO_EDGE);glTexParameteri(GL_TEXTURE_CUBE_MAP,GL_TEXTURE_WRAP_R,GL_CLAMP_TO_EDGE);glTexParameteri(GL_TEXTURE_CUBE_MAP,GL_TEXTURE_MAX_LEVEL,0);free(b);
 if(glGetError()!=GL_NO_ERROR){glDeleteTextures(1,&tex);return 0;}return tex;
}
/* Original TextureMgr00cbc310 SimpleBlackCube -> global+f0 -> RenderConfig+14.
   Native00c97e90 leaves this fallback when the scene has no probe points. */
static GLuint simple_black_cube(void){
 GLuint t=0;unsigned i;const unsigned char pixels[4*4*4]={0};glGenTextures(1,&t);glBindTexture(GL_TEXTURE_CUBE_MAP,t);
 for(i=0;i<6;i++)glTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X+i,0,GL_RGBA8,4,4,0,GL_RGBA,GL_UNSIGNED_BYTE,pixels);
 glTexParameteri(GL_TEXTURE_CUBE_MAP,GL_TEXTURE_MIN_FILTER,GL_LINEAR);glTexParameteri(GL_TEXTURE_CUBE_MAP,GL_TEXTURE_MAG_FILTER,GL_LINEAR);
 glTexParameteri(GL_TEXTURE_CUBE_MAP,GL_TEXTURE_WRAP_S,GL_CLAMP_TO_EDGE);glTexParameteri(GL_TEXTURE_CUBE_MAP,GL_TEXTURE_WRAP_T,GL_CLAMP_TO_EDGE);glTexParameteri(GL_TEXTURE_CUBE_MAP,GL_TEXTURE_WRAP_R,GL_CLAMP_TO_EDGE);glTexParameteri(GL_TEXTURE_CUBE_MAP,GL_TEXTURE_MAX_LEVEL,0);
 if(glGetError()!=GL_NO_ERROR){glDeleteTextures(1,&t);return 0;}return t;
}
int oa_ca_renderer_gpu_open(oa_ca_renderer *r){
 if(!r)return 0;if(r->gpu_ready)return 1;
 r->world_cube=load_cube(r,"creator-bank/creator-world.rgba");r->character_cube=load_cube(r,"creator-bank/creator-character.rgba");
 r->black_cube=simple_black_cube();
 if(!r->world_cube||!r->character_cube||!r->black_cube||!oa_cm_bank_open(&r->textures,read_file,r,"creator-bank/textures/")||
 !oa_cm_open(&r->material,r->character_cube,r->world_cube,oa_cm_bank_texture,&r->textures,113)){oa_ca_renderer_gpu_close(r);return 0;}
 oa_cm_environment_probe(&r->material,r->black_cube);r->gpu_ready=1;return 1;
}
void oa_ca_renderer_gpu_close(oa_ca_renderer *r){
 if(!r)return;oa_cm_close(&r->material);oa_cm_bank_close(&r->textures);
 if(r->world_cube)glDeleteTextures(1,&r->world_cube);if(r->character_cube)glDeleteTextures(1,&r->character_cube);
 if(r->black_cube)glDeleteTextures(1,&r->black_cube);r->black_cube=0;
 r->world_cube=r->character_cube=0;r->gpu_ready=0;
}
void oa_ca_renderer_close(oa_ca_renderer *r){unsigned i;if(!r)return;oa_ca_renderer_gpu_close(r);for(i=0;i<r->model_count;i++)free(r->models[i].bytes);free(r);}
static int appearance_profile(const oa_creation_state *s,unsigned *out){
 const oa_creation_source_type *src=oa_creation_source(s->race,s->sex);unsigned i;
 for(i=0;i<oa_ap_profile_count();i++){const oa_ap_profile *p=oa_ap_profile_get(i);if(p&&p->creator_type==src->creator_simtype){*out=i;return 1;}}return 0;
}
int oa_ca_actor_update_colors(oa_ca_actor *a,const oa_creation_state *s,char *e,size_t n){
 oa_creation_render_selection sel;oa_cm_instance in;if(!a||!s||oa_creation_render(s,&sel)||!oa_cm_instance_from_selection(&sel,255,&in))return error(e,n,"Character palette is not available");
 in.tattoo_texture=a->plan.tattoo_texture;
 {unsigned i;for(i=0;i<a->count;i++)if(!oa_cm_resources_ready(&a->renderer->material,&a->surfaces[i].material,&in))return error(e,n,"Original appearance textures could not be prepared");}
 a->instance=in;a->profile=*s;return 1;
}
oa_ca_actor *oa_ca_actor_prepare(oa_ca_renderer *r,const oa_creation_state *s,unsigned form,const uint32_t *equips,unsigned ne,char *e,size_t n){
 oa_ca_actor *a=NULL;oa_ap_selection select;unsigned i,j;const oa_ap_profile *profile;char path[128];
 if(e&&n)e[0]=0;if(!r||!r->gpu_ready||oa_creation_validate(s)||form>OA_AP_GAMEPLAY)return (error(e,n,"Character renderer is not ready"),NULL);
 a=(oa_ca_actor*)calloc(1,sizeof(*a));if(!a)return (error(e,n,"Not enough memory for character"),NULL);a->renderer=r;
 memset(&select,0,sizeof(select));if(!appearance_profile(s,&select.profile))goto fail;
 select.form=form;for(i=0;i<6;i++)select.option_ids[i]=s->appearance.assets[i];select.equipped_type_ids=equips;select.equipped_count=ne;
 if(!oa_ap_plan_build(&select,model_lookup,r,&a->plan))goto fail;profile=oa_ap_profile_get(select.profile);
 if(!oa_ca_actor_update_colors(a,s,e,n))goto fail;
 for(i=0;i<a->plan.count;i++){
  oa_am_model m;if(!model_lookup(r,a->plan.component[i].fab,&m))goto fail;
  for(j=0;j<oa_am_surface_count(&m);j++){
   oa_am_surface surface;ca_surface *dst;oa_cm_vertex *copy=NULL;const oa_cm_vertex *vertices;unsigned k;
   if(!oa_am_surface_get(&m,j,&surface))goto fail;
   /* Source group1 is the full near model; other assemblies are alternate LODs. */
   if(!oa_ap_component_surface_visible(&a->plan,i,&surface))continue;
   if(a->count>=CA_SURFACES)goto fail;dst=a->surfaces+a->count;
   if(!oa_cm_material_find(surface.material_id,&dst->material))goto fail;
   vertices=(const oa_cm_vertex*)surface.vertices96;
   if(surface.vertex_count&&!(vertices[0].flags&OA_CM_HAS_COLOR)){
    copy=(oa_cm_vertex*)malloc((size_t)surface.vertex_count*sizeof(*copy));if(!copy)goto fail;memcpy(copy,vertices,(size_t)surface.vertex_count*sizeof(*copy));
    /* Recorded native stream1 default-colour resource; absence is never authored. */
    for(k=0;k<surface.vertex_count;k++){memset(copy[k].rgba,255,4);copy[k].flags|=OA_CM_NATIVE_DEFAULT_COLOR;}vertices=copy;
   }
   if(!oa_cm_surface_open(&dst->gpu,vertices,surface.vertex_count,surface.indices,surface.index_count,surface.palette_count,surface.weighted)){free(copy);goto fail;}free(copy);
   dst->component=i;dst->assembly=j;dst->beard=a->plan.component[i].source_type==a->plan.selected_options[OA_AP_BEARD];a->count++;
  }
 }
 for(i=0;i<a->count;i++)if(!oa_cm_resources_ready(&r->material,&a->surfaces[i].material,&a->instance)){
  if(e&&n)snprintf(e,n,"Character material %u requires a scene resource",a->surfaces[i].material.material);goto fail;
 }
 {
  unsigned clip=form==OA_AP_CREATOR?profile->creator_face_idle_clip:profile->gameplay_idle_clip;
  snprintf(path,sizeof(path),"creator-bank/clips/%u-%u.local-trs.bin",a->plan.root_fab,clip);
  if(!read_file(r,path,&a->idle,&a->idle_size)||a->idle_size<12)goto fail;
  a->idle_bones=u32(a->idle);a->idle_frames=u32(a->idle+4);memcpy(&a->idle_fps,a->idle+8,4);
  if(a->idle_bones!=64||!a->idle_frames||a->idle_frames>10000||!isfinite(a->idle_fps)||a->idle_fps<=0||a->idle_size!=12+(size_t)a->idle_bones*a->idle_frames*48)goto fail;
  if(!oa_ca_actor_pose(a,NULL,0,0))goto fail;
 }
 return a;
fail:
 if(e&&n&&!e[0])snprintf(e,n,"Original character assets could not be prepared");oa_ca_actor_close(a);return NULL;
}
void oa_ca_actor_close(oa_ca_actor *a){unsigned i;if(!a)return;for(i=0;i<a->count;i++)oa_cm_surface_close(&a->surfaces[i].gpu);free(a->idle);free(a);}
int oa_ca_actor_pose(oa_ca_actor *a,const float *qts,unsigned bones,float time){
 if(!a)return 0;a->posed=0;
 if(!qts){unsigned frame;if(!a->idle||!isfinite(time)||time<0)return 0;frame=(unsigned)fmodf(time*a->idle_fps,(float)a->idle_frames);qts=(const float*)(a->idle+12+(size_t)frame*a->idle_bones*48);bones=a->idle_bones;}
 a->posed=oa_ap_plan_pose(&a->plan,model_lookup,a->renderer,qts,bones,a->component_world,sizeof(a->component_world)/sizeof(float));return a->posed;
}
void oa_ca_renderer_world_environment(oa_ca_renderer*r,GLuint cc,GLuint wc,GLuint probe){if(r){r->scene_character_cube=cc;r->scene_world_cube=wc;r->scene_probe=probe;}}
GLuint oa_ca_actor_begin(oa_ca_actor *a,const float eye[3]){
 oa_ca_renderer*r;if(!a||!a->posed)return 0;r=a->renderer;
 if(a->plan.form==OA_AP_CREATOR){r->material.character_cube=r->character_cube;r->material.world_cube=r->world_cube;oa_cm_environment_probe(&r->material,r->black_cube);}
 else{if(!r->scene_character_cube||!r->scene_world_cube)return 0;r->material.character_cube=r->scene_character_cube;r->material.world_cube=r->scene_world_cube;oa_cm_environment_probe(&r->material,r->scene_probe?r->scene_probe:r->black_cube);}
 return oa_cm_begin(&r->material,eye);
}
int oa_ca_actor_draw(oa_ca_actor *a,const float vp[16],const float entity[12],int depth_only){
 unsigned i,phase;float palette[OA_CM_MAX_PALETTE*12];GLuint p;int drawn=0;
 if(!a||!a->posed||!(p=oa_cm_program(&a->renderer->material)))return 0;
 glUniform1i(oa_cached_uniform(p,"depth_only"),depth_only!=0);
 for(phase=0;phase<(depth_only?1u:2u);phase++)for(i=0;i<a->count;i++){ca_surface *s=a->surfaces+i;oa_am_model m;oa_am_chunk bones;int z;
  int transparent=s->material.kind==OA_CM_FOG_ADDITIVE;
  if((unsigned)transparent!=phase)continue;
  if(transparent){glEnable(GL_BLEND);glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA);glDepthMask(GL_FALSE);}
  else{glDisable(GL_BLEND);glDepthMask(GL_TRUE);}
  if(s->material.cull==2){glFrontFace(GL_CCW);glEnable(GL_CULL_FACE);glCullFace(GL_BACK);}else return 0;
  if(!model_lookup(a->renderer,a->plan.component[s->component].fab,&m)||!oa_am_find(&m,"BONE",&bones)||!oa_am_palette(&m,s->assembly,a->component_world+s->component*64*12,bones.count,entity,palette,sizeof(palette)/sizeof(float)))return 0;
  z=oa_cm_draw(&a->renderer->material,&s->gpu,&s->material,&a->instance,s->beard,vp,palette,entity);if(z!=1){LOGE("Character appearance draw failed FAB=%u assembly=%u MID=%u result=%d",m.fab,s->assembly,s->material.material,z);return 0;}drawn++;
 }
 glDisable(GL_BLEND);glDepthMask(GL_TRUE);
 return drawn>0;
}
const oa_ap_plan *oa_ca_actor_plan(const oa_ca_actor *a){return a?&a->plan:NULL;}
