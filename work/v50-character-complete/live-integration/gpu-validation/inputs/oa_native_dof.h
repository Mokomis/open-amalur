#ifndef OA_NATIVE_DOF_H
#define OA_NATIVE_DOF_H
#include <GLES3/gl3.h>
typedef struct oa_native_dof_params{
 float far_start_world,far_range_world,max_alpha,depth_storage_scale;
}oa_native_dof_params;
typedef struct oa_native_dof{
 int w,h,half_w,half_h,ready;
 GLuint fuzz_tex,effect_tex,fuzz_fbo,effect_fbo,fuzz_program,effect_program,vao,linear_sampler;
}oa_native_dof;
/* Captured near DOF is disabled. This module implements that active path only.
 * Default start9974.3115 (~100m), range20001world units, maxalpha.7.
 * Fixed depth storage1/524288 reproduces native fuzziness G quantization;
 * do NOT substitute current clipFar. All targets RGBA8_UNORM, no dithering. */
/* Debug0 restores formerportphase;1matches captured2x2pointdownsample. */
extern int oa_native_dof_depth_phase;
void oa_native_dof_default_params(oa_native_dof_params *out);
int oa_native_dof_open(oa_native_dof *p,int full_width,int full_height);
void oa_native_dof_close(oa_native_dof *p);
/* Accepts column-major current GL VP or, preferably, pure GL projection to
 * avoid subtracting large eye translations when recovering depthB. */
int oa_native_dof_inverse_depth(float out_inverse[2],const float current_gl_vp[16]);
/* Inputs depth uses hardware0..1 and sceneRGBA8 is the ungraded opaque+
 * transparent scene. Returns effect_tex, RGBA8(fullblurRGB,CoC alpha), or0.
 * Final merge BEFORE LUT: mix(scene.rgb,effect.rgb,effect.a)+bloom*strength.
 * Depth/scene are borrowed. Leaves post state/FBO/bindings changed. */
GLuint oa_native_dof_render(oa_native_dof *p,GLuint scene_rgba8,GLuint depth,
 const float current_gl_vp[16],const oa_native_dof_params *params_or_null);
/* inverse_depth=(1/B,-A/B), where physicalZ=B/(hardwareDepth-A).
 * Explicit current camera values or captured constants avoid VP cancellation;
 * reference inverse=(-.0381861589849,.0381880663335). No GL2*d-1 conversion. */
GLuint oa_native_dof_render_constants(oa_native_dof *p,GLuint scene_rgba8,GLuint depth,
 const float inverse_depth[2],const oa_native_dof_params *params_or_null);
#endif
