#include "oa_npc.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
int oa_npcs_parse(oa_npcs *n,const uint8_t *bytes,size_t size,char *error,size_t error_size){
 size_t at=12;uint32_t count,i;memset(n,0,sizeof(*n));
 if(size<12||memcmp(bytes,"OANPCS01",8)){snprintf(error,error_size,"people asset header invalid");return 0;}
 memcpy(&count,bytes+8,4);if(count>OA_NPC_MAX){snprintf(error,error_size,"too many people");return 0;}
 for(i=0;i<count;i++){float place[4];uint32_t length;uint8_t *copy;oa_character *c=n->people+n->count;
  if(size-at<20){snprintf(error,error_size,"people asset truncated");oa_npcs_free(n);return 0;}
  memcpy(place,bytes+at,16);memcpy(&length,bytes+at+16,4);at+=20;
  if(length>size-at){snprintf(error,error_size,"people asset truncated");oa_npcs_free(n);return 0;}
  copy=(uint8_t*)malloc(length);if(!copy){snprintf(error,error_size,"people allocation failed");oa_npcs_free(n);return 0;}
  memcpy(copy,bytes+at,length);at+=length;
  if(!oa_character_parse(c,copy,length,error,error_size)){free(copy);oa_npcs_free(n);return 0;}
  memcpy(c->feet,place,12);c->facing=place[3];
  /* Spread start times so the crowd does not breathe in unison. */
  {const oa_char_clip *k=c->clips;c->time[0]=(float)((i*37u)%(k->frames-1))/k->fps;}
  oa_character_pose(c);n->count++;}
 if(at!=size){snprintf(error,error_size,"people asset has trailing bytes");oa_npcs_free(n);return 0;}
 return 1;
}
void oa_npcs_free(oa_npcs *n){unsigned i;for(i=0;i<n->count;i++)oa_character_free(n->people+i);n->count=0;}
void oa_npcs_update(oa_npcs *n,float dt){unsigned i;for(i=0;i<n->count;i++){oa_character_animate(n->people+i,0,0,dt);oa_character_pose(n->people+i);}}
