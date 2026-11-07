#include "oa_geometry_kind1.h"
#define R(a,o,v) oa_guest_read_u32(m,(a),(o),&(v))
int oa_decode_geometry1_sparse(const oa_guest_memory*m,uint32_t packet,uint32_t tables,uint32_t holder,oa_geometry1*out){
 oa_geometry1 r={0};uint32_t kind,g,range,format,strides,instance,count,index_start,vertex_start,format_stride;
 if(!out||!oa_guest_memory_valid(m)||!R(packet,0,kind)||kind!=1||!R(packet,0x2c,g)||!R(g,0x34,range)||!R(g,8,format)||
 !R(holder,0x2c,strides)||!R(tables,0x20,instance)||!R(g,0x14,r.g.ib)||!R(g,0xc,r.g.vb[0])||!R(instance,4,r.g.vb[1])||
 !R(strides,0xd8,r.g.stride[0])||!R(strides,0xdc,r.g.stride[1])||!R(g,0x2c,r.g.topology)||!R(range,0xc,count)||
 !R(range,8,index_start)||!R(range,0x14,vertex_start)||!R(format,0xd8,format_stride)||!R(packet,0x30,r.constant_address)||!R(packet,0x34,r.constant_count))return 0;
 r.g.indexed=r.g.ib!=0;if(!count&&!R(g,r.g.indexed?0x18:0x10,count))return 0;
 r.g.count=count;r.g.offset[0]=vertex_start*format_stride;r.ib_offset=index_start*2u;
 if(r.g.indexed&&!R(g,0x28,r.g.index_format))return 0;
 *out=r;return 1;
}
#undef R
int oa_submit_geometry1(const oa_geometry1*r,const oa_draw_backend*b){
 if(!r||!b||!b->vertices||!b->topology||(r->g.indexed&&(!b->indices||!b->draw_indexed))||(!r->g.indexed&&!b->draw))return 0;
 const oa_geometry0*g=&r->g;b->vertices(b->user,g->vb,g->stride,g->offset);b->topology(b->user,g->topology);
 if(g->indexed){b->indices(b->user,g->ib,g->index_format,r->ib_offset);b->draw_indexed(b->user,g->count,0,0);}else b->draw(b->user,g->count,0);
 return 1;
}

/* VA0x00c96f68..0x00c96f77: copy packet+0x34 records of48bytes from packet+0x30.
   Caller performs actual GPU map/unmap/bind; this boundary copies immutable guest data only. */
#include <string.h>
int oa_copy_instance_constants(const oa_guest_memory*m,uint32_t address,uint32_t count,void*dest,size_t capacity){
 uint64_t n=(uint64_t)count*48u;
 if(!m||!oa_guest_memory_valid(m)||n>capacity||n>UINT64_C(0x100000000)-address||(!dest&&n))return 0;
 if(!n)return 1;
 for(size_t i=0;i<m->count;++i){const oa_guest_span*s=&m->spans[i];if(address>=s->base){uint64_t start=(uint64_t)address-s->base;if(start<=s->size&&n<=s->size-start){memmove(dest,s->bytes+(size_t)start,(size_t)n);return 1;}}}
 return 0;
}
