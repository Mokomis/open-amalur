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
#define PLAYER_RATE 1.25f
#define RESPAWN_PLAYER 3.5f
#define RESPAWN_FOE 7.f
float oa_combat_clip_seconds(int clip){return clip>=0&&clip<OA_COMBAT_CLIPS?oa_combat_seconds[clip]:1.f;}
static int crossed(int clip,float before,float after){int i;for(i=0;i<OA_COMBAT_STRIKES;i++){float t=oa_combat_strikes[clip][i];if(t>0&&before<t&&after>=t)return 1;}return 0;}
void oa_combat_reset(oa_combat *c){memset(c,0,sizeof(*c));c->player_hp=c->player_max=PLAYER_HP;c->foe_hp=c->foe_max=FOE_HP;c->foe=OA_FOE_WAIT;c->play_player=c->play_foe=-1;}
/* The attack clip holds three swings. Each tap earns the next one; without another tap the swing ends just after it lands. */
static void start_swing(oa_combat *c,int clip){c->player_clip=clip;c->player_time=0;c->player_length=oa_combat_clip_seconds(clip)/PLAYER_RATE;c->play_player=clip;c->play_player_rate=PLAYER_RATE;c->queued=0;}
void oa_combat_step(oa_combat *c,float dt,int attack,const float player[3],float facing,const float foe[3]){
 float dx=foe[0]-player[0],dy=foe[1]-player[1],dist=sqrtf(dx*dx+dy*dy),ahead;
 c->play_player=c->play_foe=-1;c->hold_player=c->hold_foe=0;c->respawn_player=c->respawn_foe=0;c->foe_vx=c->foe_vy=0;c->player_turn=0;c->player_struck=c->foe_struck=0;c->stop_player=c->stop_foe=0;
 /* Player */
 if(c->player_dead){attack=0;c->player_dead_time+=dt;if(c->player_dead_time>=RESPAWN_PLAYER){c->player_dead=0;c->player_dead_time=0;c->player_hp=c->player_max;c->player_clip=0;c->respawn_player=1;c->foe=OA_FOE_WAIT;}}
 else if(c->player_clip){float before=c->player_time;c->player_time+=dt;
  if(attack&&c->player_clip!=OA_FIGHT_HIT)c->queued=1;
  if(c->player_clip!=OA_FIGHT_HIT&&crossed(c->player_clip,before*PLAYER_RATE,c->player_time*PLAYER_RATE)){
   if(c->queued)c->queued=0;else{float end=c->player_time+SWING_TAIL;if(end<c->player_length)c->player_length=end;}
   ahead=dist>1?(cosf(facing)*dx+sinf(facing)*dy)/dist:1;
   if(c->foe!=OA_FOE_DEAD&&dist<PLAYER_REACH&&ahead>.1f){c->foe_hp-=PLAYER_DAMAGE;c->foe_struck=1;c->player_hits++;
    if(c->foe_hp<=0){c->foe_hp=0;c->foe=OA_FOE_DEAD;c->foe_time=0;c->play_foe=OA_FIGHT_DEATH;c->hold_foe=1;}
    else{c->foe=OA_FOE_HIT;c->foe_time=0;c->foe_length=oa_combat_clip_seconds(OA_FIGHT_HIT);c->play_foe=OA_FIGHT_HIT;}}}
  if(c->player_time>=c->player_length){c->queued=0;c->player_clip=0;c->stop_player=1;}}
 else if(attack)start_swing(c,OA_FIGHT_ATTACK_C);
 /* Turn toward a nearby foe at the start of a swing so a tap lands. */
 if(c->play_player>=OA_FIGHT_ATTACK_A&&c->play_player<=OA_FIGHT_ATTACK_C&&c->foe!=OA_FOE_DEAD&&dist<PLAYER_REACH*1.8f&&dist>1){c->player_facing=atan2f(dy,dx);c->player_turn=1;}
 /* Foe */
 c->foe_cooldown=c->foe_cooldown>dt?c->foe_cooldown-dt:0;
 switch(c->foe){
 case OA_FOE_WAIT:if(dist<AGGRO_RANGE&&!c->player_dead)c->foe=OA_FOE_CHASE;break;
 case OA_FOE_CHASE:
  if(c->player_dead||dist>AGGRO_RANGE*1.6f){c->foe=OA_FOE_WAIT;break;}
  if(dist>1)c->foe_facing=atan2f(-dy,-dx);
  if(dist>STOP_RANGE){c->foe_vx=-dx/dist*FOE_SPEED;c->foe_vy=-dy/dist*FOE_SPEED;}
  else if(c->foe_cooldown<=0){c->foe=OA_FOE_ATTACK;c->foe_time=0;c->foe_length=oa_combat_strikes[OA_FIGHT_ATTACK_C][0]+FOE_SWING_TAIL;c->foe_hits=0;c->play_foe=OA_FIGHT_ATTACK_C;}
  break;
 case OA_FOE_ATTACK:{float before=c->foe_time;c->foe_time+=dt;
  if(crossed(OA_FIGHT_ATTACK_C,before,c->foe_time)&&!c->player_dead&&dist<FOE_REACH){c->player_hp-=FOE_DAMAGE;c->player_struck=1;
   if(c->player_hp<=0){c->player_hp=0;c->player_dead=1;c->player_dead_time=0;c->player_clip=0;c->queued=0;c->play_player=OA_FIGHT_DEATH;c->hold_player=1;c->play_player_rate=1;}
   else if(!c->player_clip){c->player_clip=OA_FIGHT_HIT;c->player_time=0;c->player_length=oa_combat_clip_seconds(OA_FIGHT_HIT);c->play_player=OA_FIGHT_HIT;c->play_player_rate=1;}}
  if(c->foe_time>=c->foe_length){c->foe=OA_FOE_CHASE;c->foe_cooldown=FOE_COOLDOWN;c->stop_foe=1;}
  break;}
 case OA_FOE_HIT:c->foe_time+=dt;if(c->foe_time>=c->foe_length){c->foe=OA_FOE_CHASE;c->foe_cooldown=FOE_COOLDOWN*.5f;}break;
 case OA_FOE_DEAD:c->foe_time+=dt;if(c->foe_time>=RESPAWN_FOE){c->foe=OA_FOE_WAIT;c->foe_hp=c->foe_max;c->respawn_foe=1;}break;
 }
 c->player_locked=c->player_dead||c->player_clip;
}
