#ifndef OA_MQ01_CURSOR_H
#define OA_MQ01_CURSOR_H
/* Authored portable cursor for the proven MQ01 stage subset.
 * NOT a native QuestMgr, persistence format, or automatic startup service.
 * Owner-thread only. Requests are ephemeral, never serialize them. */
#include <stddef.h>
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
#define OA_MQ01_QUEST_ID UINT32_C(613083)
#define OA_MQ01_SCRIPT_ID UINT32_C(613082)
#define OA_MQ01_CURSOR_VERSION 1u
typedef struct oa_mq01_cursor oa_mq01_cursor;
typedef enum {
 OA_MQ01_OK=0, OA_MQ01_NO_CHANGE=1, OA_MQ01_UNSUPPORTED=2,
 OA_MQ01_STALE=3, OA_MQ01_BUSY=4, OA_MQ01_HOST_REJECTED=5,
 OA_MQ01_BAD_ARGUMENT=6, OA_MQ01_NO_MEMORY=7, OA_MQ01_EXHAUSTED=8,
 OA_MQ01_CALLBACK_REQUIRED=9
} oa_mq01_status;
typedef enum {
 OA_MQ01_NOOP_NONE=0, OA_MQ01_NOOP_UNSTARTED=1,
 OA_MQ01_NOOP_UNDEFINED_STAGE=2, OA_MQ01_NOOP_SAME_STAGE=3,
 OA_MQ01_NOOP_ALREADY_STARTED=4
} oa_mq01_noop;
typedef enum { OA_MQ01_START=1, OA_MQ01_SET_STAGE=2 } oa_mq01_operation;
typedef struct {
 uint32_t quest_id;
 uint64_t generation,revision;
 int32_t stage_index,stage_id; /* Both -1 while explicitly unstarted. */
} oa_mq01_snapshot;
typedef struct {
 uint32_t version,quest_id,operation;
 uint64_t generation,previous_revision,request_id;
 int32_t previous_index,previous_stage,target_index,target_stage;
 uintptr_t issuer_cookie; /* Internal cursor identity; not a Lua object or stable/save ID. */
} oa_mq01_request;
/* Return 0 ONLY after validating/applying the complete required host transition
 * effects atomically; on nonzero apply NOTHING. No reentry on this cursor.
 * START must acknowledge an actual start, not a default success. SET_STAGE must
 * acknowledge required stage callbacks/events/conditions; this module supplies none. */
typedef int (*oa_mq01_apply_fn)(void *context,const oa_mq01_request *request,
                               char *error,size_t error_capacity);
/* generation is a caller-owned nonzero NEW lifetime ID. Change it when resetting,
 * restoring/recreating or beginning another game; never reuse it with old requests.
 * *out must be NULL. Unknown quest ID returns UNSUPPORTED, not a stage -1. */
oa_mq01_status oa_mq01_create(uint32_t quest_id,uint64_t generation,oa_mq01_cursor **out);
oa_mq01_status oa_mq01_destroy(oa_mq01_cursor **cursor);
oa_mq01_status oa_mq01_query(const oa_mq01_cursor *cursor,uint32_t quest_id,
                            uint64_t caller_generation,oa_mq01_snapshot *out);
/* expected must be the complete current snapshot. One pending request at a time.
 * Prepare changes no quest stage/revision. NO_CHANGE issues no request/callback.
 * An old expected snapshot cannot authorize a new transition. */
oa_mq01_status oa_mq01_prepare_start(oa_mq01_cursor *cursor,const oa_mq01_snapshot *expected,
                                    oa_mq01_request *out,oa_mq01_noop *reason);
oa_mq01_status oa_mq01_prepare_set(oa_mq01_cursor *cursor,const oa_mq01_snapshot *expected,
                                  int32_t target_stage,oa_mq01_request *out,oa_mq01_noop *reason);
/* Validates issuer, generation, previous state, revision and exact pending fields
 * BEFORE calling apply. Successful acknowledgement commits target and revision+1.
 * Rejection consumes the request and preserves stage/revision: retry must PREPARE
 * a fresh token. Stale/forged acknowledgements never invoke apply or cancel a valid token.
 * Missing callback fails and leaves the request pending for explicit cancel/review. */
oa_mq01_status oa_mq01_commit(oa_mq01_cursor *cursor,uint64_t caller_generation,
                             const oa_mq01_request *request,oa_mq01_apply_fn apply,
                             void *context,char *error,size_t error_capacity);
oa_mq01_status oa_mq01_cancel(oa_mq01_cursor *cursor,uint64_t caller_generation,
                             const oa_mq01_request *request);
const int32_t *oa_mq01_stage_ids(size_t *count); /* Synthetic0 +12authored IDs. */
const char *oa_mq01_status_name(oa_mq01_status status);
#ifdef __cplusplus
}
#endif
#endif
