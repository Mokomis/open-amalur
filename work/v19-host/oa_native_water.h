#ifndef OA_NATIVE_WATER_H
#define OA_NATIVE_WATER_H
#include <android/asset_manager.h>
#include <GLES3/gl3.h>
typedef struct { void *state; } oa_native_water;
typedef struct {
 GLuint ambient_cube;
 float sun_direction[3],sun_color[3],shadow_color[3];
 float water_fog[3]; /* depthScale, opacityScale, enabled; bridge 80,.01,1 */
} oa_native_water_environment;
/* Initialize owner to {0}. Asset path is water-native.bin relative to asset root. */
int oa_native_water_open(oa_native_water*,AAssetManager*,const char*);
void oa_native_water_gpu_close(oa_native_water*); /* retain CPU pack for surface loss */
void oa_native_water_close(oa_native_water*);
int oa_native_water_draw(oa_native_water*,const float vp[16],const float eye[3],GLuint opaque_color,GLuint opaque_depth,const float inv_depth[2],float time,const oa_native_water_environment*);
/* Conservative instance bounding-box selection; intended for generation, not whole-batch hiding. */
int oa_native_water_contains(const oa_native_water*,unsigned material,const float position[3],float tolerance);
#endif
