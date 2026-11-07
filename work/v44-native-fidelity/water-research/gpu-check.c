#include "oa_native_water.h"
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
struct AAsset{FILE*f;long bytes;};
AAsset*AAssetManager_open(AAssetManager*a,const char*p,int mode){AAsset*x=(AAsset*)calloc(1,sizeof(*x));(void)a;(void)mode;x->f=fopen(p,"rb");if(!x->f){free(x);return NULL;}fseek(x->f,0,SEEK_END);x->bytes=ftell(x->f);fseek(x->f,0,SEEK_SET);return x;}
int AAsset_read(AAsset*a,void*p,size_t n){return (int)fread(p,1,n,a->f);}
off_t AAsset_getLength(AAsset*a){return (off_t)a->bytes;}
void AAsset_close(AAsset*a){fclose(a->f);free(a);}

#include <EGL/egl.h>
int main(int argc,char**argv){
 oa_native_water w={0};AAssetManager am={0};oa_native_water_environment e={0};
 EGLDisplay display=eglGetDisplay(EGL_DEFAULT_DISPLAY);EGLConfig config;EGLint count;EGLContext context;EGLSurface surface;
 const EGLint ca[]={EGL_SURFACE_TYPE,EGL_PBUFFER_BIT,EGL_RENDERABLE_TYPE,0x0040,EGL_RED_SIZE,8,EGL_GREEN_SIZE,8,EGL_BLUE_SIZE,8,EGL_DEPTH_SIZE,24,EGL_NONE};
 const EGLint sa[]={EGL_WIDTH,64,EGL_HEIGHT,64,EGL_NONE};const EGLint cx[]={EGL_CONTEXT_CLIENT_VERSION,3,EGL_NONE};
 GLuint color,depth,cube;unsigned char pixels[64*64*4]={0};uint32_t depths[64*64];float vp[16]={0},eye[3]={8591.93f,-87036.03f,6493.06f},inv[2]={-.038186159f,.038188066f};int i,ok;
 if(argc!=2||!oa_native_water_open(&w,&am,argv[1]))return 2;
 if(!eglInitialize(display,0,0)||!eglChooseConfig(display,ca,&config,1,&count)||count<1)return 3;
 surface=eglCreatePbufferSurface(display,config,sa);context=eglCreateContext(display,config,EGL_NO_CONTEXT,cx);
 if(surface==EGL_NO_SURFACE||context==EGL_NO_CONTEXT||!eglMakeCurrent(display,surface,surface,context))return 4;
 glGenTextures(1,&color);glBindTexture(GL_TEXTURE_2D,color);glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA8,64,64,0,GL_RGBA,GL_UNSIGNED_BYTE,pixels);
 for(i=0;i<64*64;i++)depths[i]=0xffffffffu;glGenTextures(1,&depth);glBindTexture(GL_TEXTURE_2D,depth);glTexImage2D(GL_TEXTURE_2D,0,GL_DEPTH_COMPONENT24,64,64,0,GL_DEPTH_COMPONENT,GL_UNSIGNED_INT,depths);
 glGenTextures(1,&cube);glBindTexture(GL_TEXTURE_CUBE_MAP,cube);for(i=0;i<6;i++)glTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X+i,0,GL_RGBA8,1,1,0,GL_RGBA,GL_UNSIGNED_BYTE,pixels);glTexParameteri(GL_TEXTURE_CUBE_MAP,GL_TEXTURE_MIN_FILTER,GL_LINEAR);glTexParameteri(GL_TEXTURE_CUBE_MAP,GL_TEXTURE_MAG_FILTER,GL_LINEAR);
 e.ambient_cube=cube;e.sun_direction[2]=1;e.sun_color[0]=e.sun_color[1]=e.sun_color[2]=.8f;e.water_fog[0]=80;e.water_fog[1]=.01f;e.water_fog[2]=1;
 vp[0]=vp[5]=vp[10]=.0001f;vp[15]=1;glViewport(0,0,64,64);glClearColor(0,0,0,1);glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);
 ok=oa_native_water_draw(&w,vp,eye,color,depth,inv,100,&e);glFinish();printf("Native water ANGLE offscreen shader link/upload/draw %s, GLerror=%u\n",ok?"PASS":"FAIL",glGetError());
 oa_native_water_gpu_close(&w);ok=ok&&oa_native_water_draw(&w,vp,eye,color,depth,inv,101,&e);glFinish();printf("Native water GPU resource recreation %s\n",ok?"PASS":"FAIL");oa_native_water_close(&w);eglMakeCurrent(display,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(display,context);eglDestroySurface(display,surface);eglTerminate(display);return ok?0:5;
}
