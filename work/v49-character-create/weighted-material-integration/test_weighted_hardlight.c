#include <EGL/egl.h>
#include <EGL/eglext.h>
#include <GLES3/gl3.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <stdarg.h>
#include <math.h>
#include "oa_weighted_hardlight.h"
#include "oa_character_attributes.h"
#include "oa_render_cache.h"
#include "opening_sha256.h"
#define R "C:\\Users\\rwill\\Documents\\Opem Amalur\\"
#define S 256
#define CAPACITY 113
int __android_log_print(int l,const char*t,const char*f,...){va_list a;int n;(void)l;fprintf(stderr,"%s: ",t);va_start(a,f);n=vfprintf(stderr,f,a);va_end(a);fputc('\n',stderr);return n;}
void oa_desktop_material_probe_texture(GLuint x,int w,int h,const char*s){(void)x;(void)w;(void)h;(void)s;}
static void fail(const char*s){fprintf(stderr,"FAIL %s GL=%x EGL=%x\n",s,glGetError(),eglGetError());exit(2);}
static void glok(const char*s){GLenum e=glGetError();if(e){fprintf(stderr,"GL=%x %s\n",e,s);exit(2);}}
static void save(const char*n,const void*b,size_t z){FILE*f=fopen(n,"wb");if(!f||fwrite(b,1,z,f)!=z)fail("save");fclose(f);}
static int readfile(void*user,const char*name,uint8_t**b,size_t*n){FILE*f;long z;const char*deny=(const char*)user;*b=NULL;*n=0;if(deny&&strstr(name,deny))return 0;f=fopen(name,"rb");if(!f)return 0;if(fseek(f,0,SEEK_END)||((z=ftell(f))<=0)||fseek(f,0,SEEK_SET)){fclose(f);return 0;}*b=(uint8_t*)malloc((size_t)z);if(!*b||fread(*b,1,(size_t)z,f)!=(size_t)z){free(*b);*b=NULL;fclose(f);return 0;}fclose(f);*n=(size_t)z;return 1;}
static GLint U(GLuint p,const char*n){return glGetUniformLocation(p,n);}
static GLuint shader(GLenum type,const char*s){GLuint q=glCreateShader(type);GLint ok;glShaderSource(q,1,&s,NULL);glCompileShader(q);glGetShaderiv(q,GL_COMPILE_STATUS,&ok);if(!ok){char log[4096];glGetShaderInfoLog(q,sizeof(log),NULL,log);fprintf(stderr,"%s\n",log);fail("TF compile");}return q;}
static GLuint feedback_program(void){const char*fs="#version 300 es\nprecision highp float;out vec4 o;void main(){o=vec4(1.);}";
 const char*vary[6]={"W","N0","TW","BW","VC","UV"};GLuint p=glCreateProgram(),v=shader(GL_VERTEX_SHADER,oa_weighted_hardlight_vertex_source()),f=shader(GL_FRAGMENT_SHADER,fs);GLint ok;
 glAttachShader(p,v);glAttachShader(p,f);glTransformFeedbackVaryings(p,6,vary,GL_INTERLEAVED_ATTRIBS);glLinkProgram(p);glGetProgramiv(p,GL_LINK_STATUS,&ok);if(!ok){char log[4096];glGetProgramInfoLog(p,sizeof(log),NULL,log);fprintf(stderr,"%s\n",log);fail("TF link");}glDeleteShader(v);glDeleteShader(f);return p;}
static void dump_actual_sources(GLuint p){GLuint q[8];GLsizei n;int i;glGetAttachedShaders(p,8,&n,q);for(i=0;i<n;i++){GLint len,type;char name[80];char*b;glGetShaderiv(q[i],GL_SHADER_SOURCE_LENGTH,&len);glGetShaderiv(q[i],GL_SHADER_TYPE,&type);b=(char*)malloc((size_t)len+1);glGetShaderSource(q[i],len,NULL,b);snprintf(name,sizeof(name),"actual-weighted-%s.glsl",type==GL_VERTEX_SHADER?"vertex":"fragment");save(name,b,strlen(b));free(b);}}
static void camera(float vp[16],const oa_character*c){memset(vp,0,64);vp[0]=1.f/125;vp[9]=1.f/125;vp[6]=1.f/400;vp[12]=-c->feet[0]/125;vp[13]=-(c->feet[2]+90)/125;vp[14]=-c->feet[1]/400;vp[15]=1;}
static GLuint begin_at(oa_weighted_hardlight*g,const oa_character*c){float eye[3]={c->feet[0],c->feet[1]-400,c->feet[2]+90};GLuint p=oa_weighted_hardlight_begin(g,eye);if(!p)fail("actual eye frame begin");return p;}
static int pixels(const char*name){uint8_t*b=(uint8_t*)malloc(S*S*4);int i,n=0;glReadPixels(0,0,S,S,GL_RGBA,GL_UNSIGNED_BYTE,b);for(i=0;i<S*S;i++)if(b[i*4+3])n++;save(name,b,S*S*4);free(b);return n;}
int main(void){EGLDisplay d;EGLConfig cfg;EGLSurface surf;EGLContext ec;EGLint nc,maj,min;GLuint fbo,ct,depth,ubo,tf,fbprog;float *zero;FILE*log;unsigned i,caseid;oa_character c;oa_weighted_hardlight g,gtest;char error[256];uint8_t *base,*attrs,*pal,*cube;size_t bn,an,pn,cn;unsigned normal_count,palette_count;uint32_t mask;uint8_t hash[32];char hex[65];
 const EGLint ca[]={EGL_SURFACE_TYPE,EGL_PBUFFER_BIT,EGL_RENDERABLE_TYPE,EGL_OPENGL_ES3_BIT_KHR,EGL_RED_SIZE,8,EGL_GREEN_SIZE,8,EGL_BLUE_SIZE,8,EGL_ALPHA_SIZE,8,EGL_NONE},sa[]={EGL_WIDTH,S,EGL_HEIGHT,S,EGL_NONE},xa[]={EGL_CONTEXT_CLIENT_VERSION,3,EGL_NONE};
 memset(&c,0,sizeof(c));memset(&g,0,sizeof(g));memset(&gtest,0,sizeof(gtest));
 if(!readfile(NULL,R"work\\v49-character-create\\packs\\Almain_Male\\character.bin",&base,&bn)||!readfile(NULL,R"work\\v49-character-create\\vertex-contract-audit\\almain-male-attributes.oacat",&attrs,&an)||!readfile(NULL,R"work\\v49-character-create\\limb-skinning-audit\\almain-male-palette-corrections.oacpl",&pal,&pn)||!readfile(NULL,R"work\\v49-character-create\\character-ambient-audit\\opening-base-character-ambient.bgra",&cube,&cn))fail("source files");
 if(!oa_character_repairs_apply(base,bn,attrs,an,pal,pn,&normal_count,&palette_count,error,sizeof(error)))fail(error);sha256(base,bn,hash);for(i=0;i<32;i++)sprintf(hex+2*i,"%02x",hash[i]);printf("repaired_heap_sha=%s normals=%u palettes=%u\n",hex,normal_count,palette_count);
 if(!oa_character_parse(&c,base,bn,error,sizeof(error)))fail(error);
 d=eglGetDisplay(EGL_DEFAULT_DISPLAY);if(!eglInitialize(d,&maj,&min)||!eglBindAPI(EGL_OPENGL_ES_API)||!eglChooseConfig(d,ca,&cfg,1,&nc)||!nc)fail("EGL init");surf=eglCreatePbufferSurface(d,cfg,sa);ec=eglCreateContext(d,cfg,EGL_NO_CONTEXT,xa);if(!eglMakeCurrent(d,surf,surf,ec))fail("EGL context");
 log=fopen("renderer.json","w");fprintf(log,"{\"egl\":\"%d.%d\",\"vendor\":\"%s\",\"renderer\":\"%s\",\"version\":\"%s\",\"glsl\":\"%s\",\"surface\":\"256x256pbuffer,no native window\"}\n",maj,min,glGetString(GL_VENDOR),glGetString(GL_RENDERER),glGetString(GL_VERSION),glGetString(GL_SHADING_LANGUAGE_VERSION));fclose(log);
 mask=oa_weighted_hardlight_open(&g,&c,attrs,an,cube,cn,readfile,NULL,R"work\\v49-character-create\\material-integration\\native-clothing-stage\\",OA_WH_ALLOWED_MASK,CAPACITY,error,sizeof(error));printf("admitted_mask=%u diagnostic=%s\n",mask,error);if(mask!=OA_WH_ALLOWED_MASK)fail("all4source parts not admitted");dump_actual_sources(g.program);{float vp[16];camera(vp,&c);if(oa_weighted_hardlight_draw_part(&g,&c,1,vp)!=0)fail("draw admitted before valid frame eye");}
 if(g.parts[0].color_provenance!=OA_WH_COLOR_NATIVE_SHARED_ALL_FF||g.parts[1].color_provenance!=OA_WH_COLOR_AUTHORED||g.parts[2].color_provenance!=OA_WH_COLOR_NATIVE_SHARED_ALL_FF||g.parts[3].color_provenance!=OA_WH_COLOR_AUTHORED)fail("color provenance");
 glGenTextures(1,&ct);glBindTexture(GL_TEXTURE_2D,ct);glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA8,S,S,0,GL_RGBA,GL_UNSIGNED_BYTE,NULL);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST);
 glGenTextures(1,&depth);glBindTexture(GL_TEXTURE_2D,depth);glTexImage2D(GL_TEXTURE_2D,0,GL_DEPTH_COMPONENT24,S,S,0,GL_DEPTH_COMPONENT,GL_UNSIGNED_INT,NULL);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST);
 glGenFramebuffers(1,&fbo);glBindFramebuffer(GL_FRAMEBUFFER,fbo);glFramebufferTexture2D(GL_FRAMEBUFFER,GL_COLOR_ATTACHMENT0,GL_TEXTURE_2D,ct,0);glFramebufferTexture2D(GL_FRAMEBUFFER,GL_DEPTH_ATTACHMENT,GL_TEXTURE_2D,depth,0);if(glCheckFramebufferStatus(GL_FRAMEBUFFER)!=GL_FRAMEBUFFER_COMPLETE)fail("framebuffer");
 zero=(float*)calloc(CAPACITY*8,sizeof(float));glGenBuffers(1,&ubo);glBindBuffer(GL_UNIFORM_BUFFER,ubo);glBufferData(GL_UNIFORM_BUFFER,CAPACITY*8*sizeof(float),zero,GL_STATIC_DRAW);glBindBufferBase(GL_UNIFORM_BUFFER,0,ubo);free(zero);
 fbprog=feedback_program();glGenBuffers(1,&tf);glViewport(0,0,S,S);glEnable(GL_DEPTH_TEST);glDepthFunc(GL_LEQUAL);glDepthMask(GL_TRUE);glDisable(GL_BLEND);glDisable(GL_CULL_FACE);glDisable(GL_DITHER);glClearColor(0,0,0,0);
 log=fopen("pose-cases.jsonl","w");
 for(caseid=0;caseid<4;caseid++){float vp[16];unsigned clip=caseid&1u,frame=clip?8:0;float facing=caseid<2?0.f:(caseid==2?.7f:1.4f);
  memset(c.weight,0,sizeof(c.weight));memset(c.time,0,sizeof(c.time));c.weight[clip]=1;c.time[clip]=(float)frame/c.clips[clip].fps;c.facing=facing;c.feet[0]=caseid==2?35.f:caseid==3?-50.f:0;c.feet[1]=caseid==2?-15.f:caseid==3?25.f:0;c.feet[2]=caseid>=2?10.f:0;c.slope=c.lean=0;c.hidden=0;oa_character_pose(&c);camera(vp,&c);
  for(i=0;i<4;i++){oa_wh_part*q=g.parts+i;float rows[OA_CHAR_MAX_PALETTE*12];unsigned n=oa_character_bones(&c,c.parts+q->part,rows);char name[128];size_t bytes=(size_t)q->vertices*18*sizeof(float);void*mapped;int covered;unsigned k;
   snprintf(name,sizeof(name),"pose-%u-part%u-bones.bin",caseid,q->part);save(name,rows,n*48);
   glUseProgram(fbprog);glUniformMatrix4fv(U(fbprog,"mvp"),1,GL_FALSE,vp);glUniform4fv(U(fbprog,"char_bones[0]"),(GLsizei)n*3,rows);glUniform2f(U(fbprog,"char_facing_sc"),sinf(facing),cosf(facing));glUniform2f(U(fbprog,"fog"),0,0);
   glBindVertexArray(q->vao);if(q->color_provenance==OA_WH_COLOR_NATIVE_SHARED_ALL_FF)glVertexAttrib4f(7,1,1,1,1);glBindBuffer(GL_TRANSFORM_FEEDBACK_BUFFER,tf);glBufferData(GL_TRANSFORM_FEEDBACK_BUFFER,(GLsizeiptr)bytes,NULL,GL_STREAM_READ);glBindBufferBase(GL_TRANSFORM_FEEDBACK_BUFFER,0,tf);glEnable(GL_RASTERIZER_DISCARD);glBeginTransformFeedback(GL_POINTS);glDrawArrays(GL_POINTS,0,(GLsizei)q->vertices);glEndTransformFeedback();glDisable(GL_RASTERIZER_DISCARD);
   mapped=glMapBufferRange(GL_TRANSFORM_FEEDBACK_BUFFER,0,(GLsizeiptr)bytes,GL_MAP_READ_BIT);if(!mapped)fail("feedback read");snprintf(name,sizeof(name),"pose-%u-part%u-feedback.bin",caseid,q->part);save(name,mapped,bytes);if(!glUnmapBuffer(GL_TRANSFORM_FEEDBACK_BUFFER))fail("feedback unmap");glok("feedback");
   begin_at(&g,&c);glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);if(oa_weighted_hardlight_draw_part(&g,&c,q->part,vp)!=1)fail("real material draw");snprintf(name,sizeof(name),"pose-%u-part%u.rgba",caseid,q->part);covered=pixels(name);if(covered<=0)fail("empty clothing part image");
   fprintf(log,"{\"pose\":%u,\"clip\":%u,\"frame\":%u,\"facing\":%.9g,\"feet\":[%.9g,%.9g,%.9g],\"part\":%u,\"material\":%u,\"vertices\":%u,\"indices\":%u,\"palette_count\":%u,\"color_provenance\":%u,\"covered_pixels\":%d,\"mvp\":[",caseid,clip,frame,facing,c.feet[0],c.feet[1],c.feet[2],q->part,q->material,q->vertices,q->indices,n,q->color_provenance,covered);for(k=0;k<16;k++)fprintf(log,"%s%.9g",k?",":"",vp[k]);fprintf(log,"]}\n");
  }
  begin_at(&g,&c);glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);for(i=0;i<4;i++)if(oa_weighted_hardlight_draw_part(&g,&c,g.parts[i].part,vp)!=1)fail("combined draw");{char name[80];snprintf(name,sizeof(name),"pose-%u-all.rgba",caseid);if(!pixels(name))fail("empty combined");}
 }
 fclose(log);
 /* Fail-closed per-part resource test: only feet diffuse denied. Others admit. */
 mask=oa_weighted_hardlight_open(&gtest,&c,attrs,an,cube,cn,readfile,"660620-portable512",R"work\\v49-character-create\\material-integration\\native-clothing-stage\\",OA_WH_ALLOWED_MASK,CAPACITY,error,sizeof(error));if(mask!=(OA_WH_ALLOWED_MASK&~(1u<<1)))fail("partial fallback mask");printf("missing_feet_texture_mask=%u\n",mask);oa_weighted_hardlight_close(&gtest);
 {uint8_t old=attrs[100];attrs[100]^=1;mask=oa_weighted_hardlight_open(&gtest,&c,attrs,an,cube,cn,readfile,NULL,"",OA_WH_ALLOWED_MASK,CAPACITY,error,sizeof(error));attrs[100]=old;if(mask||gtest.program)fail("corrupt OACAT accepted");}
 {uint8_t old=cube[0];cube[0]^=1;mask=oa_weighted_hardlight_open(&gtest,&c,attrs,an,cube,cn,readfile,NULL,"",OA_WH_ALLOWED_MASK,CAPACITY,error,sizeof(error));cube[0]=old;if(mask||gtest.program)fail("wrong cube accepted");}
 {float vp[16];camera(vp,&c);if(oa_weighted_hardlight_draw_part(&g,&c,0,vp)!=0)fail("unsupported part not fallback");c.hidden|=1u<<1;if(oa_weighted_hardlight_draw_part(&g,&c,1,vp)!=0)fail("hidden part draw");c.hidden=0;begin_at(&g,&c);glUniform1i(U(g.program,"features"),0);if(oa_weighted_hardlight_draw_part(&g,&c,1,vp)!=0)fail("nativefeatureoff notfallback");}
 glFinish();glok("finish");printf("PASS 4parts*4production poses rendered + full vertex feedback; partial/malformed/hidden/unsupported/nativeoff fallback checks.\n");
 oa_weighted_hardlight_close(&g);glDeleteProgram(fbprog);oa_character_free(&c);free(attrs);free(pal);free(cube);eglMakeCurrent(d,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(d,ec);eglDestroySurface(d,surf);eglTerminate(d);return 0;
}
