#ifndef OA_CREATION_SESSION_H
#define OA_CREATION_SESSION_H
#include "oa_creation_gameplay.h"
#include "oa_character_appearance.h"
#include "opem_collision.h"
struct oa_stream;
typedef struct oa_creation_session oa_creation_session;
/* Render/owner thread only. Resources are borrowed except session-owned actor.
 * The callback is infallible, bounded and non-reentrant: publish already-reserved
 * state only. No allocation, storage, Lua calls or fallible GPU work here.
 * active/actor/body/pose are borrowed; copy values, never retain active/body/pose.
 * actor stays owned by session. Optional new_world ownership transfers to caller;
 * replace/destroy the old world only here. NULL means preserve current world/body.
 * loading=0 is explicit creator finish; loading=1 is restore, not startup replay.
 * Retire the old movement Lua realm only here after successful finalization.
 */
typedef void (*oa_creation_session_publish)(void *context,int loading,
 const oa_creation_active *active,oa_ca_actor *actor,
 opem_collision_world *new_world,const opem_controller *body,
 const oa_creator_game_pose *pose);
typedef struct oa_creation_session_config {
 const char *save_directory; /* Existing app-private directory; no writes on open. */
 uint32_t space,region; /* Actual1417252/1262814 first-room identity. */
 uint64_t generation,item_instance;int32_t item_index; /* Explicit source mapping. */
 int tutorials_enabled; /* Actual setting0/1. */
 oa_creator_game_backend gameplay_backend; /* Actual services, UI cap8 initially. */
 void *publish_context;oa_creation_session_publish publish;
 void *report_context;void (*report_failure)(void*,const char*);
 oa_opening_runtime_config runtime;
} oa_creation_session_config;
/* Borrows assets/renderer/config callback contexts for the entire session.
 * Reads opening-runtime/<hash-pinned source name>, including the creation/ assets.
 * Requires source first-room identity from root, generation/item mapping explicit.
 * Uses source baseHealth50 and native package4 constructor default1 explicitly.
 */
oa_creation_session *oa_creation_session_open(AAssetManager *,oa_ca_renderer *,
 const oa_creation_session_config *,char *,size_t);
void oa_creation_session_close(oa_creation_session *);
int oa_creation_session_complete(oa_creation_session *,const oa_creation_state *,
 uint64_t transaction,const oa_creator_game_pose *,char *,size_t);
int oa_creation_session_load(oa_creation_session *,struct oa_stream *,
 const opem_controller_config *,char *,size_t);
int oa_creation_session_save(oa_creation_session *,char *,size_t);
/* Distinct atomic source events; source failures latch once, no automatic retry.
 * A pose update never fabricates a cinematic completion or skip.
 */
int oa_creation_session_update_pose(oa_creation_session *,const oa_creator_game_pose *,char *,size_t);
int oa_creation_session_advance(oa_creation_session *,uint32_t game_ms,char *,size_t);
int oa_creation_session_cinematic(oa_creation_session *,int explicitly_skipped,char *,size_t);
/* Refresh cached owner/gameplay after root uses the borrowed stat/item APIs.
 * No Lua/GPU work. Root reads cached active for actual HUD/combat/menu admission.
 */
int oa_creation_session_refresh(oa_creation_session *,char *,size_t);
const oa_creation_active *oa_creation_session_active(const oa_creation_session *);
oa_ca_actor *oa_creation_session_actor(const oa_creation_session *);
oa_creation_gameplay *oa_creation_session_gameplay(oa_creation_session *);
oa_creator_game_host *oa_creation_session_game(oa_creation_session *);
const char *oa_creation_session_checkpoint_path(const oa_creation_session *);
/* Call release BEFORE renderer_gpu_close while old context is still current.
 * Rebuild AFTER same borrowed renderer gpu_open. Failed rebuild leaves actorNULL
 * and preserves committed CPU profile/gameplay/save; no preview actor is shared.
 */
void oa_creation_session_release_actor(oa_creation_session *);
int oa_creation_session_rebuild_actor(oa_creation_session *,char *,size_t);
#endif
