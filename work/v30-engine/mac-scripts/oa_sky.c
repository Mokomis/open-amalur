#include "oa_sky.h"
#include <android/log.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR,"OpemAmalurScene",__VA_ARGS__)
enum{RINGS=14,SEGMENTS=32,GRADIENT_BYTES=256*4};
/* Layer order, scroll rates, 2:1 layer scale and gradient-alpha coverage follow the game's sky pixel shader.
 * Its vertex shader was not recovered: gradient position (0.5+0.5*z), the dome offset, absolute cloud scale, horizon fade and fog colour below the horizon are host choices. */
static const char *vertex_source="#version 300 es\nlayout(location=0) in vec3 p;uniform mat4 mvp;uniform vec3 eye;uniform float radius;out vec3 dir;void main(){dir=p;vec4 c=mvp*vec4(eye+p*radius,1.0);gl_Position=vec4(c.xy,c.w*.99999,c.w);}";
static const char *fragment_source="#version 300 es\nprecision highp float;precision highp sampler3D;in vec3 dir;uniform sampler2D gradient;uniform sampler2D lower;uniform sampler2D upper;uniform sampler3D lut;uniform vec4 lower_tint;uniform vec4 upper_tint;uniform float time;uniform int use_lut;out vec4 color;"
 "void main(){vec3 d=normalize(dir);vec4 g=texture(gradient,vec2(.5+.5*d.z,.5));vec3 c=mix(vec3(.4196,.3608,.2235),g.rgb,smoothstep(-0.03,0.0,d.z));if(d.z>0.0){float guard=clamp(d.z*6.0,0.0,1.0);vec2 plane=d.xy/(d.z+.5);"
 "vec4 u=texture(upper,(plane+time*.000488)*.3);c=mix(c,u.rgb*upper_tint.rgb,u.a*upper_tint.a*g.a*guard);"
 "vec4 l=texture(lower,(plane.yx+time*.00293)*.6);c=mix(c,l.rgb*lower_tint.rgb,l.a*lower_tint.a*g.a*guard);}"
 "color=vec4(use_lut!=0?texture(lut,clamp(c,0.0,1.0)*.9375+.03125).rgb:c,1.0);}";
static GLuint compile(GLenum type,const char *source){GLint okay=0;GLuint s=glCreateShader(type);glShaderSource(s,1,&source,NULL);glCompileShader(s);glGetShaderiv(s,GL_COMPILE_STATUS,&okay);
 if(!okay){char log[1024];GLsizei n=0;glGetShaderInfoLog(s,sizeof(log)-1,&n,log);log[n]=0;LOGE("Sky shader: %s",log);glDeleteShader(s);return 0;}return s;}
static GLuint upload(const uint8_t *rgba,GLsizei w,GLsizei h,GLint wrap,int mips){GLuint t;glGenTextures(1,&t);glBindTexture(GL_TEXTURE_2D,t);glPixelStorei(GL_UNPACK_ALIGNMENT,1);glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA8,w,h,0,GL_RGBA,GL_UNSIGNED_BYTE,rgba);
 if(mips)glGenerateMipmap(GL_TEXTURE_2D);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,mips?GL_LINEAR_MIPMAP_LINEAR:GL_LINEAR);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_LINEAR);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,wrap);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,wrap);glPixelStorei(GL_UNPACK_ALIGNMENT,4);return t;}
int oa_sky_open(oa_sky *s,const uint8_t *b,size_t size){
 size_t at=8+GRADIENT_BYTES;uint32_t w,h;GLuint vs,fs;GLint okay=0;float tints[8];unsigned r,q,n=0,i=0;float *verts;unsigned short *index;memset(s,0,sizeof(*s));
 if(size<at+32+8||memcmp(b,"OASKY001",8)){LOGE("Sky asset invalid");return 0;}
 memcpy(tints,b+at,32);at+=32;memcpy(s->lower_tint,tints,16);memcpy(s->upper_tint,tints+4,16);
 vs=compile(GL_VERTEX_SHADER,vertex_source);fs=vs?compile(GL_FRAGMENT_SHADER,fragment_source):0;if(!fs){if(vs)glDeleteShader(vs);return 0;}
 s->program=glCreateProgram();glAttachShader(s->program,vs);glAttachShader(s->program,fs);glLinkProgram(s->program);glDeleteShader(vs);glDeleteShader(fs);glGetProgramiv(s->program,GL_LINK_STATUS,&okay);
 if(!okay){LOGE("Sky link failed");oa_sky_close(s);return 0;}
 s->gradient=upload(b+8,256,1,GL_CLAMP_TO_EDGE,0);
 memcpy(&w,b+at,4);memcpy(&h,b+at+4,4);at+=8;if(!w||!h||w>4096||h>4096||(uint64_t)w*h*4>size-at){LOGE("Sky lower layer invalid");oa_sky_close(s);return 0;}
 s->lower=upload(b+at,(GLsizei)w,(GLsizei)h,GL_REPEAT,1);at+=(size_t)w*h*4;
 if(size-at<8){LOGE("Sky upper layer missing");oa_sky_close(s);return 0;}memcpy(&w,b+at,4);memcpy(&h,b+at+4,4);at+=8;if(!w||!h||w>4096||h>4096||(uint64_t)w*h*4!=size-at){LOGE("Sky upper layer invalid");oa_sky_close(s);return 0;}
 s->upper=upload(b+at,(GLsizei)w,(GLsizei)h,GL_REPEAT,1);
 verts=(float*)malloc(sizeof(float)*3*(RINGS+1)*(SEGMENTS+1));index=(unsigned short*)malloc(sizeof(unsigned short)*6*RINGS*SEGMENTS);if(!verts||!index){free(verts);free(index);oa_sky_close(s);return 0;}
 for(r=0;r<=RINGS;r++){float a=(float)r/RINGS*3.14159265f-1.57079633f;for(q=0;q<=SEGMENTS;q++){float b2=(float)q/SEGMENTS*6.28318531f;verts[n++]=cosf(a)*cosf(b2);verts[n++]=cosf(a)*sinf(b2);verts[n++]=sinf(a);}}
 for(r=0;r<RINGS;r++)for(q=0;q<SEGMENTS;q++){unsigned short v=(unsigned short)(r*(SEGMENTS+1)+q);index[i++]=v;index[i++]=v+1;index[i++]=v+SEGMENTS+1;index[i++]=v+1;index[i++]=v+SEGMENTS+2;index[i++]=v+SEGMENTS+1;}
 s->count=(GLsizei)i;glGenVertexArrays(1,&s->array);glBindVertexArray(s->array);glGenBuffers(1,&s->buffer);glBindBuffer(GL_ARRAY_BUFFER,s->buffer);glBufferData(GL_ARRAY_BUFFER,(GLsizeiptr)(sizeof(float)*n),verts,GL_STATIC_DRAW);
 glGenBuffers(1,&s->indices);glBindBuffer(GL_ELEMENT_ARRAY_BUFFER,s->indices);glBufferData(GL_ELEMENT_ARRAY_BUFFER,(GLsizeiptr)(sizeof(unsigned short)*i),index,GL_STATIC_DRAW);glEnableVertexAttribArray(0);glVertexAttribPointer(0,3,GL_FLOAT,GL_FALSE,12,(const void*)0);glBindVertexArray(0);free(verts);free(index);
 s->mvp=glGetUniformLocation(s->program,"mvp");s->eye=glGetUniformLocation(s->program,"eye");s->radius=glGetUniformLocation(s->program,"radius");s->time=glGetUniformLocation(s->program,"time");
 if(glGetError()!=GL_NO_ERROR){LOGE("Sky upload failed");oa_sky_close(s);return 0;}
 s->ready=1;return 1;
}
void oa_sky_close(oa_sky *s){if(s->gradient)glDeleteTextures(1,&s->gradient);if(s->lower)glDeleteTextures(1,&s->lower);if(s->upper)glDeleteTextures(1,&s->upper);if(s->array)glDeleteVertexArrays(1,&s->array);if(s->buffer)glDeleteBuffers(1,&s->buffer);if(s->indices)glDeleteBuffers(1,&s->indices);if(s->program)glDeleteProgram(s->program);memset(s,0,sizeof(*s));}
void oa_sky_draw(const oa_sky *s,const float mvp[16],const float eye[3],float radius,float seconds,GLuint lut){
 if(!s->ready)return;
 glDepthMask(GL_FALSE);glDisable(GL_DEPTH_TEST);glUseProgram(s->program);glUniformMatrix4fv(s->mvp,1,GL_FALSE,mvp);glUniform3fv(s->eye,1,eye);glUniform1f(s->radius,radius);glUniform1f(s->time,seconds);
 glActiveTexture(GL_TEXTURE0);glBindTexture(GL_TEXTURE_2D,s->gradient);glUniform1i(glGetUniformLocation(s->program,"gradient"),0);
 glActiveTexture(GL_TEXTURE1);glBindTexture(GL_TEXTURE_2D,s->lower);glUniform1i(glGetUniformLocation(s->program,"lower"),1);
 glActiveTexture(GL_TEXTURE2);glBindTexture(GL_TEXTURE_2D,s->upper);glUniform1i(glGetUniformLocation(s->program,"upper"),2);
 glActiveTexture(GL_TEXTURE3);glBindTexture(GL_TEXTURE_3D,lut);glUniform1i(glGetUniformLocation(s->program,"lut"),3);glUniform1i(glGetUniformLocation(s->program,"use_lut"),lut!=0);
 glUniform4fv(glGetUniformLocation(s->program,"lower_tint"),1,s->lower_tint);glUniform4fv(glGetUniformLocation(s->program,"upper_tint"),1,s->upper_tint);
 glBindVertexArray(s->array);glDrawElements(GL_TRIANGLES,s->count,GL_UNSIGNED_SHORT,0);glBindVertexArray(0);
 glActiveTexture(GL_TEXTURE0);glEnable(GL_DEPTH_TEST);glDepthMask(GL_TRUE);
}
