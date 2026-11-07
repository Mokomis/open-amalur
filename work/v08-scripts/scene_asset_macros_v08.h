#ifndef OPEM_SCENE_ASSET_MACROS_V08_H
#define OPEM_SCENE_ASSET_MACROS_V08_H
#include "amalur_runtime.h"
#ifdef __cplusplus
extern "C" {
#endif
/* Installs one explicitly proven name/category mapping, never discovers one.
 * Name must be an uppercase identifier of1..127 bytes; category1..255.
 * Snapshot is LE version1/count/IDs/hashes with exact length,1..65536 entries,
 * unique hashes and nonzero unique uint32 IDs. A merged snapshot is acceptable
 * only after the host verifies its originals have no conflicting mappings.
 * Input bytes are borrowed only during this protected call; Lua owns the map.
 * Captures shared from_words and returns low=(category<<4)|0xb, high=assetID.
 * Missing names/invalid arguments return nil. Empty C strings return nil.
 * Hash0x233e41 returns ID0 per native aa7bd0. NonASCII errors explicitly.
 * Existing globals are never replaced; SH/input-key installers stay separate.
 * Discard the realm after any installation failure. No full asset manager or
 * category-specific gameplay behavior is supplied. */
int scene_asset_macro_v08_install(amalur_runtime *,const char *name,uint32_t category,
                                  const void *snapshot,size_t length,char *error,size_t capacity);
#ifdef __cplusplus
}
#endif
#endif
