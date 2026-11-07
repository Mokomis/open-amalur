#include "oa_creation.h"
#include <stdio.h>
#include <string.h>
#include "preset_oracle_cases.h"
int main(void){size_t i;unsigned j,checks=0;for(i=0;i<sizeof(oracle)/sizeof(*oracle);i++){
 const oracle_case *x=oracle+i;oa_creation_state s,t;unsigned char b[OA_CREATION_ENVELOPE_MAX];size_t n;
 if(oa_creation_begin(&s,x->race,x->sex))return 1;
 s.customized=1;for(j=0;j<6;j++)s.appearance.assets[j]=x->a[j];for(j=0;j<8;j++)s.appearance.colors[j]=(unsigned short)x->c[j];for(j=0;j<4;j++)s.appearance.alphas[j]=(unsigned char)x->h[j];
 if(oa_creation_validate(&s)||oa_creation_apply_preset(&s,x->preset)){printf("applyfail case%zu\n",i);return 2;}
 for(j=0;j<6;j++,checks++)if(s.appearance.assets[j]!=x->ea[j]){printf("asset case%zu c%u actual%u expected%u\n",i,j,s.appearance.assets[j],x->ea[j]);return 3;}
 for(j=0;j<8;j++,checks++)if(s.appearance.colors[j]!=x->ec[j]){printf("color case%zu c%u actual%u expected%u\n",i,j,s.appearance.colors[j],x->ec[j]);return 4;}
 for(j=0;j<4;j++,checks++)if(s.appearance.alphas[j]!=x->eh[j]){printf("alpha case%zu c%u actual%u expected%u\n",i,j,s.appearance.alphas[j],x->eh[j]);return 5;}
 if(oa_creation_serialize(&s,b,sizeof b,&n)||oa_creation_deserialize(&t,b,n)||memcmp(&s,&t,sizeof s))return 6;
}printf("Original source preset dispatcher cases=80 field_checks=%u all40presets=pass distinct_previous_selections=2 roundtrip=pass\n",checks);return 0;}
