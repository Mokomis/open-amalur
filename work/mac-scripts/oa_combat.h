#ifndef OA_COMBAT_H
#define OA_COMBAT_H
/* First playable fight. Clips and strike times come from game assets; health, damage,
 * reach, enemy behaviour and timing are authored host rules, not recovered game values. */
enum{OA_FIGHT_IDLE=0,OA_FIGHT_ATTACK_A=3,OA_FIGHT_ATTACK_B=4,OA_FIGHT_ATTACK_C=5,OA_FIGHT_HIT=6,OA_FIGHT_DEATH=7};
typedef enum oa_foe_state{OA_FOE_WAIT,OA_FOE_CHASE,OA_FOE_ATTACK,OA_FOE_HIT,OA_FOE_DEAD}oa_foe_state;
typedef struct oa_combat{
 float player_hp,foe_hp,player_max,foe_max;
 /* Player */
 int player_clip,player_dead,queued;
 float player_time,player_length,player_dead_time;
 unsigned player_hits;
 /* Foe */
 oa_foe_state foe;
 float foe_time,foe_length,foe_cooldown,foe_facing;
 unsigned foe_hits;
 /* Requests for the caller, rebuilt on every step. */
 int play_player,play_foe;
 float play_player_rate;
 int hold_player,hold_foe,respawn_player,respawn_foe;
 float foe_vx,foe_vy,player_facing;
 int player_turn,player_locked,player_struck,foe_struck,stop_player,stop_foe;
}oa_combat;
void oa_combat_reset(oa_combat *c);
void oa_combat_step(oa_combat *c,float dt,int attack,const float player[3],float facing,const float foe[3]);
/* Clip lengths in seconds, indexed like the clip list; supplied by generated data. */
float oa_combat_clip_seconds(int clip);
#endif
