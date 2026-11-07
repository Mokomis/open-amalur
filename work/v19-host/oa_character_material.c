#include "oa_character_material.h"
#include "oa_post.h"
#include "oa_render_cache.h"
#include <math.h>
static const char rigid_vertex[]=
"#version 300 es\n"
"layout(location=0)in vec3 p;layout(location=1)in vec4 n;layout(location=2)in vec4 vertex_color;layout(location=3)in vec2 t;layout(location=4)in vec3 tangent;layout(location=5)in vec3 bitangent;layout(location=6)in vec2 uv_second;"
"uniform mat4 mvp;uniform vec2 fog;out vec3 W;out highp vec3 N0;out vec2 UV;out highp float F;out highp float VA;out highp vec4 VC;out highp vec3 TW,BW;out vec2 UV2;flat out highp uint PW;"
"void main(){W=p;N0=normalize(n.xyz);TW=normalize(tangent);BW=normalize(bitangent);VC=vertex_color;VA=vertex_color.a;UV=t;UV2=uv_second;PW=0u;gl_Position=mvp*vec4(p,1.);F=1.-min(exp(-(fog.x*gl_Position.w+fog.y)),1.);}";
GLuint oa_character_rigid_material_program(unsigned lights){return oa_world_program_with_vertex(rigid_vertex,0,lights);}
int oa_character_hardlight_upload(GLuint p,const oa_character_hardlight *m){
 unsigned i,j;const float *value[4];if(!p||!m)return 0;value[0]=m->constant;value[1]=m->specular;value[2]=m->extra;value[3]=m->fresnel;for(i=0;i<4;i++)for(j=0;j<4;j++)if(!isfinite(value[i][j]))return 0;if(m->specular[1]<0.f||m->fresnel[1]<0.f)return 0;
 glUseProgram(p);glUniform1i(oa_cached_uniform(p,"material_family"),12);
 glUniform4fv(oa_cached_uniform(p,"material_color"),1,m->constant);
 glUniform4f(oa_cached_uniform(p,"material_specular"),m->specular[0],m->specular[1],m->extra[0],m->fresnel[0]);
 glUniform4f(oa_cached_uniform(p,"material_tiling"),1,1,m->fresnel[1],0);return 1;
}
