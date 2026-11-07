#include "room_lighting.h"
#include "room_lights.inc"
static const char identity[]="opem-room-light-data-sha256:" OPEM_ROOM_LIGHT_DATA_SHA256;
const char *opem_room_lighting_identity(void){return identity;}
int opem_room_lighting_open(opem_room_lighting *s,GLuint program){
 s->mode=glGetUniformLocation(program,"room_mode");s->number=glGetUniformLocation(program,"room_light_count");s->position_inner=glGetUniformLocation(program,"room_position_inner[0]");s->color_outer=glGetUniformLocation(program,"room_color_outer[0]");return s->mode>=0&&s->number>=0&&s->position_inner>=0&&s->color_outer>=0;
}
void opem_room_lighting_upload(const opem_room_lighting *s,int mode){
 float positions[36*4],colors[36*4];unsigned i,j;glUniform1i(s->mode,!!mode);glUniform1i(s->number,OPEM_ROOM_LIGHT_COUNT);if(!mode)return;
 for(i=0;i<OPEM_ROOM_LIGHT_COUNT;i++){const opem_room_light *l=opem_room_lights+i;for(j=0;j<3;j++){positions[i*4+j]=l->position[j];colors[i*4+j]=l->color[j]*l->multiplier;}positions[i*4+3]=l->start;colors[i*4+3]=l->end;}
 glUniform4fv(s->position_inner,OPEM_ROOM_LIGHT_COUNT,positions);glUniform4fv(s->color_outer,OPEM_ROOM_LIGHT_COUNT,colors);
}
