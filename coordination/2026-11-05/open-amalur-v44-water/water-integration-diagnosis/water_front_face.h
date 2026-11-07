#ifndef OA_WATER_FRONT_FACE_H
#define OA_WATER_FRONT_FACE_H
#include <GLES3/gl3.h>
/* Column-major perspective GL VP. Positive world-mesh orientation is retained
 * by the recovered water meshes. Native reference VP and normal camera_matrix
 * have opposite XY handedness; z-range remapping does not affect this test. */
static GLenum oa_water_front_face(const float vp[16]){
 double ax=vp[0],ay=vp[4],az=vp[8];
 double bx=vp[1],by=vp[5],bz=vp[9];
 double cx=vp[3],cy=vp[7],cz=vp[11];
 double h=(ay*bz-az*by)*cx+(az*bx-ax*bz)*cy+(ax*by-ay*bx)*cz;
 return h>0.0?GL_CW:GL_CCW;
}
#endif
