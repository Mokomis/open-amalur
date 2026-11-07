#include "oa_character_attributes.h"
#include <stdio.h>
#include <string.h>
#include <math.h>
#include <stdlib.h>
#include "opening_sha256.h"
enum {MAX_PARTS=24,VERTEX_BYTES=52};
typedef struct part {uint32_t nv,ni,pc;size_t palette,vertex,index;} part;
typedef struct attr_part {uint32_t pi,nv,stride;size_t attr;} attr_part;
static int reject(char *e,size_t n,const char *s){if(e&&n)snprintf(e,n,"%s",s);return 0;}
static uint32_t u32(const uint8_t *p){return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;}
static int span(size_t *at,size_t size,uint64_t n){if(*at>size||n>size-*at)return 0;*at+=(size_t)n;return 1;}
static float snorm(const uint8_t *p){uint32_t u=(uint32_t)p[0]|(uint32_t)p[1]<<8;int32_t v=u>=32768u?(int32_t)u-65536:(int32_t)u;return v<=-32767?-1.f:(float)v/32767.f;}
static int hexhash(const uint8_t *b,size_t n,const char *hex){uint8_t d[32];unsigned i;sha256(b,n,d);for(i=0;i<32;i++){unsigned v;if(sscanf(hex+2*i,"%2x",&v)!=1||d[i]!=v)return 0;}return 1;}
static int digest(const uint8_t *b,size_t n,const uint8_t *d){uint8_t h[32];sha256(b,n,h);return !memcmp(d,h,32);}
static int pack_parts(const uint8_t *b,size_t n,part out[MAX_PARTS],uint32_t *count){
 uint32_t j,nc,np,nt,i;size_t at=24;
 if(n<24||memcmp(b,"OACHAR01",8))return 0;
 j=u32(b+8);nc=u32(b+12);np=u32(b+16);nt=u32(b+20);
 if(!j||j>128||!nc||nc>30||!np||np>MAX_PARTS||nt>16||!span(&at,n,((j+1u)/2u)*4u))return 0;
 for(i=0;i<nc;i++){uint32_t frames;if(!span(&at,n,8))return 0;frames=u32(b+at-8);if(frames<2||frames>100000||!span(&at,n,(uint64_t)frames*j*28u))return 0;}
 for(i=0;i<nt;i++){uint32_t w,h;if(!span(&at,n,8))return 0;w=u32(b+at-8);h=u32(b+at-4);if(!w||!h||w>4096||h>4096||!span(&at,n,(uint64_t)w*h*4u))return 0;}
 for(i=0;i<np;i++){uint32_t pal;if(!span(&at,n,16))return 0;out[i].nv=u32(b+at-16);out[i].ni=u32(b+at-12);pal=u32(b+at-8);out[i].pc=pal;out[i].palette=at;
  if(!out[i].nv||out[i].nv>1000000||!out[i].ni||out[i].ni>6000000||out[i].ni%3||!pal||pal>96||!span(&at,n,(uint64_t)pal*32u))return 0;
  out[i].vertex=at;if(!span(&at,n,(uint64_t)out[i].nv*VERTEX_BYTES))return 0;out[i].index=at;if(!span(&at,n,(uint64_t)out[i].ni*4u))return 0;}
 *count=np;return at==n;
}
int oa_character_attributes_apply(uint8_t *pack,size_t pn,const uint8_t *b,size_t n,unsigned *changed,char *e,size_t cap){
 static const char PACK[]="ede399d687bcbbc9d1534a208e81a13b9b3785a6f2b52dc25b28f78f36a484a4";
 static const char ATTR[]="ab02a4a4c87996f5ac5584987455e812f6286c87a563b2bbfbca4b635c7635bf";
 part parts[MAX_PARTS];attr_part apply[MAX_PARTS];uint32_t np,nr,i,seen=0;size_t at=64;unsigned count=0;
 if(changed)*changed=0;if(e&&cap)e[0]=0;
 if(!pack||!b||pn!=15030356u||n!=998556u||!hexhash(pack,pn,PACK)||!hexhash(b,n,ATTR))return reject(e,cap,"character attribute source hash/size mismatch");
 if(memcmp(b,"OACAT01",8)||u32(b+8)!=1||u32(b+12)!=17||u32(b+16)!=12||u32(b+20)!=128||u32(b+24)!=64||u32(b+28)||!digest(pack,pn,b+32)||!pack_parts(pack,pn,parts,&np))return reject(e,cap,"character attribute header/base pack rejected");
 nr=u32(b+16);
 for(i=0;i<nr;i++){
  const uint8_t *r,*attrs,*raw;uint32_t pi,stride,nv,ni,flags,v,no,expected;size_t attr_at,raw_at;uint64_t bytes;
  if(!span(&at,n,128))return reject(e,cap,"character attribute record truncated");r=b+at-128;
  pi=u32(r);stride=u32(r+16);nv=u32(r+20);ni=u32(r+24);flags=u32(r+28);
  if(pi>=np||(seen&(1u<<pi))||nv!=parts[pi].nv||ni!=parts[pi].ni)return reject(e,cap,"character attribute part/count mismatch");
  if(stride==56){no=32;expected=15;}else if(stride==60){no=32;expected=47;}else if(stride==64){no=40;expected=31;}else return reject(e,cap,"unreviewed character source layout");
  if(flags!=expected)return reject(e,cap,"character attribute availability mismatch");seen|=1u<<pi;
  bytes=(uint64_t)nv*64u;attr_at=at;if(!span(&at,n,bytes))return reject(e,cap,"character attributes truncated");
  raw_at=at;if(!span(&at,n,(uint64_t)nv*stride))return reject(e,cap,"source character vertices truncated");
  attrs=b+attr_at;raw=b+raw_at;
  if(!digest(pack+parts[pi].vertex,(size_t)nv*52,r+32)||!digest(raw,(size_t)nv*stride,r+64)||!digest(pack+parts[pi].index,(size_t)ni*4,r+96))return reject(e,cap,"character attribute part identity mismatch");
  for(v=0;v<nv;v++){
   const uint8_t *a=attrs+(size_t)v*64,*s=raw+(size_t)v*stride,*old=pack+parts[pi].vertex+(size_t)v*52;float q=0;unsigned k;
   if(u32(a+44)!=flags||u32(a+48)!=v||memcmp(a,s+no,24)||memcmp(a+24,old+24,8)||memcmp(a+52,old,12)||memcmp(old,s,12)||memcmp(old+32,s+12,4))return reject(e,cap,"source character attribute correspondence rejected");
   for(k=0;k<3;k++){float f=snorm(a+k*2);q+=f*f;}if(q<.99f||q>1.01f)return reject(e,cap,"source character normal length rejected");
  }
  apply[i].pi=pi;apply[i].nv=nv;apply[i].stride=stride;apply[i].attr=attr_at;
 }
 if(at!=n)return reject(e,cap,"character attributes trailing bytes");
 /* The full correspondence was checked; this commit cannot fail. Preserve
  * positions, joints, weights, indices, palettes, animation and original files. */
 for(i=0;i<nr;i++){uint32_t v;for(v=0;v<apply[i].nv;v++){float f[3];unsigned k;uint8_t *dst=pack+parts[apply[i].pi].vertex+(size_t)v*52+12;const uint8_t *a=b+apply[i].attr+(size_t)v*64;for(k=0;k<3;k++)f[k]=snorm(a+k*2);{float old[3];memcpy(old,dst,12);if(fabsf(old[0]-f[0])>1e-6f||fabsf(old[1]-f[1])>1e-6f||fabsf(old[2]-f[2])>1e-6f)count++;}memcpy(dst,f,12);}}
 if(changed)*changed=count;return 1;
}

typedef struct palette_patch {uint32_t part,count;size_t source,destination;} palette_patch;
static int palette_prepare(const uint8_t *pack,size_t pn,const uint8_t *b,size_t n,palette_patch patch[2],char *e,size_t cap){
 part parts[MAX_PARTS];uint32_t np,i,seen=0,joints;size_t at=64;
 if(!pack||!b||pn!=15030356u||n!=736u||!hexhash(pack,pn,"ede399d687bcbbc9d1534a208e81a13b9b3785a6f2b52dc25b28f78f36a484a4")||!hexhash(b,n,"6ebc4821b5e2dcfbea1d5bf79fd27754820c57b3a7b73611a31acbbab242b24f"))return reject(e,cap,"character palette source hash/size mismatch");
 if(memcmp(b,"OACPL01",8)||u32(b+8)!=1||u32(b+12)!=17||u32(b+16)!=2||u32(b+20)!=128||u32(b+24)!=32||u32(b+28)||!digest(pack,pn,b+32)||!pack_parts(pack,pn,parts,&np))return reject(e,cap,"character palette header rejected");
 joints=u32(pack+8);
 for(i=0;i<2;i++){
  const uint8_t *r;uint32_t pi,count,capacity,k,v;size_t off;
  if(!span(&at,n,128))return reject(e,cap,"character palette record truncated");r=b+at-128;
  pi=u32(r);count=u32(r+12);capacity=u32(r+16);
  if(pi>=np||(pi!=2&&pi!=5)||(seen&(1u<<pi))||!count||count>capacity||capacity!=parts[pi].pc||u32(r+20)!=parts[pi].nv||u32(r+24)!=parts[pi].ni||u32(r+28))return reject(e,cap,"character palette target mismatch");
  seen|=1u<<pi;off=at;if(!span(&at,n,(uint64_t)count*32u))return reject(e,cap,"character palette payload truncated");
  if(!digest(pack+parts[pi].palette,(size_t)capacity*32,r+32)||!digest(b+off,(size_t)count*32,r+64))return reject(e,cap,"character palette bytes rejected");
  for(k=0;k<count;k++){
   const uint8_t *entry=b+off+k*32;float qt[7],q=0;unsigned z;
   if(u32(entry)>=joints)return reject(e,cap,"character palette joint unavailable");
   memcpy(qt,entry+4,28);for(z=0;z<7;z++)if(!isfinite(qt[z]))return reject(e,cap,"character palette nonfinite");
   for(z=0;z<4;z++)q+=qt[z]*qt[z];if(q<.99f||q>1.01f)return reject(e,cap,"character palette rotation invalid");
  }
  for(v=0;v<parts[pi].nv;v++){
   const uint8_t *vertex=pack+parts[pi].vertex+(size_t)v*52;unsigned z;
   for(z=0;z<4;z++){float weight;memcpy(&weight,vertex+36+z*4,4);if(weight!=0.f&&vertex[32+z]>=count)return reject(e,cap,"active character vertex exceeds authored palette");}
  }
  patch[i].part=pi;patch[i].count=count;patch[i].source=off;patch[i].destination=parts[pi].palette;
 }
 if(at!=n||seen!=((1u<<2)|(1u<<5)))return reject(e,cap,"character palette envelope incomplete");
 return 1;
}
int oa_character_repairs_apply(uint8_t *pack,size_t pn,const uint8_t *attrs,size_t an,const uint8_t *palettes,size_t paln,unsigned *normal_count,unsigned *palette_count,char *e,size_t cap){
 palette_patch patch[2];uint8_t *candidate;unsigned count=0,i;
 if(normal_count)*normal_count=0;if(palette_count)*palette_count=0;
 if(!palette_prepare(pack,pn,palettes,paln,patch,e,cap))return 0;
 candidate=malloc(pn);if(!candidate)return reject(e,cap,"character repair staging allocation failed");memcpy(candidate,pack,pn);
 if(!oa_character_attributes_apply(candidate,pn,attrs,an,&count,e,cap)){free(candidate);return 0;}
 for(i=0;i<2;i++)memcpy(candidate+patch[i].destination,palettes+patch[i].source,(size_t)patch[i].count*32u);
 /* Before parsing/upload, one infallible owner-thread commit. Original asset and
  * animations stay intact; no half normal/palette correction on rejection. */
 memcpy(pack,candidate,pn);free(candidate);if(normal_count)*normal_count=count;if(palette_count)*palette_count=2;return 1;
}
