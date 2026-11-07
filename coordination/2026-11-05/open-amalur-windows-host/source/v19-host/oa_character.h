#ifndef OA_CHARACTER_H
#define OA_CHARACTER_H
/* Skinned preview character. Clips are native Edge decompressor output baked offline;
 * part selection and movement blending are authored host policy, not native motion trees. */
#include <stddef.h>
#include <stdint.h>
enum{OA_CHAR_MAX_JOINTS=128,OA_CHAR_MAX_PALETTE=96,OA_CHAR_MAX_CLIPS=30,OA_CHAR_MAX_PARTS=24,OA_CHAR_MAX_TEXTURES=16,OA_CHAR_VERTEX_BYTES=52,OA_CHAR_PALETTE_BYTES=32};
enum{OA_CLIP_IDLE=0,OA_CLIP_WALK=1,OA_CLIP_RUN=2,OA_CLIP_COMBAT=8,OA_CLIP_RUN_START=12,OA_CLIP_RUN_STOP=13,OA_CLIP_RUN_STOP_SHORT=14,OA_CLIP_WALK_START=15,OA_CLIP_WALK_STOP=16,OA_CLIP_RUN_TURN_LEFT=17,OA_CLIP_RUN_TURN_RIGHT=18,OA_CLIP_RUN_TURN_BACK=19,OA_CLIP_WALK_TURN_LEFT=20,OA_CLIP_WALK_TURN_RIGHT=21,OA_CLIP_SLOPE_UP=22,OA_CLIP_SLOPE_DOWN=23,OA_CLIP_LEAN_LEFT=24,OA_CLIP_LEAN_RIGHT=25,OA_CLIP_IDLE_VARIATION=26};
typedef struct oa_char_clip{uint32_t frames;float fps;const float *pose;}oa_char_clip;
typedef struct oa_char_texture{uint32_t width,height;const uint8_t *rgba;}oa_char_texture;
typedef struct oa_char_part{uint32_t vertices,indices,palette_count;int32_t texture;const uint8_t *palette,*vertex;const uint32_t *index;}oa_char_part;
typedef struct oa_character{
 uint8_t *bytes;size_t size;
 uint32_t joints,clip_count,part_count,texture_count;
 int16_t parents[OA_CHAR_MAX_JOINTS];
 oa_char_clip clips[OA_CHAR_MAX_CLIPS];
 oa_char_part parts[OA_CHAR_MAX_PARTS];
 oa_char_texture textures[OA_CHAR_MAX_TEXTURES];
 float time[OA_CHAR_MAX_CLIPS],weight[OA_CHAR_MAX_CLIPS];
 /* How fast each clip's planted foot travels, measured from the clip; 0 when it has none. */
 float clip_speed[OA_CHAR_MAX_CLIPS];
 /* Moves with the clips from OA_CLIP_COMBAT when the character has them. */
 int combat_stance;
 float world_q[OA_CHAR_MAX_JOINTS][4],world_t[OA_CHAR_MAX_JOINTS][3];
 float facing,feet[3];
 /* One-shot clip layered over locomotion; -1 when none plays. */
 int oneshot,oneshot_hold;
 float oneshot_rate;
 /* Start, stop, turn or idle variation playing over locomotion; -1 when none. Only characters with every clip have these. */
 int move_clip,was_moving;
 float moved_for,idle_for,idle_next,turn_total,move_target;
 uint32_t idle_seed;
 /* Pose differences from the slope and lean clips, -1..1 each; NULL without those clips. */
 float *lean_delta,slope,lean;
 /* Parts not drawn, one bit each; used to swap weapon models. */
 uint32_t hidden;
 int ready;
}oa_character;
/* Takes ownership of a malloc buffer on success. */
int oa_character_parse(oa_character *c,uint8_t *bytes,size_t size,char *error,size_t error_size);
void oa_character_free(oa_character *c);
/* speed is 0..1 stick magnitude; velocity_units is world units per second. */
void oa_character_animate(oa_character *c,float speed,float velocity_units,float dt);
/* Radians the body may turn this frame toward an angle turn away. */
float oa_character_turn_step(const oa_character *c,float turn,float dt);
void oa_character_play(oa_character *c,int clip,int hold,float rate);
void oa_character_stop(oa_character *c);
void oa_character_pose(oa_character *c);
/* Writes three vec4 rows per palette entry, in world space. Returns the entry count. */
uint32_t oa_character_bones(const oa_character *c,const oa_char_part *part,float *rows);
#endif
