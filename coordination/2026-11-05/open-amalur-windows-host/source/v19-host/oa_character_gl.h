#ifndef OA_CHARACTER_GL_H
#define OA_CHARACTER_GL_H
#include "oa_character.h"
#include "room_lighting.h"
#include <GLES3/gl3.h>
typedef struct oa_character_gpu{
 GLuint program,arrays[OA_CHAR_MAX_PARTS],vertex[OA_CHAR_MAX_PARTS],index[OA_CHAR_MAX_PARTS],textures[OA_CHAR_MAX_TEXTURES];
 GLint mvp,bones,has_texture,sampler,alpha_cut;
 opem_room_lighting lights;
 int lights_open,ready,shared;uint32_t next_texture,next_part;
}oa_character_gpu;
int oa_character_gpu_open(oa_character_gpu *g,const oa_character *c,int outdoor);
/* Uses another model's program, and uploads over several frames so a new model never stalls one. */
int oa_character_gpu_share(oa_character_gpu *g,const oa_character_gpu *from);
int oa_character_gpu_share_step(oa_character_gpu *g,const oa_character *c);
void oa_character_gpu_close(oa_character_gpu *g);
void oa_character_gpu_draw(oa_character_gpu *g,const oa_character *c,const float mvp[16],int room_lighting,float alpha_cut);
#endif
