/* Loads the packaged character asset and checks body proportions through all clips. */
#include "oa_character.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(x) do{if(!(x)){printf("FAILED line %d: %s\n",__LINE__,#x);return 1;}checks++;}while(0)
int main(int argc,char **argv){
 oa_character c;char error[128];FILE *f;long n;uint8_t *b,*bad;int checks=0;uint32_t i,k;
 if(argc!=2)return 2;f=fopen(argv[1],"rb");if(!f)return 2;fseek(f,0,SEEK_END);n=ftell(f);rewind(f);b=(uint8_t*)malloc((size_t)n);if(fread(b,1,(size_t)n,f)!=(size_t)n)return 2;fclose(f);
 /* Every truncation must be refused without reading past the end. */
 for(k=0;k<400;k++){size_t cut=(size_t)((uint64_t)n*k/400);bad=(uint8_t*)malloc(cut+1);memcpy(bad,b,cut);CHECK(!oa_character_parse(&c,bad,cut,error,sizeof(error)));free(bad);}
 CHECK(oa_character_parse(&c,b,(size_t)n,error,sizeof(error)));CHECK(c.joints==64&&c.clip_count==3&&c.part_count>=4);
 for(i=0;i<3;i++){memset(c.weight,0,sizeof(c.weight));c.weight[i]=1;
  for(k=0;k<c.clips[i].frames-1;k+=3){float head,toe_l,toe_r;c.time[i]=(float)k/c.clips[i].fps;oa_character_pose(&c);
   head=c.world_t[21][2];toe_l=c.world_t[6][2];toe_r=c.world_t[12][2];
   CHECK(head>130&&head<195);CHECK(toe_l>-25&&toe_l<80);CHECK(toe_r>-25&&toe_r<80);}}
 memset(c.time,0,sizeof(c.time));memset(c.weight,0,sizeof(c.weight));c.weight[0]=1;c.feet[0]=100;c.feet[1]=-50;c.feet[2]=7;
 for(k=0;k<300;k++){oa_character_animate(&c,k<100?0.f:k<200?.3f:1.f,k<100?0.f:k<200?120.f:420.f,1/60.f);oa_character_pose(&c);
  CHECK(fabsf(c.weight[0]+c.weight[1]+c.weight[2]-1)<.001f);}
 CHECK(c.weight[OA_CLIP_RUN]>.99f);
 {float rows[OA_CHAR_MAX_PALETTE*12];for(i=0;i<c.part_count;i++){uint32_t m=oa_character_bones(&c,c.parts+i,rows),e;CHECK(m==c.parts[i].palette_count);
   for(e=0;e<m;e++){const float *r=rows+e*12;CHECK(fabsf(r[0]*r[0]+r[1]*r[1]+r[2]*r[2]-1)<.01f);CHECK(fabsf(r[3]-100)<220&&fabsf(r[7]+50)<220&&r[11]>-240&&r[11]<400);}}}
 oa_character_free(&c);printf("character-test: %d checks passed\n",checks);return 0;
}
