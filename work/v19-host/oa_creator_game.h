#ifndef OA_CREATOR_GAME_H
#define OA_CREATOR_GAME_H
/* Owner-thread, non-reentrant staged first-room host, not integrated gameplay.
 * Required actor/UI callbacks are unavailable by default. No QuestMgr/startup. */
#include "oa_opening_runtime.h"
#include <stdint.h>
#include <stddef.h>
#ifdef __cplusplus
extern "C" {
#endif
#define OA_CREATOR_GAME_SCENE 1417252u
#define OA_CREATOR_GAME_REGION 1262814u
#define OA_CREATOR_GAME_CONTAINER_GOR 1790948u
#define OA_CREATOR_GAME_CONTAINER_INSTANCE 1789992u
#define OA_CREATOR_GAME_SWORD_TYPE 1360571u
#define OA_CREATOR_GAME_TUTORIAL_COUNT 5u
#define OA_CREATOR_GAME_STEP_MAX_MS 1000u /* Port budget policy, not native timing. */
enum { OA_CREATOR_GAME_OK=0, OA_CREATOR_GAME_ERROR=1, OA_CREATOR_GAME_NO_CHANGE=2,
       OA_CREATOR_GAME_UNAVAILABLE=3, OA_CREATOR_GAME_LATCHED=4 };
enum { OA_CREATOR_GAME_CAP_ITEM=1,OA_CREATOR_GAME_CAP_EQUIP=2,
       OA_CREATOR_GAME_CAP_DOOR=4,OA_CREATOR_GAME_CAP_UI=8 };
enum oa_creator_game_action { OA_CREATOR_GAME_MOVE=1,OA_CREATOR_GAME_SKIP,OA_CREATOR_GAME_TAKE,
 OA_CREATOR_GAME_EQUIP,OA_CREATOR_GAME_ADVANCE,OA_CREATOR_GAME_LOAD,OA_CREATOR_GAME_MIGRATE };
typedef struct oa_creator_game_pose { float feet[3],yaw,pitch; } oa_creator_game_pose;
typedef struct oa_creator_game_tutorial { uint32_t id,active,fired,kills; } oa_creator_game_tutorial;
typedef struct oa_creator_game_state {
 oa_creator_game_pose pose;
 oa_opening_snapshot lua;
 oa_creator_game_tutorial tutorials[OA_CREATOR_GAME_TUTORIAL_COUNT];
 uint32_t inside,initialized,skipped;
 uint32_t container_count,owned,equipped,door_open,secondary_disabled,compare_enabled;
 uint64_t revision,quest_noops;
} oa_creator_game_state;
typedef struct oa_creator_game_host oa_creator_game_host;
typedef struct oa_creator_game_batch {
 enum oa_creator_game_action action;
 uint32_t required_capabilities;
 uint32_t scene,container_gor,container_instance,item_type;
 uint64_t generation,item_instance,previous_revision;
 int32_t item_index;
 const oa_creator_game_state *before,*after; /* Borrowed, never mutate/retain. */
 const oa_opening_effect *effects;
 size_t effect_count;
} oa_creator_game_batch;
/* prepare must validate/reserve EVERYTHING and apply NOTHING. On failure release
 * its reservations itself. On success token may be NULL; abort/commit are void,
 * bounded and infallible. commit is called only after any atomic file rename.
 * No reentry, Lua calls, storage writes or fallible work in commit. The caller
 * must provide actual actor/UI services, not a generic successful mock. */
typedef struct oa_creator_game_backend {
 void *context;
 uint32_t capabilities;
 int (*available)(void*,uint32_t required,char*,size_t);
 int (*prepare)(void*,const oa_creator_game_batch*,void **token,char*,size_t);
 void (*commit)(void*,void *token);
 void (*abort)(void*,void *token);
} oa_creator_game_backend;
typedef struct oa_creator_game_config {
 uint64_t generation,item_instance; /* Stable nonzero source item instance mapping. */
 int32_t item_index;
 int tutorials_enabled; /* Explicit 0/1, -1 means unavailable. */
 const char *checkpoint_path; /* Must end .opening-gameplay-v1.bin */
 void *report_context;
 void (*report_failure)(void*,const char*);
 void *pose_validation_context;
 int (*validate_load_pose)(void*,const oa_creator_game_pose*,char*,size_t);
 oa_creator_game_backend backend;
 oa_opening_runtime_config runtime;
 /* Private outer owner: only -1 (not completed) or5 (verified completion/load). */
 int32_t owner_quest_stage;
 void *durable_context;
 int (*durable_write)(void*,const oa_creator_game_state*,char*,size_t);
} oa_creator_game_config;
typedef struct oa_creator_game_stats {
 uint64_t writes,attempts,failures,reports,warnings;
 uint32_t latched,poisoned;
 oa_opening_runtime_stats runtime;
} oa_creator_game_stats;
oa_creator_game_host *oa_creator_game_create(const oa_opening_assets*,const oa_creator_game_config*,char*,size_t);
void oa_creator_game_close(oa_creator_game_host*);
/* Actual post-creator cinematic completion and explicit skip share the original
 * completion guard; neither starts a quest or completes character creation. */
int oa_creator_game_cinematic_completed(oa_creator_game_host*,char*,size_t);
int oa_creator_game_cinematic_skipped(oa_creator_game_host*,char*,size_t);
int oa_creator_game_update_pose(oa_creator_game_host*,const oa_creator_game_pose*,char*,size_t);
/* Only exact source container, item instance/generation accepted. Caller owns
 * interaction reach/visibility authorization; this is not a proximity system. */
int oa_creator_game_take_source_item(oa_creator_game_host*,uint32_t gor,uint32_t container,
                               uint64_t item_instance,uint64_t generation,char*,size_t);
int oa_creator_game_equip_source_item(oa_creator_game_host*,uint64_t item_instance,
                                uint64_t generation,char*,size_t);
int oa_creator_game_advance(oa_creator_game_host*,uint32_t game_ms,char*,size_t);
int oa_creator_game_snapshot(oa_creator_game_host*,oa_creator_game_state*,char*,size_t);
int oa_creator_game_quest_stage(oa_creator_game_host*,uint32_t quest_id,int32_t*,char*,size_t);
int oa_creator_game_save_checkpoint(oa_creator_game_host*,char*,size_t);
int oa_creator_game_load_checkpoint(oa_creator_game_host*,char*,size_t);
/* Supplied movement snapshot must have no sword/timers. registry must be exactly
 * its three source rows. A successful migration transfers ownership: caller MUST
 * retire the old movement runtime, never drive two independent Lua worlds.
 * source scene/generation must match this host. Collision validation runs first. */
int oa_creator_game_migrate_movement(oa_creator_game_host*,uint32_t scene,uint64_t generation,
 const oa_creator_game_pose*,const oa_opening_snapshot*,const oa_creator_game_tutorial *registry,
 size_t registry_count,char*,size_t);
/* Explicit acknowledgement of a reported failure, does not replay any action.
 * Accepted containment remains intact; a later explicit movement update may retry. */
int oa_creator_game_clear_failure(oa_creator_game_host*,char*,size_t);
int oa_creator_game_tutorial_set(oa_creator_game_host*,uint32_t id,int active,int fired,char*,size_t);
void oa_creator_game_get_stats(const oa_creator_game_host*,oa_creator_game_stats*);
int oa_creator_game_is_busy(const oa_creator_game_host*);
/* Private outer-envelope staging. No visible actor state is published here. */
int oa_creator_game_export(oa_creator_game_host*,const oa_creator_game_state*,void*,size_t,size_t*,char*,size_t);
int oa_creator_game_import(oa_creator_game_host*,const void*,size_t,char*,size_t);
#ifdef __cplusplus
}
#endif
#endif
