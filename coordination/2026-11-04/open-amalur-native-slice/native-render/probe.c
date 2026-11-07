#include "oa_recovered.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static unsigned checks;
#define CHECK(x) do {checks++;if(!(x)){fprintf(stderr,"FAIL line %d: %s\n",__LINE__,#x);return 1;}}while(0)
static uint32_t events[32];static unsigned ne;
static void vertices(void*u,const uint32_t*b,const uint32_t*s,const uint32_t*o){(void)u;events[ne++]=1;events[ne++]=b[0];events[ne++]=b[1];events[ne++]=s[0];events[ne++]=s[1];events[ne++]=o[0]|o[1];}
static void topo(void*u,uint32_t n){(void)u;events[ne++]=2;events[ne++]=n;}
static void indices(void*u,uint32_t b,uint32_t f,uint32_t o){(void)u;events[ne++]=3;events[ne++]=b;events[ne++]=f;events[ne++]=o;}
static void drawi(void*u,uint32_t n,uint32_t f,int32_t b){(void)u;events[ne++]=4;events[ne++]=n;events[ne++]=f;events[ne++]=(uint32_t)b;}
static void draw(void*u,uint32_t n,uint32_t f){(void)u;events[ne++]=5;events[ne++]=n;events[ne++]=f;}
static void put(uint8_t*b,unsigned o,uint32_t v){b[o]=(uint8_t)v;b[o+1]=(uint8_t)(v>>8);b[o+2]=(uint8_t)(v>>16);b[o+3]=(uint8_t)(v>>24);}
int main(void){
 uint8_t bytes[2048]={0};const uint32_t base=0xf0000000u;oa_snapshot s={bytes,sizeof(bytes),base};oa_geometry0 g;
 oa_draw_backend backend={0,vertices,topo,indices,drawi,draw};
 uint32_t src[8]={10,11,12,13,20,21,22,23},out[12]={0};
 const uint32_t expanded[12]={10,11,12,10,12,13,20,21,22,20,22,23};
 const uint32_t indexed[16]={1,0x100,0x200,36,16,0,2,4,3,0x300,57,0,4,42,0,0};
 put(bytes,0x2c,base+0x100);put(bytes,0x32c,base+0x500);put(bytes,0x420,base+0x700);
 put(bytes,0x114,0x300);put(bytes,0x10c,0x100);put(bytes,0x704,0x200);put(bytes,0x5d8,36);put(bytes,0x5dc,16);
 put(bytes,0x12c,4);put(bytes,0x118,42);put(bytes,0x128,57);put(bytes,0x110,17);
 CHECK(sizeof(void*)==8);CHECK(oa_decode_geometry0(&s,base,base+0x400,base+0x300,&g));
 CHECK(oa_submit_geometry0(&g,&backend));CHECK(ne==16);CHECK(!memcmp(events,indexed,sizeof(indexed)));
 put(bytes,0x114,0);ne=0;CHECK(oa_decode_geometry0(&s,base,base+0x400,base+0x300,&g));
 CHECK(oa_submit_geometry0(&g,&backend));CHECK(ne==11);CHECK(events[8]==5 && events[9]==17 && events[10]==0);
 s.size=0x5db;CHECK(!oa_decode_geometry0(&s,base,base+0x400,base+0x300,&g));s.size=sizeof(bytes);
 put(bytes,0x2c,0xfffffff0u);CHECK(!oa_decode_geometry0(&s,base,base+0x400,base+0x300,&g));
 CHECK(oa_expand_quads(out,sizeof(out),src,8,4));CHECK(!memcmp(out,expanded,sizeof(out)));
 CHECK(!oa_expand_quads(out,sizeof(out)-1,src,8,4));CHECK(!oa_expand_quads(out,sizeof(out),src,7,4));
 CHECK(!oa_expand_quads(src,sizeof(src),src,4,4));CHECK(oa_texture_subresource(9,3,2)==21);
 {
  uint8_t result[20], expected[20];unsigned i;
  memset(bytes,0,sizeof(bytes));memset(result,0xaa,sizeof(result));memset(expected,0xaa,sizeof(expected));
  put(bytes,0x20,base+0x200);put(bytes,0x40,2);put(bytes,0x48,base+0x300);
  put(bytes,0x204,3u|(7u<<16));put(bytes,0x20c,5u|(1u<<16));put(bytes,0x300,2u|(10u<<16));
  for(i=0;i<32;i++) bytes[0x100+i]=(uint8_t)(0x10+i);
  memcpy(expected+7,bytes+0x102,3);memcpy(expected+1,bytes+0x10a,5);
  CHECK(oa_fill_material_constants(&s,base+0x100,base+0x20,base+0x40,result,sizeof(result)));
  CHECK(!memcmp(result,expected,sizeof(result)));
  /* Sequential overlapping destinations preserve original last-write ordering. */
  put(bytes,0x20c,5u|(8u<<16));memset(result,0xaa,sizeof(result));memset(expected,0xaa,sizeof(expected));
  memcpy(expected+7,bytes+0x102,3);memcpy(expected+8,bytes+0x10a,5);
  CHECK(oa_fill_material_constants(&s,base+0x100,base+0x20,base+0x40,result,sizeof(result)));
  CHECK(!memcmp(result,expected,sizeof(result)));
  memset(result,0xaa,sizeof(result));memset(expected,0xaa,sizeof(expected));
  put(bytes,0x20c,5u|(19u<<16));
  CHECK(!oa_fill_material_constants(&s,base+0x100,base+0x20,base+0x40,result,sizeof(result)));
  CHECK(!memcmp(result,expected,sizeof(result))); /* Invalid second entry writes nothing. */
  put(bytes,0x20c,5u|(1u<<16));put(bytes,0x300,2u|(0xffffu<<16));
  CHECK(!oa_fill_material_constants(&s,base+0x100,base+0x20,base+0x40,result,sizeof(result)));
  CHECK(!memcmp(result,expected,sizeof(result)));
  put(bytes,0x300,2u|(10u<<16));
  CHECK(!oa_fill_material_constants(&s,base+0x100,base+0x20,base+0x40,bytes+0x40,20));
  put(bytes,0x48,0xfffffffdu);
  CHECK(!oa_fill_material_constants(&s,base+0x100,base+0x20,base+0x40,result,sizeof(result)));
  {oa_snapshot edge={bytes,8,UINT32_MAX-1u};bytes[0]=1;bytes[1]=0;
   CHECK(!oa_fill_material_constants(&edge,0,UINT32_MAX,edge.base,result,sizeof(result)));}
  put(bytes,0x40,0);
  CHECK(oa_fill_material_constants(&s,0,0,base+0x40,NULL,0));
 }
 printf("{\"ok\":true,\"checks\":%u,\"pointer_bits\":%u,\"module\":\"recovered-geometry-and-material-constants\",\"fixture\":\"synthetic-contract-test\",\"full_scene\":false}\n",checks,(unsigned)(sizeof(void*)*8));
 return 0;
}
