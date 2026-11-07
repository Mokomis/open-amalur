#include "oa_appearance.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
int main(int argc,char**argv){FILE*f,*list;char path[4096];unsigned models=0,surfaces=0,unsupported=0,maxb=0,maxp=0; 
 if(argc!=2)return 2;list=fopen(argv[1],"r");if(!list)return 3;
 while(fgets(path,sizeof(path),list)){unsigned char*buf;long len;oa_am_model m;oa_am_chunk b;float*world;unsigned i;size_t n;
  path[strcspn(path,"\r\n")]=0;f=fopen(path,"rb");if(!f)return 4;fseek(f,0,SEEK_END);len=ftell(f);fseek(f,0,SEEK_SET);buf=malloc(len);if(!buf)return 5;
  n=fread(buf,1,len,f);fclose(f);if(n!=(size_t)len||!oa_am_open(&m,buf,len))return 6;
  if(oa_am_open(&m,buf,len-1))return 7;if(!oa_am_open(&m,buf,len))return 8;
  oa_am_find(&m,"BONE",&b);if(b.count>maxb)maxb=b.count;
  world=malloc((b.count?b.count:1)*12*sizeof(float));if(!world)return 9;
  if(!oa_am_rest_world(&m,world,b.count*12))return 10;
  for(i=0;i<oa_am_surface_count(&m);i++){oa_am_surface s;float pal[8192*12];unsigned k;
   if(!oa_am_surface_get(&m,i,&s)){unsupported++;continue;}
   if(s.palette_count>maxp)maxp=s.palette_count;
   if(!oa_am_palette(&m,i,world,b.count,NULL,pal,sizeof(pal)/sizeof(float)))return 11;
   for(k=0;k<s.palette_count*12;k++)if(!isfinite(pal[k]))return 12;
   for(k=0;k<s.vertex_count;k++){const unsigned char*v=(const unsigned char*)s.vertices96+k*96;float weights[3];unsigned z;memcpy(weights,v+16,12);
    if(s.weighted)for(z=0;z<4;z++){float w=z==3?1-weights[0]-weights[1]-weights[2]:weights[z];if(w!=0&&v[12+z]>=s.palette_count)return 13;}
   }surfaces++;
  }
  free(world);free(buf);models++;
 }
 fclose(list);printf("{\"models\":%u,\"supported_surfaces\":%u,\"unsupported_surfaces\":%u,\"max_bones\":%u,\"max_palette\":%u}\n",models,surfaces,unsupported,maxb,maxp);return 0;
}