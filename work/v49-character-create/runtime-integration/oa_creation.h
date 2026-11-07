#ifndef OA_CREATION_H
#define OA_CREATION_H
/* C99 source-backed creation/profile data. No rendering, game calls or file I/O. */
#include <stddef.h>
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
enum { OA_CREATION_RACES=4, OA_CREATION_SEXES=2, OA_CREATION_PRESETS=5,
 OA_CREATION_PATRONS=6, OA_CREATION_SKILLS=9, OA_CREATION_ASSETS=6,
 OA_CREATION_COLORS=8, OA_CREATION_ALPHAS=4, OA_CREATION_NAME_SCALARS=16,
 OA_CREATION_NAME_BYTES=64, OA_CREATION_ENVELOPE_MAX=192 };
typedef enum oa_creation_result {
 OA_CREATION_OK=0, OA_CREATION_ARGUMENT, OA_CREATION_INVALID_STATE,
 OA_CREATION_SELECTION, OA_CREATION_NAME, OA_CREATION_LOCKED,
 OA_CREATION_SOURCE_PRESET_UNRESOLVED, OA_CREATION_TRANSACTION,
 OA_CREATION_ALREADY_COMMITTED, OA_CREATION_CAPACITY, OA_CREATION_CORRUPT,
 OA_CREATION_VERSION, OA_CREATION_CATALOGUE
} oa_creation_result;
enum { OA_CREATION_ALMAIN=0,OA_CREATION_VARANI,OA_CREATION_LJOSALFAR,OA_CREATION_DOKKALFAR };
enum { OA_CREATION_MALE=0,OA_CREATION_FEMALE=1 };
enum { OA_CREATION_HEAD=0,OA_CREATION_HAIR,OA_CREATION_BEARD,OA_CREATION_EARS,
 OA_CREATION_TATTOO,OA_CREATION_ACCESSORY };
enum { OA_CREATION_SKIN=0,OA_CREATION_HAIR_COLOR,OA_CREATION_EYE_COLOR,
 OA_CREATION_TATTOO_COLOR,OA_CREATION_BEARD_COLOR,OA_CREATION_EYEBROW,
 OA_CREATION_EYELINER,OA_CREATION_LIPSTICK };
enum { OA_CREATION_TATTOO_ALPHA=0,OA_CREATION_EYEBROW_ALPHA,
 OA_CREATION_EYELINER_ALPHA,OA_CREATION_LIPSTICK_ALPHA };
enum { OA_CREATION_DRAFT=0,OA_CREATION_PENDING=1,OA_CREATION_COMMITTED=2 };
enum { OA_CREATION_VISUALS_NOT_IMPLEMENTED=1u, OA_CREATION_FEMALE_ANIMATION_UNVERIFIED=2u,
 OA_CREATION_EARS_UNSPECIFIED=4u, OA_CREATION_ASSET_AVAILABILITY_UNVERIFIED=8u,
 OA_CREATION_NATIVE_NAME_FILTER_UNVERIFIED=16u };
typedef struct oa_creation_appearance {
 uint32_t assets[OA_CREATION_ASSETS]; /* Native simtype IDs, not baked part indices. */
 uint16_t colors[OA_CREATION_COLORS]; /* One-based source-list index;0 only if absent. */
 uint8_t alphas[OA_CREATION_ALPHAS];
} oa_creation_appearance;
typedef struct oa_creation_source_type {
 const char *race,*sex,*default_name;
 uint32_t race_hash,sex_hash,player_simtype,creator_simtype,rig_fab;
 uint32_t race_mask,sex_mask;
 oa_creation_appearance defaults;
} oa_creation_source_type;
typedef struct oa_creation_patron { const char *name; uint32_t buff_id; } oa_creation_patron;
typedef struct oa_creation_color_record {
 uint32_t words[5]; /* Raw source: option key,2 color words,2 texture/application words. */
} oa_creation_color_record;
typedef struct oa_creation_state {
 uint32_t guard,revision;
 uint64_t transaction;
 uint8_t race,sex,preset,patron,phase,customized,name_is_default;
 oa_creation_appearance appearance;
 char name[OA_CREATION_NAME_BYTES+1];
} oa_creation_state;
typedef struct oa_creation_render_selection {
 uint32_t player_simtype,creator_simtype,rig_fab;
 uint32_t head_simtype,hair_simtype,beard_simtype,ears_simtype,tattoo_simtype,accessory_simtype;
 oa_creation_color_record colors[OA_CREATION_COLORS];
 uint32_t present_color_mask,head_diffuse_id,body_diffuse_id,warnings;
 uint8_t alphas[OA_CREATION_ALPHAS];
} oa_creation_render_selection;
typedef struct oa_creation_commit {
 uint64_t transaction;
 uint32_t revision;
 oa_creation_state profile; /* PENDING copy; host owns its transaction. */
 int16_t skill_delta_raw[OA_CREATION_SKILLS]; /* 10 native units per displayed rank. */
 uint32_t patron_buff_id,patron_caster_tag;
 int32_t patron_duration;
 uint8_t restore_health_to_max;
} oa_creation_commit;
/* Source ordering for skills is exposed so host never guesses array order. */
extern const char *const oa_creation_skill_names[OA_CREATION_SKILLS];
const char *oa_creation_result_string(oa_creation_result result);
const oa_creation_source_type *oa_creation_source(unsigned race,unsigned sex);
const oa_creation_patron *oa_creation_source_patron(unsigned race,unsigned patron);
const oa_creation_appearance *oa_creation_source_preset(unsigned race,unsigned sex,unsigned one_based_preset);
size_t oa_creation_color_count(unsigned race,unsigned sex,unsigned channel);
const oa_creation_color_record *oa_creation_source_color(unsigned race,unsigned sex,unsigned channel,unsigned one_based_index);
int oa_creation_asset_supported(unsigned race,unsigned sex,unsigned category,uint32_t asset_id);
uint32_t oa_creation_catalogue_crc(void);
oa_creation_result oa_creation_begin(oa_creation_state *state,unsigned race,unsigned sex);
oa_creation_result oa_creation_validate(const oa_creation_state *state);
oa_creation_result oa_creation_select_type(oa_creation_state *state,unsigned race,unsigned sex);
oa_creation_result oa_creation_select_patron(oa_creation_state *state,unsigned patron);
oa_creation_result oa_creation_select_patron_id(oa_creation_state *state,uint32_t buff_id);
oa_creation_result oa_creation_apply_preset(oa_creation_state *state,unsigned one_based_preset);
oa_creation_result oa_creation_select_asset(oa_creation_state *state,unsigned category,uint32_t asset_id);
oa_creation_result oa_creation_select_color(oa_creation_state *state,unsigned channel,unsigned one_based_index);
oa_creation_result oa_creation_select_alpha(oa_creation_state *state,unsigned channel,unsigned value);
/* Custom host policy: strict UTF8,1..16 Unicode scalars, no ASCII controls.
 * Native editbox counting/sanitization is unverified; do not call this equivalent. */
oa_creation_result oa_creation_set_name(oa_creation_state *state,const char *utf8,size_t bytes);
oa_creation_result oa_creation_render(const oa_creation_state *state,oa_creation_render_selection *out);
/* token is supplied by host, nonzero and unique per host transaction.
 * PENDING+same token retries the same candidate; COMMITTED never emits effects.
 * Apply stats/buff AND acknowledgement/profile atomically in host persistence;
 * this memory-only module cannot close a crash window across separate writes. */
oa_creation_result oa_creation_finalize(oa_creation_state *state,uint64_t token,oa_creation_commit *out);
oa_creation_result oa_creation_acknowledge(oa_creation_state *state,uint64_t token);
oa_creation_result oa_creation_cancel_pending(oa_creation_state *state,uint64_t token);
/* Separate OACREA1 envelope; no native/legacy save/settings bytes or files touched. */
size_t oa_creation_serialized_size(const oa_creation_state *state);
oa_creation_result oa_creation_serialize(const oa_creation_state *state,void *buffer,size_t capacity,size_t *written);
oa_creation_result oa_creation_deserialize(oa_creation_state *state,const void *buffer,size_t size);
#ifdef __cplusplus
}
#endif
#endif
