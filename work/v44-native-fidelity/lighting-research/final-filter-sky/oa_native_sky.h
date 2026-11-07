#ifndef OA_NATIVE_SKY_H
#define OA_NATIVE_SKY_H
#include <GLES3/gl3.h>
#include <stdint.h>
#include <android/asset_manager.h>
typedef struct oa_native_sky{int ready,owns_clouds;GLuint program,vao,vbo,ibo,gradient,lower,upper,cloud_sampler,gradient_sampler;}oa_native_sky;
/* Cloud textures are borrowed (not deleted). Correct native identities:
 * lower=710562 (4096² BC3 source), upper=159747 (2048² BC3 source).
 * Existing build_sky.py's lower/upper names are reversed. Pass platform
 * textures decoded/transcoded from those assets with correct mip chains.
 * Optional gradient is32x4RGBA8; NULL uses preserved native325844 asset. */
int oa_native_sky_open(oa_native_sky *p,GLuint lower,GLuint upper,const uint8_t gradient[512]);
int oa_native_sky_open_assets(oa_native_sky *p,AAssetManager *manager,const char *lower_path,const char *upper_path);
void oa_native_sky_close(oa_native_sky *p);
/* params20 is native constantblock float4s4..8:
 * lowerTint, upperTint, transition(0,0,gradientV,time), luminanceFactors,
 * luminanceTint(rgb;wunused). VP is current FULL worldGLVP, no eyecentring.
 * Draw into current sceneFBO, ideally as background before scenegeometry.
 * No LUT or extra fog/horizon blend. DepthLEQUAL/no writes; root restoresstate. */
void oa_native_sky_draw(oa_native_sky *p,const float gl_vp[16],const float params[20]);
void oa_native_sky_bridge_noon_parameters(float params[20],float time);
#endif
