#include "oa_combat.h"
#include "oa_combat_clips.h"
#include <math.h>
#include <string.h>
/* Authored rules. Distances are world units, 100 per metre. */
#define PLAYER_HP 100.f
#define FOE_HP 100.f
#define PLAYER_DAMAGE 22.f
#define FOE_DAMAGE 9.f
#define PLAYER_REACH 240.f
#define FOE_REACH 210.f
#define AGGRO_RANGE 1400.f
#define STOP_RANGE 165.f
#define FOE_SPEED 300.f
#define FOE_COOLDOWN 1.3f
#define SWING_TAIL .3f
#define FOE_SWING_TAIL .55f
#define PLAYER_RATE 1.f
#define CHAIN_AFTER .2f
#define FOE_STRIKE 1.1333f
#define RESPAWN_PLAYER 3.5f
#define RESPAWN_FOE 7.f
float oa_combat_clip_seconds(int clip){return clip>=0&&clip<OA_COMBAT_CLIPS?oa_combat_seconds[clip]:1.f;}
static int crossed(int clip,float before,float after){int i;for(i=0;i<OA_COMBAT_STRIKES;i++){float t=oa_combat_strikes[clip][i];if(t>0&&before<t&&after>=t)return 1;}return 0;}
void oa_combat_reset(oa_combat *c){memset(c,0,sizeof(*c));c->player_hp=c->player_max=PLAYER_HP;c->foe_hp=c->foe_max=FOE_HP;c->foe=OA_FOE_WAIT;c->play_player=c->play_foe=-1;c->player_damage=PLAYER_DAMAGE;c->foe_damage=FOE_DAMAGE;}
/* A tap during a swing earns the next one soon after the swing lands; the timing of that window is authored. */
static void start_swing(oa_combat *c,int clip){c->player_clip=clip;c->player_time=0;c->player_free_at=0;c->player_length=oa_combat_clip_seconds(clip)/PLAYER_RATE;c->play_player=clip;c->play_player_rate=PLAYER_RATE;c->queued=0;}
void oa_combat_hurt_player(oa_combat *c,float damage){if(c->player_dead)return;c->player_hp-=damage;c->player_struck=1;
 if(c->player_hp<=0){c->player_hp=0;c->player_dead=1;c->player_dead_time=0;c->player_clip=0;c->queued=0;c->play_player=OA_FIGHT_DEATH;c->hold_player=1;c->play_player_rate=1;}
 else if(!c->player_clip){c->player_clip=OA_FIGHT_HIT;c->player_time=0;c->player_length=oa_combat_clip_seconds(OA_FIGHT_HIT);c->play_player=OA_FIGHT_HIT;c->play_player_rate=1;}}
void oa_combat_step(oa_combat *c,float dt,int attack,const float player[3],float facing,const float foe[3]){
 float dx=foe[0]-player[0],dy=foe[1]-player[1],dist=sqrtf(dx*dx+dy*dy),ahead;
 c->play_player=c->play_foe=-1;c->hold_player=c->hold_foe=0;c->respawn_player=c->respawn_foe=0;c->foe_vx=c->foe_vy=0;c->player_turn=0;c->player_struck=c->foe_struck=0;c->stop_player=c->stop_foe=0;c->swing_landed=0;
 /* Player */
 if(c->player_dead){attack=0;c->player_dead_time+=dt;if(c->player_dead_time>=RESPAWN_PLAYER){c->player_dead=0;c->player_dead_time=0;c->player_hp=c->player_max;c->player_clip=0;c->respawn_player=1;c->foe=OA_FOE_WAIT;}}
 else if(c->player_clip){float before=c->player_time;c->player_time+=dt;
  if(attack&&oa_fight_is_swing(c->player_clip))c->queued=1;
  if(oa_fight_is_swing(c->player_clip)&&crossed(c->player_clip,before*PLAYER_RATE,c->player_time*PLAYER_RATE)){
   c->swing_landed=1;c->player_free_at=c->player_time+CHAIN_AFTER;
   ahead=dist>1?(cosf(facing)*dx+sinf(facing)*dy)/dist:1;
   if(c->foe!=OA_FOE_DEAD&&dist<PLAYER_REACH&&ahead>.1f){c->foe_hp-=c->player_damage;c->foe_struck=1;c->player_hits++;
    if(c->foe_hp<=0){c->foe_hp=0;c->foe=OA_FOE_DEAD;c->foe_time=0;c->play_foe=OA_FIGHT_DEATH;c->hold_foe=1;}
    else{c->foe=OA_FOE_HIT;c->foe_time=0;c->foe_length=1.3667f;c->play_foe=OA_FIGHT_HIT;}}}
  {static const int next[4]={OA_FIGHT_ATTACK_A,OA_FIGHT_ATTACK_B,OA_FIGHT_ATTACK_C,OA_FIGHT_ATTACK_D};int free=c->player_free_at>0&&c->player_time>=c->player_free_at;
   if(free&&c->queued&&c->player_stage<3&&oa_fight_is_swing(c->player_clip)){c->player_stage++;start_swing(c,next[c->player_stage]);}
   else if(c->player_time>=c->player_length){if(c->queued&&oa_fight_is_swing(c->player_clip)){c->player_stage=0;start_swing(c,OA_FIGHT_ATTACK_A);}else{c->queued=0;c->player_clip=0;c->player_stage=0;c->player_free_at=0;c->stop_player=1;}}}}
 else if(attack){c->player_stage=0;start_swing(c,OA_FIGHT_ATTACK_A);}
 /* Turn toward a nearby foe at the start of a swing so a tap lands. */
 if(oa_fight_is_swing(c->play_player)&&c->foe!=OA_FOE_DEAD&&dist<PLAYER_REACH*1.8f&&dist>1){c->player_facing=atan2f(dy,dx);c->player_turn=1;}
 /* Foe */
 c->foe_cooldown=c->foe_cooldown>dt?c->foe_cooldown-dt:0;
 switch(c->foe){
 case OA_FOE_WAIT:if(dist<AGGRO_RANGE&&!c->player_dead)c->foe=OA_FOE_CHASE;break;
 case OA_FOE_CHASE:
  if(c->player_dead||dist>AGGRO_RANGE*1.6f){c->foe=OA_FOE_WAIT;break;}
  if(dist>1)c->foe_facing=atan2f(-dy,-dx);
  if(dist>STOP_RANGE){c->foe_vx=-dx/dist*FOE_SPEED;c->foe_vy=-dy/dist*FOE_SPEED;}
  else if(c->foe_cooldown<=0){c->foe=OA_FOE_ATTACK;c->foe_time=0;c->foe_length=FOE_STRIKE+FOE_SWING_TAIL;c->foe_hits=0;c->play_foe=OA_FIGHT_ATTACK_C;}
  break;
 case OA_FOE_ATTACK:{float before=c->foe_time;c->foe_time+=dt;
  if(before<FOE_STRIKE&&c->foe_time>=FOE_STRIKE&&!c->player_dead&&dist<FOE_REACH){c->player_hp-=c->foe_damage;c->player_struck=1;
   if(c->player_hp<=0){c->player_hp=0;c->player_dead=1;c->player_dead_time=0;c->player_clip=0;c->queued=0;c->play_player=OA_FIGHT_DEATH;c->hold_player=1;c->play_player_rate=1;}
   else if(!c->player_clip){c->player_clip=OA_FIGHT_HIT;c->player_time=0;c->player_length=oa_combat_clip_seconds(OA_FIGHT_HIT);c->play_player=OA_FIGHT_HIT;c->play_player_rate=1;}}
  if(c->foe_time>=c->foe_length){c->foe=OA_FOE_CHASE;c->foe_cooldown=FOE_COOLDOWN;c->stop_foe=1;}
  break;}
 case OA_FOE_HIT:c->foe_time+=dt;if(c->foe_time>=c->foe_length){c->foe=OA_FOE_CHASE;c->foe_cooldown=FOE_COOLDOWN*.5f;}break;
 case OA_FOE_DEAD:c->foe_time+=dt;if(c->foe_time>=RESPAWN_FOE){c->foe=OA_FOE_WAIT;c->foe_hp=c->foe_max;c->respawn_foe=1;}break;
 }
 c->player_locked=c->player_dead||(c->player_clip&&!(c->player_free_at>0&&c->player_time>=c->player_free_at));
}
