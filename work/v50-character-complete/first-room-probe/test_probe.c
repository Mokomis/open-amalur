#include <EGL/egl.h>
#include <EGL/eglext.h>
#include <GLES3/gl3.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
static void fail(const char*s){fprintf(stderr,"FAIL %s GL%x EGL%x\n",s,glGetError(),eglGetError());exit(2);}
static GLuint shader(GLenum type,const char*s){GLuint q=glCreateShader(type);GLint ok;char log[4096];glShaderSource(q,1,&s,0);glCompileShader(q);glGetShaderiv(q,GL_COMPILE_STATUS,&ok);if(!ok){glGetShaderInfoLog(q,sizeof(log),0,log);fprintf(stderr,"%s\n",log);fail("shader");}return q;}
int main(void){EGLDisplay d;EGLConfig cfg;EGLContext ec;EGLSurface es;EGLint n,ma,mi;GLuint cube,vs,fs,p,vao;GLint ok;unsigned k,f,w,h,nl,fmt,z,count=0;uint8_t *data,*expected[6][6];FILE*in;char magic[8];const float dirs[6][3]={{1,0,0},{-1,0,0},{0,1,0},{0,-1,0},{0,0,1},{0,0,-1}};
const EGLint ca[]={EGL_SURFACE_TYPE,EGL_PBUFFER_BIT,EGL_RENDERABLE_TYPE,EGL_OPENGL_ES3_BIT_KHR,EGL_RED_SIZE,8,EGL_GREEN_SIZE,8,EGL_BLUE_SIZE,8,EGL_ALPHA_SIZE,8,EGL_NONE},sa[]={EGL_WIDTH,1,EGL_HEIGHT,1,EGL_NONE},xa[]={EGL_CONTEXT_CLIENT_VERSION,3,EGL_NONE};
d=eglGetDisplay(EGL_DEFAULT_DISPLAY);if(!eglInitialize(d,&ma,&mi)||!eglBindAPI(EGL_OPENGL_ES_API)||!eglChooseConfig(d,ca,&cfg,1,&n)||!n)fail("EGL");es=eglCreatePbufferSurface(d,cfg,sa);ec=eglCreateContext(d,cfg,EGL_NO_CONTEXT,xa);if(!eglMakeCurrent(d,es,es,ec))fail("context");
printf("renderer=%s\nversion=%s\n",(char*)glGetString(GL_RENDERER),(char*)glGetString(GL_VERSION));
in=fopen("1576506.oacube","rb");if(!in||fread(magic,1,8,in)!=8||memcmp(magic,"OACUBE1\0",8))fail("magic");fread(&w,4,1,in);fread(&h,4,1,in);fread(&nl,4,1,in);fread(&fmt,4,1,in);if(w!=128||h!=128||nl!=6||fmt!=GL_RGBA8)fail("header");
glGenTextures(1,&cube);glBindTexture(GL_TEXTURE_CUBE_MAP,cube);
for(k=0;k<nl;k++){unsigned ww=w>>k,hh=h>>k,face=ww*hh*4;fread(&z,4,1,in);if(z!=6*face)fail("extent");data=malloc(z);if(fread(data,1,z,in)!=z)fail("payload");for(f=0;f<6;f++){expected[k][f]=malloc(4);memcpy(expected[k][f],data+f*face+4*((hh/2)*ww+ww/2),4);glTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X+f,k,GL_RGBA8,ww,hh,0,GL_RGBA,GL_UNSIGNED_BYTE,data+f*face);}free(data);}if(fgetc(in)!=EOF)fail("tail");fclose(in);
glTexParameteri(GL_TEXTURE_CUBE_MAP,GL_TEXTURE_MIN_FILTER,GL_NEAREST_MIPMAP_NEAREST);glTexParameteri(GL_TEXTURE_CUBE_MAP,GL_TEXTURE_MAG_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_CUBE_MAP,GL_TEXTURE_MAX_LEVEL,5);glTexParameteri(GL_TEXTURE_CUBE_MAP,GL_TEXTURE_WRAP_S,GL_CLAMP_TO_EDGE);glTexParameteri(GL_TEXTURE_CUBE_MAP,GL_TEXTURE_WRAP_T,GL_CLAMP_TO_EDGE);if(glGetError())fail("upload");
vs=shader(GL_VERTEX_SHADER,"#version 300 es\nvoid main(){vec2 p=vec2((gl_VertexID<<1)&2,gl_VertexID&2);gl_Position=vec4(p*2.-1.,0.,1.);}");
fs=shader(GL_FRAGMENT_SHADER,"#version 300 es\nprecision highp float;uniform highp samplerCube tex;uniform vec3 dir;uniform float lod;out vec4 o;void main(){o=textureLod(tex,dir,lod);}");
p=glCreateProgram();glAttachShader(p,vs);glAttachShader(p,fs);glLinkProgram(p);glGetProgramiv(p,GL_LINK_STATUS,&ok);if(!ok)fail("link");glUseProgram(p);glUniform1i(glGetUniformLocation(p,"tex"),0);glGenVertexArrays(1,&vao);glBindVertexArray(vao);glViewport(0,0,1,1);glDisable(GL_DITHER);
for(k=0;k<6;k++)for(f=0;f<6;f++){uint8_t rgba[4];glUniform3fv(glGetUniformLocation(p,"dir"),1,dirs[f]);glUniform1f(glGetUniformLocation(p,"lod"),(float)k);glDrawArrays(GL_TRIANGLES,0,3);glReadPixels(0,0,1,1,GL_RGBA,GL_UNSIGNED_BYTE,rgba);if(memcmp(rgba,expected[k][f],4)){fprintf(stderr,"mip%u face%u actual%u,%u,%u,%u expected%u,%u,%u,%u\n",k,f,rgba[0],rgba[1],rgba[2],rgba[3],expected[k][f][0],expected[k][f][1],expected[k][f][2],expected[k][f][3]);fail("sample");}count++;free(expected[k][f]);}if(glGetError())fail("draw");printf("PASS %u face/mip GL cube center samples exact; all36faces/mips uploaded GL0\n",count);return 0;}
