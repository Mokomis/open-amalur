#ifndef OA_OPENING_RUNTIME_H
#define OA_OPENING_RUNTIME_H
#include <stddef.h>
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
#define OA_OPENING_MAX_TIMERS 128u
#define OA_OPENING_MAX_EFFECTS 512u
typedef struct oa_opening_runtime oa_opening_runtime;
typedef struct oa_opening_assets {
 void *context;
 int (*size)(void *,const char *,size_t *,char *,size_t);
 int (*read)(void *,const char *,void *,size_t,char *,size_t);
} oa_opening_assets;
enum oa_opening_query {OA_OPENING_IS_EQUIPPED=1,OA_OPENING_GATEWAY_OPEN,OA_OPENING_TUTORIALS_ENABLED,OA_OPENING_TUTORIAL_FIRED,OA_OPENING_TUTORIAL_ACTIVE};
enum oa_opening_effect_kind {OA_OPENING_OPEN_GATEWAY=1,OA_OPENING_SET_STAGE,OA_OPENING_KILL_TUTORIAL,OA_OPENING_MODAL_TUTORIAL,OA_OPENING_SECONDARY_DISABLED,OA_OPENING_COMPARE_ENABLED,OA_OPENING_AUTOSAVE_REQUEST};
typedef struct oa_opening_timer {uint32_t hash;uint64_t due_ms,serial;uint32_t argc;int32_t item_index;} oa_opening_timer;
/* Typed authored-port envelope, NOT a disk/native save format. Host must couple
 * with matching inventory indices, quest/door state and scene generation. */
typedef struct oa_opening_snapshot {
 uint32_t version,wos_flags,sword_flags,cinematic_flags;
 int32_t sword_get;
 uint64_t clock_ms,serial;
 uint32_t timer_count;
 oa_opening_timer timers[OA_OPENING_MAX_TIMERS];
} oa_opening_snapshot;
typedef struct oa_opening_effect {
 enum oa_opening_effect_kind kind;
 uint32_t argc;
 int32_t args[2];
 const char *source_callback; /* Static borrowed name; contains no Lua pointer. */
} oa_opening_effect;
typedef struct oa_opening_host {
 void *context;
 const char *player_identity; /* Copied: stable scene/slot/generation string. */
 int (*query_bool)(void *,enum oa_opening_query,int32_t,int *,char *,size_t);
 /* Return nonzero for unknown; INT32_MIN is reserved for an omitted/unknown result. */
 int (*quest_stage)(void *,uint32_t,int32_t *,char *,size_t);
 /* Validate/prepare ALL effects before committing; return0 only when the whole
  * batch was applied. On failure apply NOTHING. Candidate is copied C data,
  * allowing checkpoints without runtime reentry. Callbacks must bound host work. */
 int (*apply_effects)(void *,const oa_opening_effect *,size_t,const oa_opening_snapshot *,char *,size_t);
 void (*warning)(void *,const char *);
} oa_opening_host;
typedef struct oa_opening_runtime_config {size_t lua_memory_bytes;uint64_t instruction_budget;} oa_opening_runtime_config;
typedef struct oa_opening_runtime_stats {size_t lua_bytes,lua_limit;uint64_t instruction_budget,calls,rejections,rebuilds;int poisoned;} oa_opening_runtime_stats;
/* Asset callbacks return0 on success and must fill exactly the measured size.
 * Owner-thread only; host callbacks cannot reenter. Sources are hash-pinned. */
oa_opening_runtime *oa_opening_runtime_create_from_assets(const oa_opening_assets *,const oa_opening_host *,const oa_opening_runtime_config *,char *,size_t);
void oa_opening_runtime_close(oa_opening_runtime *);
int oa_opening_runtime_cinematic_finished(oa_opening_runtime *,int,char *,size_t);
int oa_opening_runtime_volume_exit(oa_opening_runtime *,const char *,const char *,char *,size_t);
int oa_opening_runtime_sword_acquired(oa_opening_runtime *,int32_t,const char *,int32_t,char *,size_t);
int oa_opening_runtime_sword_equipped(oa_opening_runtime *,int32_t,char *,size_t);
int oa_opening_runtime_advance(oa_opening_runtime *,uint32_t,char *,size_t);
int oa_opening_runtime_snapshot(oa_opening_runtime *,oa_opening_snapshot *,char *,size_t);
int oa_opening_runtime_restore(oa_opening_runtime *,const oa_opening_snapshot *,char *,size_t);
void oa_opening_runtime_get_stats(const oa_opening_runtime *,oa_opening_runtime_stats *);
#ifdef __cplusplus
}
#endif
#endif
