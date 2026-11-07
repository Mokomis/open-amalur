#include "oa_actors.h"
#include "oa_actor_ai.h"
#include "oa_nav.h"
#include "oa_audio.h"
#include <android/asset_manager.h>
#include <android/log.h>
#include <math.h>
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO,"OpemAmalurScene",__VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR,"OpemAmalurScene",__VA_ARGS__)
enum{SLOTS=40,NEAR_MAX=256,JOBS=64,FAR_STRIDE=16,RAY_STRIDE=12,SHADOW_MAX=6,STATE_NONE=0,STATE_QUEUED,STATE_CPU,STATE_BUILD,STATE_GPU};
#define THINK_RANGE 7000.f
#define DRAW_RANGE 10000.f
#define LOAD_RANGE 11000.f
#define UNLOAD_RANGE 14000.f
#define PLAYER_REACH 240.f
#define TURN_REACH 430.f
#define FOCUS_RANGE 2200.f
#define SHADOW_RANGE 3000.f
#define CAPSULE_RANGE 5000.f
#define PLAYER_RADIUS 32.f
typedef struct model{int state;oa_character proto;oa_character_gpu gpu;}model;
enum{ROUTE_POINTS=16};
typedef struct slot{int actor,tick,capsule_ok,path_count,path_at;float pending,capsule_wait,stuck,replan,path[ROUTE_POINTS][2];oa_character body;opem_controller capsule;}slot;
struct oa_actors{
 struct AAssetManager *assets;oa_actor_type *types;model *models;oa_actor *actors;unsigned type_count,actor_count,frame;float rescan;
 slot slots[SLOTS];int near_list[NEAR_MAX];unsigned near_count;
 pthread_t thread;pthread_mutex_t lock;pthread_cond_t wake;int jobs[JOBS];unsigned job_count;int stop,thread_ok;
 oa_actors_stats stats;
 oa_nav nav;uint8_t *nav_bits;
 oa_audio *audio;int *voice_group;
};
static int64_t now_ns(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return (int64_t)t.tv_sec*1000000000+t.tv_nsec;}
static void *worker(void *arg){oa_actors *a=(oa_actors*)arg;
 for(;;){int job;char name[48],error[128]="";AAsset *asset;uint8_t *bytes=NULL;size_t size=0;oa_character proto;int ok=0;
  pthread_mutex_lock(&a->lock);while(!a->job_count&&!a->stop)pthread_cond_wait(&a->wake,&a->lock);if(a->stop){pthread_mutex_unlock(&a->lock);return NULL;}job=a->jobs[--a->job_count];pthread_mutex_unlock(&a->lock);
  snprintf(name,sizeof(name),"actors/a%d.bin",job);asset=AAssetManager_open(a->assets,name,AASSET_MODE_STREAMING);
  if(asset){size=(size_t)AAsset_getLength64(asset);bytes=(uint8_t*)malloc(size);if(bytes&&AAsset_read(asset,bytes,size)==(int)size)ok=oa_character_parse(&proto,bytes,size,error,sizeof(error));AAsset_close(asset);}
  if(!ok){LOGE("Actor model %d rejected: %s",job,error);free(bytes);}
  pthread_mutex_lock(&a->lock);if(ok){a->models[job].proto=proto;a->models[job].state=STATE_CPU;}else a->models[job].state=STATE_NONE;pthread_mutex_unlock(&a->lock);}
}
oa_actors *oa_actors_open(struct AAssetManager *assets){
 oa_actors *a=(oa_actors*)calloc(1,sizeof(*a));AAsset *asset;const uint8_t *b;size_t size;uint32_t head[2];unsigned i;
 if(!a)return NULL;a->assets=assets;for(i=0;i<SLOTS;i++)a->slots[i].actor=-1;
 asset=AAssetManager_open(assets,"actors/index.bin",AASSET_MODE_BUFFER);if(!asset){LOGE("No actor index");free(a);return NULL;}
 b=(const uint8_t*)AAsset_getBuffer(asset);size=(size_t)AAsset_getLength64(asset);
 if(!b||size<12||memcmp(b,"OAAI",4)){LOGE("Actor index invalid");AAsset_close(asset);free(a);return NULL;}
 memcpy(head,b+4,8);
 if(size!=12u+(size_t)head[0]*sizeof(oa_actor_type)+(size_t)head[1]*20u){LOGE("Actor index size invalid");AAsset_close(asset);free(a);return NULL;}
 a->type_count=head[0];a->actor_count=head[1];a->types=(oa_actor_type*)malloc(sizeof(oa_actor_type)*(a->type_count+1));a->models=(model*)calloc(a->type_count+1,sizeof(model));a->actors=(oa_actor*)malloc(sizeof(oa_actor)*(a->actor_count+1));
 if(!a->types||!a->models||!a->actors){AAsset_close(asset);free(a->types);free(a->models);free(a->actors);free(a);return NULL;}
 memcpy(a->types,b+12,sizeof(oa_actor_type)*a->type_count);
 for(i=0;i<a->actor_count;i++){const uint8_t *r=b+12+sizeof(oa_actor_type)*a->type_count+i*20u;float place[4];uint16_t ids[2];memcpy(place,r,16);memcpy(ids,r+16,4);
  if(ids[0]>=a->type_count){LOGE("Actor type invalid");ids[0]=0;}
  oa_actor_init(a->actors+i,place,place[3],a->types[ids[0]].hp,i+1);a->actors[i].type=ids[0];a->actors[i].group=ids[1];}
 AAsset_close(asset);
 asset=AAssetManager_open(assets,"actors/nav.bin",AASSET_MODE_BUFFER);
 if(asset){const uint8_t *nb=(const uint8_t*)AAsset_getBuffer(asset);size_t ns=(size_t)AAsset_getLength64(asset);uint32_t dims[2];float place[3];
  if(nb&&ns>=20){memcpy(dims,nb,8);memcpy(place,nb+8,12);if(ns==20u+((size_t)dims[0]*dims[1]+7u)/8u&&(a->nav_bits=(uint8_t*)malloc(ns-20u))!=NULL){memcpy(a->nav_bits,nb+20,ns-20u);a->nav.width=dims[0];a->nav.height=dims[1];a->nav.x0=place[0];a->nav.y0=place[1];a->nav.step=place[2];a->nav.bits=a->nav_bits;}}
  AAsset_close(asset);}
 if(!a->nav.bits)LOGE("No navigation map");
 pthread_mutex_init(&a->lock,NULL);pthread_cond_init(&a->wake,NULL);a->thread_ok=!pthread_create(&a->thread,NULL,worker,a);
 LOGI("Actors types=%u actors=%u",a->type_count,a->actor_count);a->stats.total=a->actor_count;return a;
}
void oa_actors_close(oa_actors *a){unsigned i;if(!a)return;
 if(a->thread_ok){pthread_mutex_lock(&a->lock);a->stop=1;pthread_cond_signal(&a->wake);pthread_mutex_unlock(&a->lock);pthread_join(a->thread,NULL);}
 pthread_mutex_destroy(&a->lock);pthread_cond_destroy(&a->wake);
 for(i=0;i<a->type_count;i++)if(a->models[i].state>=STATE_CPU)oa_character_free(&a->models[i].proto);
 free(a->voice_group);free(a->nav_bits);free(a->types);free(a->models);free(a->actors);free(a);
}
typedef struct candidate{float d;int i;}candidate;
static int by_distance(const void *x,const void *y){float p=((const candidate*)x)->d,q=((const candidate*)y)->d;return p<q?-1:p>q;}
static void release_slot(oa_actors *a,int s){if(a->slots[s].actor>=0)a->actors[a->slots[s].actor].slot=-1;a->slots[s].actor=-1;}
/* Chooses which models to hold and which actors get a posed body. */
static void rescan(oa_actors *a,const float player[3]){
 static candidate list[SLOTS*8];unsigned n=0,i,m;unsigned char *want=(unsigned char*)calloc(a->type_count+1,1);if(!want)return;
 for(i=0;i<a->actor_count;i++){const oa_actor *x=a->actors+i;float dx=x->pos[0]-player[0],dy=x->pos[1]-player[1],d=dx*dx+dy*dy;
  if(d<UNLOAD_RANGE*UNLOAD_RANGE)want[x->type]|=1;
  if(d<LOAD_RANGE*LOAD_RANGE&&oa_actor_visible(x))want[x->type]|=2;
  if(d<DRAW_RANGE*DRAW_RANGE&&oa_actor_visible(x)&&n<SLOTS*8&&a->models[x->type].state==STATE_GPU){list[n].d=d;list[n].i=(int)i;n++;}}
 pthread_mutex_lock(&a->lock);
 for(m=0;m<a->type_count;m++){model *q=a->models+m;if((want[m]&2)&&q->state==STATE_NONE&&a->job_count<JOBS){q->state=STATE_QUEUED;a->jobs[a->job_count++]=(int)m;pthread_cond_signal(&a->wake);}}
 pthread_mutex_unlock(&a->lock);
 qsort(list,n,sizeof(candidate),by_distance);if(n>SLOTS)n=SLOTS;
 {unsigned char chosen[SLOTS]={0};int s;
  for(s=0;s<SLOTS;s++){int who=a->slots[s].actor,keep=0;for(i=0;i<n&&!keep;i++)if(list[i].i==who){keep=1;chosen[i]=1;}if(who>=0&&!keep)release_slot(a,s);}
  for(i=0;i<n;i++){if(chosen[i])continue;for(s=0;s<SLOTS;s++)if(a->slots[s].actor<0){oa_actor *x=a->actors+list[i].i;slot *sl=a->slots+s;sl->actor=list[i].i;sl->tick=s;sl->pending=0;sl->capsule_ok=0;sl->capsule_wait=0;sl->stuck=0;sl->path_count=0;sl->path_at=0;sl->replan=0;sl->body=a->models[x->type].proto;x->slot=s;
    {const oa_char_clip *k=sl->body.clips;sl->body.time[0]=(float)((unsigned)list[i].i*37u%(k->frames-1))/k->fps;}
    /* A body seen again after dying stays down. */
    if(x->act==OA_ACT_DEAD&&a->types[x->type].clip_death>=0){int c=a->types[x->type].clip_death;oa_character_play(&sl->body,c,1,1);sl->body.time[c]=(float)(sl->body.clips[c].frames-1)/sl->body.clips[c].fps;}
    break;}}}
 /* Models nobody is near go away, once no body uses them. */
 for(m=0;m<a->type_count;m++){model *q=a->models+m;int used=0,s;if(want[m]||q->state<STATE_CPU)continue;for(s=0;s<SLOTS;s++)if(a->slots[s].actor>=0&&a->actors[a->slots[s].actor].type==m)used=1;if(used)continue;
  pthread_mutex_lock(&a->lock);if(q->state>=STATE_BUILD)oa_character_gpu_close(&q->gpu);oa_character_free(&q->proto);q->state=STATE_NONE;pthread_mutex_unlock(&a->lock);}
 free(want);
}
static void capsule_config(opem_controller_config *c,const oa_actor_type *t){float r=t->radius<12.f?12.f:t->radius>70.f?70.f:t->radius;opem_controller_config_default(c);c->radius=r;c->height=r*5.f>480.f?480.f:r*5.f;c->step_height=r<25.f?r:25.f;c->max_speed=1000.f;c->require_ceiling=0;}
/* Each creature speaks from its own sound set; which sound on which event is authored. */
void oa_actors_use_audio(oa_actors *a,oa_audio *audio){unsigned i;if(!a)return;a->audio=audio;free(a->voice_group);a->voice_group=(int*)malloc(sizeof(int)*(a->type_count+1));if(!a->voice_group)return;for(i=0;i<a->type_count;i++){char low[24];int k;for(k=0;k<23&&a->types[i].name[k];k++){char c=a->types[i].name[k];low[k]=c==' '?'_':(char)(c>='A'&&c<='Z'?c+32:c);}low[k]=0;a->voice_group[i]=oa_audio_group(audio,low);if(a->voice_group[i]<0&&a->types[i].kind!=OA_KIND_ANIMAL)a->voice_group[i]=oa_audio_group(audio,"human");}}
static void voice(oa_actors *a,const oa_actor *x,int bodyfall){if(!a->audio||!a->voice_group)return;oa_audio_play(a->audio,bodyfall?oa_audio_group(a->audio,"bodyfall"):a->voice_group[x->type],x->pos,.8f,3000.f);}
static void handle(oa_actors *a,oa_actor *x,const oa_actor_events *e){if(e->play>=0||e->died)voice(a,x,0);if(e->died)voice(a,x,1);if(x->slot>=0){oa_character *b=&a->slots[x->slot].body;if(e->stop)oa_character_stop(b);if(e->play>=0)oa_character_play(b,e->play,e->hold,1);}}
static void angle_toward(float *yaw,float target,float amount){float d=fmodf(target-*yaw+9.424778f,6.283185f);if(d<0)d+=6.283185f;d-=3.141593f;*yaw+=d*(amount>1?1:amount);}
void oa_actors_update(oa_actors *a,const opem_collision_world *world,const float player[3],float facing,int alive,float swing_damage,float dt,oa_actors_frame *out){
 int64_t start=now_ns();unsigned i,moving=0,chasing=0,rays=0,capsules=0,paths=0;int path_budget=1;float best_turn=TURN_REACH*TURN_REACH;
 memset(out,0,sizeof(*out));if(!a)return;
 a->frame++;a->rescan-=dt;if(a->rescan<=0){a->rescan=.25f;rescan(a,player);}
 a->near_count=0;
 for(i=0;i<a->actor_count;i++){oa_actor *x=a->actors+i;const oa_actor_type *t=a->types+x->type;float dx=x->pos[0]-player[0],dy=x->pos[1]-player[1],d2=dx*dx+dy*dy;int is_near=d2<THINK_RANGE*THINK_RANGE;oa_actor_events e;float step=dt;
  /* Far actors keep their own lives at a low rate and without collision. */
  if(!is_near){if((i+a->frame)%FAR_STRIDE)continue;step=dt*FAR_STRIDE;}
  memset(&e,0,sizeof(e));e.play=-1;oa_actor_think(x,t,player,alive,step,&e);
  /* Nobody sets off for somewhere they do not fit. */
  if(x->act==OA_ACT_WALK&&a->nav.bits&&oa_nav_blocked(&a->nav,x->goal[0],x->goal[1])){x->goal[0]=x->pos[0];x->goal[1]=x->pos[1];}
  if(e.damage>0&&is_near)out->damage+=e.damage;
  handle(a,x,&e);
  if(is_near){
   if(a->near_count<NEAR_MAX)a->near_list[a->near_count++]=(int)i;
   if(e.alerted&&x->group){unsigned k;for(k=0;k<a->actor_count;k++){oa_actor *o=a->actors+k;float ox=o->pos[0]-x->pos[0],oy=o->pos[1]-x->pos[1];if(o->group==x->group&&ox*ox+oy*oy<3000.f*3000.f)oa_actor_alert(o,a->types+o->type);}}
   if(x->act==OA_ACT_CHASE||x->act==OA_ACT_ATTACK)chasing++;}
  if(x->vx!=0||x->vy!=0){float vx=x->vx,vy=x->vy;moving++;
   if(is_near&&world){float speed=sqrtf(vx*vx+vy*vy);slot *sl=x->slot>=0?a->slots+x->slot:NULL;
    /* Chasing or heading home, a nearby character follows a route around obstacles when the straight line is blocked. */
    if(sl&&a->nav.bits&&(x->act==OA_ACT_CHASE||x->act==OA_ACT_RETURN)){const float goal[2]={x->act==OA_ACT_CHASE?player[0]:x->home[0],x->act==OA_ACT_CHASE?player[1]:x->home[1]};
     sl->replan-=step;if(sl->replan<=0&&path_budget>0){sl->path_count=oa_nav_path(&a->nav,x->pos,goal,sl->path,ROUTE_POINTS);sl->path_at=0;sl->replan=.7f+(float)(i%8)*.05f;path_budget--;paths++;}
     while(sl->path_at<sl->path_count){float wx=sl->path[sl->path_at][0]-x->pos[0],wy=sl->path[sl->path_at][1]-x->pos[1],wd=sqrtf(wx*wx+wy*wy);if(wd<110.f&&sl->path_at+1<sl->path_count){sl->path_at++;continue;}if(wd>1.f){vx=wx/wd*speed;vy=wy/wd*speed;}break;}}
    if(x->detour>0){float q=x->detour_side*1.1f,c=cosf(q),s=sinf(q),rx=vx*c-vy*s;vy=vx*s+vy*c;vx=rx;x->detour-=step;}
    /* Close characters move through the same capsule collision as the player; farther ones feel ahead with rays. */
    if(sl&&d2<CAPSULE_RANGE*CAPSULE_RANGE){opem_controller_config cfg;char why[64];capsule_config(&cfg,t);
     /* The spawn search is far too slow for a frame, so a character starts where it stands, a little above the ground, if that spot is clear. */
     if(!sl->capsule_ok&&(sl->capsule_wait-=step)<=0){float at[3]={x->pos[0],x->pos[1],x->pos[2]+12.f};if(opem_controller_clear(world,&cfg,at,why,sizeof(why))){memset(&sl->capsule,0,sizeof(sl->capsule));memcpy(sl->capsule.feet,at,12);memcpy(sl->capsule.last_safe_feet,at,12);sl->capsule.valid=1;sl->capsule_ok=1;sl->stuck=0;}else sl->capsule_wait=2.f;}
     if(sl->capsule_ok){float was[2]={sl->capsule.feet[0],sl->capsule.feet[1]},wanted=speed*step;
      if(opem_controller_step(world,&cfg,&sl->capsule,vx,vy,step>.1f?.1f:step,why,sizeof(why))){float mx=sl->capsule.feet[0]-was[0],my=sl->capsule.feet[1]-was[1];memcpy(x->pos,sl->capsule.feet,12);x->ground=x->pos[2];
       sl->stuck=(wanted>.01f&&mx*mx+my*my<wanted*wanted*.09f)?sl->stuck+step:0;if(sl->stuck>.3f&&x->detour<=0){x->detour=1.1f;x->detour_side=x->detour_side>0?-1.f:1.f;sl->stuck=0;}
       angle_toward(&x->yaw,atan2f(vy,vx),step*9.f);capsules++;continue;}
      sl->capsule_ok=0;sl->capsule_wait=1.f;}}
    if((i+a->frame)%RAY_STRIDE==0){float down[3]={0,0,-1},top[3]={x->pos[0],x->pos[1],x->pos[2]+180.f},hit=0,knee[3]={x->pos[0],x->pos[1],x->pos[2]+70.f},ahead[3]={vx/speed,vy/speed,0};rays+=2;
     if(opem_collision_ray(world,top,down,420.f,&hit)&&hit<420.f)x->ground=top[2]-hit;
     if(opem_collision_ray(world,knee,ahead,t->radius+90.f,&hit)&&hit<t->radius+90.f&&x->detour<=0){x->detour=.9f;x->detour_side=(i&1)?1.f:-1.f;}}}
   x->pos[0]+=vx*step;x->pos[1]+=vy*step;angle_toward(&x->yaw,atan2f(vy,vx),step*9.f);}
  if(is_near)x->pos[2]+=(x->ground-x->pos[2])*(step*8.f>1?1:step*8.f);
  if(x->act==OA_ACT_ATTACK)angle_toward(&x->yaw,atan2f(-dy,-dx),step*9.f);}
 /* Nobody stands inside the player. */
 {unsigned p;for(p=0;p<a->near_count;p++){oa_actor *x=a->actors+a->near_list[p];float ox,oy,d,want;if(x->act==OA_ACT_DEAD)continue;ox=x->pos[0]-player[0];oy=x->pos[1]-player[1];d=ox*ox+oy*oy;want=a->types[x->type].radius+PLAYER_RADIUS;if(d<want*want&&d>1.f){d=sqrtf(d);x->pos[0]+=ox/d*(want-d)*.5f;x->pos[1]+=oy/d*(want-d)*.5f;if(x->slot>=0&&a->slots[x->slot].capsule_ok){a->slots[x->slot].capsule.feet[0]=x->pos[0];a->slots[x->slot].capsule.feet[1]=x->pos[1];}}}}
 /* Fighters keep apart. */
 {unsigned p,q;for(p=0;p<a->near_count;p++){oa_actor *x=a->actors+a->near_list[p];if(x->act!=OA_ACT_CHASE)continue;for(q=0;q<a->near_count;q++){oa_actor *o;float ox,oy,d,want;if(q==p)continue;o=a->actors+a->near_list[q];if(o->act==OA_ACT_DEAD)continue;ox=x->pos[0]-o->pos[0];oy=x->pos[1]-o->pos[1];d=ox*ox+oy*oy;want=a->types[x->type].radius+a->types[o->type].radius;if(d<want*want&&d>1.f){d=sqrtf(d);x->pos[0]+=ox/d*(want-d)*.2f;x->pos[1]+=oy/d*(want-d)*.2f;}}}}
 /* The player's swing lands on every enemy in front. */
 {unsigned p;for(p=0;p<a->near_count;p++){oa_actor *x=a->actors+a->near_list[p];const oa_actor_type *t=a->types+x->type;float dx=x->pos[0]-player[0],dy=x->pos[1]-player[1],d2=dx*dx+dy*dy;if(t->kind==OA_KIND_PERSON||x->act==OA_ACT_DEAD)continue;
   if(t->kind==OA_KIND_HOSTILE&&d2<best_turn&&fabsf(x->pos[2]-player[2])<300.f){best_turn=d2;out->turn_yaw=atan2f(dy,dx);out->has_turn=1;}
   if(swing_damage>0){float reach=PLAYER_REACH+t->radius,d=sqrtf(d2),ahead=d>1?(cosf(facing)*dx+sinf(facing)*dy)/d:1;if(d<reach&&ahead>.1f&&fabsf(x->pos[2]-player[2])<300.f){oa_actor_events e;memset(&e,0,sizeof(e));e.play=-1;oa_actor_hurt(x,t,swing_damage,&e);out->hits++;if(e.stop||e.play>=0||e.hold||e.died)handle(a,x,&e);if(e.died){out->kills++;out->killed=t->name;}
     if(e.alerted&&x->group){unsigned k;for(k=0;k<a->near_count;k++){oa_actor *o=a->actors+a->near_list[k];if(o->group==x->group)oa_actor_alert(o,a->types+o->type);}}}}}}
 /* Pose near bodies every frame and far ones less often. */
 {int s;unsigned count=0;for(s=0;s<SLOTS;s++){slot *sl=a->slots+s;oa_actor *x;const oa_actor_type *t;float dx,dy,d2,v;int stride;if(sl->actor<0)continue;count++;x=a->actors+sl->actor;t=a->types+x->type;dx=x->pos[0]-player[0];dy=x->pos[1]-player[1];d2=dx*dx+dy*dy;
   sl->pending+=dt;stride=d2<2500.f*2500.f?1:d2<5000.f*5000.f?2:4;if((++sl->tick)%stride)continue;
   v=sqrtf(x->vx*x->vx+x->vy*x->vy);memcpy(sl->body.feet,x->pos,12);sl->body.facing=x->yaw;
   if(v<1.f)oa_character_animate(&sl->body,0,0,sl->pending);else oa_character_animate(&sl->body,v>t->walk*1.3f?1.f:.3f,v,sl->pending);
   oa_character_pose(&sl->body);sl->pending=0;}
  a->stats.slots=count;}
 a->stats.near_count=a->near_count;a->stats.moving=moving;a->stats.chasing=chasing;a->stats.rays=rays;a->stats.capsules=capsules;a->stats.paths=paths>a->stats.paths?paths:a->stats.paths;{float took=(float)(now_ns()-start)*1e-6f;a->stats.update_ms=took;if(took>a->stats.update_worst)a->stats.update_worst=took;}
}
int oa_actors_focus(const oa_actors *a,const float player[3],float *health,const char **name){unsigned p;float best=FOCUS_RANGE*FOCUS_RANGE;int found=0;if(!a)return 0;
 for(p=0;p<a->near_count;p++){const oa_actor *x=a->actors+a->near_list[p];const oa_actor_type *t=a->types+x->type;float dx=x->pos[0]-player[0],dy=x->pos[1]-player[1],d=dx*dx+dy*dy;if((x->act==OA_ACT_CHASE||x->act==OA_ACT_ATTACK||x->act==OA_ACT_HIT)&&d<best){best=d;*health=t->hp>0?x->hp/t->hp:0;*name=t->name;found=1;}}
 return found;}
/* Test route: nearest enemy not yet visited, so a run stays inside the world and meets every fight in turn. */
int oa_actors_next_stop(oa_actors *a,const float from[3],float out[3]){static unsigned char *seen;static unsigned seen_count;unsigned i;int pass;if(!a||!a->actor_count)return 0;
 if(seen_count!=a->actor_count){free(seen);seen=(unsigned char*)calloc(a->actor_count,1);seen_count=seen?a->actor_count:0;if(!seen)return 0;}
 for(i=0;i<a->actor_count;i++){float dx=a->actors[i].home[0]-from[0],dy=a->actors[i].home[1]-from[1];if(dx*dx+dy*dy<3500.f*3500.f)seen[i]=1;}
 for(pass=0;pass<2;pass++){float best=1e30f;int who=-1;for(i=0;i<a->actor_count;i++){float dx,dy,d;if(seen[i]||a->types[a->actors[i].type].kind!=OA_KIND_HOSTILE)continue;dx=a->actors[i].home[0]-from[0];dy=a->actors[i].home[1]-from[1];d=dx*dx+dy*dy;if(d<best){best=d;who=(int)i;}}
  if(who>=0){memcpy(out,a->actors[who].home,12);return 1;}memset(seen,0,seen_count);}
 return 0;}
void oa_actors_gpu_update(oa_actors *a,const oa_character_gpu *from){unsigned m;if(!a||!from->ready)return;
 /* One model at a time, a little per frame. */
 for(m=0;m<a->type_count;m++){model *q=a->models+m;int state;pthread_mutex_lock(&a->lock);state=q->state;pthread_mutex_unlock(&a->lock);
  if(state==STATE_CPU){if(!oa_character_gpu_share(&q->gpu,from)){LOGE("Actor model %u unavailable",m);continue;}q->state=STATE_BUILD;state=STATE_BUILD;}
  if(state==STATE_BUILD){int r=oa_character_gpu_share_step(&q->gpu,&q->proto);if(r>0)q->state=STATE_GPU;else if(r<0){LOGE("Actor model %u upload failed",m);oa_character_gpu_close(&q->gpu);q->state=STATE_CPU;}return;}}
}
void oa_actors_gpu_close(oa_actors *a){unsigned m;int s;if(!a)return;for(s=0;s<SLOTS;s++)release_slot(a,s);pthread_mutex_lock(&a->lock);for(m=0;m<a->type_count;m++)if(a->models[m].state>=STATE_BUILD){oa_character_gpu_close(&a->models[m].gpu);a->models[m].state=STATE_CPU;}pthread_mutex_unlock(&a->lock);}
static int on_screen(const float m[16],const float p[3],float r){int j;for(j=0;j<3;j++){int sign;for(sign=-1;sign<=1;sign+=2){float n[4];int k;for(k=0;k<4;k++)n[k]=m[k*4+3]+(float)sign*m[k*4+j];if(n[0]*p[0]+n[1]*p[1]+n[2]*p[2]+n[3]+r*sqrtf(n[0]*n[0]+n[1]*n[1]+n[2]*n[2])<0)return 0;}}return 1;}
void oa_actors_draw(oa_actors *a,const float mvp[16],int room_lighting){int s;unsigned drawn=0;if(!a)return;
 for(s=0;s<SLOTS;s++){slot *sl=a->slots+s;oa_actor *x;float c[3];if(sl->actor<0)continue;x=a->actors+sl->actor;if(!oa_actor_visible(x)||a->models[x->type].state!=STATE_GPU)continue;c[0]=x->pos[0];c[1]=x->pos[1];c[2]=x->pos[2]+90.f;if(!on_screen(mvp,c,a->types[x->type].radius*6.f))continue;
  oa_character_gpu_draw(&a->models[x->type].gpu,&sl->body,mvp,room_lighting,.5f);drawn++;}
 a->stats.drawn=drawn;a->stats.models=0;{unsigned m;for(m=0;m<a->type_count;m++)if(a->models[m].state==STATE_GPU)a->stats.models++;}}
void oa_actors_draw_shadow(oa_actors *a,const float mvp[16],const float center[3]){int s,n=0;if(!a)return;for(s=0;s<SLOTS&&n<SHADOW_MAX;s++){slot *sl=a->slots+s;oa_actor *x;float dx,dy;if(sl->actor<0)continue;x=a->actors+sl->actor;dx=x->pos[0]-center[0];dy=x->pos[1]-center[1];if(dx*dx+dy*dy>SHADOW_RANGE*SHADOW_RANGE||!oa_actor_visible(x)||a->models[x->type].state!=STATE_GPU)continue;oa_character_gpu_draw(&a->models[x->type].gpu,&sl->body,mvp,0,.5f);n++;}}
void oa_actors_get_stats(oa_actors *a,oa_actors_stats *out){memset(out,0,sizeof(*out));if(a){*out=a->stats;out->total=a->actor_count;a->stats.update_worst=0;a->stats.paths=0;}}
