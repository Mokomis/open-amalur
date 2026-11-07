#ifndef OA_CREATION_GAMEPLAY_H
#define OA_CREATION_GAMEPLAY_H
#include "oa_creation.h"
#include "oa_creator_game.h"
#include <stddef.h>
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
enum {OA_CG_OK=0,OA_CG_ERROR=1,OA_CG_UNAVAILABLE=2,OA_CG_ALREADY_ACTIVE=3};
typedef struct oa_patron_effect {uint32_t stat_key,operation,value_bits;} oa_patron_effect;
typedef struct oa_patron_record {uint32_t id;const char *name;uint32_t count;oa_patron_effect effects[3];} oa_patron_record;
enum { OA_CG_ITEMS_MAX=256 };
typedef struct oa_creation_item {uint32_t type,count;int32_t equipped_slot;uint32_t hidden;} oa_creation_item;
typedef struct oa_creation_owner_state {
 int32_t skill_raw[9]; /* Real authoritative raw ranks, ten units/display rank. */
 uint32_t patron_id,health,max_health;
 uint32_t destiny_buff_id,destiny_identifier; /* Fateless One385357/tag9325294. */
 uint32_t game_started,passive_aggressive_disabled,destiny_locked,fateweaver_locked;
 int32_t quest_stage; /* -1 before actual completion, 5 only after source callback. */
 uint32_t finalized,package4_active;
 uint32_t stealth_buff_registered,reckoning_buff_registered;
 uint32_t stealth_exiting,target_can_see_player,reckoning_active;
 uint32_t item_count;
 oa_creation_item items[OA_CG_ITEMS_MAX];
 uint64_t revision;
} oa_creation_owner_state;
typedef struct oa_creation_active {
 oa_creation_state profile;
 oa_creation_owner_state owner;
 oa_creator_game_state gameplay;
} oa_creation_active;
typedef struct oa_creation_gameplay oa_creation_gameplay;
/* Complete profile/gameplay reservation, including selected CPU/GPU appearance.
 * PREPARE reserves all memory/resources and applies nothing; COMMIT is infallible.
 * Caller must inspect and reserve actual render/equipment/collision/UI services.
 * A successful generic mock is not a production implementation. No reentry.
 * The opaque reservation token may be NULL. Callback pointers/bytes are borrowed. */
typedef struct oa_creation_publish {
 void *context;
 int (*prepare)(void*,int loading,const oa_creation_active*,const oa_creation_render_selection*,void**,char*,size_t);
 void (*commit)(void*,void*);
 void (*abort)(void*,void*);
} oa_creation_publish;
typedef struct oa_creation_gameplay_config {
 uint64_t generation,item_instance;
 int32_t item_index;
 int tutorials_enabled;
 int package4_active; /* Explicit0/1, -1 unavailable; asset presence is not ownership. */
 uint32_t current_health,base_max_health; /* Unmodified actual host base, never an already patron-buffed maximum. */
 const char *path; /* Dedicated *.creation-gameplay-v1.bin, no draft/old save. */
 oa_creation_publish appearance;
 oa_creator_game_backend gameplay_backend; /* Actual item/door/UI services after completion. */
 void *report_context;void (*report_failure)(void*,const char*);
 void *pose_context;int (*validate_load_pose)(void*,const oa_creator_game_pose*,char*,size_t);
 oa_opening_runtime_config runtime;
} oa_creation_gameplay_config;
/* Native shipped enumerator CONSTRUCTOR defaults, not current user entitlement/
 * overrides: packages1,2,3,4,6..11active,12inactive. Unknown IDs unavailable. */
int oa_creation_source_package_default(unsigned package_id,int *active);
oa_creation_gameplay *oa_creation_gameplay_create(const oa_opening_assets*,const oa_creation_gameplay_config*,char*,size_t);
void oa_creation_gameplay_close(oa_creation_gameplay*);
/* Explicit successful creator-confirm boundary. Does not modify the caller draft.
 * Reserves full appearance, executes the unchanged source MQ01 startup body under
 * production Lua budgets, then atomically persists profile+stats+gameplay and
 * publishes. Never called for cinematic skip. No stage25 accepted as progress. */
int oa_creation_gameplay_complete(oa_creation_gameplay*,const oa_creation_state *draft,
 uint64_t transaction,const oa_creator_game_pose*,char*,size_t);
int oa_creation_gameplay_save(oa_creation_gameplay*,char*,size_t);
int oa_creation_gameplay_load(oa_creation_gameplay*,char*,size_t);
int oa_creation_gameplay_snapshot(oa_creation_gameplay*,oa_creation_active*,char*,size_t);
/* Borrowed active game host. Only after completion/load. Do not close it.
 * Source volume/item/equip/timer APIs are in oa_creator_game.h. Their source
 * autosave joins this SAME profile+gameplay file. One opening Lua realm. */
oa_creator_game_host *oa_creation_gameplay_game(oa_creation_gameplay*);
typedef struct oa_creation_buff_instance {uint32_t id,identifier;int32_t duration_ms;} oa_creation_buff_instance;
/* Exactly four permanent source-owned buffs after completion: selected patron,
 * FatelessOne, Stealth_GlobalCritBonus and All_reckoning. Modifier conditions are
 * evaluated by stat(), not by faking these as unconditional flat bonuses. */
int oa_creation_gameplay_buff(oa_creation_gameplay*,unsigned index,oa_creation_buff_instance*);
const oa_patron_record *oa_creation_patron_record(uint32_t id);
/* Real source modifier evaluator. Integer mode matches native signed truncation;
 * float mode matches00e2c6b0. No guessed base values: caller supplies actual stat.
 * Query unknown selected buff or nonfinite/out-of-range values fails. */
int oa_creation_patron_apply(uint32_t buff,uint32_t stat_key,int integer_mode,
                            float base,float *out,char*,size_t);
int oa_creation_skill_raw(const oa_creation_owner_state*,unsigned skill,int32_t*);
int oa_creation_skill_tier_active(const oa_creation_owner_state*,unsigned skill,unsigned tier);
enum {OA_CG_ACTION_DESTINY=1,OA_CG_ACTION_FATEWEAVE,OA_CG_ACTION_AGGRESSIVE};
int oa_creation_gameplay_action_allowed(oa_creation_gameplay*,unsigned action);
/* Feed actual owner stealth/visibility/ReckoningMode624629 state; these gates
 * participate in actual stat evaluation, not just an initialization flag. */
int oa_creation_gameplay_combat_gates(oa_creation_gameplay*,int stealth_exiting,int target_sees_player,int reckoning_active,char*,size_t);
int oa_creation_gameplay_stat(oa_creation_gameplay*,uint32_t key,int integer_mode,float base,float*out,char*,size_t);
/* Exact named source skill states plus Stealth_Exiting/ReckoningMode. Unknown
 * states return unavailable; sparse source tier thresholds are not invented. */
int oa_creation_gameplay_actor_state(oa_creation_gameplay*,const char*name,int*out,char*,size_t);
int oa_creation_gameplay_health(oa_creation_gameplay*,int32_t signed_delta,char*,size_t);
/* All exact source common/hidden/recipe item records are owned and persisted.
 * Root binds selected equipment and these stat/lock queries to real engine systems.
 * Unrelated quest stages and a full native QuestMgr are not implemented. */
#ifdef __cplusplus
}
#endif
#endif
