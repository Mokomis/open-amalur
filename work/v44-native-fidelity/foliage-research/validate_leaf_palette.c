#include "native_foliage_wind.h"
#include <stdio.h>
#include <string.h>
int main(void){float p[12];float e[12]={0x1.8f0ca60000000p-1f,0x1.5f42d80000000p-4f,0x1.fc2e200000000p-1f,0x1.2bc3200000000p-1f,0x1.9294ea0000000p-1f,0x1.d208540000000p-1f,0x1.fb4dd60000000p-1f,0x1.310aac0000000p-1f,0x1.324b900000000p-4f,0x1.8680160000000p-1f,0x0.0p+0f,0x0.0p+0f};oa_native_leaf_palette(305493984u,p);int err=0;for(int i=0;i<12;i++){printf("%d %.9g %.9g %d\n",i,p[i],e[i],memcmp(p+i,e+i,4));err|=memcmp(p+i,e+i,4);}return err!=0;}
