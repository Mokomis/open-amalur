#include "oa_packet_builder.h"
#include <string.h>
#define R(a,o,v) oa_guest_read_u32(m,(a),(o),&(v))
int oa_build_skinned_packet(const oa_guest_memory*m,const oa_packet_inputs*i,uint32_t out[14]){
 uint32_t count,owner_flags,props,prop_flags,class_flags,layout,material_flags,object_data,p[14]={0};
 if(!i||!out||!i->material||i->pass>3||!oa_guest_memory_valid(m)||!R(i->owner,0x34,count)||!count||count>INT32_MAX||
 !R(i->owner,0x78,owner_flags)||!R(i->properties,0xc,props)||!R(i->properties,0x14,prop_flags)||
 !R(i->class_flags_address,0,class_flags)||!R(i->material,0x14,layout)||!R(layout,0x48,material_flags)||!R(i->properties,4,object_data))return 0;
 uint32_t index=1+((class_flags>>1)&1u)*2+i->pass*4;
 uint32_t face=(prop_flags>>16)&255;
 if(owner_flags&1u){if(face==1)face=2;else if(face==2)face=1;else face=0;}
 p[0]=1;p[1]=(((props>>(i->pass*8))&0x3fu)|(face<<6))<<24;
 p[2]=i->material;p[4]=object_data;p[8]=i->constant_block;p[11]=i->geometry;p[13]=count;
 if(!R(i->bindings,8+index*8,p[3])||!R(i->bindings,0x128+index*8,p[5])||!R(i->owner,0x30,p[12]))return 0;
 if((material_flags&4u)&&!R(i->owner,0x54,p[6]))return 0;
 memcpy(out,p,sizeof p);return 1;
}
#undef R
