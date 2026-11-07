#ifndef OA_CHARACTER_ATTRIBUTES_H
#define OA_CHARACTER_ATTRIBUTES_H
#include <stddef.h>
#include <stdint.h>
/* Optional source-verified Almain male normal correction. All checks complete
 * before any mutation; only normals in the caller-owned52B heap pack change.
 * Call BEFORE oa_character_parse. Existing asset files are never written. */
int oa_character_attributes_apply(uint8_t *pack,size_t pack_size,
 const uint8_t *sidecar,size_t sidecar_size,unsigned *changed,char *error,size_t capacity);
/* Source normals + two per-assembly palette prefixes commit together to heap.
 * Two shirt auxiliary joints retain the documented existing ancestor policy. */
int oa_character_repairs_apply(uint8_t *pack,size_t pack_size,
 const uint8_t *attrs,size_t attrs_size,const uint8_t *palettes,size_t palettes_size,
 unsigned *normal_count,unsigned *palette_count,char *error,size_t capacity);
#endif
