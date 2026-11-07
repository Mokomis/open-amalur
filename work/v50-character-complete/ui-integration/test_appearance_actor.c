#include "desktop_compat.h"
#include <EGL/egl.h>
#include <EGL/eglext.h>
#include <GLES3/gl3.h>
#include <android/asset_manager.h>
#include "oa_character_appearance.h"
#include "oa_render_cache.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <math.h>
struct AAsset{FILE*f;off64_t n;};
AAsset *AAssetManager_open(AAssetManager*m,const char*name,int mode){AAsset*a;char p[2500];FILE*f;(void)mode;snprintf(p,sizeof p,"%s/%s",m->root,name);f=fopen(p,"rb");if(!f)return NULL;a=calloc(1,sizeof(*a));if(!a){fclose(f);return NULL;}a->f=f;_fseeki64(f,0,SEEK_END);a->n=_ftelli64(f);rewind(f);return a;}
int AAsset_read(AAsset*a,void*p,size_t n){return (int)fread(p,1,n,a->f);}
off64_t AAsset_getLength64(AAsset*a){return a->n;}
void AAsset_close(AAsset*a){if(a){fclose(a->f);free(a);}}
int __android_log_print(int l,const char*t,const char*f,...){va_list a;int n;(void)l;fprintf(stderr,"%s: ",t);va_start(a,f);n=vfprintf(stderr,f,a);va_end(a);fputc('\n',stderr);return n;}
void oa_desktop_material_probe_texture(GLuint x,int w,int h,const char*s){(void)x;(void)w;(void)h;(void)s;}
static void fail(const char*s){fprintf(stderr,"FAIL %s GL=%x EGL=%x\n",s,glGetError(),eglGetError());exit(2);}
static void norm(float*v){float d=sqrtf(v[0]*v[0]+v[1]*v[1]+v[2]*v[2]);unsigned i;for(i=0;i<3;i++)v[i]/=d;}
static void cross(const float*a,const float*b,float*r){r[0]=a[1]*b[2]-a[2]*b[1];r[1]=a[2]*b[0]-a[0]*b[2];r[2]=a[0]*b[1]-a[1]*b[0];}
static float dot(const float*a,const float*b){return a[0]*b[0]+a[1]*b[1]+a[2]*b[2];}
static void view(float*m,float*eye,int face){
 float target[3]={0,0,face?171.f:99.f},up[3]={0,0,1},f[3],r[3],u[3],v[16]={0},p[16]={0},dist=face?70.f:280.f;int i,k,row,col;
 eye[0]=dist*.87f;eye[1]=-dist*.49f;eye[2]=target[2]+dist*.07f;
 for(i=0;i<3;i++)f[i]=target[i]-eye[i];norm(f);cross(f,up,r);norm(r);cross(r,f,u);
 v[0]=r[0];v[4]=r[1];v[8]=r[2];v[12]=-dot(r,eye);v[1]=u[0];v[5]=u[1];v[9]=u[2];v[13]=-dot(u,eye);v[2]=-f[0];v[6]=-f[1];v[10]=-f[2];v[14]=dot(f,eye);v[15]=1;
 p[0]=2.41421356f;p[5]=2.41421356f;p[10]=(1200.f+2.f)/(2.f-1200.f);p[11]=-1;p[14]=2.f*1200.f*2.f/(2.f-1200.f);
 for(col=0;col<4;col++)for(row=0;row<4;row++){float a=0;for(k=0;k<4;k++)a+=p[k*4+row]*v[col*4+k];m[col*4+row]=a;}
}
static void image(unsigned race,unsigned sex,int face){unsigned char *b=malloc(640*640*4);FILE*f;char n[128];glReadPixels(0,0,640,640,GL_RGBA,GL_UNSIGNED_BYTE,b);snprintf(n,sizeof n,"actor-%u-%u-%d.rgba",race,sex,face);f=fopen(n,"wb");if(!f)fail("image");fwrite(b,1,640*640*4,f);fclose(f);free(b);}
static const float entity_identity[12]={1,0,0,0,0,1,0,0,0,0,1,0};
static int exercise(oa_ca_actor *a,int face){
 float eye[3],vp[16];GLuint p;int ok;unsigned char sample[16*16*4];
 view(vp,eye,face);glViewport(0,0,640,640);glDisable(GL_BLEND);glDisable(GL_CULL_FACE);glEnable(GL_DEPTH_TEST);glDepthFunc(GL_LEQUAL);glDepthMask(GL_TRUE);glClearColor(.024f,.031f,.035f,1);glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);
 oa_render_cache_begin_frame();if(!oa_ca_actor_pose(a,NULL,0,0)||(p=oa_ca_actor_begin(a,eye))==0)return 0;
 glUniform3f(oa_cached_uniform(p,"sun_color"),.8f,.7027452f,.6211765f);glUniform3f(oa_cached_uniform(p,"sun_dir"),.54710889f,.49847338f,.67245513f);glUniform3f(oa_cached_uniform(p,"shadow_color"),.10588236f,.01568628f,0);
 ok=oa_ca_actor_draw(a,vp,entity_identity,0);glReadPixels(312,312,16,16,GL_RGBA,GL_UNSIGNED_BYTE,sample);return ok&&glGetError()==GL_NO_ERROR;
}
int main(void){
 EGLDisplay d;EGLConfig cfg;EGLSurface es;EGLContext ec;EGLint n,ma,mi;AAssetManager mgr;oa_ca_renderer*r;unsigned race,sex;FILE*results;
 const EGLint ca[]={EGL_SURFACE_TYPE,EGL_PBUFFER_BIT,EGL_RENDERABLE_TYPE,EGL_OPENGL_ES3_BIT_KHR,EGL_RED_SIZE,8,EGL_GREEN_SIZE,8,EGL_BLUE_SIZE,8,EGL_ALPHA_SIZE,8,EGL_DEPTH_SIZE,24,EGL_NONE},sa[]={EGL_WIDTH,640,EGL_HEIGHT,640,EGL_NONE},xa[]={EGL_CONTEXT_CLIENT_VERSION,3,EGL_NONE};
 const float entity[12]={1,0,0,0,0,1,0,0,0,0,1,0};
 d=eglGetDisplay(EGL_DEFAULT_DISPLAY);if(!eglInitialize(d,&ma,&mi)||!eglBindAPI(EGL_OPENGL_ES_API)||!eglChooseConfig(d,ca,&cfg,1,&n)||!n)fail("EGL");es=eglCreatePbufferSurface(d,cfg,sa);ec=eglCreateContext(d,cfg,EGL_NO_CONTEXT,xa);if(!eglMakeCurrent(d,es,es,ec))fail("makecurrent");
 memset(&mgr,0,sizeof mgr);snprintf(mgr.root,sizeof mgr.root,"actor-assets");r=oa_ca_renderer_create(&mgr);if(!r||!oa_ca_renderer_gpu_open(r))fail("renderer");
 results=fopen("actor-results.csv","w");fprintf(results,"race,sex,prepare,body,face,error\n");
 for(race=0;race<4;race++)for(sex=0;sex<2;sex++){
  oa_creation_state s;oa_ca_actor*a;char err[256];int pass[2]={0,0},face;oa_creation_begin(&s,race,sex);a=oa_ca_actor_prepare(r,&s,OA_AP_CREATOR,NULL,0,err,sizeof err);
  if(!a){fprintf(results,"%u,%u,0,0,0,%s\n",race,sex,err);continue;}
  for(face=0;face<2;face++){
   float eye[3],vp[16];GLuint p;view(vp,eye,face);glViewport(0,0,640,640);glDisable(GL_BLEND);glDisable(GL_CULL_FACE);glEnable(GL_DEPTH_TEST);glDepthFunc(GL_LEQUAL);glDepthMask(GL_TRUE);glClearColor(.024f,.031f,.035f,1);glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);
   oa_render_cache_begin_frame();if(!oa_ca_actor_pose(a,NULL,0,0)||(p=oa_ca_actor_begin(a,eye))==0)fail("pose/begin");
   glUniform3f(oa_cached_uniform(p,"sun_color"),.8f,.7027452f,.6211765f);glUniform3f(oa_cached_uniform(p,"sun_dir"),.54710889f,.49847338f,.67245513f);glUniform3f(oa_cached_uniform(p,"shadow_color"),.10588236f,.01568628f,0);
   pass[face]=oa_ca_actor_draw(a,vp,entity,0);image(race,sex,face);if(glGetError()!=GL_NO_ERROR)fail("draw GL");
  }
  fprintf(results,"%u,%u,1,%d,%d,\n",race,sex,pass[0],pass[1]);oa_ca_actor_close(a);
 }
 fclose(results);
 {unsigned cases=0,failures=0,form,cat,idx,alpha;FILE*f=fopen("all-option-gpu-results.csv","w");
 const uint32_t gear[5]={1321542,1321543,1330206,1330207,1381439};const unsigned edges[]={0,1,63,84,87,127,178,254,255};
 fprintf(f,"form,race,sex,category,index,asset,prepare,draw,error\n");
 for(form=0;form<2;form++)for(race=0;race<4;race++)for(sex=0;sex<2;sex++){
  oa_creation_state base,candidate;oa_ca_actor*a;char error[256];oa_creation_begin(&base,race,sex);
  for(cat=0;cat<6;cat++)for(idx=0;idx<oa_creation_asset_option_count(race,sex,cat);idx++){
   uint32_t id=0;int ok;candidate=base;oa_creation_asset_option(race,sex,cat,idx,&id);
   if(oa_creation_select_asset(&candidate,cat,id))fail("source choice");
   a=oa_ca_actor_prepare(r,&candidate,form,form?gear:NULL,form?5:0,error,sizeof error);ok=a?exercise(a,1):0;
   fprintf(f,"%u,%u,%u,%u,%u,%u,%d,%d,%s\n",form,race,sex,cat,idx,id,a!=NULL,ok,a?"":error);cases++;if(!ok)failures++;oa_ca_actor_close(a);
  }
  a=oa_ca_actor_prepare(r,&base,form,form?gear:NULL,form?5:0,error,sizeof error);if(!a)fail("base sweep");
  for(cat=0;cat<8;cat++)for(idx=1;idx<=oa_creation_color_count(race,sex,cat);idx++){
   candidate=base;if(oa_creation_select_color(&candidate,cat,idx)||!oa_ca_actor_update_colors(a,&candidate,error,sizeof error)||!exercise(a,1)){failures++;fprintf(f,"%u,%u,%u,color%u,%u,0,1,0,%s\n",form,race,sex,cat,idx,error);}cases++;
  }
  for(cat=0;cat<4;cat++)for(alpha=0;alpha<sizeof(edges)/sizeof(*edges);alpha++){
   candidate=base;if(oa_creation_select_alpha(&candidate,cat,edges[alpha])||!oa_ca_actor_update_colors(a,&candidate,error,sizeof error)||!exercise(a,1)){failures++;fprintf(f,"%u,%u,%u,alpha%u,%u,0,1,0,%s\n",form,race,sex,cat,edges[alpha],error);}cases++;
  }
  oa_ca_actor_close(a);
  for(idx=1;idx<=5;idx++){
   candidate=base;if(oa_creation_apply_preset(&candidate,idx))fail("all source presets accepted");
   a=oa_ca_actor_prepare(r,&candidate,form,form?gear:NULL,form?5:0,error,sizeof error);if(!a||!exercise(a,1)){failures++;fprintf(f,"%u,%u,%u,preset,%u,0,%d,0,%s\n",form,race,sex,idx,a!=NULL,error);}cases++;oa_ca_actor_close(a);
  }
 }
 fclose(f);printf("GPU sweep cases=%u failures=%u forms=creator+gameplay allsourceassets+colours+opacityboundaries+40presets\n",cases,failures);
 if(failures)return 3;
 }
 oa_ca_renderer_close(r);eglMakeCurrent(d,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(d,ec);eglDestroySurface(d,es);eglTerminate(d);printf("Actor fixture finished; inspectCSV/images for useful results\n");return 0;
}
