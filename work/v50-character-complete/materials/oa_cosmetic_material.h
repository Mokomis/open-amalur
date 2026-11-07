#ifndef OA_COSMETIC_MATERIAL_H
#define OA_COSMETIC_MATERIAL_H
#include <stddef.h>
#include <stdint.h>
#include <GLES3/gl3.h>
#include "oa_creation.h"
enum { OA_CM_HARDLIGHT=0,OA_CM_SKIN=1,OA_CM_HEAD=2,OA_CM_HAIR=3,
 OA_CM_EYE=4,OA_CM_DOT3=5,OA_CM_REFLECT=6,OA_CM_FOG_ADDITIVE=7,OA_CM_MAX_PALETTE=78,
 OA_CM_HAS_UV0=1,OA_CM_HAS_N=2,OA_CM_HAS_T=4,OA_CM_HAS_B=8,
 OA_CM_WEIGHTED=16,OA_CM_HAS_COLOR=32,OA_CM_HAS_UV1=64,OA_CM_NATIVE_DEFAULT_COLOR=128 };
/* Agreed fixed96B decoded source view. Bone indices are unsigned source bytes;
 * native SNORM16 source W3 -> float, fourth weight is reconstructed UNCLAMPED.
 * Missing source56 color requires explicit native_shared_all_ff provenance flag.
 * The last two words are source vertex ordinal/reserved, not shader attributes. */
typedef struct oa_cm_vertex {
 float p[3];uint8_t joints[4];float weight[3],uv0[2],uv1[2];
 float n[3],t[3],b[3];uint8_t rgba[4];uint32_t flags,source_vertex,reserved;
} oa_cm_vertex;
typedef struct oa_cm_material {
 uint32_t material,shader,kind,alpha_test,cull,cutoff_byte,normal_policy;
 float constant[4],specular[4],extra[4],fresnel[4];
 uint32_t source_slots[32];
} oa_cm_material;
/* Exact native instance array order. Hair/beard pairs selected per surface;
 * native setter preserves existing alphas except explicit overlay alpha changes.
 * skin alpha is explicit (concrete source player blueprint initializes255). */
typedef struct oa_cm_instance {
 float color[8][4];uint32_t head_diffuse,body_diffuse,tattoo_texture;
 float beard[2][4];
 float probe_instance_tint[4],dynamic_tint[4],luminance_factors[4],luminance_tint[4];
} oa_cm_instance;
typedef GLuint (*oa_cm_texture_lookup)(void *user,uint32_t native_asset,GLenum target);
typedef struct oa_cm_context {
 GLuint program,character_cube,world_cube,environment_probe,dummy_ao,dummy_shadow,dummy_grid;
 oa_cm_texture_lookup texture;void *texture_user;int frame_ready;
} oa_cm_context;
typedef struct oa_cm_surface {
 GLuint vao,vbo,ibo;uint32_t vertices,indices,palette_count,weighted,flags;
} oa_cm_surface;
/* Catalog generated from original materials; returns0 for unreviewed shader. */
int oa_cm_material_find(uint32_t native_mid,oa_cm_material *out);
/* Pure state conversion: no GL, no mutation of creation/profile/user files.
 * skin_alpha_byte is caller supplied or concrete blueprint's255. */
int oa_cm_instance_from_selection(const oa_creation_render_selection *,
 uint8_t skin_alpha_byte,oa_cm_instance *);
void oa_cm_packed_color(uint32_t argb,float rgba[4]);
/* Context borrows two valid cube textures and resource lookup texture objects.
 * texture lookup may cache/load native-ID OATX; no object is substituted on failure.
 * open zeroed object, close before reopening. Zero return keeps previous renderer. */
int oa_cm_open(oa_cm_context *,GLuint character_cube,GLuint world_cube,
 oa_cm_texture_lookup,void *,unsigned lights);
void oa_cm_close(oa_cm_context *);
/* Dynamic EnvironmentProbeMap is an explicit borrowed scene-selected cube; source
 * slot21 does not select it. Reflect draws fallback until this is supplied. */
void oa_cm_environment_probe(oa_cm_context *,GLuint);
GLuint oa_cm_program(const oa_cm_context *);
/* Caller owns framebuffer, viewport, depth, culling, blending and camera.
 * begin sets safe ambient-only state, with actual WORLD eye; host may THEN set
 * shared sun/point/AO/shadow/fog uniforms. draw does not overwrite those globals. */
GLuint oa_cm_begin(oa_cm_context *,const float world_eye[3]);
int oa_cm_surface_open(oa_cm_surface *,const oa_cm_vertex *,uint32_t vertices,
 const uint32_t *,uint32_t indices,uint32_t palette_count,int weighted);
void oa_cm_surface_close(oa_cm_surface *);
/* Bone rows already WORLD-space with per-component source bind/remaps applied;
 * entity_rows are3 vec4 direction rows, used for native unskinned B only.
 * rigid surfaces consume bone rows[0..2] for P/N/T and same entity-only B rule.
 * Caller supplies beard_pair=1 ONLY for source Beard shader/material identity.
 * returns1 draw submitted,0 invalid/unsupported/resource missing,-1 GL error. */
/* Loads/validates exactly the same fallible resources as draw, without draw/FBO/
 * viewport changes. Does not require begin; use before atomic publication.
 * Callback texture allocation/bindings may change, so invalidate external cache. */
int oa_cm_resources_ready(oa_cm_context *,const oa_cm_material *,const oa_cm_instance *);
int oa_cm_draw(oa_cm_context *,const oa_cm_surface *,const oa_cm_material *,
 const oa_cm_instance *,int beard_pair,const float world_vp[16],
 const float *world_palette_rows,const float entity_rows[12]);
const char *oa_cm_vertex_source(void);
/* Returned assembled fragment is malloc-owned; optional custom VS for GPU tests. */
char *oa_cm_fragment_source(unsigned lights);
#endif
