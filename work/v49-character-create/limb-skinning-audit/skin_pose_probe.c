#include "oa_character.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
static int put(FILE*f,const void*p,size_t n){return fwrite(p,1,n,f)==n;}
int main(int argc,char**argv){
 FILE*f;long n;uint8_t*b;oa_character c;char err[256];uint32_t a,j,casecount=2,ci,frame,pc; uint8_t replacement[2][OA_CHAR_MAX_PALETTE*32];
 if(argc!=3 && argc!=4)return 2;f=fopen(argv[1],"rb");if(!f)return 3;fseek(f,0,SEEK_END);n=ftell(f);rewind(f);
 if(n<=0)return 4;b=(uint8_t*)malloc((size_t)n);if(!b||fread(b,1,(size_t)n,f)!=(size_t)n)return 5;fclose(f);
 if(!oa_character_parse(&c,b,(size_t)n,err,sizeof(err))){fprintf(stderr,"%s",err);free(b);return 6;}
 if(argc==4){
  uint8_t header[64],record[128];uint32_t k;FILE*pf=fopen(argv[3],"rb");if(!pf)return 11;
  if(fread(header,1,64,pf)!=64||memcmp(header,"OACPL01",7))return 12;
  for(k=0;k<2;k++){uint32_t pi,nnew,cap;
   if(fread(record,1,128,pf)!=128)return 13;
   memcpy(&pi,record,4);memcpy(&nnew,record+12,4);memcpy(&cap,record+16,4);
   if(pi>=c.part_count||cap!=c.parts[pi].palette_count||nnew>cap||cap>OA_CHAR_MAX_PALETTE)return 14;
   memcpy(replacement[k],c.parts[pi].palette,cap*32);
   if(fread(replacement[k],32,nnew,pf)!=nnew)return 15;
   c.parts[pi].palette=replacement[k];
  }
  if(fgetc(pf)!=EOF)return 16;fclose(pf);
 }
 f=fopen(argv[2],"wb");if(!f)return 7;
 if(!put(f,"OASKPR1\0",8)||!put(f,&casecount,4)||!put(f,&c.joints,4)||!put(f,&c.part_count,4))return 8;
 for(a=0;a<2;a++){
  ci=a;frame=a?8:0;
  memset(c.weight,0,sizeof(c.weight));memset(c.time,0,sizeof(c.time));c.weight[ci]=1;c.time[ci]=(float)frame/c.clips[ci].fps;c.facing=0;memset(c.feet,0,sizeof(c.feet));c.slope=c.lean=0;
  oa_character_pose(&c);
  if(!put(f,&ci,4)||!put(f,&frame,4)||!put(f,c.world_q,c.joints*16)||!put(f,c.world_t,c.joints*12))return 9;
  for(j=0;j<c.part_count;j++){float rows[OA_CHAR_MAX_PALETTE*12];pc=oa_character_bones(&c,c.parts+j,rows);if(!put(f,&pc,4)||!put(f,rows,pc*48))return 10;}
 }
 fclose(f);oa_character_free(&c);puts("production oa_character_parse/pose/bones PASS idle0 + walk8");return 0;
}
