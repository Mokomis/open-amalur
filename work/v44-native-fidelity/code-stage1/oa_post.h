#ifndef OA_POST_H
#define OA_POST_H
/* Outdoor material shader, bloom, ambient occlusion, color grading and an effects load. */
#include <GLES3/gl3.h>
#include "oa_native_bloom.h"
#include "oa_native_ao.h"
typedef struct oa_post{oa_native_bloom native_bloom;oa_native_ao native_ao;GLuint ao_current,opaque_color,opaque_depth,opaque_fbo;int w,h,ready,native_mode;GLuint scene_tex,depth_tex,scene_fbo,bloom_tex[2],bloom_fbo[2],ao_tex,ao_fbo,bright,blur,ao,final,empty,fx,fx_vao,fx_vbo,fx_tex;float *fx_cpu;}oa_post;
typedef struct oa_lightgrid{GLuint tex,ubo;float origin[2],scale;int width,height;unsigned references,dropped;}oa_lightgrid;
GLuint oa_world_program(int variant,unsigned lights);
int oa_lightgrid_open(oa_lightgrid *g,const float (*lights)[8],unsigned count);
void oa_lightgrid_close(oa_lightgrid *g);
GLuint oa_post_program(const char *vertex,const char *fragment);
int oa_post_open(oa_post *p,int width,int height);
void oa_post_close(oa_post *p);
void oa_post_begin(oa_post *p);
GLuint oa_post_make_ao(oa_post *p,const float vp[16]);
int oa_post_snapshot(oa_post *p);
void oa_post_end(oa_post *p,GLuint lut,float bloom,float cut,float near_plane,float far_plane,int use_ao,int use_bloom,int width,int height,const float native_post[4]);
void oa_post_fx(oa_post *p,const float mvp[16],const float eye[3],const float center[3],int count,float seconds);
#endif
