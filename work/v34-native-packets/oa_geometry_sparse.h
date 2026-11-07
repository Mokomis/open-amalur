#ifndef OA_GEOMETRY_SPARSE_H
#define OA_GEOMETRY_SPARSE_H
#include <stdint.h>
#include <stddef.h>
typedef struct {uint32_t base;size_t size;const uint8_t*bytes;} oa_guest_span;
typedef struct {const oa_guest_span*spans;size_t count;} oa_guest_memory;
typedef struct {uint32_t vb[2],stride[2],offset[2],topology,ib,index_format,count;int indexed;} oa_geometry0;
typedef struct {
 void*user;
 void(*vertices)(void*,const uint32_t[2],const uint32_t[2],const uint32_t[2]);
 void(*topology)(void*,uint32_t);
 void(*indices)(void*,uint32_t,uint32_t,uint32_t);
 void(*draw_indexed)(void*,uint32_t,uint32_t,int32_t);
 void(*draw)(void*,uint32_t,uint32_t);
} oa_draw_backend;
int oa_guest_memory_valid(const oa_guest_memory*);
int oa_decode_geometry0_sparse(const oa_guest_memory*,uint32_t packet,uint32_t tables,uint32_t holder,oa_geometry0*);
int oa_submit_geometry0(const oa_geometry0*,const oa_draw_backend*);
#endif
