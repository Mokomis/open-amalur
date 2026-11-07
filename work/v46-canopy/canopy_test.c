#include "oa_canopy.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
static uint32_t u(const unsigned char*p){uint32_t v;memcpy(&v,p,4);return v;}
int main(int argc,char**argv){FILE*f;long size;unsigned char*b,*m;oa_canopy*c;unsigned i,j,n,e,tests=0;assert(argc==2);f=fopen(argv[1],"rb");assert(f);assert(!fseek(f,0,SEEK_END));size=ftell(f);rewind(f);b=malloc((size_t)size);m=malloc((size_t)size);assert(fread(b,(size_t)size,1,f)==1);fclose(f);
 c=oa_canopy_open(b,(size_t)size);assert(c);assert(oa_canopy_space(c)==431638);assert(oa_canopy_admits(c,431638));assert(oa_canopy_set_space(c,431646));assert(oa_canopy_admitted(c)==2);assert(oa_canopy_admits(c,0));assert(oa_canopy_admits(c,431646));assert(oa_canopy_admits(c,431650));assert(!oa_canopy_admits(c,431642));assert(!oa_canopy_admits(c,431638));assert(!oa_canopy_admits(c,999999));tests+=10;
 n=u(b+8);e=u(b+12);
 for(i=0;i<e;i++){const unsigned char*r=b+32+n*4+i*60;float center[3],normal[3],right[3],a[3],z[3];uint32_t idA=u(r),idB=u(r+4);memcpy(center,r+12,12);memcpy(normal,r+24,12);memcpy(right,r+36,12);
  for(j=0;j<3;j++){a[j]=center[j]+100*normal[j];z[j]=center[j]-100*normal[j];}
  assert(oa_canopy_set_space(c,idA));oa_canopy_move(c,a);oa_canopy_move(c,z);assert(oa_canopy_space(c)==idB);assert(oa_canopy_admits(c,idA));tests+=2;
  oa_canopy_restore(c,0);assert(oa_canopy_space(c)==0);assert(oa_canopy_admits(c,431642));oa_canopy_move(c,a);oa_canopy_move(c,z);assert(oa_canopy_space(c)==idB);tests+=3;
  assert(oa_canopy_set_space(c,idB));oa_canopy_move(c,z);oa_canopy_move(c,a);assert(oa_canopy_space(c)==idA);tests++;
  for(j=0;j<3;j++){a[j]+=right[j]*3;z[j]+=right[j]*3;}
  assert(oa_canopy_set_space(c,idA));oa_canopy_move(c,a);oa_canopy_move(c,z);assert(oa_canopy_space(c)==idA);tests++;
 }
 assert(!oa_canopy_set_space(c,999999));assert(oa_canopy_set_space(c,0));assert(oa_canopy_space(c)==431638);oa_canopy_close(c);tests+=3;
 for(i=0;i<(unsigned)size;i++)assert(!oa_canopy_open(b,i));tests+=(unsigned)size;
 memcpy(m,b,(size_t)size);m[0]^=1;assert(!oa_canopy_open(m,(size_t)size));tests++;
 /* Deterministic parser fuzz: legal mutations may open, but must remain memory safe. */
 for(i=0;i<10000;i++){uint32_t x=i*1664525u+1013904223u;float feet[3]={0,0,0};memcpy(m,b,(size_t)size);m[x%(uint32_t)size]^=(unsigned char)(1u<<(i%8));c=oa_canopy_open(m,(size_t)size);if(c){oa_canopy_move(c,feet);feet[0]=3000;oa_canopy_move(c,feet);oa_canopy_close(c);}}tests+=10000;
 assert(oa_canopy_admits(NULL,431642));free(m);free(b);printf("PASS real-source graph, live bridge membership, %u portals both directions/finite bounds, truncation and 10000 parser mutations; %u checks\n",e,tests);return 0;}
