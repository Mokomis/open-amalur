#ifndef OA_ACTOR_AI_H
#define OA_ACTOR_AI_H
/* What each character does. All of this is authored behaviour: the game's behaviour trees are not recovered.
 * Distances are world units, 100 per metre. */
#include <stdint.h>
enum{OA_KIND_PERSON,OA_KIND_ANIMAL,OA_KIND_HOSTILE};
typedef enum{OA_ACT_IDLE,OA_ACT_WALK,OA_ACT_FLEE,OA_ACT_CHASE,OA_ACT_ATTACK,OA_ACT_HIT,OA_ACT_DEAD,OA_ACT_RETURN}oa_actor_act;
/* Stored as is in the actor index. */
typedef struct oa_actor_type{float walk,run,radius,hp,damage,aggro,reach,attack_len,hit_len;int32_t clip_attack,clip_hit,clip_death;uint32_t kind;char name[24];}oa_actor_type;
typedef struct oa_actor{float home[3],pos[3],goal[2],yaw,hp,timer,clock,cool,vx,vy,detour,detour_side,ground;uint32_t seed;int32_t slot;uint16_t type,group;uint8_t act;}oa_actor;
/* Requests for the caller, rebuilt on every step. */
typedef struct oa_actor_events{int play,hold,stop,died,alerted;float damage;}oa_actor_events;
void oa_actor_init(oa_actor *a,const float pos[3],float yaw,float hp,uint32_t seed);
void oa_actor_think(oa_actor *a,const oa_actor_type *t,const float player[3],int player_alive,float dt,oa_actor_events *e);
void oa_actor_hurt(oa_actor *a,const oa_actor_type *t,float damage,oa_actor_events *e);
void oa_actor_alert(oa_actor *a,const oa_actor_type *t);
/* Bodies stay on the ground for a while, then are gone until the respawn. */
static inline int oa_actor_visible(const oa_actor *a){return a->act!=OA_ACT_DEAD||a->timer<15.f;}
#endif
