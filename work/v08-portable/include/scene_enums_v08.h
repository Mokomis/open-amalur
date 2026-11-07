#ifndef OPEM_SCENE_ENUMS_V08_H
#define OPEM_SCENE_ENUMS_V08_H
#include "amalur_runtime.h"
#ifdef __cplusplus
extern "C" {
#endif
#define SCENE_ENUMS_V08_MAX_ENTRIES 65536u
#define SCENE_ENUMS_V08_MAX_BYTES (12u+12u*SCENE_ENUMS_V08_MAX_ENTRIES)
/* Explicit selected-source snapshot, not an archive merge or discovery API.
 * Bytes: "AENU", LE u32 version1, LE u32 count, then count triples
 * (u32 groupHash, u32 memberHash, u32 valueBits). Exact length required;
 * count0..65536, duplicate hash pairs rejected even if their values agree.
 * All storage is copied into Lua-owned private tables. Caller may free/change
 * the snapshot after return. No C-owned allocation survives this call.
 * Installs only STE(group,member), refusing existing globals and metatable _G.
 * Exactly two strings are required; invalid arity/types/misses return one nil.
 * Native ASCII casefold/NUL hash behavior comes from scene_asset_ascii_hash.
 * NonASCII before NUL errors explicitly. Values are exact signedint32 numbers.
 * Protected Lua allocations; failure leaves a Lua error atop the caller stack
 * and copies its text to error. Discard realm after installation failure.
 * Success preserves caller stack. No native enum loader or gameplay behavior
 * is supplied; source selection and conflict audit remain the host's job. */
int scene_enums_v08_install(amalur_runtime *,const void *snapshot,size_t length,
                           char *error,size_t capacity);
#ifdef __cplusplus
}
#endif
#endif
