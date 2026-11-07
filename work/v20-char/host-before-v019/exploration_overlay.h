#ifndef OPEM_EXPLORATION_OVERLAY_H
#define OPEM_EXPLORATION_OVERLAY_H
#include <GLES3/gl3.h>
#include "exploration_input.h"
#include "interaction_state.h"
typedef struct exploration_overlay {GLuint program,buffer,array;GLint screen;float *vertices;unsigned count;} exploration_overlay;
int exploration_overlay_open(exploration_overlay *o);
void exploration_overlay_close(exploration_overlay *o);
void exploration_overlay_draw(exploration_overlay *o,int width,int height,const exploration_input *input,int walking,int collision_ready,const oa_interaction *interaction,int room_lighting);
#endif
