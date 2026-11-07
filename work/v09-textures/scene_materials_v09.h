#ifndef OPEM_SCENE_MATERIALS_V09_H
#define OPEM_SCENE_MATERIALS_V09_H
#include <stddef.h>
#include <stdint.h>
#define SCENE_MATERIALS_V09_MAX_BYTES (384u*1024u*1024u)
#define SCENE_MATERIALS_V09_MAX_TEXTURES 256u
#define SCENE_MATERIALS_V09_MAX_DRAWS 4096u
#define SCENE_MATERIALS_V09_MAX_VERTICES 8000000u
#define SCENE_MATERIALS_V09_MAX_DIMENSION 4096u
#define SCENE_MATERIALS_V09_FALLBACK UINT32_MAX
typedef struct scene_material_draw_v09 {uint32_t first_vertex,vertex_count,texture_index;} scene_material_draw_v09;
typedef struct scene_material_texture_v09 {uint32_t width,height,rgba_bytes;unsigned char *rgba;} scene_material_texture_v09;
typedef struct scene_materials_v09 {
    uint32_t vertex_count,draw_count,texture_count;
    unsigned char scene_sha256[32];
    float *uv;
    scene_material_draw_v09 *draws;
    scene_material_texture_v09 *textures;
    size_t owned_bytes;
} scene_materials_v09;
/* Authored OMAT09 sidecar, not a native format. Exact compiled scene SHA and
 * expanded scene vertex count are mandatory. Output must be zero initialized.
 * Copies all payloads; caller can free input immediately. No GPU allocation.
 * Full contiguous triangle draw coverage, finite native UVs and RGBA8 only.
 * A fallback draw is explicit and carries no recovered material claim. */
int scene_materials_v09_load(const void *,size_t,uint32_t,const unsigned char[32],scene_materials_v09 *,char *,size_t);
void scene_materials_v09_free(scene_materials_v09 *);
#endif
