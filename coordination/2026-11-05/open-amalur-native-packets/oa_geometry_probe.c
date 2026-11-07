#include "oa_geometry_sparse.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <inttypes.h>
static uint32_t u32(const unsigned char*p){return (uint32_t)p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24);}
typedef struct {uint32_t fields[14];unsigned sequence[8],calls;} observation;
static void vertices(void*ctx,const uint32_t b[2],const uint32_t s[2],const uint32_t o[2]){observation*p=ctx;memcpy(p->fields,b,8);memcpy(p->fields+2,s,8);memcpy(p->fields+4,o,8);p->sequence[p->calls++]=1;}
static void topology(void*ctx,uint32_t n){observation*p=ctx;p->fields[6]=n;p->sequence[p->calls++]=2;}
static void indices(void*ctx,uint32_t b,uint32_t f,uint32_t o){observation*p=ctx;p->fields[7]=b;p->fields[8]=f;p->fields[13]=o;p->sequence[p->calls++]=3;}
static void indexed(void*ctx,uint32_t n,uint32_t f,int32_t b){observation*p=ctx;p->fields[9]=n;p->fields[10]=1;p->fields[11]=f;p->fields[12]=(uint32_t)b;p->sequence[p->calls++]=4;}
static void draw(void*ctx,uint32_t n,uint32_t f){observation*p=ctx;p->fields[9]=n;p->fields[11]=f;p->sequence[p->calls++]=5;}
int main(int argc,char**argv){
 if(argc!=2)return 2;FILE*f=fopen(argv[1],"rb");if(!f)return 3;fseek(f,0,SEEK_END);long n=ftell(f);rewind(f);if(n<80||n>1048576){fclose(f);return 4;}unsigned char*data=malloc((size_t)n);if(!data){fclose(f);return 5;}if(fread(data,1,(size_t)n,f)!=(size_t)n){fclose(f);free(data);return 6;}fclose(f);
 uint32_t h[20];for(unsigned i=0;i<20;++i)h[i]=u32(data+i*4);if(h[0]!=0x5053414f||h[1]!=1||h[2]!=6)return 7;
 oa_guest_span spans[8];size_t pos=80;
 for(unsigned i=0;i<h[2];++i){if(pos+8>(size_t)n)return 8;spans[i].base=u32(data+pos);spans[i].size=u32(data+pos+4);pos+=8;if(spans[i].size>(size_t)n-pos)return 9;spans[i].bytes=data+pos;pos+=spans[i].size;}if(pos!=(size_t)n)return 10;
 oa_guest_memory memory={spans,h[2]};oa_geometry0 geometry;
 if(!oa_decode_geometry0_sparse(&memory,h[3],h[4],h[5],&geometry))return 11;
 observation got={0};oa_draw_backend backend={&got,vertices,topology,indices,indexed,draw};
 if(!oa_submit_geometry0(&geometry,&backend))return 12;
 if(memcmp(got.fields,h+6,14*sizeof(uint32_t))){for(unsigned i=0;i<14;++i)if(got.fields[i]!=h[6+i])fprintf(stderr,"field%u actual%"PRIu32" expected%"PRIu32"\n",i,got.fields[i],h[6+i]);return 13;}
 const unsigned sequence[4]={1,2,3,4};if(got.calls!=4||memcmp(sequence,got.sequence,sizeof(sequence)))return 14;
 oa_geometry0 untouched,invalid;memset(&untouched,0xa5,sizeof(untouched));invalid=untouched;
 uint32_t geometry_address=u32(spans[0].bytes+0x2c);unsigned gi=0;while(gi<h[2]&&spans[gi].base!=geometry_address)++gi;if(gi==h[2])return 19;
 size_t original=spans[gi].size;spans[gi].size=original-1;if(oa_decode_geometry0_sparse(&memory,h[3],h[4],h[5],&invalid)||memcmp(&invalid,&untouched,sizeof(invalid)))return 15;spans[gi].size=original;
 spans[6]=spans[0];memory.count=7;if(oa_guest_memory_valid(&memory))return 16;
 spans[6].base=UINT32_MAX;spans[6].size=8;if(oa_guest_memory_valid(&memory))return 17;
 memory.count=5;if(oa_decode_geometry0_sparse(&memory,h[3],h[4],h[5],&invalid))return 18;
 printf("{\"native_packet_match\":true,\"draw_count\":%"PRIu32",\"vb\":[\"0x%08"PRIx32"\",\"0x%08"PRIx32"\"],\"strides\":[%"PRIu32",%"PRIu32"],\"index_format\":%"PRIu32",\"topology\":%"PRIu32",\"fixture_bytes\":%ld,\"negative_checks\":4}\n",geometry.count,geometry.vb[0],geometry.vb[1],geometry.stride[0],geometry.stride[1],geometry.index_format,geometry.topology,n);free(data);return 0;
}
