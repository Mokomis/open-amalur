#include "oa_actor_ai.h"
#include <math.h>
#include <string.h>
#define WANDER_PERSON 800.f
#define WANDER_ANIMAL 2500.f
#define WANDER_HOSTILE 1000.f
#define FLEE_RANGE 1200.f
#define LEASH 4000.f
#define RESPAWN 90.f
#define RESPAWN_DISTANCE 7000.f
#define HEIGHT_LIMIT 600.f
#define STRIKE_AT .45f
static float roll(oa_actor *a){uint32_t x=a->seed?a->seed:1u;x^=x<<13;x^=x>>17;x^=x<<5;a->seed=x;return (float)(x&0xffffffu)/16777216.f;}
void oa_actor_init(oa_actor *a,const float pos[3],float yaw,float hp,uint32_t seed){memset(a,0,sizeof(*a));memcpy(a->home,pos,12);memcpy(a->pos,pos,12);a->ground=pos[2];a->yaw=yaw;a->hp=hp;a->seed=seed*2654435761u+1u;a->slot=-1;a->timer=2.f+roll(a)*10.f;}
static void go_idle(oa_actor *a){a->act=OA_ACT_IDLE;a->vx=a->vy=0;a->timer=3.f+roll(a)*10.f;}
static void steer(oa_actor *a,float x,float y,float speed){float dx=x-a->pos[0],dy=y-a->pos[1],d=sqrtf(dx*dx+dy*dy);if(d>1.f){a->vx=dx/d*speed;a->vy=dy/d*speed;}else a->vx=a->vy=0;}
void oa_actor_alert(oa_actor *a,const oa_actor_type *t){if(t->kind==OA_KIND_HOSTILE&&(a->act==OA_ACT_IDLE||a->act==OA_ACT_WALK))a->act=OA_ACT_CHASE;}
void oa_actor_hurt(oa_actor *a,const oa_actor_type *t,float damage,oa_actor_events *e){
 if(a->act==OA_ACT_DEAD)return;a->hp-=damage;a->vx=a->vy=0;
 if(a->hp<=0){a->hp=0;a->act=OA_ACT_DEAD;a->timer=0;e->died=1;e->play=t->clip_death;e->hold=1;return;}
 if(t->kind==OA_KIND_HOSTILE){a->act=OA_ACT_HIT;a->timer=t->hit_len;e->play=t->clip_hit;e->alerted=1;}
 else{a->act=OA_ACT_FLEE;a->timer=5.f;}
}
void oa_actor_think(oa_actor *a,const oa_actor_type *t,const float player[3],int alive,float dt,oa_actor_events *e){
 float dx=player[0]-a->pos[0],dy=player[1]-a->pos[1],dist=sqrtf(dx*dx+dy*dy),hx=a->home[0]-a->pos[0],hy=a->home[1]-a->pos[1],hd=sqrtf(hx*hx+hy*hy);
 int reachable=alive&&fabsf(player[2]-a->pos[2])<HEIGHT_LIMIT,hostile=t->kind==OA_KIND_HOSTILE;
 a->cool=a->cool>dt?a->cool-dt:0;
 if((a->act==OA_ACT_IDLE||a->act==OA_ACT_WALK)&&hostile&&reachable&&dist<t->aggro){a->act=OA_ACT_CHASE;e->alerted=1;}
 if((a->act==OA_ACT_IDLE||a->act==OA_ACT_WALK)&&t->kind==OA_KIND_ANIMAL&&dist<FLEE_RANGE){a->act=OA_ACT_FLEE;a->timer=4.f;}
 switch((oa_actor_act)a->act){
 case OA_ACT_IDLE:a->vx=a->vy=0;a->timer-=dt;
  if(a->timer<=0){float angle=roll(a)*6.283185f,r=roll(a)*(t->kind==OA_KIND_PERSON?WANDER_PERSON:t->kind==OA_KIND_ANIMAL?WANDER_ANIMAL:WANDER_HOSTILE);a->goal[0]=a->home[0]+cosf(angle)*r;a->goal[1]=a->home[1]+sinf(angle)*r;a->act=OA_ACT_WALK;a->timer=r/(t->walk>1?t->walk:1)+2.f;}
  break;
 case OA_ACT_WALK:{float gx=a->goal[0]-a->pos[0],gy=a->goal[1]-a->pos[1];a->timer-=dt;if(gx*gx+gy*gy<60.f*60.f||a->timer<=0)go_idle(a);else steer(a,a->goal[0],a->goal[1],t->walk);break;}
 case OA_ACT_FLEE:a->timer-=dt;if(a->timer<=0)go_idle(a);else steer(a,a->pos[0]-dx,a->pos[1]-dy,t->run);break;
 case OA_ACT_CHASE:
  if(!alive||dist>t->aggro*2.f||hd>LEASH){a->act=OA_ACT_RETURN;break;}
  if(dist>t->reach*.75f)steer(a,player[0],player[1],t->run);
  else{a->vx=a->vy=0;if(dist>1)a->yaw=atan2f(dy,dx);if(a->cool<=0&&reachable){a->act=OA_ACT_ATTACK;a->clock=0;e->play=t->clip_attack;}}
  break;
 case OA_ACT_ATTACK:{float before=a->clock,strike=t->attack_len*STRIKE_AT;a->vx=a->vy=0;a->clock+=dt;
  if(before<strike&&a->clock>=strike&&alive&&dist<t->reach+40.f&&fabsf(player[2]-a->pos[2])<HEIGHT_LIMIT)e->damage=t->damage;
  if(a->clock>=t->attack_len){a->act=OA_ACT_CHASE;a->cool=1.1f+roll(a)*.8f;e->stop=1;}
  break;}
 case OA_ACT_HIT:a->vx=a->vy=0;a->timer-=dt;if(a->timer<=0){a->act=OA_ACT_CHASE;a->cool=.5f;e->stop=1;}break;
 case OA_ACT_DEAD:a->vx=a->vy=0;a->timer+=dt;if(a->timer>=RESPAWN&&dist>RESPAWN_DISTANCE){memcpy(a->pos,a->home,12);a->ground=a->home[2];a->hp=t->hp;go_idle(a);e->stop=1;}break;
 case OA_ACT_RETURN:if(hd<80.f){a->hp=t->hp;go_idle(a);}else steer(a,a->home[0],a->home[1],t->run);break;
 }
}
