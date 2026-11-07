#ifndef OPEM_ROOM_LIGHTING_H
#define OPEM_ROOM_LIGHTING_H
#include <GLES3/gl3.h>
typedef struct opem_room_light {float position[3],color[3],multiplier,start,end;} opem_room_light;
typedef struct opem_room_lighting {GLint mode,number,position_inner,color_outer;} opem_room_lighting;
int opem_room_lighting_open(opem_room_lighting *,GLuint program);
void opem_room_lighting_upload(const opem_room_lighting *,int room_mode);
const char *opem_room_lighting_identity(void);
#endif
