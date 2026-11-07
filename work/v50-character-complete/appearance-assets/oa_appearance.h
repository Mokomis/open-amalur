#ifndef OA_APPEARANCE_H
#define OA_APPEARANCE_H
#include <stddef.h>
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
/* Borrowed immutable OAAM001 bytes. Caller keeps memory alive. No global cache/IO/GL. */
typedef struct {const unsigned char *bytes;size_t size;uint32_t fab,chunks,dir;} oa_am_model;
typedef struct {const unsigned char *data;uint32_t count,stride;} oa_am_chunk;
typedef struct {
 const void *vertices96;const uint32_t *indices;uint32_t vertex_count,index_count;
 uint32_t material_id,assembly,group_mask,weighted,palette_count,source_vb,source_ib;
 int32_t rigid_bone;const unsigned char *remaps52;
} oa_am_surface;
enum {OA_AM_UV0=1,OA_AM_NORMAL=2,OA_AM_TANGENT=4,OA_AM_BITANGENT=8,
 OA_AM_WEIGHTED=16,OA_AM_COLOR=32,OA_AM_UV1=64};
enum {OA_AP_CREATOR=0,OA_AP_GAMEPLAY=1};
int oa_am_open(oa_am_model*,const void*,size_t);
int oa_am_find(const oa_am_model*,const char tag[4],oa_am_chunk*);
uint32_t oa_am_surface_count(const oa_am_model*);
int oa_am_surface_get(const oa_am_model*,uint32_t,oa_am_surface*);
/* Source Qxyzw/Txyzw/Sxyzw, standard column vectors. Conjugates raw Q once. */
void oa_am_source_tqs_matrix(const float q[4],const float t[3],const float s[3],float out[12]);
/* own-component rest hierarchy; no bone collapse/inverse bind on rigid. */
int oa_am_rest_world(const oa_am_model*,float *rows12,size_t float_capacity);
/* Exact per-surface source remap offset followed by own-component global bone.
   root_world_rows12 is optional entity transform; NULL=identity.
   bone_world_rows12 must contain this model's full own-rig world bones.
   Palette output count is remap_count (weighted) or 1 (rigid).
   Poses/rig mapping remain caller responsibility; never borrows an incompatible male rig. */
int oa_am_palette(const oa_am_model*,uint32_t assembly,const float *bone_world_rows12,
 uint32_t bone_count,const float *root_world_rows12,float *out_rows12,size_t float_capacity);
typedef struct {const unsigned char *pairs12;uint32_t count,mount_key,slot_key,flags;} oa_am_child_map;
uint32_t oa_am_child_map_count(const oa_am_model*);
int oa_am_child_map_get(const oa_am_model*,uint32_t,oa_am_child_map*);
/* 00ccd2c0 ordinary path: explicit authored mapping, then unmatched source locals.
   No previous-child-pose/additive override state is invented (nativeflag8 path). */
int oa_am_child_pose(const oa_am_model *parent,uint32_t map_index,
 const float *parent_world,uint32_t parent_bones,const oa_am_model *child,
 float *child_world,size_t float_capacity);
int oa_am_local_pose(const oa_am_model*,const float *source_local_qts48,
 uint32_t source_bones,float *world,size_t float_capacity);
#ifdef __cplusplus
}
#endif
#endif
