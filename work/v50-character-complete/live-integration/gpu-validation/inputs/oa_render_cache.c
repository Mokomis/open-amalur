#include "oa_render_cache.h"
#include <stdint.h>
#include <string.h>
enum{CACHE_CAPACITY=1024,CACHE_NAME_BYTES=64};
typedef struct uniform_entry{GLuint program;GLint location;uint32_t hash;char name[CACHE_NAME_BYTES];}uniform_entry;
static uniform_entry entries[CACHE_CAPACITY];
static oa_render_cache_stats stats;
int oa_render_cache_enabled=1;
void oa_render_cache_reset(void){memset(entries,0,sizeof(entries));memset(&stats,0,sizeof(stats));}
void oa_render_cache_begin_frame(void){memset(&stats,0,sizeof(stats));}
const oa_render_cache_stats *oa_render_cache_get_stats(void){return &stats;}
void oa_render_program_setup(void){stats.program_setups++;}
GLint oa_cached_uniform(GLuint program,const char *name){uint32_t hash=2166136261u;unsigned length=0,i;stats.uniform_requests++;
 if(!oa_render_cache_enabled||!program||!name){stats.uniform_gl_queries++;return glGetUniformLocation(program,name);}
 while(name[length]){hash=(hash^(unsigned char)name[length])*16777619u;if(++length>=CACHE_NAME_BYTES){stats.uniform_gl_queries++;return glGetUniformLocation(program,name);}}
 hash^=program*2654435761u;
 for(i=0;i<CACHE_CAPACITY;i++){uniform_entry *e=entries+((hash+i)&(CACHE_CAPACITY-1));
  if(e->program==program&&e->hash==hash&&!strcmp(e->name,name)){stats.uniform_hits++;return e->location;}
  if(!e->program){GLint location;stats.uniform_gl_queries++;location=glGetUniformLocation(program,name);e->program=program;e->hash=hash;e->location=location;memcpy(e->name,name,length+1);return location;}}
 stats.uniform_gl_queries++;return glGetUniformLocation(program,name);}
void oa_cached_bind_texture(GLuint slots[8],unsigned unit,GLuint texture){stats.texture_requests++;
 if(unit<8&&oa_render_cache_enabled&&slots[unit]==texture){stats.texture_hits++;return;}
 glActiveTexture(GL_TEXTURE0+unit);glBindTexture(GL_TEXTURE_2D,texture);stats.texture_gl_binds++;if(unit<8)slots[unit]=texture;}
