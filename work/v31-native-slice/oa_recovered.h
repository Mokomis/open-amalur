#ifndef OA_RECOVERED_H
#define OA_RECOVERED_H
#include <stddef.h>
#include <stdint.h>
/* Capture addresses and resource tokens remain 32-bit; never cast them to host pointers. */
typedef struct { const uint8_t *bytes; size_t size; uint32_t base; } oa_snapshot;
typedef struct {
    uint32_t vb[2], stride[2], offset[2], topology, ib, index_format, count;
    int indexed;
} oa_geometry0;
typedef struct {
    void *user;
    void (*vertices)(void *, const uint32_t[2], const uint32_t[2], const uint32_t[2]);
    void (*topology)(void *, uint32_t);
    void (*indices)(void *, uint32_t, uint32_t, uint32_t);
    void (*draw_indexed)(void *, uint32_t, uint32_t, int32_t);
    void (*draw)(void *, uint32_t, uint32_t);
} oa_draw_backend;
/* Recovered kind-0 geometry submission inside cs:15032 function 0x00c961e0.
 * Material/state setup is deliberately outside this first ported boundary. */
int oa_decode_geometry0(const oa_snapshot *, uint32_t packet, uint32_t tables, uint32_t holder, oa_geometry0 *);
int oa_submit_geometry0(const oa_geometry0 *, const oa_draw_backend *);
/* Quad expansion ordering transcribed from immediate_draw, called by 0x00c961e0. */
int oa_expand_quads(void *dst, size_t capacity, const void *src, uint32_t vertices, uint32_t stride);
uint32_t oa_texture_subresource(uint8_t mip_count, uint32_t mip, uint32_t slice);
#endif
