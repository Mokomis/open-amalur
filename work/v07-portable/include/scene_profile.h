#ifndef OPEM_SCENE_PROFILE_H
#define OPEM_SCENE_PROFILE_H
#include "amalur_runtime.h"
#ifdef __cplusplus
extern "C" {
#endif
#define AMALUR_SCENE_PROFILE_SHA256 "16a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314"
/* Explicit initialization profile for that exact original executable. Installs
 * only zero-argument GAME.get_game_engine_version via the normal registry/provider
 * API; other argument shapes remain an explicit unsupported domain.
 * Call during fresh-realm setup: normal set_provider replaces the whole provider
 * set, so this does not merge providers installed earlier. Other engine services
 * remain missing. No game version guard or recovered source is changed.
 * On any failure discard the realm; Lua errors are protected and diagnosed. */
int scene_profile_install(amalur_runtime *,const char *target_sha256,char *error,size_t error_capacity);
#ifdef __cplusplus
}
#endif
#endif
