#include "oa_audio.h"
#include <aaudio/AAudio.h>
#include <android/asset_manager.h>
#include <android/log.h>
#include <math.h>
#include <pthread.h>
#include <stdatomic.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO,"OpemAmalurScene",__VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR,"OpemAmalurScene",__VA_ARGS__)
enum{VOICES=32,COMMANDS=64,MIX_RATE=48000,MAX_BLOCK_FRAMES=2048,JOBS=128};
typedef struct sound{uint8_t *bytes;const uint8_t *data;size_t data_size;int channels,rate,block,state;int16_t coefs[7][2];}sound;
typedef struct group{char name[24];uint32_t count;uint32_t *ids;}group;
typedef struct voice{int active,loop,channels,in_block,frames,have_block;const sound *s;size_t at;double pos,step;float gain,gain_target,left,right,range,xyz[3],positional;int16_t pcm[MAX_BLOCK_FRAMES*2];}voice;
typedef struct command{const sound *s;float gain,range,xyz[3];int loop,positional;}command;
struct oa_audio{
 struct AAssetManager *assets;AAudioStream *stream;group *groups;sound *sounds;uint32_t group_count,sound_count,seed;
 voice voices[VOICES];command queue[COMMANDS];atomic_uint head,tail;
 float listener[3],yaw;atomic_int active;
 pthread_t thread;pthread_mutex_t lock;pthread_cond_t wake;int jobs[JOBS],job_count,stop,thread_ok;
 struct{int group;float gain;int wanted;}beds[4];int bed_count;
 oa_audio_stats stats;
};
static int64_t now_ns(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return (int64_t)t.tv_sec*1000000000+t.tv_nsec;}
static uint16_t rd16(const uint8_t *b){return (uint16_t)(b[0]|b[1]<<8);}
static uint32_t rd32(const uint8_t *b){return (uint32_t)b[0]|(uint32_t)b[1]<<8|(uint32_t)b[2]<<16|(uint32_t)b[3]<<24;}
/* FORK container: the wave format sits at 0x2c, its coefficient table after it, then the blocks up to the offset of the second record, stored big endian at 0x20. */
static int parse_sound(sound *s,uint8_t *b,size_t n){uint32_t i;size_t extra,start,end;if(n<0x60||memcmp(b,"FORK",4)||rd16(b+0x2c)!=2)return 0;
 s->channels=rd16(b+0x2e);s->rate=(int)rd32(b+0x30);s->block=rd16(b+0x38);extra=rd16(b+0x3c);if((s->channels!=1&&s->channels!=2)||s->block<16||s->block>8192||extra<4||rd16(b+0x40)>7)return 0;
 for(i=0;i<7;i++){s->coefs[i][0]=(int16_t)rd16(b+0x42+i*4);s->coefs[i][1]=(int16_t)rd16(b+0x44+i*4);}
 start=0x3eu +extra;end=(size_t)b[0x20]<<24|(size_t)b[0x21]<<16|(size_t)b[0x22]<<8|(size_t)b[0x23];if(end<=start||end>n)end=n;
 s->bytes=b;s->data=b+start;s->data_size=end-start;return 1;}
static void *loader(void *arg){oa_audio *a=(oa_audio*)arg;
 for(;;){int job;char name[40];AAsset *as;uint8_t *b=NULL;size_t n=0;sound parsed;int ok=0;
  pthread_mutex_lock(&a->lock);while(!a->job_count&&!a->stop)pthread_cond_wait(&a->wake,&a->lock);if(a->stop){pthread_mutex_unlock(&a->lock);return NULL;}job=a->jobs[--a->job_count];pthread_mutex_unlock(&a->lock);
  memset(&parsed,0,sizeof(parsed));snprintf(name,sizeof(name),"audio/s%d.bin",job);as=AAssetManager_open(a->assets,name,AASSET_MODE_STREAMING);
  if(as){n=(size_t)AAsset_getLength64(as);b=(uint8_t*)malloc(n);if(b&&AAsset_read(as,b,n)==(int)n)ok=parse_sound(&parsed,b,n);AAsset_close(as);}
  if(!ok)free(b);
  pthread_mutex_lock(&a->lock);parsed.state=ok?2:3;a->sounds[job]=parsed;pthread_mutex_unlock(&a->lock);}
}
static void request(oa_audio *a,uint32_t id){pthread_mutex_lock(&a->lock);if(a->sounds[id].state==0&&a->job_count<JOBS){a->sounds[id].state=1;a->jobs[a->job_count++]=(int)id;pthread_cond_signal(&a->wake);}pthread_mutex_unlock(&a->lock);}
static void next_block(voice *v){const sound *s=v->s;size_t left;
 if(v->at>=s->data_size){if(!v->loop){v->active=0;return;}v->at=0;}
 left=s->data_size-v->at;if(left>(size_t)s->block)left=(size_t)s->block;
 if(left<(size_t)7*(size_t)s->channels){if(v->loop){v->at=0;left=(size_t)s->block;}else{v->active=0;return;}}
 v->frames=oa_adpcm_block(s->data+v->at,(int)left,s->channels,s->coefs,v->pcm,MAX_BLOCK_FRAMES);v->at+=left;v->pos=fmod(v->pos,1.0);if(v->frames<2)v->active=0;}
static aaudio_data_callback_result_t mix(AAudioStream *st,void *user,void *audio,int32_t frames){oa_audio *a=(oa_audio*)user;float *o=(float*)audio;int64_t t0=now_ns();int32_t f;int i;unsigned h,t,count=0;float yaw_c,yaw_s,lx,ly,lz;(void)st;
 memset(o,0,sizeof(float)*2u*(size_t)frames);
 h=atomic_load_explicit(&a->head,memory_order_acquire);t=atomic_load_explicit(&a->tail,memory_order_relaxed);
 for(;t!=h;t++){const command *c=a->queue+t%COMMANDS;for(i=0;i<VOICES;i++){voice *v=a->voices+i;if(!v->active){v->active=1;v->loop=c->loop;v->s=c->s;v->at=0;v->pos=0;v->frames=0;v->channels=c->s->channels;v->step=(double)c->s->rate/MIX_RATE;v->gain=c->gain;v->range=c->range;memcpy(v->xyz,c->xyz,12);v->positional=(float)c->positional;v->left=v->right=c->positional?0.f:c->gain;break;}}}
 atomic_store_explicit(&a->tail,t,memory_order_release);
 if(!atomic_load_explicit(&a->active,memory_order_relaxed))return AAUDIO_CALLBACK_RESULT_CONTINUE;
 lx=a->listener[0];ly=a->listener[1];lz=a->listener[2];yaw_c=cosf(a->yaw);yaw_s=sinf(a->yaw);
 for(i=0;i<VOICES;i++){voice *v=a->voices+i;float l,r,dl,dr;if(!v->active)continue;count++;
  if(v->positional>0){float dx=v->xyz[0]-lx,dy=v->xyz[1]-ly,dz=v->xyz[2]-lz,d=sqrtf(dx*dx+dy*dy+dz*dz),fall=1.f-d/v->range,side=d>1?(dx*yaw_s-dy*yaw_c)/d:0;if(fall<0)fall=0;fall*=fall*v->gain;l=fall*(.5f-side*.45f)*1.4f;r=fall*(.5f+side*.45f)*1.4f;}else{l=r=v->gain;}
  dl=(l-v->left)/(float)frames;dr=(r-v->right)/(float)frames;
  for(f=0;f<frames&&v->active;f++){int k;float sl,sr,fr;
   if(v->frames<2||v->pos>=(double)(v->frames-1)){double over=v->frames>=2?v->pos-(double)(v->frames-1):0;next_block(v);if(!v->active)break;v->pos=over;}
   k=(int)v->pos;fr=(float)(v->pos-k);
   if(v->channels==1){sl=sr=((float)v->pcm[k]+((float)v->pcm[k+1]-(float)v->pcm[k])*fr)/32768.f;}
   else{sl=((float)v->pcm[k*2]+((float)v->pcm[k*2+2]-(float)v->pcm[k*2])*fr)/32768.f;sr=((float)v->pcm[k*2+1]+((float)v->pcm[k*2+3]-(float)v->pcm[k*2+1])*fr)/32768.f;}
   o[f*2]+=sl*v->left;o[f*2+1]+=sr*v->right;v->left+=dl;v->right+=dr;v->pos+=v->step;}
  v->left=l;v->right=r;}
 for(f=0;f<frames*2;f++){float s=o[f];o[f]=s>1?1:s<-1?-1:s;}
 a->stats.voices=count;a->stats.mix_ms=(float)(now_ns()-t0)*1e-6f;
 return AAUDIO_CALLBACK_RESULT_CONTINUE;
}
oa_audio *oa_audio_open(struct AAssetManager *assets){oa_audio *a=(oa_audio*)calloc(1,sizeof(*a));AAsset *as;const uint8_t *b;size_t size,at;uint32_t i;AAudioStreamBuilder *bd=NULL;
 if(!a)return NULL;a->assets=assets;a->seed=12345;atomic_store(&a->active,1);
 as=AAssetManager_open(assets,"audio/index.bin",AASSET_MODE_BUFFER);if(!as){LOGE("No sound index");free(a);return NULL;}
 b=(const uint8_t*)AAsset_getBuffer(as);size=(size_t)AAsset_getLength64(as);if(!b||size<12||memcmp(b,"OAAU",4)){AAsset_close(as);free(a);return NULL;}
 a->group_count=rd32(b+4);a->sound_count=rd32(b+8);a->groups=(group*)calloc(a->group_count+1u,sizeof(group));a->sounds=(sound*)calloc(a->sound_count+1u,sizeof(sound));at=12;
 for(i=0;i<a->group_count&&at+28<=size;i++){group *g=a->groups+i;uint32_t k;memcpy(g->name,b+at,24);g->name[23]=0;g->count=rd32(b+at+24);at+=28;g->ids=(uint32_t*)malloc(sizeof(uint32_t)*(g->count+1u));for(k=0;k<g->count&&at+4<=size;k++,at+=4)g->ids[k]=rd32(b+at);}
 AAsset_close(as);
 pthread_mutex_init(&a->lock,NULL);pthread_cond_init(&a->wake,NULL);a->thread_ok=!pthread_create(&a->thread,NULL,loader,a);
 if(AAudio_createStreamBuilder(&bd)==AAUDIO_OK){AAudioStreamBuilder_setFormat(bd,AAUDIO_FORMAT_PCM_FLOAT);AAudioStreamBuilder_setChannelCount(bd,2);AAudioStreamBuilder_setSampleRate(bd,MIX_RATE);AAudioStreamBuilder_setPerformanceMode(bd,AAUDIO_PERFORMANCE_MODE_LOW_LATENCY);AAudioStreamBuilder_setDataCallback(bd,mix,a);
  if(AAudioStreamBuilder_openStream(bd,&a->stream)==AAUDIO_OK){if(AAudioStream_requestStart(a->stream)!=AAUDIO_OK)LOGE("Sound start failed");else LOGI("Sound ready groups=%u sounds=%u rate=%d",a->group_count,a->sound_count,AAudioStream_getSampleRate(a->stream));}else{LOGE("Sound stream unavailable");a->stream=NULL;}
  AAudioStreamBuilder_delete(bd);}
 return a;
}
void oa_audio_close(oa_audio *a){uint32_t i;if(!a)return;if(a->stream){AAudioStream_requestStop(a->stream);AAudioStream_close(a->stream);}
 if(a->thread_ok){pthread_mutex_lock(&a->lock);a->stop=1;pthread_cond_signal(&a->wake);pthread_mutex_unlock(&a->lock);pthread_join(a->thread,NULL);}
 pthread_mutex_destroy(&a->lock);pthread_cond_destroy(&a->wake);for(i=0;i<a->group_count;i++)free(a->groups[i].ids);for(i=0;i<a->sound_count;i++)free(a->sounds[i].bytes);free(a->groups);free(a->sounds);free(a);}
void oa_audio_set_active(oa_audio *a,int on){if(a)atomic_store(&a->active,on);}
int oa_audio_group(const oa_audio *a,const char *name){uint32_t i;if(!a)return -1;for(i=0;i<a->group_count;i++)if(!strcmp(a->groups[i].name,name))return (int)i;return -1;}
void oa_audio_listener(oa_audio *a,const float p[3],float yaw){if(!a)return;memcpy(a->listener,p,12);a->yaw=yaw;
 {int i;for(i=0;i<a->bed_count;i++)if(a->beds[i].wanted){const group *g=a->groups+a->beds[i].group;if(g->count){const sound *s=a->sounds+g->ids[0];if(s->state==2){unsigned h=atomic_load(&a->head);command *c=a->queue+h%COMMANDS;memset(c,0,sizeof(*c));c->s=s;c->gain=a->beds[i].gain;c->loop=1;c->range=1;atomic_store(&a->head,h+1);a->beds[i].wanted=0;}}}}}
void oa_audio_play(oa_audio *a,int gi,const float p[3],float gain,float range){const group *g;uint32_t id;const sound *s;unsigned h,t;if(!a||gi<0||(uint32_t)gi>=a->group_count)return;g=a->groups+gi;if(!g->count)return;
 a->seed=a->seed*1664525u+1013904223u;id=g->ids[(a->seed>>16)%g->count];s=a->sounds+id;request(a,id);if(s->state!=2)return;
 if(p){float dx=p[0]-a->listener[0],dy=p[1]-a->listener[1];if(dx*dx+dy*dy>range*range)return;}
 h=atomic_load_explicit(&a->head,memory_order_relaxed);t=atomic_load_explicit(&a->tail,memory_order_acquire);if(h-t>=COMMANDS)return;
 {command *c=a->queue+h%COMMANDS;memset(c,0,sizeof(*c));c->s=s;c->gain=gain;c->range=range;if(p){memcpy(c->xyz,p,12);c->positional=1;}atomic_store_explicit(&a->head,h+1,memory_order_release);}}
void oa_audio_loop(oa_audio *a,int gi,float gain){const group *g;if(!a||gi<0||(uint32_t)gi>=a->group_count||a->bed_count>=4)return;g=a->groups+gi;if(g->count){request(a,g->ids[0]);a->beds[a->bed_count].group=gi;a->beds[a->bed_count].gain=gain;a->beds[a->bed_count].wanted=1;a->bed_count++;}}
void oa_audio_get_stats(oa_audio *a,oa_audio_stats *o){memset(o,0,sizeof(*o));if(a){*o=a->stats;if(a->stream)o->underruns=(unsigned)AAudioStream_getXRunCount(a->stream);}}
