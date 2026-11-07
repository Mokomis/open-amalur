#ifndef OPEM_SCENE_ASSET_KEYS_H
#define OPEM_SCENE_ASSET_KEYS_H
#include "amalur_runtime.h"
#ifdef __cplusplus
extern "C" {
#endif
/* Optional, explicit inputdeviceaction_init snapshot. Data-derived v1 layout:
 * u32 version, u32 count, count u32 IDs, count u32 case-folded hashes, all LE.
 * Current admitted IDs are nonzero uint32, with no duplicate IDs or hashes.
 * This is a bounded snapshot lookup, not the complete native asset manager.
 * Buffer is borrowed only until install returns; caller keeps ownership.
 * Success installs SH and INPUT_ACTION_KEY, refusing existing globals.
 * Failure preserves previous Lua stack and appends the original Lua error.
 * Discard the realm after any failure: OOM during final publication may leave
 * a partial installation. Shared bootstrap already destroys failed realms.
 * All map storage lives inside the capped Lua allocator. */
int scene_asset_keys_install(amalur_runtime *runtime,const void *bytes,size_t length,
                             char *error,size_t error_capacity);
/* ASCII case-folded hash from native00af08b0 and table01721040, seed0.
 * Stops at the first NUL, matching native strlen. Returns nonzero on non-ASCII
 * before NUL or a length outside the native signed-int32 domain. */
int scene_asset_ascii_hash(const char *bytes,size_t length,uint32_t *hash);
#ifdef __cplusplus
}
#endif
#endif
