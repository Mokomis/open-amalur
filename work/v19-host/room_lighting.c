#include "room_lighting.h"
#include "oa_scene_profile.h"
static const oa_scene_profile *scene;
void opem_room_lighting_use_scene(const oa_scene_profile *p){scene=p&&p->active?p:0;}
#include <math.h>
#include "room_lights.inc"
#include "room_environment.inc"
#include "town_environment.inc"
static const char identity[]="opem-room-light-data-sha256:" OPEM_ROOM_LIGHT_DATA_SHA256;
const char *opem_room_lighting_identity(void){return identity;}
const float *opem_town_sun(void){return scene?scene->sun_direction:opem_town_sun_direction;}
const float *opem_town_sun_rgb(void){return scene?scene->sun_color:opem_town_sun_color;}
const float *opem_town_shadow_rgba(void){return scene?scene->shadow:opem_town_shadow_color;}
int opem_room_lighting_open(opem_room_lighting *s,GLuint program,int outdoor){
 s->outdoor=outdoor;
 /* Outdoors the color table is applied once, in the final post pass. */
 glUseProgram(program);glUniform1i(glGetUniformLocation(program,"room_no_lut"),outdoor);
 s->mode=glGetUniformLocation(program,"room_mode");s->number=glGetUniformLocation(program,"room_light_count");s->position_inner=glGetUniformLocation(program,"room_position_inner[0]");s->color_outer=glGetUniformLocation(program,"room_color_outer[0]");s->cube_sampler=glGetUniformLocation(program,"room_cube");s->sun_color=glGetUniformLocation(program,"room_sun_color");s->sun_direction=glGetUniformLocation(program,"room_sun_direction");s->shadow_color=glGetUniformLocation(program,"room_shadow_color");
 {unsigned f;glGenTextures(1,&s->cube);glActiveTexture(GL_TEXTURE1);glBindTexture(GL_TEXTURE_CUBE_MAP,s->cube);glPixelStorei(GL_UNPACK_ALIGNMENT,1);for(f=0;f<6;f++){unsigned char face[256];const unsigned char *src=outdoor?(scene?scene->cube+f*256:opem_town_cube[f]):opem_env_cube[f];if(outdoor){unsigned k;/* Active native view7498 is RGBA8, source dump has R/B reversed. */for(k=0;k<256;k+=4){face[k]=src[k+2];face[k+1]=src[k+1];face[k+2]=src[k];face[k+3]=src[k+3];}src=face;}glTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X+f,0,GL_RGBA8,8,8,0,GL_RGBA,GL_UNSIGNED_BYTE,src);}glPixelStorei(GL_UNPACK_ALIGNMENT,4);glTexParameteri(GL_TEXTURE_CUBE_MAP,GL_TEXTURE_MIN_FILTER,GL_LINEAR);glTexParameteri(GL_TEXTURE_CUBE_MAP,GL_TEXTURE_MAG_FILTER,GL_LINEAR);glTexParameteri(GL_TEXTURE_CUBE_MAP,GL_TEXTURE_WRAP_S,GL_CLAMP_TO_EDGE);glTexParameteri(GL_TEXTURE_CUBE_MAP,GL_TEXTURE_WRAP_T,GL_CLAMP_TO_EDGE);glTexParameteri(GL_TEXTURE_CUBE_MAP,GL_TEXTURE_WRAP_R,GL_CLAMP_TO_EDGE);glActiveTexture(GL_TEXTURE2);glGenTextures(1,&s->lut);glBindTexture(GL_TEXTURE_3D,s->lut);glPixelStorei(GL_UNPACK_ALIGNMENT,1);if(outdoor){unsigned char linear_lut[16384];unsigned k;/* Native PS1855 writes decoded sRGB nodes into RGBA8 before interpolation. */for(k=0;k<16384;k++){double x=(scene?scene->lut[k]:opem_town_lut[k])/255.;linear_lut[k]=(k%4==3)?255:(unsigned char)floor((x<=.04045?x/12.92:pow((x+.055)/1.055,2.4))*255.+.5);}glTexImage3D(GL_TEXTURE_3D,0,GL_RGBA8,16,16,16,0,GL_RGBA,GL_UNSIGNED_BYTE,linear_lut);}else glTexImage3D(GL_TEXTURE_3D,0,GL_SRGB8_ALPHA8,16,16,16,0,GL_RGBA,GL_UNSIGNED_BYTE,opem_env_lut);glPixelStorei(GL_UNPACK_ALIGNMENT,4);glTexParameteri(GL_TEXTURE_3D,GL_TEXTURE_MIN_FILTER,GL_LINEAR);glTexParameteri(GL_TEXTURE_3D,GL_TEXTURE_MAG_FILTER,GL_LINEAR);glTexParameteri(GL_TEXTURE_3D,GL_TEXTURE_WRAP_S,GL_CLAMP_TO_EDGE);glTexParameteri(GL_TEXTURE_3D,GL_TEXTURE_WRAP_T,GL_CLAMP_TO_EDGE);glTexParameteri(GL_TEXTURE_3D,GL_TEXTURE_WRAP_R,GL_CLAMP_TO_EDGE);glActiveTexture(GL_TEXTURE0);s->lut_sampler=glGetUniformLocation(program,"room_lut");}
 /* All active samplers need distinct units even when room_mode is zero.
  * The shader's uniform branch does not remove sampler-type validation. */
 glUniform1i(s->cube_sampler,1);glUniform1i(s->lut_sampler,2);
 glUniform1i(glGetUniformLocation(program,"room_shadow_map"),3);
 return s->lut_sampler>=0&&s->lut&&s->mode>=0&&s->number>=0&&s->position_inner>=0&&s->color_outer>=0&&s->cube_sampler>=0&&s->sun_color>=0&&s->sun_direction>=0&&s->shadow_color>=0&&s->cube;
}
void opem_room_lighting_upload(const opem_room_lighting *s,int mode){
 float positions[36*4],colors[36*4];unsigned i,j;glUniform1i(s->mode,!!mode);glUniform1i(s->number,s->outdoor?0:OPEM_ROOM_LIGHT_COUNT);if(!mode)return;
 glActiveTexture(GL_TEXTURE1);glBindTexture(GL_TEXTURE_CUBE_MAP,s->cube);glActiveTexture(GL_TEXTURE2);glBindTexture(GL_TEXTURE_3D,s->lut);glActiveTexture(GL_TEXTURE0);glUniform1i(s->cube_sampler,1);glUniform1i(s->lut_sampler,2);glUniform3fv(s->sun_color,1,s->outdoor?opem_town_sun_rgb():opem_env_sun_color);glUniform3fv(s->sun_direction,1,s->outdoor?opem_town_sun():opem_env_sun_direction);glUniform4fv(s->shadow_color,1,s->outdoor?opem_town_shadow_rgba():opem_env_shadow_color);
 for(i=0;i<OPEM_ROOM_LIGHT_COUNT;i++){const opem_room_light *l=opem_room_lights+i;for(j=0;j<3;j++){positions[i*4+j]=l->position[j];colors[i*4+j]=l->color[j]*l->multiplier;}positions[i*4+3]=l->start;colors[i*4+3]=l->end;}
 glUniform4fv(s->position_inner,OPEM_ROOM_LIGHT_COUNT,positions);glUniform4fv(s->color_outer,OPEM_ROOM_LIGHT_COUNT,colors);
}
void opem_room_lighting_close(opem_room_lighting *s){if(s->cube)glDeleteTextures(1,&s->cube);if(s->lut)glDeleteTextures(1,&s->lut);s->cube=0;s->lut=0;}
