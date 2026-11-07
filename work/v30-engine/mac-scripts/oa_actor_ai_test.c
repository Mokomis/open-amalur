#include "oa_actor_ai.h"
#include <stdio.h>
#include <string.h>
static int checks,failed;
#define CHECK(x) do{checks++;if(!(x)){failed++;printf("FAILED line %d: %s\n",__LINE__,#x);}}while(0)
static const oa_actor_type foe={150,420,35,70,6,1600,215,1.f,.5f,3,4,5,OA_KIND_HOSTILE,"Foe"},deer={150,640,35,40,0,0,0,1,1,-1,-1,-1,OA_KIND_ANIMAL,"Deer"},man={150,420,35,70,6,0,0,1,1,-1,-1,-1,OA_KIND_PERSON,"Man"};
static void run(oa_actor *a,const oa_actor_type *t,const float p[3],int alive,float secs,oa_actor_events *sum){int i,n=(int)(secs*60.f);memset(sum,0,sizeof(*sum));sum->play=-1;for(i=0;i<n;i++){oa_actor_events e;memset(&e,0,sizeof(e));e.play=-1;oa_actor_think(a,t,p,alive,1.f/60.f,&e);if(e.play>=0)sum->play=e.play;sum->damage+=e.damage;sum->alerted|=e.alerted;a->pos[0]+=a->vx/60.f;a->pos[1]+=a->vy/60.f;}}
int main(void){oa_actor a;oa_actor_events e;const float home[3]={0,0,0},near_p[3]={1000,0,0},far_p[3]={50000,0,0},close_p[3]={100,0,0},high_p[3]={100,0,5000};
 oa_actor_init(&a,home,0,foe.hp,1);run(&a,&foe,far_p,1,1,&e);CHECK(a.act==OA_ACT_IDLE||a.act==OA_ACT_WALK);CHECK(!e.alerted);
 oa_actor_init(&a,home,0,foe.hp,2);run(&a,&foe,near_p,1,.1f,&e);CHECK(a.act==OA_ACT_CHASE);CHECK(e.alerted);CHECK(a.vx>0);
 oa_actor_init(&a,home,0,foe.hp,3);run(&a,&foe,close_p,1,.1f,&e);CHECK(a.act==OA_ACT_ATTACK);CHECK(e.play==foe.clip_attack);
 run(&a,&foe,close_p,1,1.f,&e);CHECK(e.damage==foe.damage);CHECK(a.act==OA_ACT_CHASE);CHECK(a.cool>0);
 /* A foe on another level cannot strike. */
 oa_actor_init(&a,home,0,foe.hp,4);run(&a,&foe,high_p,1,3,&e);CHECK(e.damage==0);
 /* A foe ignores a dead player and walks home. */
 oa_actor_init(&a,home,0,foe.hp,5);a.act=OA_ACT_CHASE;a.pos[0]=2000;a.hp=10;run(&a,&foe,near_p,0,10,&e);CHECK(a.act==OA_ACT_IDLE||a.act==OA_ACT_WALK);CHECK(a.hp==foe.hp);CHECK(a.pos[0]<1100);
 /* The leash holds. */
 oa_actor_init(&a,home,0,foe.hp,6);a.act=OA_ACT_CHASE;a.pos[0]=4100;{const float p[3]={4500,0,0};run(&a,&foe,p,1,.05f,&e);}CHECK(a.act==OA_ACT_RETURN);
 /* Hurt, then killed once. */
 memset(&e,0,sizeof(e));e.play=-1;oa_actor_init(&a,home,0,foe.hp,7);oa_actor_hurt(&a,&foe,10,&e);CHECK(a.act==OA_ACT_HIT);CHECK(a.hp==60);CHECK(e.play==foe.clip_hit);CHECK(e.alerted);
 memset(&e,0,sizeof(e));e.play=-1;oa_actor_hurt(&a,&foe,100,&e);CHECK(a.act==OA_ACT_DEAD);CHECK(e.died==1);CHECK(e.hold==1);CHECK(e.play==foe.clip_death);
 memset(&e,0,sizeof(e));e.play=-1;oa_actor_hurt(&a,&foe,100,&e);CHECK(e.died==0);
 run(&a,&foe,close_p,1,20,&e);CHECK(!oa_actor_visible(&a));CHECK(a.act==OA_ACT_DEAD);
 run(&a,&foe,close_p,1,80,&e);CHECK(a.act==OA_ACT_DEAD);
 run(&a,&foe,far_p,1,1,&e);CHECK(a.act!=OA_ACT_DEAD);CHECK(a.hp==foe.hp);
 /* A nearby foe joins when its group is alerted; a body does not. */
 oa_actor_init(&a,home,0,foe.hp,8);oa_actor_alert(&a,&foe);CHECK(a.act==OA_ACT_CHASE);
 a.act=OA_ACT_DEAD;oa_actor_alert(&a,&foe);CHECK(a.act==OA_ACT_DEAD);
 /* Animals run away from the player and settle. */
 oa_actor_init(&a,home,0,deer.hp,9);run(&a,&deer,near_p,1,.5f,&e);CHECK(a.act==OA_ACT_FLEE);CHECK(a.vx<0);run(&a,&deer,far_p,1,5,&e);CHECK(a.act!=OA_ACT_FLEE);
 /* People wander near home and never fight. */
 oa_actor_init(&a,home,0,man.hp,10);run(&a,&man,close_p,1,120,&e);CHECK(a.act==OA_ACT_IDLE||a.act==OA_ACT_WALK);CHECK(e.damage==0);CHECK(a.pos[0]*a.pos[0]+a.pos[1]*a.pos[1]<1000.f*1000.f);
 printf("actor ai checks %d failed %d\n",checks,failed);return failed!=0;}
