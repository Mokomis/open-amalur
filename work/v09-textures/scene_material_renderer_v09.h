#ifndef OPEM_SCENE_MATERIAL_RENDERER_V09_H
#define OPEM_SCENE_MATERIAL_RENDERER_V09_H
#include "scene_materials_v09.h"
#include <GLES3/gl3.h>
typedef struct scene_material_renderer_v09 {
    GLuint uv_buffer;
    GLuint textures[SCENE_MATERIALS_V09_MAX_TEXTURES];
    uint32_t texture_count,vertex_count,draw_count;
    size_t gpu_bytes;
    int ready;
} scene_material_renderer_v09;
/* Current GLES3 context and initialized world VAO required; position/normal/
 * fallback color remain locations0/1/2. Attaches UV location3 to world_vao.
 * Host policy: repeat sampling, linear mipmaps generated from recovered top
 * RGBA8 level, opaque diagnostic lighting. No native sampler/lighting parity.
 * Caller retains matching materials until close; open never stores pointers.
 * Output renderer must be zero initialized. Close before destroying context. */
int scene_material_renderer_v09_open(scene_material_renderer_v09 *,const scene_materials_v09 *,GLuint world_vao,char *,size_t);
/* Caller binds world program/VAO and matrix. Uniforms int has_texture and
 * sampler2D base_texture must be active. Draws complete package coverage,
 * including explicit fallback ranges. Leaves texture unit0 unbound. */
int scene_material_renderer_v09_draw(const scene_material_renderer_v09 *,const scene_materials_v09 *,GLint has_texture_uniform,GLint sampler_uniform);
void scene_material_renderer_v09_close(scene_material_renderer_v09 *);
#endif
