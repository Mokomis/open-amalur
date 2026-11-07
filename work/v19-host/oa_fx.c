#include "oa_fx.h"
#include <GLES3/gl3.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <android/log.h>
#define FX_LOG(...) __android_log_print(ANDROID_LOG_INFO,"OpemAmalurScene",__VA_ARGS__)
enum{FN_NATIVE=1,FN_SOFT=2,FN_COLOR8=4,FN_SHAPE=8,FN_VELOCITY_AXIS=16,FN_SOURCE_ANGLE=32,FN_INPUT_ZERO=64,FX_INSTANCE_FLOATS=20};
typedef struct fx_native{uint32_t flags;float x0,x1,y0,y1,angle0,angle1;}fx_native;
int oa_fx_native_shape=1;
/* Billboards with the game's own spawn rates, lifetimes, gradients and sizes. Effects start within the game's cluster fade distance. The particle limit, and how velocity and spin are read, are this code's choices. */
enum{FX_MAX=3000,FX_TYPE_FLOATS=53,FX_FADE_NEAR=8000,FX_FADE_FAR=10000};
typedef struct fx_type{float tex,add,period,period_var,burst,box[3],off[3],vel[3],rnd[3],life,life_var,size0,size1,cols,rows,spin,spin2,color[4][4],alpha[6][2];}fx_type;
typedef struct fx_place{float pos[3],type,q[4];}fx_place;
typedef struct fx_part{float pos[3],vel[3],age,life,angle,spin,start_frame;int type,place;}fx_part;
struct oa_fx{fx_native *native;unsigned texture_overrides,native_profiles,draw_frame;int shape_mode,observed_mode;uint32_t textures,types,places;GLuint *tex;fx_type *type;fx_place *place;float *wait;fx_part *part;int live;uint32_t seed;GLuint program,vao,quad,inst;float *cpu;GLint u_mvp,u_right,u_up,u_fog,u_fogc,u_add,u_forward,u_depth,u_invdepth,u_invsize,u_hasdepth;};
static const char fx_vs[]="#version 300 es\nprecision highp float;precision highp int;layout(location=0)in vec2 c;layout(location=1)in vec4 ps;layout(location=2)in vec4 col;layout(location=3)in vec4 cell;layout(location=4)in float ang;layout(location=5)in vec2 shape;layout(location=6)in vec3 axis;uniform mat4 mvp;uniform vec3 right_v,up_v,camera_forward;uniform vec2 fog;out vec2 UV;out highp vec4 C;out highp float F,particleClipZ;flat out highp int NF;void main(){NF=int(shape.y);float si=sin(ang),co=cos(ang);vec2 r=vec2(c.x*co-c.y*si,c.x*si+c.y*co)*ps.w;vec3 rv=right_v,uv=up_v;if((NF&8)!=0){vec2 p=vec2(c.x,-c.y)*vec2(ps.w,shape.x);r=vec2(p.x*co-p.y*si,p.x*si+p.y*co);if((NF&16)!=0){uv=normalize(axis);vec3 side=cross(camera_forward,uv);rv=dot(side,side)>1e-10?normalize(side):right_v;}}vec3 p=ps.xyz+rv*r.x+uv*r.y;gl_Position=mvp*vec4(p,1.);particleClipZ=.5*(gl_Position.z+gl_Position.w);UV=cell.xy+(c*vec2(.5,-.5)+.5)*cell.zw;C=(NF&4)!=0?roundEven(clamp(col,0.,1.)*255.)/255.:col;F=1.-min(exp(-(fog.x*gl_Position.w+fog.y)),1.);}";
static const char fx_fs[]="#version 300 es\nprecision highp float;precision highp int;in vec2 UV;in highp vec4 C;in highp float F,particleClipZ;flat in highp int NF;uniform sampler2D t;uniform highp sampler2D scene_depth;uniform vec2 inverse_depth,inverse_size;uniform int has_depth;uniform vec3 fogc;uniform float add_mode;out vec4 o;void main(){vec4 d=texture(t,UV)*C;if((NF&1)!=0){if((NF&2)!=0&&has_depth!=0){float z=texture(scene_depth,gl_FragCoord.xy*inverse_size).r;float sceneZ=1./(inverse_depth.x*z+inverse_depth.y);float x=(sceneZ-particleClipZ)*.0199999996;float soft=min(x*x,1.);if(soft<=0.)soft=1.;d.a*=soft;}o=vec4(d.rgb,d.a*(1.-F));}else if(add_mode>.5)o=vec4(d.rgb*(1.-F),d.a);else o=vec4(mix(d.rgb,fogc,F),d.a);}";
static GLuint shader(GLenum kind,const char *src){GLint ok=0;GLuint s=glCreateShader(kind);glShaderSource(s,1,&src,NULL);glCompileShader(s);glGetShaderiv(s,GL_COMPILE_STATUS,&ok);if(!ok){char text[1024];GLsizei n=0;glGetShaderInfoLog(s,sizeof(text)-1,&n,text);text[n]=0;FX_LOG("FX shader compile failed: %s",text);glDeleteShader(s);return 0;}return s;}
static float rnd(oa_fx *f){f->seed=f->seed*1103515245u+12345u;return (float)((f->seed>>16)&0x7fff)/32767.f;}
static float rnd2(oa_fx *f){return rnd(f)*2.f-1.f;}
static void qrot3(float o[3],const float q[4],const float v[3]){float t[3]={2*(q[1]*v[2]-q[2]*v[1]),2*(q[2]*v[0]-q[0]*v[2]),2*(q[0]*v[1]-q[1]*v[0])};o[0]=v[0]+q[3]*t[0]+q[1]*t[2]-q[2]*t[1];o[1]=v[1]+q[3]*t[1]+q[2]*t[0]-q[0]*t[2];o[2]=v[2]+q[3]*t[2]+q[0]*t[1]-q[1]*t[0];}
static uint32_t fx_word(const uint8_t *p){uint32_t v;memcpy(&v,p,4);return v;}
static int native_texture(AAssetManager *manager,unsigned index){
 char path[64];AAsset *a;const uint8_t *b;size_t n,at=20;unsigned w,h,levels,k;snprintf(path,sizeof(path),"fx/t%u.bin",index);a=AAssetManager_open(manager,path,AASSET_MODE_BUFFER);if(!a)return 0;b=(const uint8_t*)AAsset_getBuffer(a);n=(size_t)AAsset_getLength64(a);
 if(!b||n<20||memcmp(b,"OATX",4)||fx_word(b+4)!=GL_RGBA8)goto bad;w=fx_word(b+8);h=fx_word(b+12);levels=fx_word(b+16);if(!w||!h||w>8192||h>8192||!levels||levels>16)goto bad;
 for(k=0;k<levels;k++){unsigned bytes,x=w>>k?w>>k:1,y=h>>k?h>>k:1;if(at+4>n)goto bad;bytes=fx_word(b+at);at+=4;if(bytes!=(size_t)x*y*4||bytes>n-at)goto bad;at+=bytes;}if(at!=n)goto bad;
 at=20;for(k=0;k<levels;k++){unsigned bytes=fx_word(b+at),x=w>>k?w>>k:1,y=h>>k?h>>k:1;at+=4;glTexImage2D(GL_TEXTURE_2D,k,GL_RGBA8,x,y,0,GL_RGBA,GL_UNSIGNED_BYTE,b+at);at+=bytes;}
 glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAX_LEVEL,levels-1);glTexParameterf(GL_TEXTURE_2D,0x84FE,1.f);AAsset_close(a);return 1;
 bad:AAsset_close(a);FX_LOG("Native FX texture override invalid index=%u",index);return 0;
}
static void native_profiles(oa_fx *f,AAssetManager *manager){
 AAsset *a=AAssetManager_open(manager,"fx/native-types.bin",AASSET_MODE_BUFFER);const uint8_t *b;size_t size;unsigned n,k;if(!a)return;b=(const uint8_t*)AAsset_getBuffer(a);size=(size_t)AAsset_getLength64(a);if(!b||size<12||memcmp(b,"OAFXN01",8))goto done;n=fx_word(b+8);if(n>f->types||size!=12+(size_t)n*32)goto done;
 for(k=0;k<n;k++){const uint8_t *r=b+12+k*32;unsigned type=fx_word(r),flags=fx_word(r+4),j;float v[6];int valid=1;memcpy(v,r+8,24);if(type>=f->types||flags&~127u)continue;for(j=0;j<6;j++)if(!isfinite(v[j]))valid=0;if((flags&FN_SHAPE)&&(v[0]<=0||v[1]<=0||v[2]<=0||v[3]<=0))valid=0;if(valid){f->native[type].flags=flags;memcpy(&f->native[type].x0,v,24);f->native_profiles++;}}
 done:AAsset_close(a);
}
oa_fx *oa_fx_open(AAssetManager *manager){
 AAsset *as=AAssetManager_open(manager,"fx/fx.bin",AASSET_MODE_BUFFER);const uint8_t *b;size_t n,at=8;oa_fx *f;uint32_t head[4],i;
 if(!as)return NULL;
 b=(const uint8_t*)AAsset_getBuffer(as);n=(size_t)AAsset_getLength64(as);
 if(!b||n<24||memcmp(b,"OAFX0001",8)){AAsset_close(as);return NULL;}
 memcpy(head,b+at,16);at+=16;
 f=(oa_fx*)calloc(1,sizeof(*f));
 if(!f||head[3]!=FX_TYPE_FLOATS||sizeof(fx_type)!=FX_TYPE_FLOATS*sizeof(float)){free(f);AAsset_close(as);return NULL;}
 f->textures=head[0];f->types=head[1];f->places=head[2];f->seed=431608;f->shape_mode=-1;f->observed_mode=-1;f->native=(fx_native*)calloc(f->types+1,sizeof(fx_native));if(!f->native){free(f);AAsset_close(as);return NULL;}
 f->tex=(GLuint*)calloc(f->textures+1u,sizeof(GLuint));glGenTextures((GLsizei)f->textures,f->tex);
 for(i=0;i<f->textures;i++){uint32_t wh[2];memcpy(wh,b+at,8);at+=8;glBindTexture(GL_TEXTURE_2D,f->tex[i]);if(native_texture(manager,i))f->texture_overrides++;else{glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA8,(GLsizei)wh[0],(GLsizei)wh[1],0,GL_RGBA,GL_UNSIGNED_BYTE,b+at);glGenerateMipmap(GL_TEXTURE_2D);}glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_LINEAR_MIPMAP_LINEAR);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_LINEAR);at+=(size_t)wh[0]*wh[1]*4u;}
 f->type=(fx_type*)malloc(sizeof(fx_type)*(f->types+1u));memcpy(f->type,b+at,sizeof(fx_type)*f->types);at+=sizeof(fx_type)*f->types;
 f->place=(fx_place*)malloc(sizeof(fx_place)*(f->places+1u));memcpy(f->place,b+at,sizeof(fx_place)*f->places);at+=sizeof(fx_place)*f->places;
 AAsset_close(as);native_profiles(f,manager);FX_LOG("Native FX profiles=%u authored_texture_overrides=%u shape_policy_candidate=%d",f->native_profiles,f->texture_overrides,oa_fx_native_shape);
 f->wait=(float*)calloc(f->places+1u,sizeof(float));f->part=(fx_part*)malloc(sizeof(fx_part)*FX_MAX);f->cpu=(float*)malloc(sizeof(float)*FX_INSTANCE_FLOATS*FX_MAX);
 {GLuint vs=shader(GL_VERTEX_SHADER,fx_vs),fs=shader(GL_FRAGMENT_SHADER,fx_fs);static const float quad[8]={-1,-1,1,-1,-1,1,1,1};if(!vs||!fs){if(vs)glDeleteShader(vs);if(fs)glDeleteShader(fs);oa_fx_close(f);return NULL;}f->program=glCreateProgram();glAttachShader(f->program,vs);glAttachShader(f->program,fs);glLinkProgram(f->program);glDeleteShader(vs);glDeleteShader(fs);{GLint ok=0;glGetProgramiv(f->program,GL_LINK_STATUS,&ok);if(!ok){char text[1024];GLsizei n=0;glGetProgramInfoLog(f->program,sizeof(text)-1,&n,text);text[n]=0;FX_LOG("FX shader link failed: %s",text);oa_fx_close(f);return NULL;}}
  f->u_mvp=glGetUniformLocation(f->program,"mvp");f->u_right=glGetUniformLocation(f->program,"right_v");f->u_up=glGetUniformLocation(f->program,"up_v");f->u_fog=glGetUniformLocation(f->program,"fog");f->u_fogc=glGetUniformLocation(f->program,"fogc");f->u_add=glGetUniformLocation(f->program,"add_mode");f->u_forward=glGetUniformLocation(f->program,"camera_forward");f->u_depth=glGetUniformLocation(f->program,"scene_depth");f->u_invdepth=glGetUniformLocation(f->program,"inverse_depth");f->u_invsize=glGetUniformLocation(f->program,"inverse_size");f->u_hasdepth=glGetUniformLocation(f->program,"has_depth");
  glGenVertexArrays(1,&f->vao);glGenBuffers(1,&f->quad);glGenBuffers(1,&f->inst);glBindVertexArray(f->vao);glBindBuffer(GL_ARRAY_BUFFER,f->quad);glBufferData(GL_ARRAY_BUFFER,sizeof(quad),quad,GL_STATIC_DRAW);glEnableVertexAttribArray(0);glVertexAttribPointer(0,2,GL_FLOAT,GL_FALSE,0,0);
  glBindBuffer(GL_ARRAY_BUFFER,f->inst);glBufferData(GL_ARRAY_BUFFER,(GLsizeiptr)(sizeof(float)*FX_INSTANCE_FLOATS*FX_MAX),NULL,GL_STREAM_DRAW);
  {static const int sizes[4]={4,4,4,1},at_[4]={0,16,32,48};int a;for(a=0;a<4;a++){glEnableVertexAttribArray((GLuint)a+1u);glVertexAttribPointer((GLuint)a+1u,sizes[a],GL_FLOAT,GL_FALSE,FX_INSTANCE_FLOATS*4,(void*)(intptr_t)at_[a]);glVertexAttribDivisor((GLuint)a+1u,1);}}
  glEnableVertexAttribArray(5);glVertexAttribPointer(5,2,GL_FLOAT,GL_FALSE,FX_INSTANCE_FLOATS*4,(void*)52);glVertexAttribDivisor(5,1);glEnableVertexAttribArray(6);glVertexAttribPointer(6,3,GL_FLOAT,GL_FALSE,FX_INSTANCE_FLOATS*4,(void*)64);glVertexAttribDivisor(6,1);
  glBindVertexArray(0);glBindBuffer(GL_ARRAY_BUFFER,0);}
 return f;}
void oa_fx_close(oa_fx *f){if(!f)return;glDeleteTextures((GLsizei)f->textures,f->tex);glDeleteProgram(f->program);glDeleteVertexArrays(1,&f->vao);glDeleteBuffers(1,&f->quad);glDeleteBuffers(1,&f->inst);free(f->tex);free(f->native);free(f->type);free(f->place);free(f->wait);free(f->part);free(f->cpu);free(f);}
int oa_fx_live(const oa_fx *f){return f?f->live:0;}
void oa_fx_update(oa_fx *f,const float eye[3],float dt){
 uint32_t i;int k;if(!f)return;if(f->shape_mode!=oa_fx_native_shape){f->shape_mode=oa_fx_native_shape;f->live=0;memset(f->wait,0,sizeof(float)*(f->places+1));f->seed=431608;FX_LOG("Native FX shape candidate mode=%d; emitter simulation reset",f->shape_mode);}
 for(k=0;k<f->live;){fx_part *p=f->part+k;p->age+=dt;if(p->age>=p->life){*p=f->part[--f->live];continue;}p->pos[0]+=p->vel[0]*dt;p->pos[1]+=p->vel[1]*dt;p->pos[2]+=p->vel[2]*dt;p->angle+=p->spin*dt;k++;}
 for(i=0;i<f->places;i++){const fx_place *pl=f->place+i;const fx_type *t=f->type+(int)pl->type;float dx=pl->pos[0]-eye[0],dy=pl->pos[1]-eye[1],dz=pl->pos[2]-eye[2];
  if(dx*dx+dy*dy+dz*dz>(float)FX_FADE_FAR*FX_FADE_FAR)continue;
  f->wait[i]-=dt;
  while(f->wait[i]<=0&&f->live<FX_MAX){int b,burst=(int)t->burst;f->wait[i]+=t->period+t->period_var*rnd2(f)>.02f?t->period+t->period_var*rnd2(f):.02f;
   for(b=0;b<burst&&f->live<FX_MAX;b++){fx_part *p=f->part+f->live++;float v[3]={t->box[0]*rnd2(f)+t->off[0],t->box[1]*rnd2(f)+t->off[1],t->box[2]*rnd2(f)+t->off[2]},w[3]={t->vel[0]+t->rnd[0]*rnd2(f),t->vel[1]+t->rnd[1]*rnd2(f),t->vel[2]+t->rnd[2]*rnd2(f)},o[3];
    {float cq[4]={-pl->q[0],-pl->q[1],-pl->q[2],pl->q[3]};const float *q=(oa_fx_native_shape&&(f->native[(int)pl->type].flags&FN_SHAPE))?cq:pl->q;qrot3(o,q,v);p->pos[0]=pl->pos[0]+o[0];p->pos[1]=pl->pos[1]+o[1];p->pos[2]=pl->pos[2]+o[2];qrot3(p->vel,q,w);}p->age=0;p->life=t->life+t->life_var*rnd2(f);if(p->life<.05f)p->life=.05f;p->angle=rnd(f)*6.283f;p->spin=(t->spin2+(t->spin-t->spin2)*rnd(f))*.01745f;p->start_frame=rnd(f)*t->cols*t->rows;p->type=(int)pl->type;p->place=(int)i;}}
  if(f->wait[i]<=0)f->wait[i]=.1f;}
}
static void colour_at(const fx_type *t,float a,float o[4]){
 int i,e;const float (*c)[4]=t->color;if(a>=c[3][0]){for(e=0;e<3;e++)o[e]=c[3][e+1];}else{float m,span;for(i=0;i<2&&a>c[i+1][0];i++);span=c[i+1][0]-c[i][0];m=span>1e-4f?(a-c[i][0])/span:0;m=fmaxf(0,fminf(1,m));for(e=0;e<3;e++)o[e]=c[i][e+1]+(c[i+1][e+1]-c[i][e+1])*m;}
 {const float (*k)[2]=t->alpha;if(a>=k[5][0])o[3]=k[5][1];else{float span,m;for(i=0;i<4&&a>k[i+1][0];i++);span=k[i+1][0]-k[i][0];m=span>1e-4f?(a-k[i][0])/span:0;m=fmaxf(0,fminf(1,m));o[3]=k[i][1]+(k[i+1][1]-k[i][1])*m;}}
}
void oa_fx_draw(oa_fx *f,const float mvp[16],const float fog_color[3],float fog_a,float fog_b,unsigned scene_depth,const float inverse_depth[2],int width,int height){
 float right[3]={mvp[0],mvp[4],mvp[8]},up[3]={mvp[1],mvp[5],mvp[9]},n;float eye_far=(float)FX_FADE_FAR;unsigned native_count=0,soft_count=0,shaped_count=0;float forward[3]={mvp[3],mvp[7],mvp[11]};int mode,k;GLboolean was_blend,was_depth,was_cull,was_write;(void)eye_far;
 if(!f||!f->live||!f->program)return;
 n=sqrtf(right[0]*right[0]+right[1]*right[1]+right[2]*right[2]);right[0]/=n;right[1]/=n;right[2]/=n;n=sqrtf(up[0]*up[0]+up[1]*up[1]+up[2]*up[2]);up[0]/=n;up[1]/=n;up[2]/=n;
 was_blend=glIsEnabled(GL_BLEND);was_depth=glIsEnabled(GL_DEPTH_TEST);was_cull=glIsEnabled(GL_CULL_FACE);glGetBooleanv(GL_DEPTH_WRITEMASK,&was_write);
 glUseProgram(f->program);glUniformMatrix4fv(f->u_mvp,1,GL_FALSE,mvp);glUniform3fv(f->u_right,1,right);glUniform3fv(f->u_up,1,up);glUniform2f(f->u_fog,fog_a,fog_b);glUniform3fv(f->u_fogc,1,fog_color);
 glUniform3fv(f->u_forward,1,forward);glUniform1i(f->u_depth,1);glUniform1i(f->u_hasdepth,scene_depth!=0&&inverse_depth!=NULL);if(inverse_depth)glUniform2fv(f->u_invdepth,1,inverse_depth);glUniform2f(f->u_invsize,1.f/width,1.f/height);glActiveTexture(GL_TEXTURE1);glBindSampler(1,0);glBindTexture(GL_TEXTURE_2D,scene_depth);if(scene_depth){glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_COMPARE_MODE,GL_NONE);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,GL_CLAMP_TO_EDGE);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,GL_CLAMP_TO_EDGE);}glActiveTexture(GL_TEXTURE0);glBindSampler(0,0);
 glBindVertexArray(f->vao);glBindBuffer(GL_ARRAY_BUFFER,f->inst);glEnable(GL_BLEND);glEnable(GL_DEPTH_TEST);glDepthMask(GL_FALSE);glDisable(GL_CULL_FACE);glActiveTexture(GL_TEXTURE0);
 for(mode=0;mode<2;mode++){uint32_t tx;glUniform1f(f->u_add,(float)mode);if(mode)glBlendFunc(GL_SRC_ALPHA,GL_ONE);else glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA);
  for(tx=0;tx<f->textures;tx++){int count=0;float *v=f->cpu;
   for(k=0;k<f->live;k++){const fx_part *p=f->part+k;const fx_type *t=f->type+p->type;const fx_native *nt=f->native+p->type;unsigned flags=nt->flags;float a,c[4],frames,du,dv;int frame,cx;if(!oa_fx_native_shape)flags&=7u;
    if((uint32_t)t->tex!=tx||((flags&FN_NATIVE)?1:(int)t->add)!=mode)continue;
    a=p->age/p->life;colour_at(t,a,c);frames=t->cols*t->rows;frame=(int)(p->start_frame+a*frames)%(int)frames;cx=(int)t->cols;du=1.f/t->cols;dv=1.f/t->rows;
    v[0]=p->pos[0];v[1]=p->pos[1];v[2]=p->pos[2];v[3]=(t->size0+(t->size1-t->size0)*a)*.5f;v[4]=c[0];v[5]=c[1];v[6]=c[2];v[7]=c[3];v[8]=(float)(frame%cx)*du;v[9]=(float)(frame/cx)*dv;v[10]=du;v[11]=dv;v[12]=p->angle;v[13]=v[3];v[14]=(float)flags;v[15]=v[19]=0;v[16]=0;v[17]=0;v[18]=1;
    if(flags&FN_SHAPE){float input=(flags&FN_INPUT_ZERO)?0:a;v[3]=nt->x0+(nt->x1-nt->x0)*input;v[13]=nt->y0+(nt->y1-nt->y0)*input;if(flags&FN_SOURCE_ANGLE)v[12]=(nt->angle0+(nt->angle1-nt->angle0)*fmodf(fabsf(p->angle),6.283185307f)/6.283185307f)*.017453292519943295f;if(flags&FN_VELOCITY_AXIS){float len=sqrtf(p->vel[0]*p->vel[0]+p->vel[1]*p->vel[1]+p->vel[2]*p->vel[2]);if(len>1e-6f){v[16]=p->vel[0]/len;v[17]=p->vel[1]/len;v[18]=p->vel[2]/len;}else{const fx_place *pl=f->place+p->place;float cq[4]={-pl->q[0],-pl->q[1],-pl->q[2],pl->q[3]},axis[3]={-1,0,0};qrot3(v+16,cq,axis);}}shaped_count++;}if(flags&FN_NATIVE)native_count++;if(flags&FN_SOFT)soft_count++;
    v+=FX_INSTANCE_FLOATS;count++;}
   if(!count)continue;
   glBufferData(GL_ARRAY_BUFFER,(GLsizeiptr)(sizeof(float)*FX_INSTANCE_FLOATS*(size_t)count),f->cpu,GL_STREAM_DRAW);glBindTexture(GL_TEXTURE_2D,f->tex[tx]);glDrawArraysInstanced(GL_TRIANGLE_STRIP,0,4,count);}}
 if(native_count&&(f->observed_mode!=oa_fx_native_shape||f->draw_frame++%240u==0)){f->observed_mode=oa_fx_native_shape;FX_LOG("Native FX rendered native_particles=%u soft_particles=%u shaped_particles=%u shape_candidate=%d depth_snapshot=%d",native_count,soft_count,shaped_count,oa_fx_native_shape,scene_depth!=0);}
 glBindBuffer(GL_ARRAY_BUFFER,0);glBindVertexArray(0);glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA);if(was_blend)glEnable(GL_BLEND);else glDisable(GL_BLEND);if(was_depth)glEnable(GL_DEPTH_TEST);else glDisable(GL_DEPTH_TEST);if(was_cull)glEnable(GL_CULL_FACE);else glDisable(GL_CULL_FACE);glDepthMask(was_write);
}
