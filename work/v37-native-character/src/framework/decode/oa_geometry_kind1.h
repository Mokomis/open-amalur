#ifndef OA_GEOMETRY_KIND1_H
#define OA_GEOMETRY_KIND1_H
#include "oa_geometry_sparse.h"
typedef struct {oa_geometry0 g;uint32_t ib_offset,constant_address,constant_count;} oa_geometry1;
/* Geometry tail only. Caller must prepare VS constant slot5; this decoder records its source metadata. */
int oa_decode_geometry1_sparse(const oa_guest_memory*,uint32_t packet,uint32_t tables,uint32_t holder,oa_geometry1*);
int oa_submit_geometry1(const oa_geometry1*,const oa_draw_backend*);
int oa_copy_instance_constants(const oa_guest_memory*,uint32_t address,uint32_t count,void*dest,size_t capacity);
#endif
