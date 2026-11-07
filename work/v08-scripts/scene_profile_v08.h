#ifndef OPEM_SCENE_PROFILE_V08_H
#define OPEM_SCENE_PROFILE_V08_H
#include "amalur_runtime.h"
#ifdef __cplusplus
extern "C" {
#endif
#define AMALUR_SCENE_PROFILE_V08_SHA256 "16a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314"
typedef enum scene_controller_domain_v08 {
    SCENE_CONTROLLER_DOMAIN_NATIVE_KIND = 0,
    SCENE_CONTROLLER_DOMAIN_ANDROID_LOGICAL_STANDARD = 1,
    SCENE_CONTROLLER_DOMAIN_ANDROID_LOGICAL_REVERSED = 2
} scene_controller_domain_v08;
typedef struct scene_controller_state_v08 {
    int is_set;                 /* Exactly0 or1; unset queries fail explicitly. */
    int32_t native_device_kind;  /* Used only in NATIVE_KIND; no Android mapping. */
    /* Trailing zero preserves source initializers {is_set, native_kind}.
     * Android domains select explicit host logical-layout policy, not native
     * device kinds, locale, controller presence, or printed button labels. */
    scene_controller_domain_v08 domain;
} scene_controller_state_v08;
typedef struct scene_content_state_v08 {
    int is_set;                 /* Exactly0 or1; unknown queries fail. */
    uint32_t registered_mask;
    uint32_t active_mask;
} scene_content_state_v08;
typedef struct scene_platform_state_v08 {
    int is_set;                 /* Exactly0 or1; unknown queries fail. */
    int32_t name_hash;           /* Explicit SH platform name, not native enum. */
} scene_platform_state_v08;
typedef struct scene_quick_save_state_v08 {
    int is_set;                 /* Exactly0 or1; unknown queries fail. */
    int supported;              /* Exactly0 or1; explicit host capability. */
} scene_quick_save_state_v08;
typedef struct scene_profile_v08_options {
    const char *target_sha256;
    scene_controller_state_v08 controller;
    /* Separate copied state. Omitted trailing initializers remain unknown. */
    scene_content_state_v08 content;
    /* Immutable per realm; copied on install. Omitted initializer is unknown. */
    scene_platform_state_v08 platform;
    /* 0 unknown, 1 explicitly new initially empty preference session. No
     * import/save/persistence; immutable flag, mutable Lua-owned dictionary. */
    int fresh_profile;
    /* Immutable copied capability; does not implement saving. */
    scene_quick_save_state_v08 quick_save;
    /* 0 unknown; 1 explicitly no mounted OST/audio language packs. Copied,
     * immutable per realm. Automatic display text is new host fallback. */
    int no_language_packs;
    /* 0 unknown; explicit renderer cap1..16. Android preview chooses1;
     * original Windows16 is a separate native fixture, not preview parity. */
    int max_anisotropy;
} scene_profile_v08_options;
/* Fresh-realm profile: normal provider API replaces its whole provider set.
 * GAME.get_empty_object_handle admits zero arguments and returns the captured
 * canonical type11 token low0xfb/high0; no object lookup or validity semantics.
 * Supplies zero-argument GAME.get_game_engine_version and
 * INPUT.is_east_asian_controller_button_swap_required, and one-argument
 * GAME.is_content_package_active for exact numeric integers0..31, plus
 * zero-argument WINDOW.get_platform returning the copied platform name hash.
 * PROFILE.get_variable admits one numeric signed-int32 hash and returns the
 * stored number or nil if missing. PROFILE.set_variable admits that hash and
 * a numeric signed-int32 value, stores/replaces it and returns no values.
 * Both require an explicitly fresh session; unknown state errors. No disk I/O.
 * SAVE_RESTORE.does_platform_support_quick_save admits zero arguments and
 * returns the explicit known host capability. Other services remain errors.
 * GAME.get_available_ost_languages/get_available_audio_languages return new
 * plain {-1} arrays only for no_language_packs1. The corresponding
 * get_available_ost_language_names/get_available_audio_language_names return
 * new {"Automatic"} arrays: explicit host fallback, not native localized label
 * parity. All four require zero arguments; unknown catalog state errors.
 * WINDOW.get_max_anisotrophy (native spelling) requires zero arguments and
 * returns copied max_anisotropy1..16;0 unknown errors. This advertises an
 * explicit host renderer capability and does not implement texture filtering.
 * GAME/INPUT/WINDOW/PROFILE/SAVE_RESTORE must be registered. Existing native
 * user preferences and saves are never read/written.
 * State is copied into Lua-owned storage; no host state pointers survive this
 * call. Initial unset state is valid, but querying it fails until explicitly set.
 * Discard realm after any installation failure (publication is not transactional).
 * All Lua allocations/errors are protected. No concurrent use of one realm. */
int scene_profile_v08_install(amalur_runtime *,const scene_profile_v08_options *,char *error,size_t capacity);
/* Mutates the already-installed Lua-owned state, preserving captured provider
 * function identity. Copies immediately; caller can release/change its input.
 * Unsetting restores explicit query errors in every domain. Invalid is_set or
 * domain values are rejected without changing prior state. Android STANDARD
 * returns false (Android keycode A confirms/B backs); REVERSED returns true.
 * These are new host policies, not claimed native kind mappings. Fails if this
 * profile was not installed. All users must recompile after struct changes. */
int scene_profile_v08_set_controller(amalur_runtime *,const scene_controller_state_v08 *,char *error,size_t capacity);
/* Independent copied content state; retains captured query identity. Query
 * returns the selected bit of registered_mask & active_mask. Unknown state
 * errors even for zero masks. Invalid is_set rejects without mutation.
 * A known empty Android mount set is an explicit port policy, not a report
 * about native DLC entitlement or the user's native game installation. */
int scene_profile_v08_set_content(amalur_runtime *,const scene_content_state_v08 *,char *error,size_t capacity);
#ifdef __cplusplus
}
#endif
#endif
