#include "oa_geometry_kind1.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
int main(int argc,char**argv){
 if(argc!=3)return 2;unsigned char source[288],expected[288],dest[304];
 FILE*f=fopen(argv[1],"rb");if(!f)return 3;size_t n=fread(source,1,288,f);fclose(f);if(n!=288)return 4;
 f=fopen(argv[2],"rb");if(!f)return 5;n=fread(expected,1,288,f);fclose(f);if(n!=288)return 6;
 oa_guest_span s={0x052a8260,288,source};oa_guest_memory m={&s,1};memset(dest,0xa5,sizeof dest);
 if(!oa_copy_instance_constants(&m,s.base,6,dest+8,288)||memcmp(dest+8,expected,288))return 7;
 for(int i=0;i<8;i++)if(dest[i]!=0xa5||dest[296+i]!=0xa5)return 8;
 unsigned char before[304];memcpy(before,dest,sizeof dest);unsigned checks=0;
 if(oa_copy_instance_constants(&m,s.base,6,dest+8,287)||memcmp(before,dest,sizeof dest))return 9;++checks;
 s.size=287;if(oa_copy_instance_constants(&m,s.base,6,dest+8,288)||memcmp(before,dest,sizeof dest))return 10;s.size=288;++checks;
 if(oa_copy_instance_constants(&m,0xfffffff0u,6,dest+8,288)||memcmp(before,dest,sizeof dest))return 11;++checks;
 if(oa_copy_instance_constants(&m,s.base,0xffffffffu,dest+8,288)||memcmp(before,dest,sizeof dest))return 12;++checks;
 if(oa_copy_instance_constants(&m,s.base+1,6,dest+8,288)||memcmp(before,dest,sizeof dest))return 13;++checks;
 if(oa_copy_instance_constants(&m,s.base,6,NULL,288))return 14;++checks;
 if(!oa_copy_instance_constants(&m,s.base,0,NULL,0))return 15;
 printf("{\"original_cb5_bytes_match\":true,\"record_count\":6,\"bytes\":288,\"boundary_checks\":%u,\"zero_count\":true}\n",checks);return 0;
}
