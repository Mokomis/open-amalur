#ifndef AMALUR_SCENE_MESH_H
#define AMALUR_SCENE_MESH_H
#include <stddef.h>
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
#define AMALUR_SCENE_MAX_BYTES (256u*1024u*1024u)
typedef struct amalur_scene_mesh {
    uint32_t vertex_count;
    float bounds_min[3],bounds_max[3];
    float *vertices; /* Owned triangle soup: position3,normal3,color3. */
} amalur_scene_mesh;
/* Authored interchange format, NOT the game's original binary scene format.
 * Header:8bytes OMSC07\0\0,LEu32 count,6LEf32 min/max; then count*9LEf32.
 * Exact file length, nonempty triangle list, finite values and stated bounds
 * are validated. Initialize output to zero before first use; clear releases its
 * vertex allocation. The caller owns source provenance and extraction evidence. */
int amalur_scene_mesh_parse(const void *bytes,size_t length,amalur_scene_mesh *mesh,char *error,size_t capacity);
void amalur_scene_mesh_clear(amalur_scene_mesh *mesh);
#ifdef __cplusplus
}
#endif
#endif
