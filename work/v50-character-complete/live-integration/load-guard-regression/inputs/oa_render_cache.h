#ifndef OA_RENDER_CACHE_H
#define OA_RENDER_CACHE_H
#include <GLES3/gl3.h>
typedef struct oa_render_cache_stats{unsigned uniform_requests,uniform_gl_queries,uniform_hits,texture_requests,texture_gl_binds,texture_hits,program_setups;}oa_render_cache_stats;
/* Render-thread only. Reset after graphics-context teardown/recreation. */
extern int oa_render_cache_enabled;
void oa_render_cache_reset(void);
void oa_render_cache_begin_frame(void);
const oa_render_cache_stats *oa_render_cache_get_stats(void);
GLint oa_cached_uniform(GLuint program,const char *name);
void oa_cached_bind_texture(GLuint slots[8],unsigned unit,GLuint texture);
void oa_render_program_setup(void);
#endif
