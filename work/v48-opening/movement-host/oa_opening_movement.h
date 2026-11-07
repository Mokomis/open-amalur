#ifndef OA_OPENING_MOVEMENT_H
#define OA_OPENING_MOVEMENT_H
#include "oa_opening_runtime.h"
#include <stdint.h>
#include <stddef.h>
typedef struct oa_movement_host oa_movement_host;
typedef struct oa_movement_pose {float feet[3],yaw,pitch;} oa_movement_pose;
typedef struct oa_movement_tutorial {uint32_t id,active,fired,kills;} oa_movement_tutorial;
enum {OA_MOVEMENT_OK=0,OA_MOVEMENT_ERROR=1,OA_MOVEMENT_LATCHED=2,OA_MOVEMENT_UNAVAILABLE=3};
enum {OA_MOVEMENT_SERVICE_VOLUMES=1u,OA_MOVEMENT_SERVICE_TUTORIAL_REGISTRY=2u,OA_MOVEMENT_SERVICE_CHECKPOINT=4u,OA_MOVEMENT_SERVICE_QUEST=8u,OA_MOVEMENT_SERVICE_SWORD=16u,OA_MOVEMENT_SERVICE_NATIVE_DOOR=32u};
typedef struct oa_movement_config {
 uint64_t generation; /* Explicit persistent scene/player registry generation. */
 const char *checkpoint_path; /* Dedicated *.opening-checkpoint-v1.bin only. */
 void *report_context;
 void (*report_failure)(void *,const char *); /* Once per latched episode. */
 oa_opening_runtime_config runtime;
 /* Optional CURRENT-collision validation of a fully decoded saved pose, before
  * ANY Lua/registry/pose mutation. Candidate is borrowed for this call only.
  * Stage a temporary controller; commit it only after load returns0. */
 void *pose_validation_context;
 int (*validate_load_pose)(void *,const oa_movement_pose *,char *,size_t);
} oa_movement_config;
typedef struct oa_movement_stats {
 uint32_t scene,region,inside_mask,containment_initialized,cinematic_skipped,latched;
 uint64_t generation,checkpoint_writes,event_failures,failure_reports;
 oa_opening_runtime_stats runtime;
} oa_movement_stats;
/* Thread-confined. Explicit source feet-point containment; no guessed radius,
 * capsule tolerance, swept trigger or automatic cinematic completion. */
oa_movement_host *oa_movement_host_create(const oa_opening_assets *,const oa_movement_config *,char *,size_t);
void oa_movement_host_close(oa_movement_host *);
int oa_movement_host_cinematic_skipped(oa_movement_host *,char *,size_t);
int oa_movement_host_update_pose(oa_movement_host *,const oa_movement_pose *,char *,size_t);
int oa_movement_host_retry_failed_exit(oa_movement_host *,char *,size_t);
int oa_movement_host_load_checkpoint(oa_movement_host *,char *,size_t);
/* Explicit movement-only checkpoint; no quest/inventory/legacy save claim. */
int oa_movement_host_save_checkpoint(oa_movement_host *,char *,size_t);
int oa_movement_host_tutorial_set(oa_movement_host *,uint32_t,int active,int fired,char *,size_t);
int oa_movement_host_tutorial_get(const oa_movement_host *,uint32_t,oa_movement_tutorial *);
int oa_movement_host_snapshot(oa_movement_host *,oa_movement_pose *,oa_opening_snapshot *,char *,size_t);
void oa_movement_host_get_stats(const oa_movement_host *,oa_movement_stats *);
unsigned oa_movement_host_services(const oa_movement_host *);
#endif
