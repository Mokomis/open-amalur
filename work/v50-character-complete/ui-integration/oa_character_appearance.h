#ifndef OA_CHARACTER_APPEARANCE_H
#define OA_CHARACTER_APPEARANCE_H
#include "oa_creation.h"
#include "oa_appearance_selection.h"
#include <android/asset_manager.h>
#include <GLES3/gl3.h>
typedef struct oa_ca_renderer oa_ca_renderer;
typedef struct oa_ca_actor oa_ca_actor;
/* Immutable source bank and shared materials. Actor publication stays separate. */
oa_ca_renderer *oa_ca_renderer_create(AAssetManager *);
int oa_ca_renderer_gpu_open(oa_ca_renderer *);
void oa_ca_renderer_gpu_close(oa_ca_renderer *);
void oa_ca_renderer_close(oa_ca_renderer *);
/* Borrowed actual room cubes/probe, never deleted. Creator always restores its own environment. */
void oa_ca_renderer_world_environment(oa_ca_renderer *,GLuint character_cube,GLuint world_cube,GLuint environment_probe);
/* Source-hash-pinned cube borrowed from the renderer's bank; GPU context only. */
GLuint oa_ca_renderer_source_probe(oa_ca_renderer *,uint32_t native_texture_id);
/* Preparation owns new surfaces and leaves any current actor untouched. */
oa_ca_actor *oa_ca_actor_prepare(oa_ca_renderer *,const oa_creation_state *,
 unsigned form,const uint32_t *equipped_types,unsigned equipped_count,char *,size_t);
void oa_ca_actor_close(oa_ca_actor *);
int oa_ca_actor_update_colors(oa_ca_actor *,const oa_creation_state *,char *,size_t);
/* Source root-local frame supplied explicitly for gameplay. NULL uses creator
   source-linked idle. Time is renderer policy; source QTS bytes remain unchanged. */
int oa_ca_actor_pose(oa_ca_actor *,const float *root_qts48,unsigned root_bones,float time);
/* Normalized actual horizontal motion; blocked input must supply zero. */
int oa_ca_actor_locomotion(oa_ca_actor *,float speed,float dt);
GLuint oa_ca_actor_begin(oa_ca_actor *,const float eye[3]);
/* begin precedes host lighting uniforms. Entity affine rows transform every
   component palette; native unskinned B uses these entity rows exactly once. */
int oa_ca_actor_draw(oa_ca_actor *,const float vp[16],const float entity[12],int depth_only);
const oa_ap_plan *oa_ca_actor_plan(const oa_ca_actor *);
#endif
