#include <EGL/egl.h>
#include <EGL/eglext.h>
#include <GLES3/gl3.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <stddef.h>
#include <math.h>
#include "oa_character_material.h"
#include "oa_post.h"
#include "oa_render_cache.h"
#define SZ 32
int __android_log_print(int level,const char *tag,const char *fmt,...){va_list a;int n;(void)level;fprintf(stderr,"%s: ",tag);va_start(a,fmt);n=vfprintf(stderr,fmt,a);va_end(a);fputc('\n',stderr);return n;}
void oa_desktop_material_probe_texture(GLuint t,int w,int h,const char *s){(void)t;(void)w;(void)h;(void)s;}
typedef struct Vertex{float p[3],n[4],vc[4],uv[2],t[3],b[3],uv2[2];} Vertex;
static const float norms[3][3]={{0,0,2},{.4f,0,3},{0,.5f,4}};
static const float tangs[3][3]={{3,0,.1f},{2,.2f,0},{4,0,.4f}};
static const float bitans[3][3]={{0,4,.1f},{.2f,3,0},{0,2,.3f}};
static const float pxy[3][2]={{-1,-1},{3,-1},{-1,3}};
static const unsigned char diffuse[4]={80,120,160,255},normalmap[4]={204,102,128,255},specmap[4]={91,201,17,255},cubecolor[4]={101,173,219,255};
static void fail(const char*s){fprintf(stderr,"FAIL: %s EGL=%x GL=%x\n",s,eglGetError(),glGetError());exit(2);}
static void checkgl(const char *s){GLenum e=glGetError();if(e){fprintf(stderr,"GL error %x at %s\n",e,s);exit(2);}}
static GLint ul(GLuint p,const char*n){return glGetUniformLocation(p,n);}
static void u1i(GLuint p,const char*n,int v){glUniform1i(ul(p,n),v);}
static void u3(GLuint p,const char*n,float x,float y,float z){glUniform3f(ul(p,n),x,y,z);}
static GLuint tex2(const unsigned char*px){GLuint t;glGenTextures(1,&t);glBindTexture(GL_TEXTURE_2D,t);glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA8,1,1,0,GL_RGBA,GL_UNSIGNED_BYTE,px);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,GL_CLAMP_TO_EDGE);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,GL_CLAMP_TO_EDGE);return t;}
static GLuint cube(void){GLuint t;int f;glGenTextures(1,&t);glBindTexture(GL_TEXTURE_CUBE_MAP,t);for(f=0;f<6;f++)glTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X+f,0,GL_RGBA8,1,1,0,GL_RGBA,GL_UNSIGNED_BYTE,cubecolor);glTexParameteri(GL_TEXTURE_CUBE_MAP,GL_TEXTURE_MIN_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_CUBE_MAP,GL_TEXTURE_MAG_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_CUBE_MAP,GL_TEXTURE_WRAP_S,GL_CLAMP_TO_EDGE);glTexParameteri(GL_TEXTURE_CUBE_MAP,GL_TEXTURE_WRAP_T,GL_CLAMP_TO_EDGE);glTexParameteri(GL_TEXTURE_CUBE_MAP,GL_TEXTURE_WRAP_R,GL_CLAMP_TO_EDGE);return t;}
static void save_sources(GLuint p){GLuint sh[8];GLsizei n;int i;glGetAttachedShaders(p,8,&n,sh);for(i=0;i<n;i++){GLint bytes,type;char name[80];char *s;FILE*f;glGetShaderiv(sh[i],GL_SHADER_TYPE,&type);glGetShaderiv(sh[i],GL_SHADER_SOURCE_LENGTH,&bytes);s=(char*)malloc((size_t)bytes+1);glGetShaderSource(sh[i],bytes,NULL,s);sprintf(name,"actual-linked-%s.glsl",type==GL_VERTEX_SHADER?"vertex":"fragment");f=fopen(name,"wb");if(!f)fail("write shader");fwrite(s,1,strlen(s),f);fclose(f);free(s);}}
static void fillverts(Vertex v[3],float a,int unit){int i,j;for(i=0;i<3;i++){float lengths[3]={0,0,0};memset(v+i,0,sizeof(v[i]));v[i].p[0]=pxy[i][0];v[i].p[1]=pxy[i][1];v[i].vc[0]=204.f/255;v[i].vc[1]=153.f/255;v[i].vc[2]=230.f/255;v[i].vc[3]=a;v[i].uv[0]=v[i].uv[1]=.5f;for(j=0;j<3;j++){lengths[0]+=norms[i][j]*norms[i][j];lengths[1]+=tangs[i][j]*tangs[i][j];lengths[2]+=bitans[i][j]*bitans[i][j];}for(j=0;j<3;j++){v[i].n[j]=norms[i][j]/(unit?sqrtf(lengths[0]):1);v[i].t[j]=tangs[i][j]/(unit?sqrtf(lengths[1]):1);v[i].b[j]=bitans[i][j]/(unit?sqrtf(lengths[2]):1);}}}
int main(void){
 EGLDisplay d;EGLConfig cfg;EGLContext ctx;EGLSurface surf;EGLint ncfg,major,minor;
 const EGLint ca[]={EGL_SURFACE_TYPE,EGL_PBUFFER_BIT,EGL_RENDERABLE_TYPE,EGL_OPENGL_ES3_BIT_KHR,EGL_RED_SIZE,8,EGL_GREEN_SIZE,8,EGL_BLUE_SIZE,8,EGL_ALPHA_SIZE,8,EGL_DEPTH_SIZE,0,EGL_NONE};
 const EGLint sa[]={EGL_WIDTH,SZ,EGL_HEIGHT,SZ,EGL_NONE},xa[]={EGL_CONTEXT_CLIENT_VERSION,3,EGL_NONE};
 GLuint prog,vao,vbo,ubo,ts[8],cu,gridtex,depthtex,fbo,color;unsigned short nogrid[8]={65535,65535,65535,65535,65535,65535,65535,65535};float lightzero[8]={0};int i,a,fr,co,ag,id=0,diag,unit;FILE *out,*info;Vertex v[3];unsigned char pixels[SZ*SZ*4];float alpha[3]={0,.6f,1};float eye[3]={4,0,-1};
 const float mvp[16]={1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1};
 oa_character_hardlight mat={{1,1,1,1},{2.3f,20,0,0},{.15f,1,1,0},{1.4f,2.4f,0,0}};
 d=eglGetDisplay(EGL_DEFAULT_DISPLAY);if(d==EGL_NO_DISPLAY||!eglInitialize(d,&major,&minor))fail("eglInitialize");
 if(!eglBindAPI(EGL_OPENGL_ES_API)||!eglChooseConfig(d,ca,&cfg,1,&ncfg)||!ncfg)fail("config");
 surf=eglCreatePbufferSurface(d,cfg,sa);ctx=eglCreateContext(d,cfg,EGL_NO_CONTEXT,xa);if(surf==EGL_NO_SURFACE||ctx==EGL_NO_CONTEXT||!eglMakeCurrent(d,surf,surf,ctx))fail("context");
 info=fopen("renderer.json","w");fprintf(info,"{\"egl_major\":%d,\"egl_minor\":%d,\"egl_vendor\":\"%s\",\"gl_vendor\":\"%s\",\"gl_renderer\":\"%s\",\"gl_version\":\"%s\",\"glsl\":\"%s\",\"surface\":\"EGL32x32pbuffer; no native window\"}\n",major,minor,eglQueryString(d,EGL_VENDOR),glGetString(GL_VENDOR),glGetString(GL_RENDERER),glGetString(GL_VERSION),glGetString(GL_SHADING_LANGUAGE_VERSION));fclose(info);
 prog=oa_character_rigid_material_program(1);if(!prog)fail("actual rigid material factory link");glUseProgram(prog);save_sources(prog);
 if(!oa_character_hardlight_upload(prog,&mat))fail("actual material upload");
 {float s[4],t[4];int family=0;glGetUniformfv(prog,ul(prog,"material_specular"),s);glGetUniformfv(prog,ul(prog,"material_tiling"),t);glGetUniformiv(prog,ul(prog,"material_family"),&family);if(family!=12||s[1]!=20||s[2]!=.15f||s[3]!=1.4f||t[2]!=2.4f)fail("material uniform mapping");}
 for(i=0;i<8;i++){char name[8];glActiveTexture(GL_TEXTURE0+i);ts[i]=tex2(i==0?diffuse:i==1?normalmap:i==2?specmap:diffuse);sprintf(name,"t%d",i);u1i(prog,name,i);}
 glActiveTexture(GL_TEXTURE8);cu=cube();u1i(prog,"cube",8);glActiveTexture(GL_TEXTURE9);glBindTexture(GL_TEXTURE_CUBE_MAP,cu);u1i(prog,"native_reflection_cube",9);
 glActiveTexture(GL_TEXTURE10);tex2(diffuse);u1i(prog,"ambient_occlusion",10);
 glActiveTexture(GL_TEXTURE11);glGenTextures(1,&depthtex);glBindTexture(GL_TEXTURE_2D,depthtex);glTexImage2D(GL_TEXTURE_2D,0,GL_DEPTH_COMPONENT16,1,1,0,GL_DEPTH_COMPONENT,GL_UNSIGNED_SHORT,NULL);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_COMPARE_MODE,GL_COMPARE_REF_TO_TEXTURE);u1i(prog,"shadow_map",11);
 glActiveTexture(GL_TEXTURE12);glGenTextures(1,&gridtex);glBindTexture(GL_TEXTURE_2D,gridtex);glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA16UI,2,1,0,GL_RGBA_INTEGER,GL_UNSIGNED_SHORT,nogrid);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST);u1i(prog,"light_grid",12);
 glGenBuffers(1,&ubo);glBindBuffer(GL_UNIFORM_BUFFER,ubo);glBufferData(GL_UNIFORM_BUFFER,sizeof(lightzero),lightzero,GL_STATIC_DRAW);glBindBufferBase(GL_UNIFORM_BUFFER,0,ubo);
 glGenVertexArrays(1,&vao);glBindVertexArray(vao);glGenBuffers(1,&vbo);glBindBuffer(GL_ARRAY_BUFFER,vbo);glBufferData(GL_ARRAY_BUFFER,sizeof(v),NULL,GL_DYNAMIC_DRAW);
#define ATTR(loc,count,member) glVertexAttribPointer(loc,count,GL_FLOAT,GL_FALSE,sizeof(Vertex),(void*)offsetof(Vertex,member));glEnableVertexAttribArray(loc)
 ATTR(0,3,p);ATTR(1,4,n);ATTR(2,4,vc);ATTR(3,2,uv);ATTR(4,3,t);ATTR(5,3,b);ATTR(6,2,uv2);
 glActiveTexture(GL_TEXTURE15);glGenTextures(1,&color);glBindTexture(GL_TEXTURE_2D,color);glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA8,SZ,SZ,0,GL_RGBA,GL_UNSIGNED_BYTE,NULL);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST);glGenFramebuffers(1,&fbo);glBindFramebuffer(GL_FRAMEBUFFER,fbo);glFramebufferTexture2D(GL_FRAMEBUFFER,GL_COLOR_ATTACHMENT0,GL_TEXTURE_2D,color,0);if(glCheckFramebufferStatus(GL_FRAMEBUFFER)!=GL_FRAMEBUFFER_COMPLETE)fail("RGBA8fbo");
 glViewport(0,0,SZ,SZ);glDisable(GL_DEPTH_TEST);glDisable(GL_CULL_FACE);glDisable(GL_BLEND);glDisable(GL_DITHER);
 glUniformMatrix4fv(ul(prog,"mvp"),1,GL_FALSE,mvp);u3(prog,"eye",eye[0],eye[1],eye[2]);u3(prog,"sun_dir",0,0,1);u3(prog,"sun_color",0,0,0);u3(prog,"shadow_color",0,0,0);u3(prog,"fog_color",0,0,0);glUniform2f(ul(prog,"fog"),0,0);u1i(prog,"features",128|16|4);u1i(prog,"native_ao_on",0);u1i(prog,"shadow_on",0);u1i(prog,"depth_only",0);u1i(prog,"geometry_kind",0);glUniform2i(ul(prog,"grid_size"),1,1);u3(prog,"grid",0,0,1);
 checkgl("initial setup");
 out=fopen("gpu-cases.jsonl","w");if(!out)fail("write cases");
 for(diag=0;diag<2;diag++)for(unit=0;unit<(diag?2:1);unit++)for(a=0;a<(diag?1:3);a++)for(fr=0;fr<(diag?1:2);fr++)for(co=0;co<(diag?1:2);co++)for(ag=0;ag<(diag?1:2);ag++){
  char file[80];FILE*f;float av=diag?1:alpha[a];fillverts(v,av,unit);glBindBuffer(GL_ARRAY_BUFFER,vbo);glBufferSubData(GL_ARRAY_BUFFER,0,sizeof(v),v);
  mat.constant[0]=co?.13f:1;mat.constant[1]=co?.95f:1;mat.constant[2]=co?.27f:1;mat.constant[3]=co?.37f:1;mat.fresnel[0]=fr?1.4f:0;
  if(!oa_character_hardlight_upload(prog,&mat))fail("case upload");u1i(prog,"oa_probe",diag?1:0);glUniform2f(ul(prog,"ambient_scales"),ag?5.f:0.f,ag?.9f:0.f);glUniform4f(ul(prog,"sky_light"),ag?.7f:0,ag?.9f:0,ag?.3f:0,ag?3.2f:0);
  glClearColor(1,0,1,1);glClear(GL_COLOR_BUFFER_BIT);glDrawArrays(GL_TRIANGLES,0,3);glReadPixels(0,0,SZ,SZ,GL_RGBA,GL_UNSIGNED_BYTE,pixels);checkgl("case draw/read");
  sprintf(file,"case-%02d.rgba",id);f=fopen(file,"wb");if(!f)fail("write pixels");fwrite(pixels,1,sizeof(pixels),f);fclose(f);
  fprintf(out,"{\"id\":%d,\"file\":\"%s\",\"alpha\":%.9g,\"fresnel_on\":%d,\"constant_changed\":%d,\"generic_ambient_nonzero\":%d,\"diagnostic_normal\":%d,\"unit_basis_input\":%d,\"center_rgba\":[%u,%u,%u,%u]}\n",id,file,av,fr,co,ag,diag,unit,pixels[4*(16*SZ+16)],pixels[4*(16*SZ+16)+1],pixels[4*(16*SZ+16)+2],pixels[4*(16*SZ+16)+3]);id++;
 }
 fclose(out);
 {GLuint ft;GLenum complete;float encoded[SZ*SZ*4];FILE*nf;glActiveTexture(GL_TEXTURE15);glGenTextures(1,&ft);glBindTexture(GL_TEXTURE_2D,ft);glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA32F,SZ,SZ,0,GL_RGBA,GL_FLOAT,NULL);glFramebufferTexture2D(GL_FRAMEBUFFER,GL_COLOR_ATTACHMENT0,GL_TEXTURE_2D,ft,0);complete=glCheckFramebufferStatus(GL_FRAMEBUFFER);
 if(complete==GL_FRAMEBUFFER_COMPLETE){glDrawArrays(GL_TRIANGLES,0,3);glReadPixels(0,0,SZ,SZ,GL_RGBA,GL_FLOAT,encoded);checkgl("float normal diagnostic");nf=fopen("mapped-normal-rgba32f.bin","wb");if(!nf)fail("write float normal");fwrite(encoded,1,sizeof(encoded),nf);fclose(nf);}
 else {fprintf(stderr,"Float diagnostic unsupported FBOstatus=%x\n",complete);}
 if(complete==GL_FRAMEBUFFER_COMPLETE){
  const char *qv="#version 300 es\nvoid main(){vec2 p=vec2(float((gl_VertexID<<1)&2),float(gl_VertexID&2));gl_Position=vec4(p*2.-1.,0,1);}";
  const char *qf="#version 300 es\nprecision highp float;precision highp int;uniform float value;uniform int half_on;out vec4 o;void main(){float v=half_on!=0?unpackHalf2x16(packHalf2x16(vec2(value,0.))).x:value;o=vec4(v,v,v,1.);}";
  GLuint ht;float values[3]={.10002f,.3333f,.42158926f};GLuint qp=oa_post_program(qv,qf);int vi,ho;FILE*qout=fopen("conversion-probe.jsonl","w");
  if(!qp||!qout)fail("conversion probe");glGenTextures(1,&ht);glBindTexture(GL_TEXTURE_2D,ht);glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA16F,SZ,SZ,0,GL_RGBA,GL_HALF_FLOAT,NULL);glUseProgram(qp);
  for(vi=0;vi<3;vi++)for(ho=0;ho<2;ho++){float fp[4],hp[4];unsigned char bp[4];glUniform1f(ul(qp,"value"),values[vi]);glUniform1i(ul(qp,"half_on"),ho);
   glFramebufferTexture2D(GL_FRAMEBUFFER,GL_COLOR_ATTACHMENT0,GL_TEXTURE_2D,ft,0);glDrawArrays(GL_TRIANGLES,0,3);glReadPixels(16,16,1,1,GL_RGBA,GL_FLOAT,fp);
   glFramebufferTexture2D(GL_FRAMEBUFFER,GL_COLOR_ATTACHMENT0,GL_TEXTURE_2D,ht,0);if(glCheckFramebufferStatus(GL_FRAMEBUFFER)!=GL_FRAMEBUFFER_COMPLETE)fail("half target probe");glDrawArrays(GL_TRIANGLES,0,3);glReadPixels(16,16,1,1,GL_RGBA,GL_FLOAT,hp);glFramebufferTexture2D(GL_FRAMEBUFFER,GL_COLOR_ATTACHMENT0,GL_TEXTURE_2D,color,0);glDrawArrays(GL_TRIANGLES,0,3);glReadPixels(16,16,1,1,GL_RGBA,GL_UNSIGNED_BYTE,bp);checkgl("conversion probe");
   fprintf(qout,"{\"input\":%.9g,\"half_on\":%d,\"float_output\":%.12g,\"target_RGBA16F\":%.12g,\"rgba8\":%u}\n",values[vi],ho,fp[0],hp[0],bp[0]);}
  fclose(qout);glDeleteProgram(qp);glUseProgram(prog);
 }}
 glFinish();checkgl("finish");
 {oa_character_hardlight bad=mat;bad.constant[0]=NAN;if(oa_character_hardlight_upload(prog,&bad))fail("reject NaN");bad=mat;bad.specular[1]=-1;if(oa_character_hardlight_upload(prog,&bad))fail("reject negative gloss");bad=mat;bad.fresnel[1]=-1;if(oa_character_hardlight_upload(prog,&bad))fail("reject negative power");}
 printf("PASS: actual factory linked; %d RGBA8 fixture cases; uniform mapping and invalid-profile rejection passed.\n",id);
 glDeleteProgram(prog);eglMakeCurrent(d,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(d,ctx);eglDestroySurface(d,surf);eglTerminate(d);return 0;
}
