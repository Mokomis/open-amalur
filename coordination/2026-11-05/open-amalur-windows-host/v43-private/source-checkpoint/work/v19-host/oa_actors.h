#ifndef OA_ACTORS_H
#define OA_ACTORS_H
/* Every character and creature of the zone. Placement, models and clips come from the game; behaviour is oa_actor_ai.
 * Models load on a background thread near the player. GL work stays on the render thread. */
#include "oa_character_gl.h"
#include "opem_collision.h"
struct oa_audio;
typedef struct oa_actors oa_actors;
typedef struct oa_actors_frame{float damage,turn_yaw;int has_turn,kills,hits;const char *killed;}oa_actors_frame;
typedef struct oa_actors_stats{unsigned total,near_count,moving,chasing,slots,drawn,models,rays,capsules,paths;float update_ms,update_worst;}oa_actors_stats;
struct AAssetManager;
oa_actors *oa_actors_open(struct AAssetManager *assets);
void oa_actors_close(oa_actors *a);
void oa_actors_update(oa_actors *a,const opem_collision_world *world,const float player[3],float facing,int alive,float swing_damage,float dt,oa_actors_frame *out);
/* The enemy to show in the HUD. Returns 0 when nobody is engaged. */
int oa_actors_focus(const oa_actors *a,const float player[3],float *health,const char **name);
int oa_actors_next_stop(oa_actors *a,const float from[3],float out[3]);
void oa_actors_use_audio(oa_actors *a,struct oa_audio *audio);
/* Render thread. */
void oa_actors_gpu_update(oa_actors *a,const oa_character_gpu *from);
void oa_actors_gpu_close(oa_actors *a);
void oa_actors_draw(oa_actors *a,const float mvp[16],int room_lighting);
void oa_actors_draw_shadow(oa_actors *a,const float mvp[16],const float center[3]);
void oa_actors_get_stats(oa_actors *a,oa_actors_stats *out);
#endif
