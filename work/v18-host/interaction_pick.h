#ifndef OA_INTERACTION_PICK_H
#define OA_INTERACTION_PICK_H
#include <stdint.h>
/* Authored targeting against actual rendered triangle positions, both sides. */
int oa_mesh_pick(const float *vertices,uint32_t total,uint32_t first,uint32_t count,
 const float eye[3],const float direction[3],float reach,float hit[3],float *distance);
#endif
