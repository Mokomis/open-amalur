#include "oa_fx.h"
#include <GLES3/gl3.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>
/* Billboards with the game's own spawn rates, lifetimes, gradients and sizes. Effects start within the game's cluster fade distance. The particle limit, and how velocity and spin are read, are this code's choices. */
enum{FX_MAX=3000,FX_TYPE_FLOATS=53,FX_FADE_NEAR=8000,FX_FADE_FAR=10000};
typedef struct fx_type{float tex,add,period,period_var,burst,box[3],off[3],vel[3],rnd[3],life,life_var,size0,size1,cols,rows,spin,spin2,color[4][4],alpha[6][2];}fx_type;
typedef struct fx_place{float pos[3],type,q[4];}fx_place;
typedef struct fx_part{float pos[3],vel[3],age,life,angle,spin,start_frame;int type;}fx_part;
struct oa_fx{uint32_t textures,types,places;GLuint *tex;fx_type *type;fx_place *place;float *wait;fx_part *part;int live,seed;GLuint program,vao,quad,inst;float *cpu;GLint u_mvp,u_right,u_up,u_fog,u_fogc,u_add;};
static const char fx_vs[]="#version 300 es\nlayout(location=0)in vec2 c;layout(location=1)in vec4 ps;layout(location=2)in vec4 col;layout(location=3)in vec4 cell;layout(location=4)in float ang;uniform mat4 mvp;uniform vec3 right_v,up_v;uniform vec2 fog;out vec2 UV;out mediump vec4 C;out mediump float F;void main(){float s=sin(ang),k=cos(ang);vec2 r=vec2(c.x*k-c.y*s,c.x*s+c.y*k)*ps.w;vec3 p=ps.xyz+right_v*r.x+up_v*r.y;gl_Position=mvp*vec4(p,1.0);UV=cell.xy+(c*vec2(.5,-.5)+.5)*cell.zw;C=col;F=1.0-min(exp(-(fog.x*gl_Position.w+fog.y)),1.0);}";
static const char fx_fs[]="#version 300 es\nprecision mediump float;in highp vec2 UV;in vec4 C;in float F;uniform sampler2D t;uniform vec3 fogc;uniform float add_mode;out vec4 o;void main(){vec4 d=texture(t,UV)*C;if(add_mode>.5)o=vec4(d.rgb*(1.0-F),d.a);else o=vec4(mix(d.rgb,fogc,F),d.a);}";
static GLuint shader(GLenum kind,const char *src){GLuint s=glCreateShader(kind);glShaderSource(s,1,&src,NULL);glCompileShader(s);return s;}
static float rnd(oa_fx *f){f->seed=f->seed*1103515245+12345;return (float)((f->seed>>16)&0x7fff)/32767.f;}
static float rnd2(oa_fx *f){return rnd(f)*2.f-1.f;}
static void qrot3(float o[3],const float q[4],const float v[3]){float t[3]={2*(q[1]*v[2]-q[2]*v[1]),2*(q[2]*v[0]-q[0]*v[2]),2*(q[0]*v[1]-q[1]*v[0])};o[0]=v[0]+q[3]*t[0]+q[1]*t[2]-q[2]*t[1];o[1]=v[1]+q[3]*t[1]+q[2]*t[0]-q[0]*t[2];o[2]=v[2]+q[3]*t[2]+q[0]*t[1]-q[1]*t[0];}
oa_fx *oa_fx_open(AAssetManager *manager){
 AAsset *as=AAssetManager_open(manager,"fx/fx.bin",AASSET_MODE_BUFFER);const uint8_t *b;size_t n,at=8;oa_fx *f;uint32_t head[4],i;
 if(!as)return NULL;
 b=(const uint8_t*)AAsset_getBuffer(as);n=(size_t)AAsset_getLength64(as);
 if(!b||n<24||memcmp(b,"OAFX0001",8)){AAsset_close(as);return NULL;}
 memcpy(head,b+at,16);at+=16;
 f=(oa_fx*)calloc(1,sizeof(*f));
 if(!f||head[3]!=FX_TYPE_FLOATS||sizeof(fx_type)!=FX_TYPE_FLOATS*sizeof(float)){free(f);AAsset_close(as);return NULL;}
 f->textures=head[0];f->types=head[1];f->places=head[2];f->seed=431608;
 f->tex=(GLuint*)calloc(f->textures+1u,sizeof(GLuint));glGenTextures((GLsizei)f->textures,f->tex);
 for(i=0;i<f->textures;i++){uint32_t wh[2];memcpy(wh,b+at,8);at+=8;glBindTexture(GL_TEXTURE_2D,f->tex[i]);glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA8,(GLsizei)wh[0],(GLsizei)wh[1],0,GL_RGBA,GL_UNSIGNED_BYTE,b+at);glGenerateMipmap(GL_TEXTURE_2D);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_LINEAR_MIPMAP_LINEAR);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_LINEAR);at+=(size_t)wh[0]*wh[1]*4u;}
 f->type=(fx_type*)malloc(sizeof(fx_type)*(f->types+1u));memcpy(f->type,b+at,sizeof(fx_type)*f->types);at+=sizeof(fx_type)*f->types;
 f->place=(fx_place*)malloc(sizeof(fx_place)*(f->places+1u));memcpy(f->place,b+at,sizeof(fx_place)*f->places);at+=sizeof(fx_place)*f->places;
 AAsset_close(as);
 f->wait=(float*)calloc(f->places+1u,sizeof(float));f->part=(fx_part*)malloc(sizeof(fx_part)*FX_MAX);f->cpu=(float*)malloc(sizeof(float)*13u*FX_MAX);
 {GLuint vs=shader(GL_VERTEX_SHADER,fx_vs),fs=shader(GL_FRAGMENT_SHADER,fx_fs);static const float quad[8]={-1,-1,1,-1,-1,1,1,1};f->program=glCreateProgram();glAttachShader(f->program,vs);glAttachShader(f->program,fs);glLinkProgram(f->program);glDeleteShader(vs);glDeleteShader(fs);
  f->u_mvp=glGetUniformLocation(f->program,"mvp");f->u_right=glGetUniformLocation(f->program,"right_v");f->u_up=glGetUniformLocation(f->program,"up_v");f->u_fog=glGetUniformLocation(f->program,"fog");f->u_fogc=glGetUniformLocation(f->program,"fogc");f->u_add=glGetUniformLocation(f->program,"add_mode");
  glGenVertexArrays(1,&f->vao);glGenBuffers(1,&f->quad);glGenBuffers(1,&f->inst);glBindVertexArray(f->vao);glBindBuffer(GL_ARRAY_BUFFER,f->quad);glBufferData(GL_ARRAY_BUFFER,sizeof(quad),quad,GL_STATIC_DRAW);glEnableVertexAttribArray(0);glVertexAttribPointer(0,2,GL_FLOAT,GL_FALSE,0,0);
  glBindBuffer(GL_ARRAY_BUFFER,f->inst);glBufferData(GL_ARRAY_BUFFER,(GLsizeiptr)(sizeof(float)*13u*FX_MAX),NULL,GL_STREAM_DRAW);
  {static const int sizes[4]={4,4,4,1},at_[4]={0,16,32,48};int a;for(a=0;a<4;a++){glEnableVertexAttribArray((GLuint)a+1u);glVertexAttribPointer((GLuint)a+1u,sizes[a],GL_FLOAT,GL_FALSE,52,(void*)(intptr_t)at_[a]);glVertexAttribDivisor((GLuint)a+1u,1);}}
  glBindVertexArray(0);glBindBuffer(GL_ARRAY_BUFFER,0);}
 return f;}
void oa_fx_close(oa_fx *f){if(!f)return;glDeleteTextures((GLsizei)f->textures,f->tex);glDeleteProgram(f->program);glDeleteVertexArrays(1,&f->vao);glDeleteBuffers(1,&f->quad);glDeleteBuffers(1,&f->inst);free(f->tex);free(f->type);free(f->place);free(f->wait);free(f->part);free(f->cpu);free(f);}
int oa_fx_live(const oa_fx *f){return f?f->live:0;}
void oa_fx_update(oa_fx *f,const float eye[3],float dt){
 uint32_t i;int k;if(!f)return;
 for(k=0;k<f->live;){fx_part *p=f->part+k;p->age+=dt;if(p->age>=p->life){*p=f->part[--f->live];continue;}p->pos[0]+=p->vel[0]*dt;p->pos[1]+=p->vel[1]*dt;p->pos[2]+=p->vel[2]*dt;p->angle+=p->spin*dt;k++;}
 for(i=0;i<f->places;i++){const fx_place *pl=f->place+i;const fx_type *t=f->type+(int)pl->type;float dx=pl->pos[0]-eye[0],dy=pl->pos[1]-eye[1],dz=pl->pos[2]-eye[2];
  if(dx*dx+dy*dy+dz*dz>(float)FX_FADE_FAR*FX_FADE_FAR)continue;
  f->wait[i]-=dt;
  while(f->wait[i]<=0&&f->live<FX_MAX){int b,burst=(int)t->burst;f->wait[i]+=t->period+t->period_var*rnd2(f)>.02f?t->period+t->period_var*rnd2(f):.02f;
   for(b=0;b<burst&&f->live<FX_MAX;b++){fx_part *p=f->part+f->live++;float v[3]={t->box[0]*rnd2(f)+t->off[0],t->box[1]*rnd2(f)+t->off[1],t->box[2]*rnd2(f)+t->off[2]},w[3]={t->vel[0]+t->rnd[0]*rnd2(f),t->vel[1]+t->rnd[1]*rnd2(f),t->vel[2]+t->rnd[2]*rnd2(f)},o[3];
    qrot3(o,pl->q,v);p->pos[0]=pl->pos[0]+o[0];p->pos[1]=pl->pos[1]+o[1];p->pos[2]=pl->pos[2]+o[2];qrot3(p->vel,pl->q,w);p->age=0;p->life=t->life+t->life_var*rnd2(f);if(p->life<.05f)p->life=.05f;p->angle=rnd(f)*6.283f;p->spin=(t->spin2+(t->spin-t->spin2)*rnd(f))*.01745f;p->start_frame=rnd(f)*t->cols*t->rows;p->type=(int)pl->type;}}
  if(f->wait[i]<=0)f->wait[i]=.1f;}
}
static void colour_at(const fx_type *t,float a,float o[4]){int i;const float (*c)[4]=t->color;for(i=0;i<3&&a>c[i+1][0];i++);{float span=c[i+1][0]-c[i][0],m=span>1e-4f?(a-c[i][0])/span:0;int e;if(m<0)m=0;if(m>1)m=1;for(e=0;e<3;e++)o[e]=c[i][e+1]+(c[i+1][e+1]-c[i][e+1])*m;}
 {const float (*k)[2]=t->alpha;for(i=0;i<5&&a>k[i+1][0];i++);{float span=k[i+1][0]-k[i][0],m=span>1e-4f?(a-k[i][0])/span:0;if(m<0)m=0;if(m>1)m=1;o[3]=k[i][1]+(k[i+1][1]-k[i][1])*m;}}}
void oa_fx_draw(oa_fx *f,const float mvp[16],const float fog_color[3],float fog_a,float fog_b){
 float right[3]={mvp[0],mvp[4],mvp[8]},up[3]={mvp[1],mvp[5],mvp[9]},n;float eye_far=(float)FX_FADE_FAR;int mode,k;GLboolean was_blend,was_depth,was_cull,was_write;(void)eye_far;
 if(!f||!f->live||!f->program)return;
 n=sqrtf(right[0]*right[0]+right[1]*right[1]+right[2]*right[2]);right[0]/=n;right[1]/=n;right[2]/=n;n=sqrtf(up[0]*up[0]+up[1]*up[1]+up[2]*up[2]);up[0]/=n;up[1]/=n;up[2]/=n;
 was_blend=glIsEnabled(GL_BLEND);was_depth=glIsEnabled(GL_DEPTH_TEST);was_cull=glIsEnabled(GL_CULL_FACE);glGetBooleanv(GL_DEPTH_WRITEMASK,&was_write);
 glUseProgram(f->program);glUniformMatrix4fv(f->u_mvp,1,GL_FALSE,mvp);glUniform3fv(f->u_right,1,right);glUniform3fv(f->u_up,1,up);glUniform2f(f->u_fog,fog_a,fog_b);glUniform3fv(f->u_fogc,1,fog_color);
 glBindVertexArray(f->vao);glBindBuffer(GL_ARRAY_BUFFER,f->inst);glEnable(GL_BLEND);glEnable(GL_DEPTH_TEST);glDepthMask(GL_FALSE);glDisable(GL_CULL_FACE);glActiveTexture(GL_TEXTURE0);
 for(mode=0;mode<2;mode++){uint32_t tx;glUniform1f(f->u_add,(float)mode);if(mode)glBlendFunc(GL_SRC_ALPHA,GL_ONE);else glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA);
  for(tx=0;tx<f->textures;tx++){int count=0;float *v=f->cpu;
   for(k=0;k<f->live;k++){const fx_part *p=f->part+k;const fx_type *t=f->type+p->type;float a,c[4],frames,du,dv;int frame,cx;
    if((uint32_t)t->tex!=tx||(int)t->add!=mode)continue;
    a=p->age/p->life;colour_at(t,a,c);frames=t->cols*t->rows;frame=(int)(p->start_frame+a*frames)%(int)frames;cx=(int)t->cols;du=1.f/t->cols;dv=1.f/t->rows;
    v[0]=p->pos[0];v[1]=p->pos[1];v[2]=p->pos[2];v[3]=(t->size0+(t->size1-t->size0)*a)*.5f;v[4]=c[0];v[5]=c[1];v[6]=c[2];v[7]=c[3];v[8]=(float)(frame%cx)*du;v[9]=(float)(frame/cx)*dv;v[10]=du;v[11]=dv;v[12]=p->angle;v+=13;count++;}
   if(!count)continue;
   glBufferData(GL_ARRAY_BUFFER,(GLsizeiptr)(sizeof(float)*13u*(size_t)count),f->cpu,GL_STREAM_DRAW);glBindTexture(GL_TEXTURE_2D,f->tex[tx]);glDrawArraysInstanced(GL_TRIANGLE_STRIP,0,4,count);}}
 glBindBuffer(GL_ARRAY_BUFFER,0);glBindVertexArray(0);glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA);if(was_blend)glEnable(GL_BLEND);else glDisable(GL_BLEND);if(was_depth)glEnable(GL_DEPTH_TEST);else glDisable(GL_DEPTH_TEST);if(was_cull)glEnable(GL_CULL_FACE);else glDisable(GL_CULL_FACE);glDepthMask(was_write);
}
