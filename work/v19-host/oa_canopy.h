#ifndef OA_CANOPY_H
#define OA_CANOPY_H
#include <stddef.h>
#include <stdint.h>
typedef struct oa_canopy oa_canopy;
/* Source region graph and explicit scene identity; no inferred distance cutoff. */
oa_canopy *oa_canopy_open(const void *bytes,size_t size);
void oa_canopy_close(oa_canopy *c);
int oa_canopy_set_space(oa_canopy *c,uint32_t space);
/* Zero is unknown on save restore; it preserves dense rendering until a portal is crossed. */
void oa_canopy_restore(oa_canopy *c,uint32_t space);
void oa_canopy_move(oa_canopy *c,const float feet[3]);
int oa_canopy_admits(const oa_canopy *c,uint32_t space);
uint32_t oa_canopy_space(const oa_canopy *c);
uint32_t oa_canopy_initial(const oa_canopy *c);
unsigned oa_canopy_admitted(const oa_canopy *c);
#endif
