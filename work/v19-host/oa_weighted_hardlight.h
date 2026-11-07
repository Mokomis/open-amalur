#ifndef OA_WEIGHTED_HARDLIGHT_H
#define OA_WEIGHTED_HARDLIGHT_H
#include <stddef.h>
#include <stdint.h>
#include <GLES3/gl3.h>
#include "oa_character.h"
enum {OA_WH_ALLOWED_MASK=(1u<<1)|(1u<<2)|(1u<<3)|(1u<<5),
 OA_WH_COLOR_AUTHORED=1,OA_WH_COLOR_NATIVE_SHARED_ALL_FF=2};
/* Callback returns a malloc-owned complete file; adapter frees it. Names are
 * prefix + exact staged portable OATX filenames. No engine/user files are written. */
typedef int (*oa_wh_read_malloc)(void *user,const char *name,uint8_t **bytes,size_t *size);
typedef struct oa_wh_part {GLuint vao,vbo,ibo,texture[3];unsigned part,material,vertices,indices,color_provenance,source_stride;} oa_wh_part;
typedef struct oa_weighted_hardlight {GLuint program,cube,dummy_ao,dummy_shadow,dummy_grid;uint32_t ready_mask;int frame_ready;const oa_character *owner;oa_wh_part parts[4];} oa_weighted_hardlight;
/* Explicit opt-in only. c must come from the pinned Almain pack after BOTH
 * production oa_character_repairs_apply repairs, then oa_character_parse.
 * attrs=original pinned OACAT; cube=1536 authored BGRA bytes of opening BASE/Start
 * CHARACTER cube1. Neither caller buffer is retained. Returns admitted PART bits;
 * missing/failed parts remain absent for old-path fallback. A partial result can
 * carry a diagnostic in error. Start with zeroed object; close before reopening. */
uint32_t oa_weighted_hardlight_open(oa_weighted_hardlight *,const oa_character *,
 const uint8_t *attrs,size_t attrs_size,const uint8_t *character_cube_bgra,size_t cube_size,
 oa_wh_read_malloc read_file,void *user,const char *texture_prefix,
 uint32_t allow_part_mask,unsigned light_capacity,char *error,size_t error_capacity);
void oa_weighted_hardlight_close(oa_weighted_hardlight *);
GLuint oa_weighted_hardlight_program(const oa_weighted_hardlight *);
uint32_t oa_weighted_hardlight_ready_mask(const oa_weighted_hardlight *);
/* Per-frame optional safe starting point: selects program, ambient-only native
 * material defaults, binds typed dummy AO/shadow/grid at9/10/11, owned cube8.
 * Requires finite actual WORLD eye (rim is view-dependent even without lights).
 * Host may THEN upload actual shared sun/point/AO/fog uniforms and resources.
 * It does not touch FBO, viewport, depth, blend or cull state. */
GLuint oa_weighted_hardlight_begin(oa_weighted_hardlight *,const float world_eye[3]);
/* world_vp transforms WORLD positions. Production bone rows already include
 * facing/feet. B uses facing only. Returns1submitted,0unsupported/hidden/invalid
 * caller state,-1GLerror. Caller skips old part only after success.
 * Binds program,VAO,textures0/1/2/8; leaves caller raster/depth/blend/FBO unchanged.
 * Native source is opaque back-cull/CW; host controls current GL view conventions.
 * Call begin with actual world eye before draw; open alone does not admit a frame.
 * c and its immutable parsed heap must outlive this adapter. */
int oa_weighted_hardlight_draw_part(oa_weighted_hardlight *,const oa_character *,
 unsigned part,const float world_vp[16]);
/* For auditing/integration only; immutable native-basis adapter vertex string. */
const char *oa_weighted_hardlight_vertex_source(void);
#endif
