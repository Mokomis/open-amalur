#ifndef OA_NATIVE_AO_H
#define OA_NATIVE_AO_H
#include <GLES3/gl3.h>
typedef struct oa_native_ao {int w,h,ready;GLuint tex[3],fbo[3],ao,blur,vao;} oa_native_ao;
int oa_native_ao_open(oa_native_ao *p,int width,int height);
void oa_native_ao_close(oa_native_ao *p);
/* Input depth must have dimensionsw,h and stored GLhardware0..1 perspective
 * depth. Output finalRGBA8 has AO inR and yzw1. Full native/current extent.
 * Leaves framebuffer,viewport,program,VAO,textures changed, depth/blend/cull/
 * scissor/dither disabled. Parent must bind ordinary scene state afterward.
 * Depth-only prepass is sufficient; geometric normals are derived from depth.
 */
GLuint oa_native_ao_render(oa_native_ao *p,GLuint depth,const float gl_vp[16]);
/* Explicit reference/dynamic parameter path. Block layout is ao-constants.json;
 * depthCut is hardwaredepth at6000worldunits. Does not own or change inputdepth.
 */
GLuint oa_native_ao_render_constants(oa_native_ao *p,GLuint depth,const float block[32],float depth_cut);
#endif
