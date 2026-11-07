#ifndef OA_NATIVE_SHADOW_H
#define OA_NATIVE_SHADOW_H
#include <GLES3/gl3.h>
#include "oa_native_shadow_math.h"
typedef struct oa_native_shadow {int resolution,ready;GLuint depth,fbo,resolve,vao;float depth_ab[2];oa_native_shadow_cascade cascade[3];} oa_native_shadow;
int oa_native_shadow_open(oa_native_shadow *p,int resolution);
void oa_native_shadow_close(oa_native_shadow *p);
int oa_native_shadow_update(oa_native_shadow *p,const float gl_vp[16],const float eye[3],const float sun_dir[3],const oa_native_shadow_config *config);
/* For i=2,1,0: begin(i), root draws casters with cascade[i].vp, resolve(i).
 * One reused1024D16 matches capture; caller owns castershaders/materialalpha
 * and culling exceptions. Actual cameraeye preferred; NULL derives it. */
void oa_native_shadow_begin(oa_native_shadow *p,int cascade);
/* AOshadowRGBA8 initialized(AO,1,1,1). WritesGonly alpha-blended, nearest
 * scenedepth + linearLEQUAL shadow. Leaves poststate changed; colourmaskRGBA
 * restored afterward. Inputdepth is not attached (avoids GLfeedback). */
void oa_native_shadow_resolve(oa_native_shadow *p,int cascade,GLuint scene_depth,GLuint ao_shadow_fbo,int width,int height);
#endif
