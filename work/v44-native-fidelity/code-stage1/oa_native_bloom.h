#ifndef OA_NATIVE_BLOOM_H
#define OA_NATIVE_BLOOM_H
#include <GLES3/gl3.h>
/* Captured bridge bloom, phases118..133. Scene input must have the native
 * RGBA8_UNORM contract. Other float scene pipelines remain a source mismatch.
 * Call with fullscreen post state: no depth/scissor/cull, full colour mask,
 * no framebuffer sRGB conversion, empty VAO bound. Dither is disabled inside.
 * The module leaves framebuffer/viewport/program/texture0 changed and blending
 * disabled. Caller owns restoring ordinary scene state. */
typedef struct oa_native_bloom {
 int w[4],h[4],ready;
 GLuint tex[7],fbo[7],copy,extract,blur;
} oa_native_bloom;
int oa_native_bloom_open(oa_native_bloom *p,int full_w,int full_h);
void oa_native_bloom_close(oa_native_bloom *p);
/* params are measured exposure,minLum,inverseRange (three floats).
 * Returns reconstructed quarter-size bloom, not already multiplied by merge. */
GLuint oa_native_bloom_render(oa_native_bloom *p,GLuint scene,const float params[3]);
#endif
