#ifndef OA_CHARACTER_H
#define OA_CHARACTER_H
/* Skinned preview character. Clips are native Edge decompressor output baked offline;
 * part selection and movement blending are authored host policy, not native motion trees. */
#include <stddef.h>
#include <stdint.h>
enum{OA_CHAR_MAX_JOINTS=96,OA_CHAR_MAX_PALETTE=64,OA_CHAR_MAX_CLIPS=4,OA_CHAR_MAX_PARTS=8,OA_CHAR_MAX_TEXTURES=8,OA_CHAR_VERTEX_BYTES=52,OA_CHAR_PALETTE_BYTES=32};
enum{OA_CLIP_IDLE=0,OA_CLIP_WALK=1,OA_CLIP_RUN=2};
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
 float world_q[OA_CHAR_MAX_JOINTS][4],world_t[OA_CHAR_MAX_JOINTS][3];
 float facing,feet[3];
 int ready;
}oa_character;
/* Takes ownership of a malloc buffer on success. */
int oa_character_parse(oa_character *c,uint8_t *bytes,size_t size,char *error,size_t error_size);
void oa_character_free(oa_character *c);
/* speed is 0..1 stick magnitude; velocity_units is world units per second. */
void oa_character_animate(oa_character *c,float speed,float velocity_units,float dt);
void oa_character_pose(oa_character *c);
/* Writes three vec4 rows per palette entry, in world space. Returns the entry count. */
uint32_t oa_character_bones(const oa_character *c,const oa_char_part *part,float *rows);
#endif
