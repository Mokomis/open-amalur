#include "oa_packet_builder.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static uint32_t u32(const unsigned char*p){return (uint32_t)p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24);}
int main(int argc,char**argv){
 if(argc!=2)return 2;FILE*f=fopen(argv[1],"rb");if(!f)return 3;fseek(f,0,SEEK_END);long n=ftell(f);rewind(f);if(n<100||n>1048576)return 4;unsigned char*data=malloc((size_t)n);if(!data)return 5;if(fread(data,1,(size_t)n,f)!=(size_t)n)return 6;fclose(f);
 uint32_t h[25];for(unsigned k=0;k<25;k++)h[k]=u32(data+k*4);if(h[0]!=0x5042414f||h[1]!=1||h[2]!=7)return 7;
 oa_guest_span spans[7];size_t pos=100;for(unsigned k=0;k<7;k++){if(pos+8>(size_t)n)return 8;spans[k].base=u32(data+pos);spans[k].size=u32(data+pos+4);pos+=8;if(spans[k].size>(size_t)n-pos)return 9;spans[k].bytes=data+pos;pos+=spans[k].size;}if(pos!=(size_t)n)return 10;
 oa_guest_memory m={spans,7};oa_packet_inputs i;memcpy(&i,h+3,sizeof i);uint32_t out[14];if(!oa_build_skinned_packet(&m,&i,out))return 11;
 if(memcmp(out,h+11,sizeof out)){for(unsigned k=0;k<14;k++)if(out[k]!=h[11+k])fprintf(stderr,"word%u got%08x expected%08x\n",k,out[k],h[11+k]);return 12;}
 uint32_t old[14];memcpy(old,out,sizeof out);m.count=6;if(oa_build_skinned_packet(&m,&i,out)||memcmp(out,old,sizeof out))return 13;m.count=7;
 i.pass=4;if(oa_build_skinned_packet(&m,&i,out)||memcmp(out,old,sizeof out))return 14;i.pass=h[9];i.material=0;if(oa_build_skinned_packet(&m,&i,out)||memcmp(out,old,sizeof out))return 15;
 printf("{\"original_packet_match\":true,\"matched_bytes\":56,\"kind\":%u,\"palette_count\":%u,\"geometry\":\"0x%08x\",\"negative_checks\":3}\n",out[0],out[13],out[11]);free(data);return 0;
}
