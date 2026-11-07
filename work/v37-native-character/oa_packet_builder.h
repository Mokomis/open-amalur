#ifndef OA_PACKET_BUILDER_H
#define OA_PACKET_BUILDER_H
#include "oa_geometry_sparse.h"
typedef struct {uint32_t owner,properties,bindings,material,geometry,constant_block,pass,class_flags_address;} oa_packet_inputs;
/* Positive-count skinned packet tail of VA0x00cb64c0 only. Caller supplies
   allocation and constant block; matrix generation and arena locks are outside this boundary. */
int oa_build_skinned_packet(const oa_guest_memory*,const oa_packet_inputs*,uint32_t out[14]);
#endif
