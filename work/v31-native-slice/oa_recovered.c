#include "oa_recovered.h"
#include <string.h>
#include <limits.h>
static int read32(const oa_snapshot *s, uint32_t a, uint32_t offset, uint32_t *v) {
    uint64_t address=(uint64_t)a+offset, index;
    const uint8_t *p;
    if(!s || !s->bytes || address>UINT32_MAX || address<s->base) return 0;
    index=address-s->base;
    if(index>s->size || s->size-index<4) return 0;
    p=s->bytes+(size_t)index;
    *v=(uint32_t)p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24);
    return 1;
}
int oa_decode_geometry0(const oa_snapshot *s,uint32_t packet,uint32_t tables,uint32_t holder,oa_geometry0 *out) {
    oa_geometry0 r={0}; uint32_t kind,g,strides,instance,count;
    if(!out || !read32(s,packet,0,&kind) || kind!=0 ||
       !read32(s,packet,0x2c,&g) || !read32(s,holder,0x2c,&strides) ||
       !read32(s,tables,0x20,&instance) || !read32(s,g,0x14,&r.ib) ||
       !read32(s,g,0x0c,&r.vb[0]) || !read32(s,instance,4,&r.vb[1]) ||
       !read32(s,strides,0xd8,&r.stride[0]) || !read32(s,strides,0xdc,&r.stride[1]) ||
       !read32(s,g,0x2c,&r.topology)) return 0;
    r.indexed=r.ib!=0;
    if(!read32(s,g,r.indexed?0x18:0x10,&count)) return 0;
    r.count=count;
    if(r.indexed && !read32(s,g,0x28,&r.index_format)) return 0;
    *out=r; return 1;
}
int oa_submit_geometry0(const oa_geometry0 *g,const oa_draw_backend *b) {
    if(!g || !b || !b->vertices || !b->topology ||
       (g->indexed && (!b->indices || !b->draw_indexed)) || (!g->indexed && !b->draw)) return 0;
    b->vertices(b->user,g->vb,g->stride,g->offset);
    b->topology(b->user,g->topology);
    if(g->indexed) {b->indices(b->user,g->ib,g->index_format,0);b->draw_indexed(b->user,g->count,0,0);}
    else b->draw(b->user,g->count,0);
    return 1;
}
int oa_expand_quads(void *dst,size_t capacity,const void *src,uint32_t vertices,uint32_t stride) {
    uint64_t bytes=(uint64_t)(vertices/4)*6*stride; uint32_t q;
    const uint8_t *in=src;uint8_t *out=dst; static const uint8_t order[6]={0,1,2,0,2,3};
    if(!dst || !src || !stride || vertices%4 || bytes>capacity || bytes>SIZE_MAX) return 0;
    /* The caller supplies a separate immutable captured vertex stream. */
    if((uintptr_t)dst<=(uintptr_t)src) {
        if((uintptr_t)src-(uintptr_t)dst<bytes) return 0;
    } else if((uintptr_t)dst-(uintptr_t)src<(uint64_t)vertices*stride) return 0;
    for(q=0;q<vertices/4;q++) {uint32_t i;for(i=0;i<6;i++)
        memcpy(out+((size_t)q*6+i)*stride,in+((size_t)q*4+order[i])*stride,stride);}
    return 1;
}
uint32_t oa_texture_subresource(uint8_t count,uint32_t mip,uint32_t slice) {return (uint32_t)count*slice+mip;}
