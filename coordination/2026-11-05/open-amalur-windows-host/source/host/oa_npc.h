#ifndef OA_NPC_H
#define OA_NPC_H
/* Townspeople placed from their object records. Standing idle only; no behaviour yet. */
#include "oa_character.h"
enum{OA_NPC_MAX=16};
typedef struct oa_npcs{unsigned count;oa_character people[OA_NPC_MAX];}oa_npcs;
/* Copies what it needs; bytes remain owned by the caller. */
int oa_npcs_parse(oa_npcs *n,const uint8_t *bytes,size_t size,char *error,size_t error_size);
void oa_npcs_free(oa_npcs *n);
void oa_npcs_update(oa_npcs *n,float dt);
#endif
