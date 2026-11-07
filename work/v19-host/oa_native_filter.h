#ifndef OA_NATIVE_FILTER_H
#define OA_NATIVE_FILTER_H
#include <GLES3/gl3.h>
typedef struct oa_native_filter{int w,h,ready;GLuint tex,fbo,program,vao,sampler;}oa_native_filter;
int oa_native_filter_open(oa_native_filter *p,int source_width,int source_height);
void oa_native_filter_close(oa_native_filter *p);
/* Bind p.fbo as the final scene+bloom+LUT destination, RGBA8.
 * Its shader MUST output alpha=dot(gradedRGB,(.299,.587,.114)).
 * Source alpha is luminance, not opacity. The native filter outputs alpha1.
 * draw accepts source0 to use p.tex, or another RGBA8/luma-alpha source.
 * For captured1:1 behavior output dimensions equal source dimensions.
 * Leaves ordinary post state/bindings changed; root restores scene state. */
void oa_native_filter_begin(oa_native_filter *p);
void oa_native_filter_draw(oa_native_filter *p,GLuint source,GLuint target_fbo,int output_width,int output_height);
#endif
