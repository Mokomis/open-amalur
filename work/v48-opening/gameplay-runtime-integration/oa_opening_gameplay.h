#ifndef OA_OPENING_GAMEPLAY_H
#define OA_OPENING_GAMEPLAY_H
/* Owner-thread, non-reentrant staged first-room host, not integrated gameplay.
 * Required actor/UI callbacks are unavailable by default. No QuestMgr/startup. */
#include "oa_opening_runtime.h"
#include <stdint.h>
#include <stddef.h>
#ifdef __cplusplus
extern "C" {
#endif
#define OA_GAMEPLAY_SCENE 1417252u
#define OA_GAMEPLAY_REGION 1262814u
#define OA_GAMEPLAY_CONTAINER_GOR 1790948u
#define OA_GAMEPLAY_CONTAINER_INSTANCE 1789992u
#define OA_GAMEPLAY_SWORD_TYPE 1360571u
#define OA_GAMEPLAY_TUTORIAL_COUNT 5u
#define OA_GAMEPLAY_STEP_MAX_MS 1000u /* Port budget policy, not native timing. */
enum { OA_GAMEPLAY_OK=0, OA_GAMEPLAY_ERROR=1, OA_GAMEPLAY_NO_CHANGE=2,
       OA_GAMEPLAY_UNAVAILABLE=3, OA_GAMEPLAY_LATCHED=4 };
enum { OA_GAMEPLAY_CAP_ITEM=1,OA_GAMEPLAY_CAP_EQUIP=2,
       OA_GAMEPLAY_CAP_DOOR=4,OA_GAMEPLAY_CAP_UI=8 };
enum oa_gameplay_action { OA_GAMEPLAY_MOVE=1,OA_GAMEPLAY_SKIP,OA_GAMEPLAY_TAKE,
 OA_GAMEPLAY_EQUIP,OA_GAMEPLAY_ADVANCE,OA_GAMEPLAY_LOAD,OA_GAMEPLAY_MIGRATE };
typedef struct oa_gameplay_pose { float feet[3],yaw,pitch; } oa_gameplay_pose;
typedef struct oa_gameplay_tutorial { uint32_t id,active,fired,kills; } oa_gameplay_tutorial;
typedef struct oa_gameplay_state {
 oa_gameplay_pose pose;
 oa_opening_snapshot lua;
 oa_gameplay_tutorial tutorials[OA_GAMEPLAY_TUTORIAL_COUNT];
 uint32_t inside,initialized,skipped;
 uint32_t container_count,owned,equipped,door_open,secondary_disabled,compare_enabled;
 uint64_t revision,quest_noops;
} oa_gameplay_state;
typedef struct oa_gameplay_host oa_gameplay_host;
typedef struct oa_gameplay_batch {
 enum oa_gameplay_action action;
 uint32_t required_capabilities;
 uint32_t scene,container_gor,container_instance,item_type;
 uint64_t generation,item_instance,previous_revision;
 int32_t item_index;
 const oa_gameplay_state *before,*after; /* Borrowed, never mutate/retain. */
 const oa_opening_effect *effects;
 size_t effect_count;
} oa_gameplay_batch;
/* prepare must validate/reserve EVERYTHING and apply NOTHING. On failure release
 * its reservations itself. On success token may be NULL; abort/commit are void,
 * bounded and infallible. commit is called only after any atomic file rename.
 * No reentry, Lua calls, storage writes or fallible work in commit. The caller
 * must provide actual actor/UI services, not a generic successful mock. */
typedef struct oa_gameplay_backend {
 void *context;
 uint32_t capabilities;
 int (*available)(void*,uint32_t required,char*,size_t);
 int (*prepare)(void*,const oa_gameplay_batch*,void **token,char*,size_t);
 void (*commit)(void*,void *token);
 void (*abort)(void*,void *token);
} oa_gameplay_backend;
typedef struct oa_gameplay_config {
 uint64_t generation,item_instance; /* Stable nonzero source item instance mapping. */
 int32_t item_index;
 int tutorials_enabled; /* Explicit 0/1, -1 means unavailable. */
 const char *checkpoint_path; /* Must end .opening-gameplay-v1.bin */
 void *report_context;
 void (*report_failure)(void*,const char*);
 void *pose_validation_context;
 int (*validate_load_pose)(void*,const oa_gameplay_pose*,char*,size_t);
 oa_gameplay_backend backend;
 oa_opening_runtime_config runtime;
} oa_gameplay_config;
typedef struct oa_gameplay_stats {
 uint64_t writes,attempts,failures,reports,warnings;
 uint32_t latched,poisoned;
 oa_opening_runtime_stats runtime;
} oa_gameplay_stats;
oa_gameplay_host *oa_gameplay_create(const oa_opening_assets*,const oa_gameplay_config*,char*,size_t);
void oa_gameplay_close(oa_gameplay_host*);
int oa_gameplay_cinematic_skipped(oa_gameplay_host*,char*,size_t);
int oa_gameplay_update_pose(oa_gameplay_host*,const oa_gameplay_pose*,char*,size_t);
/* Only exact source container, item instance/generation accepted. Caller owns
 * interaction reach/visibility authorization; this is not a proximity system. */
int oa_gameplay_take_source_item(oa_gameplay_host*,uint32_t gor,uint32_t container,
                               uint64_t item_instance,uint64_t generation,char*,size_t);
int oa_gameplay_equip_source_item(oa_gameplay_host*,uint64_t item_instance,
                                uint64_t generation,char*,size_t);
int oa_gameplay_advance(oa_gameplay_host*,uint32_t game_ms,char*,size_t);
int oa_gameplay_snapshot(oa_gameplay_host*,oa_gameplay_state*,char*,size_t);
int oa_gameplay_quest_stage(oa_gameplay_host*,uint32_t quest_id,int32_t*,char*,size_t);
int oa_gameplay_save_checkpoint(oa_gameplay_host*,char*,size_t);
int oa_gameplay_load_checkpoint(oa_gameplay_host*,char*,size_t);
/* Supplied movement snapshot must have no sword/timers. registry must be exactly
 * its three source rows. A successful migration transfers ownership: caller MUST
 * retire the old movement runtime, never drive two independent Lua worlds.
 * source scene/generation must match this host. Collision validation runs first. */
int oa_gameplay_migrate_movement(oa_gameplay_host*,uint32_t scene,uint64_t generation,
 const oa_gameplay_pose*,const oa_opening_snapshot*,const oa_gameplay_tutorial *registry,
 size_t registry_count,char*,size_t);
/* Explicit acknowledgement of a reported failure, does not replay any action.
 * Accepted containment remains intact; a later explicit movement update may retry. */
int oa_gameplay_clear_failure(oa_gameplay_host*,char*,size_t);
int oa_gameplay_tutorial_set(oa_gameplay_host*,uint32_t id,int active,int fired,char*,size_t);
void oa_gameplay_get_stats(const oa_gameplay_host*,oa_gameplay_stats*);
#ifdef __cplusplus
}
#endif
#endif
