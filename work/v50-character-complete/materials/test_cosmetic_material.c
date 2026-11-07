#include <EGL/egl.h>
#include <EGL/eglext.h>
#include <GLES3/gl3.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <stdarg.h>
#include <math.h>
#include "oa_cosmetic_material.h"
#include "oa_cosmetic_texture_bank.h"
#include "cosmetic_texture_pins.inc"
#define S 64
int __android_log_print(int l,const char*t,const char*f,...){va_list a;int n;(void)l;fprintf(stderr,"%s: ",t);va_start(a,f);n=vfprintf(stderr,f,a);va_end(a);fputc('\n',stderr);return n;}
void oa_desktop_material_probe_texture(GLuint x,int w,int h,const char*s){(void)x;(void)w;(void)h;(void)s;}
static void fail(const char*s){fprintf(stderr,"FAIL %s GL=%x EGL=%x\n",s,glGetError(),eglGetError());exit(2);}
static int readbank(void*user,const char*name,uint8_t**b,size_t*n){FILE*f;long z;*b=NULL;*n=0;f=fopen(name,"rb");if(!f)return 0;fseek(f,0,SEEK_END);z=ftell(f);rewind(f);if(z<=0){fclose(f);return 0;}*b=(uint8_t*)malloc((size_t)z);if(!*b||fread(*b,1,(size_t)z,f)!=(size_t)z){free(*b);*b=NULL;fclose(f);return 0;}fclose(f);*n=(size_t)z;if(user)(*b)[*n-1]^=1;return 1;}
static void bank_test(void){oa_cm_texture_bank bank={0},bad={0};unsigned k;FILE*f=fopen("actual-texture-uploads.csv","w");if(!oa_cm_bank_open(&bank,readbank,NULL,"textures/"))fail("bankopen");
 for(k=0;k<sizeof(cm_bank_pins)/sizeof(cm_bank_pins[0]);k++){const CMBankPin*p=cm_bank_pins+k;GLuint t=oa_cm_bank_texture(&bank,p->asset,p->target);if(!t)fail("pinnedsourceupload");fprintf(f,"%u,%u,%u,%zu\n",p->asset,p->target,t,p->bytes);}
 if(bank.count!=412)fail("bankcount");fclose(f);oa_cm_bank_close(&bank);
 if(!oa_cm_bank_open(&bad,readbank,(void*)1,"textures/"))fail("badbankopen");if(oa_cm_bank_texture(&bad,1290634,GL_TEXTURE_2D)||bad.count)fail("corruptionnotrejected");if(oa_cm_bank_texture(&bad,2,GL_TEXTURE_2D)||bad.count)fail("unreviewednotrejected");oa_cm_bank_close(&bad);printf("PASS412pinnedactualtextureuploads andcorrupt/unreviewedreject\n");
}
static GLuint maps[8],cc,probe;static unsigned maskGreen=255;
static GLuint tex2(const uint8_t v[4]){GLuint t;glGenTextures(1,&t);glBindTexture(GL_TEXTURE_2D,t);glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA8,1,1,0,GL_RGBA,GL_UNSIGNED_BYTE,v);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,GL_REPEAT);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,GL_REPEAT);return t;}
static GLuint cub(const uint8_t v[4]){unsigned k;GLuint t;glGenTextures(1,&t);glBindTexture(GL_TEXTURE_CUBE_MAP,t);for(k=0;k<6;k++)glTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X+k,0,GL_RGBA8,1,1,0,GL_RGBA,GL_UNSIGNED_BYTE,v);glTexParameteri(GL_TEXTURE_CUBE_MAP,GL_TEXTURE_MIN_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_CUBE_MAP,GL_TEXTURE_MAG_FILTER,GL_NEAREST);return t;}
static GLuint lookup(void*user,uint32_t id,GLenum target){(void)user;if(target==GL_TEXTURE_CUBE_MAP)return probe;switch(id){case 1290634:case 1290637:case 744833:case 660620:case 535019:case 1641589:return maps[0];case 513640:case 513762:case 1302963:case 665299:case 660621:case 535020:case 1641590:return maps[1];case 513642:case 513765:case 1302962:case 665298:case 665189:case 535021:case 1641591:return maps[2];case 518404:case 1554724:case 1348471:case 744834:case 1645088:case 518046:return maps[3];case 1346365:return maps[4];case 250070:return maps[5];default:return maps[0];}}
static void image(const char*file){uint8_t b[S*S*4];FILE*f;glReadPixels(0,0,S,S,GL_RGBA,GL_UNSIGNED_BYTE,b);f=fopen(file,"wb");if(!f)fail("write");fwrite(b,1,sizeof(b),f);fclose(f);}
static void mask(unsigned v){uint8_t b[4]={1,(uint8_t)v,2,3};maskGreen=v;glActiveTexture(GL_TEXTURE3);glBindTexture(GL_TEXTURE_2D,maps[3]);glTexSubImage2D(GL_TEXTURE_2D,0,0,0,1,1,GL_RGBA,GL_UNSIGNED_BYTE,b);}
static void logcase(FILE*f,unsigned n,const char*name,unsigned mid,oa_cm_context*g,oa_cm_surface*s,oa_cm_material*m,oa_cm_instance*inst,const float*vp,const float*bones,const float*entity){uint8_t px[4];int draw;char file[80];float eye[3]={0,0,3};if(!oa_cm_begin(g,eye))fail("begin");glClearColor(0,0,0,0);glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);draw=oa_cm_draw(g,s,m,inst,0,vp,bones,entity);if(draw!=1)fail("draw");glReadPixels(S/2,S/2,1,1,GL_RGBA,GL_UNSIGNED_BYTE,px);fprintf(f,"%u,%s,%u,%u,%u,%u,%u,%u,%g,%g,%g,%g,%g,%g,%g,%g\n",n,name,mid,maskGreen,px[0],px[1],px[2],px[3],inst->color[2][0],inst->color[2][1],inst->color[2][2],inst->color[2][3],inst->color[5][3],inst->color[4][3],inst->color[6][3],inst->color[7][3]);snprintf(file,sizeof(file),"case-%02u.rgba",n);image(file);}
int main(void){EGLDisplay d;EGLConfig cfg;EGLSurface es;EGLContext ec;EGLint n,ma,mi;GLuint fbo,color,depth,ubo;oa_cm_context g={0};oa_cm_surface surf={0};oa_cm_vertex v[4];const uint32_t ix[6]={0,1,2,0,2,3};float vp[16]={1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1};float bones[12]={1,0,0,0,0,1,0,0,0,0,1,0},entity[12]={1,0,0,0,0,1,0,0,0,0,1,0},zeros[113*8]={0};FILE*f;unsigned k,caseid=0;oa_cm_instance in;oa_cm_material m;char*fs;
 const EGLint ca[]={EGL_SURFACE_TYPE,EGL_PBUFFER_BIT,EGL_RENDERABLE_TYPE,EGL_OPENGL_ES3_BIT_KHR,EGL_RED_SIZE,8,EGL_GREEN_SIZE,8,EGL_BLUE_SIZE,8,EGL_ALPHA_SIZE,8,EGL_NONE},sa[]={EGL_WIDTH,S,EGL_HEIGHT,S,EGL_NONE},xa[]={EGL_CONTEXT_CLIENT_VERSION,3,EGL_NONE};
 d=eglGetDisplay(EGL_DEFAULT_DISPLAY);if(!eglInitialize(d,&ma,&mi)||!eglBindAPI(EGL_OPENGL_ES_API)||!eglChooseConfig(d,ca,&cfg,1,&n)||!n)fail("EGL");es=eglCreatePbufferSurface(d,cfg,sa);ec=eglCreateContext(d,cfg,EGL_NO_CONTEXT,xa);if(!eglMakeCurrent(d,es,es,ec))fail("makecurrent");
 f=fopen("renderer.json","w");fprintf(f,"{\"egl\":\"%d.%d\",\"vendor\":\"%s\",\"renderer\":\"%s\",\"version\":\"%s\",\"glsl\":\"%s\"}\n",ma,mi,glGetString(GL_VENDOR),glGetString(GL_RENDERER),glGetString(GL_VERSION),glGetString(GL_SHADING_LANGUAGE_VERSION));fclose(f);
 bank_test();
 {const uint8_t c[8][4]={{100,120,140,255},{128,128,255,255},{50,64,220,255},{0,255,0,255},{64,128,192,255},{0,90,0,255},{0,160,0,255},{0,0,0,255}};for(k=0;k<8;k++)maps[k]=tex2(c[k]);}{const uint8_t a[4]={80,120,160,255},b[4]={20,30,40,255};cc=cub(a);probe=cub(b);}
 {const uint8_t makeup[16]={255,0,0,255,0,255,0,255,0,0,255,255,64,128,192,255},tattoo[16]={0,0,0,255,0,255,0,255,0,64,0,255,0,128,0,255};glBindTexture(GL_TEXTURE_2D,maps[4]);glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA8,2,2,0,GL_RGBA,GL_UNSIGNED_BYTE,makeup);glBindTexture(GL_TEXTURE_2D,maps[5]);glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA8,2,2,0,GL_RGBA,GL_UNSIGNED_BYTE,tattoo);}
 if(!oa_cm_open(&g,cc,cc,lookup,NULL,113))fail("material compile/link");
 fs=oa_cm_fragment_source(113);f=fopen("actual-cosmetic-fragment.glsl","wb");fwrite(fs,1,strlen(fs),f);fclose(f);free(fs);f=fopen("actual-cosmetic-vertex.glsl","wb");fwrite(oa_cm_vertex_source(),1,strlen(oa_cm_vertex_source()),f);fclose(f);
 glGenBuffers(1,&ubo);glBindBuffer(GL_UNIFORM_BUFFER,ubo);glBufferData(GL_UNIFORM_BUFFER,sizeof(zeros),zeros,GL_STATIC_DRAW);glBindBufferBase(GL_UNIFORM_BUFFER,0,ubo);
 memset(v,0,sizeof(v));for(k=0;k<4;k++){v[k].p[0]=k==0||k==3?-1:1;v[k].p[1]=k<2?-1:1;v[k].weight[0]=1;v[k].n[2]=1;v[k].t[0]=1;v[k].b[1]=1;v[k].uv0[0]=v[k].p[0]*.5f+.5f;v[k].uv0[1]=v[k].p[1]*.5f+.5f;v[k].uv1[0]=v[k].uv0[1];v[k].uv1[1]=v[k].uv0[0];v[k].rgba[0]=204;v[k].rgba[1]=153;v[k].rgba[2]=255;v[k].rgba[3]=153;v[k].flags=127;v[k].source_vertex=k;}if(!oa_cm_surface_open(&surf,v,4,ix,6,1,1))fail("surface");
 glGenFramebuffers(1,&fbo);glBindFramebuffer(GL_FRAMEBUFFER,fbo);glGenTextures(1,&color);glBindTexture(GL_TEXTURE_2D,color);glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA8,S,S,0,GL_RGBA,GL_UNSIGNED_BYTE,NULL);glFramebufferTexture2D(GL_FRAMEBUFFER,GL_COLOR_ATTACHMENT0,GL_TEXTURE_2D,color,0);glGenRenderbuffers(1,&depth);glBindRenderbuffer(GL_RENDERBUFFER,depth);glRenderbufferStorage(GL_RENDERBUFFER,GL_DEPTH_COMPONENT16,S,S);glFramebufferRenderbuffer(GL_FRAMEBUFFER,GL_DEPTH_ATTACHMENT,GL_RENDERBUFFER,depth);if(glCheckFramebufferStatus(GL_FRAMEBUFFER)!=GL_FRAMEBUFFER_COMPLETE)fail("fbo");glViewport(0,0,S,S);glDisable(GL_DEPTH_TEST);glDisable(GL_CULL_FACE);glDisable(GL_BLEND);
 memset(&in,0,sizeof(in));in.tattoo_texture=250070;for(k=0;k<4;k++){in.probe_instance_tint[k]=1;in.dynamic_tint[k]=1;in.luminance_tint[k]=1;}in.luminance_factors[0]=.2126f;in.luminance_factors[1]=.7152f;in.luminance_factors[2]=.0722f;for(k=0;k<8;k++){in.color[k][0]=.2f+.05f*k;in.color[k][1]=.4f-.02f*k;in.color[k][2]=.6f-.03f*k;in.color[k][3]=.5f;}in.color[0][0]=.08f;in.color[1][0]=.7f;in.color[2][0]=.8313726186752319f;in.color[2][1]=.6823529601097107f;in.color[2][2]=.6039215922355652f;memcpy(in.beard,in.color,32);
 f=fopen("cases.csv","w");fprintf(f,"case,name,mid,mask,r,g,b,a,skinR,skinG,skinB,skinA,tattooA,blushA,eyelinerA,lipstickA\n");
 if(!oa_cm_material_find(513702,&m))fail("lookup skin");
 for(k=0;k<3;k++){in.color[2][3]=k==0?0:k==1?.6f:1;logcase(f,caseid++,"skin",513702,&g,&surf,&m,&in,vp,bones,entity);}
 mask(231);logcase(f,caseid++,"skin-below",513702,&g,&surf,&m,&in,vp,bones,entity);mask(232);logcase(f,caseid++,"skin-equal",513702,&g,&surf,&m,&in,vp,bones,entity);mask(255);logcase(f,caseid++,"skin-above",513702,&g,&surf,&m,&in,vp,bones,entity);
 if(!oa_cm_material_find(513975,&m))fail("lookup head");for(k=0;k<5;k++){unsigned a;for(a=4;a<8;a++)in.color[a][3]=a<k+4?.5f:0;logcase(f,caseid++,"head-overlay",513975,&g,&surf,&m,&in,vp,bones,entity);}
 if(!oa_cm_material_find(1302951,&m))fail("lookup hair");for(k=0;k<3;k++){mask(k==0?122:k==1?123:255);logcase(f,caseid++,"hair-cut",1302951,&g,&surf,&m,&in,vp,bones,entity);}mask(255);
 if(!oa_cm_material_find(665977,&m))fail("lookup beard");logcase(f,caseid++,"beard",665977,&g,&surf,&m,&in,vp,bones,entity);
 if(!oa_cm_material_find(790131,&m))fail("lookup eye");logcase(f,caseid++,"eye",790131,&g,&surf,&m,&in,vp,bones,entity);m.constant[0]=.3f;logcase(f,caseid++,"eye-emissive",790131,&g,&surf,&m,&in,vp,bones,entity);
 if(!oa_cm_material_find(660429,&m))fail("lookup hard");logcase(f,caseid++,"hardlight",660429,&g,&surf,&m,&in,vp,bones,entity);
 if(!oa_cm_material_find(535023,&m))fail("lookup mouth");logcase(f,caseid++,"mouth",535023,&g,&surf,&m,&in,vp,bones,entity);
 if(!oa_cm_material_find(1641598,&m))fail("lookup reflect");oa_cm_environment_probe(&g,probe);logcase(f,caseid++,"reflect",1641598,&g,&surf,&m,&in,vp,bones,entity);
 in.probe_instance_tint[0]=.2f;in.probe_instance_tint[1]=.5f;in.probe_instance_tint[2]=.8f;logcase(f,caseid++,"reflect-tint",1641598,&g,&surf,&m,&in,vp,bones,entity);
 if(!oa_cm_material_find(518048,&m))fail("lookup headaux");logcase(f,caseid++,"head-aux",518048,&g,&surf,&m,&in,vp,bones,entity);
 fclose(f);printf("PASS %u actual compiled material/raster cases; GL=%x\n",caseid,glGetError());oa_cm_surface_close(&surf);oa_cm_close(&g);eglMakeCurrent(d,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(d,ec);eglDestroySurface(d,es);eglTerminate(d);return 0;}
