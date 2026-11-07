#include "oa_geometry_sparse.h"
int oa_guest_memory_valid(const oa_guest_memory*m){
 if(!m||(!m->spans&&m->count))return 0;
 for(size_t i=0;i<m->count;++i){const oa_guest_span*s=&m->spans[i];uint64_t end;
  if(!s->bytes||!s->size||s->size>UINT64_C(0x100000000)-s->base)return 0;end=(uint64_t)s->base+s->size;
  for(size_t j=0;j<i;++j){const oa_guest_span*t=&m->spans[j];if(s->base<(uint64_t)t->base+t->size&&t->base<end)return 0;}
 }return 1;
}
static int read32(const oa_guest_memory*m,uint32_t address,uint32_t off,uint32_t*out){
 uint64_t a=(uint64_t)address+off;if(!m||a>UINT32_MAX-3u)return 0;
 for(size_t i=0;i<m->count;++i){const oa_guest_span*s=&m->spans[i];if(a>=s->base&&a-s->base<=s->size&&s->size-(size_t)(a-s->base)>=4){const uint8_t*p=s->bytes+(size_t)(a-s->base);*out=(uint32_t)p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24);return 1;}}
 return 0;
}
/* Recovered kind0 tail of VA0x00c961e0, same field reads as v31 decoder.
   Preserve all guest/resource addresses as32bit tokens; never dereference them as host pointers. */
int oa_decode_geometry0_sparse(const oa_guest_memory*m,uint32_t packet,uint32_t tables,uint32_t holder,oa_geometry0*out){
 oa_geometry0 r={0};uint32_t kind,g,strides,instance,count;
 if(!out||!oa_guest_memory_valid(m)||!read32(m,packet,0,&kind)||kind!=0||
 !read32(m,packet,0x2c,&g)||!read32(m,holder,0x2c,&strides)||!read32(m,tables,0x20,&instance)||
 !read32(m,g,0x14,&r.ib)||!read32(m,g,0x0c,&r.vb[0])||!read32(m,instance,4,&r.vb[1])||
 !read32(m,strides,0xd8,&r.stride[0])||!read32(m,strides,0xdc,&r.stride[1])||!read32(m,g,0x2c,&r.topology))return 0;
 r.indexed=r.ib!=0;if(!read32(m,g,r.indexed?0x18:0x10,&count))return 0;r.count=count;
 if(r.indexed&&!read32(m,g,0x28,&r.index_format))return 0;*out=r;return 1;
}
int oa_submit_geometry0(const oa_geometry0*g,const oa_draw_backend*b){
 if(!g||!b||!b->vertices||!b->topology||(g->indexed&&(!b->indices||!b->draw_indexed))||(!g->indexed&&!b->draw))return 0;
 b->vertices(b->user,g->vb,g->stride,g->offset);b->topology(b->user,g->topology);
 if(g->indexed){b->indices(b->user,g->ib,g->index_format,0);b->draw_indexed(b->user,g->count,0,0);}else b->draw(b->user,g->count,0);
 return 1;
}
