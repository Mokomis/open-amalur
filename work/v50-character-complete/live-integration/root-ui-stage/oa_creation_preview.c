#include "oa_creation_preview.h"
#include "oa_creation_layout.h"
#include "oa_render_cache.h"
#include <android/log.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <stdio.h>
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO,"OpemAmalurScene",__VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR,"OpemAmalurScene",__VA_ARGS__)
void oa_creation_preview_cpu_open(oa_creation_preview *p,AAssetManager *manager){
 if(p&&manager&&!p->renderer)p->renderer=oa_ca_renderer_create(manager);
}
void oa_creation_preview_gpu_open(oa_creation_preview *p){
 float lights[113*8]={-39.48135376f,-85.85845947f,147.49841309f,100.f,.1254902035f,.1333333403f,.3450980484f,2000.f};
 const unsigned short indices[8]={0,65535,65535,65535,65535,65535,65535,65535};
 if(!p||!p->renderer||p->ready)return;
 if(!oa_ca_renderer_gpu_open(p->renderer))return;
 glGenBuffers(1,&p->light_ubo);glBindBuffer(GL_UNIFORM_BUFFER,p->light_ubo);glBufferData(GL_UNIFORM_BUFFER,sizeof(lights),lights,GL_STATIC_DRAW);
 glGenTextures(1,&p->light_grid);glBindTexture(GL_TEXTURE_2D,p->light_grid);glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA16UI,2,1,0,GL_RGBA_INTEGER,GL_UNSIGNED_SHORT,indices);
 glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,GL_CLAMP_TO_EDGE);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,GL_CLAMP_TO_EDGE);
 p->ready=glGetError()==GL_NO_ERROR;if(!p->ready)oa_creation_preview_gpu_close(p);
}
void oa_creation_preview_gpu_close(oa_creation_preview *p){
 if(!p)return;oa_ca_actor_close(p->actor);p->actor=NULL;
 if(p->light_ubo)glDeleteBuffers(1,&p->light_ubo);if(p->light_grid)glDeleteTextures(1,&p->light_grid);
 p->light_ubo=p->light_grid=0;oa_ca_renderer_gpu_close(p->renderer);p->ready=0;p->failed_revision=0;
}
void oa_creation_preview_cpu_close(oa_creation_preview *p){if(p){oa_creation_preview_gpu_close(p);oa_ca_renderer_close(p->renderer);memset(p,0,sizeof(*p));}}
int oa_creation_preview_available(const oa_creation_preview *p,const oa_creation_state *s){
 return p&&p->ready&&p->actor&&s&&!oa_creation_validate(s)&&
 p->shown.race==s->race&&p->shown.sex==s->sex&&
 !memcmp(&p->shown.appearance,&s->appearance,sizeof(s->appearance));
}
const char *oa_creation_preview_error(const oa_creation_preview *p){return p&&p->error[0]?p->error:NULL;}
static void norm(float *v){float n=sqrtf(v[0]*v[0]+v[1]*v[1]+v[2]*v[2]);unsigned i;for(i=0;i<3;i++)v[i]/=n;}
static void cross(const float *a,const float *b,float *v){v[0]=a[1]*b[2]-a[2]*b[1];v[1]=a[2]*b[0]-a[0]*b[2];v[2]=a[0]*b[1]-a[1]*b[0];}
static float dot(const float *a,const float *b){return a[0]*b[0]+a[1]*b[1]+a[2]*b[2];}
static void inspect_matrix(float *m,float *eye,float aspect,float zoom,int face){
 const float target[3]={0,0,face?171.f:103.f},up[3]={0,0,1};
 float distance=(face?70.f:280.f)/zoom;
 float f[3],r[3],u[3],v[16]={0},pr[16]={0};int i,row,col,k;
 eye[0]=distance*.87f;eye[1]=-distance*.49f;eye[2]=target[2]+distance*.07f;
 for(i=0;i<3;i++)f[i]=target[i]-eye[i];norm(f);cross(f,up,r);norm(r);cross(r,f,u);
 v[0]=r[0];v[4]=r[1];v[8]=r[2];v[12]=-dot(r,eye);v[1]=u[0];v[5]=u[1];v[9]=u[2];v[13]=-dot(u,eye);v[2]=-f[0];v[6]=-f[1];v[10]=-f[2];v[14]=dot(f,eye);v[15]=1;
 pr[0]=2.41421356f/aspect;pr[5]=2.41421356f;pr[10]=(1200.f+2.f)/(2.f-1200.f);pr[11]=-1;pr[14]=2.f*1200.f*2.f/(2.f-1200.f);
 for(col=0;col<4;col++)for(row=0;row<4;row++){float a=0;for(k=0;k<4;k++)a+=pr[k*4+row]*v[col*4+k];m[col*4+row]=a;}
}
static int same_geometry(const oa_creation_state *a,const oa_creation_state *b){
 return a->guard==b->guard&&a->race==b->race&&a->sex==b->sex&&!memcmp(a->appearance.assets,b->appearance.assets,sizeof(a->appearance.assets));
}
int oa_creation_preview_draw(oa_creation_preview *p,const oa_creation_state *s,float angle,float zoom,int face,int width,int height,float dt){
 oa_creation_layout layout;float m[16],eye[3],entity[12]={0};int x,y,w,h,ok;GLuint program;
 if(!p||!p->ready||width<1||height<1||!isfinite(angle)||!isfinite(zoom)||zoom<.65f||zoom>2.2f||oa_creation_validate(s))return 0;
 if(!p->actor||!same_geometry(&p->shown,s)){
  oa_ca_actor *candidate;
  if(p->failed_revision==s->revision&&same_geometry(&p->failed_profile,s)&&!memcmp(&p->failed_profile.appearance,&s->appearance,sizeof(s->appearance)))return 0;
  candidate=oa_ca_actor_prepare(p->renderer,s,OA_AP_CREATOR,NULL,0,p->error,sizeof(p->error));
  if(!candidate){p->failed_revision=s->revision;p->failed_profile=*s;LOGE("Creator appearance unavailable race=%u sex=%u: %s",s->race,s->sex,p->error);return 0;}
  oa_ca_actor_close(p->actor);p->actor=candidate;p->shown=*s;p->failed_revision=0;p->time=0;
  LOGI("Creator selected source appearance ready race=%u sex=%u components=%u",s->race,s->sex,oa_ca_actor_plan(candidate)->count);
 }else if(s->revision!=p->shown.revision||memcmp(&p->shown.appearance,&s->appearance,sizeof(s->appearance))){
  if(!oa_ca_actor_update_colors(p->actor,s,p->error,sizeof(p->error)))return 0;p->shown=*s;
 }
 if(isfinite(dt)&&dt>0)p->time+=fminf(dt,.1f);
 if(!oa_ca_actor_pose(p->actor,NULL,0,p->time))return 0;
 oa_creation_layout_get(width,height,&layout);
 x=(int)layout.preview[0];w=(int)layout.preview[2];h=(int)layout.preview[3];y=height-(int)(layout.preview[1]+layout.preview[3]);
 if(w<1||h<1||y<0)return 0;
 entity[0]=cosf(angle);entity[1]=-sinf(angle);entity[4]=sinf(angle);entity[5]=cosf(angle);entity[10]=1;
 inspect_matrix(m,eye,(float)w/h,zoom,face);
 glViewport(x,y,w,h);glEnable(GL_SCISSOR_TEST);glScissor(x,y,w,h);glEnable(GL_DEPTH_TEST);glDepthFunc(GL_LEQUAL);glDepthMask(GL_TRUE);glColorMask(GL_TRUE,GL_TRUE,GL_TRUE,GL_TRUE);glDisable(GL_BLEND);glClearDepthf(1);glClear(GL_DEPTH_BUFFER_BIT);
 program=oa_ca_actor_begin(p->actor,eye);if(!program)ok=0;else{
  glUniform3f(oa_cached_uniform(program,"sun_dir"),.547108889f,.498473376f,.672455132f);
  glUniform3f(oa_cached_uniform(program,"sun_color"),.8f,.702745152f,.621176541f);
  glUniform3f(oa_cached_uniform(program,"shadow_color"),.105882362f,.0156862792f,0);
  glUniform3f(oa_cached_uniform(program,"fog_color"),.305882365f,.317647070f,.321568638f);
  glUniform2f(oa_cached_uniform(program,"fog"),29.135700226f/500000.f,-.201980025f);
  glUniform1i(oa_cached_uniform(program,"features"),255);
  glUniform3f(oa_cached_uniform(program,"grid"),0,0,1);glUniform2i(oa_cached_uniform(program,"grid_size"),1,1);
  glActiveTexture(GL_TEXTURE11);glBindTexture(GL_TEXTURE_2D,p->light_grid);glBindBufferBase(GL_UNIFORM_BUFFER,0,p->light_ubo);
  ok=oa_ca_actor_draw(p->actor,m,entity,0);
 }
 glDisable(GL_SCISSOR_TEST);glDisable(GL_DEPTH_TEST);glDisable(GL_CULL_FACE);glDepthMask(GL_FALSE);glViewport(0,0,width,height);return ok;
}
