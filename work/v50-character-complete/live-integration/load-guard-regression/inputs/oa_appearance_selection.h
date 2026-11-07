#ifndef OA_APPEARANCE_SELECTION_H
#define OA_APPEARANCE_SELECTION_H
#include "oa_appearance.h"
/* CPU-owned immutable model bytes supplied by cache; no GL or file IO in this module.
   Renderer reserves/releases its GPU surfaces/materials by FAB+assembly, independently.
   A completed plan has explicit CREATOR/GAMEPLAY form; publication is caller's transaction. */
enum {OA_AP_HEAD,OA_AP_HAIR,OA_AP_BEARD,OA_AP_EARS,OA_AP_TATTOO,OA_AP_ACCESSORY,OA_AP_CATEGORIES};
typedef struct {
 uint32_t profile; /* 0..7 in source profile catalogue order */
 uint32_t form; /* OA_AP_CREATOR / OA_AP_GAMEPLAY */
 uint32_t option_ids[OA_AP_CATEGORIES]; /* original SimTypeIDs; 0=source initialization default */
 const uint32_t *equipped_type_ids;uint32_t equipped_count; /* actual inventory; never guessed */
} oa_ap_selection;
typedef struct {
 uint32_t simtype,category_hash,race_mask,sex_mask,model_variants[3],mount_hash,tattoo_texture;
} oa_ap_option;
typedef struct {
 const char *name;uint32_t race_bit,sex_bit,creator_type,gameplay_type,creator_fab,gameplay_fab;
 uint32_t default_options[OA_AP_CATEGORIES],creator_idle_clip;
 uint32_t creator_face_idle_clip,gameplay_idle_clip,gameplay_walk_clip,gameplay_run_clip;
} oa_ap_profile;
typedef int (*oa_ap_model_lookup)(void *user,uint32_t fab,oa_am_model *borrowed);
typedef struct {
 uint32_t fab,source_type,slot_key,map_index;int32_t parent;uint32_t native_flags;float source_scale;
} oa_ap_component;
typedef struct {
 oa_ap_component component[32];uint32_t count,root_fab,actor_type,tattoo_texture;
 uint32_t selected_options[OA_AP_CATEGORIES];uint32_t form;
} oa_ap_plan;
const oa_ap_profile *oa_ap_profile_get(uint32_t);
uint32_t oa_ap_profile_count(void);
const oa_ap_option *oa_ap_option_get(uint32_t simtype);
uint32_t oa_ap_option_count(uint32_t profile,uint32_t category);
const oa_ap_option *oa_ap_option_at(uint32_t profile,uint32_t category,uint32_t index);
/* Validate original source masks/IDs first. Builds authored component hierarchy using
   original child slot maps; source empty/None is valid, no index clamping. */
int oa_ap_plan_build(const oa_ap_selection*,oa_ap_model_lookup,void *user,oa_ap_plan*);
/* Exact source-frame index (no invented chooser timing). Root clip is linked to
   this form's own source rig. All component world arrays preserve every own bone.
   Caller allocates component_count*64*12 floats for this bounded bank. */
int oa_ap_plan_pose(const oa_ap_plan*,oa_ap_model_lookup,void *user,
 const float *root_local_qts48,uint32_t root_bones,
 float *component_world_rows12,size_t floats_capacity);
int oa_ap_component_surface_visible(const oa_ap_plan*,uint32_t component,const oa_am_surface*);
#endif
