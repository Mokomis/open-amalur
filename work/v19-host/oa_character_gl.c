#include "oa_character_gl.h"
#include "room_lighting_shader.h"
#include <android/log.h>
#include <stdint.h>
#include <string.h>
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR,"OpemAmalurScene",__VA_ARGS__)
static const char *vertex_source=
 "#version 300 es\nlayout(location=0) in vec3 p;layout(location=1) in vec3 n_in;layout(location=2) in vec2 texcoord;layout(location=3) in uvec4 j;layout(location=4) in vec4 w;"
 "uniform mat4 mvp;uniform vec4 bones[288];out vec3 normal;out vec3 color;out vec2 uv;out vec3 world_position;"
 "void main(){vec4 P=vec4(p,1.0);vec3 s=vec3(0.0),m=vec3(0.0);for(int i=0;i<4;i++){int b=int(j[i])*3;vec4 r0=bones[b],r1=bones[b+1],r2=bones[b+2];"
 "s+=w[i]*vec3(dot(r0,P),dot(r1,P),dot(r2,P));m+=w[i]*vec3(dot(r0.xyz,n_in),dot(r1.xyz,n_in),dot(r2.xyz,n_in));}"
 "world_position=s;gl_Position=mvp*vec4(s,1.0);normal=m;color=vec3(0.8);uv=texcoord;}";
static GLuint compile(GLenum type,const char *source){GLint okay=0;GLuint s=glCreateShader(type);glShaderSource(s,1,&source,NULL);glCompileShader(s);glGetShaderiv(s,GL_COMPILE_STATUS,&okay);
 if(!okay){char log[1024];GLsizei n=0;glGetShaderInfoLog(s,sizeof(log)-1,&n,log);log[n]=0;LOGE("Character shader: %s",log);glDeleteShader(s);return 0;}return s;}
static void upload_texture(oa_character_gpu *g,const oa_character *c,uint32_t i){const oa_char_texture *t=c->textures+i;glGenTextures(1,&g->textures[i]);glBindTexture(GL_TEXTURE_2D,g->textures[i]);glPixelStorei(GL_UNPACK_ALIGNMENT,1);
  glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA8,(GLsizei)t->width,(GLsizei)t->height,0,GL_RGBA,GL_UNSIGNED_BYTE,t->rgba);glGenerateMipmap(GL_TEXTURE_2D);
  glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_LINEAR_MIPMAP_LINEAR);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_LINEAR);}
static void upload_part(oa_character_gpu *g,const oa_character *c,uint32_t i){const oa_char_part *p=c->parts+i;
  glGenVertexArrays(1,&g->arrays[i]);glBindVertexArray(g->arrays[i]);glGenBuffers(1,&g->vertex[i]);glBindBuffer(GL_ARRAY_BUFFER,g->vertex[i]);
  glBufferData(GL_ARRAY_BUFFER,(GLsizeiptr)((size_t)p->vertices*OA_CHAR_VERTEX_BYTES),p->vertex,GL_STATIC_DRAW);
  glGenBuffers(1,&g->index[i]);glBindBuffer(GL_ELEMENT_ARRAY_BUFFER,g->index[i]);glBufferData(GL_ELEMENT_ARRAY_BUFFER,(GLsizeiptr)((size_t)p->indices*4u),p->index,GL_STATIC_DRAW);
  glEnableVertexAttribArray(0);glVertexAttribPointer(0,3,GL_FLOAT,GL_FALSE,OA_CHAR_VERTEX_BYTES,(const void*)(uintptr_t)0);
  glEnableVertexAttribArray(1);glVertexAttribPointer(1,3,GL_FLOAT,GL_FALSE,OA_CHAR_VERTEX_BYTES,(const void*)(uintptr_t)12);
  glEnableVertexAttribArray(2);glVertexAttribPointer(2,2,GL_FLOAT,GL_FALSE,OA_CHAR_VERTEX_BYTES,(const void*)(uintptr_t)24);
  glEnableVertexAttribArray(3);glVertexAttribIPointer(3,4,GL_UNSIGNED_BYTE,OA_CHAR_VERTEX_BYTES,(const void*)(uintptr_t)32);
  glEnableVertexAttribArray(4);glVertexAttribPointer(4,4,GL_FLOAT,GL_FALSE,OA_CHAR_VERTEX_BYTES,(const void*)(uintptr_t)36);}
int oa_character_gpu_share(oa_character_gpu *g,const oa_character_gpu *from){if(!from->ready)return 0;memset(g,0,sizeof(*g));g->program=from->program;g->mvp=from->mvp;g->bones=from->bones;g->has_texture=from->has_texture;g->sampler=from->sampler;g->alpha_cut=from->alpha_cut;g->lights=from->lights;g->shared=1;return 1;}
int oa_character_gpu_share_step(oa_character_gpu *g,const oa_character *c){if(g->next_texture<c->texture_count)upload_texture(g,c,g->next_texture++);else{int n;for(n=0;n<2&&g->next_part<c->part_count;n++)upload_part(g,c,g->next_part++);glBindVertexArray(0);}
 if(glGetError()!=GL_NO_ERROR)return -1;if(g->next_texture<c->texture_count||g->next_part<c->part_count)return 0;g->ready=1;return 1;}
int oa_character_gpu_open(oa_character_gpu *g,const oa_character *c,int outdoor){
 GLuint vs,fs;GLint okay=0;uint32_t i;memset(g,0,sizeof(*g));
 vs=compile(GL_VERTEX_SHADER,vertex_source);fs=vs?compile(GL_FRAGMENT_SHADER,opem_room_fragment):0;if(!fs){if(vs)glDeleteShader(vs);return 0;}
 g->program=glCreateProgram();glAttachShader(g->program,vs);glAttachShader(g->program,fs);glLinkProgram(g->program);glDeleteShader(vs);glDeleteShader(fs);
 glGetProgramiv(g->program,GL_LINK_STATUS,&okay);
 if(!okay){char log[1024];GLsizei n=0;glGetProgramInfoLog(g->program,sizeof(log)-1,&n,log);log[n]=0;LOGE("Character link: %s",log);oa_character_gpu_close(g);return 0;}
 g->mvp=glGetUniformLocation(g->program,"mvp");g->bones=glGetUniformLocation(g->program,"bones[0]");g->has_texture=glGetUniformLocation(g->program,"has_texture");g->sampler=glGetUniformLocation(g->program,"base_texture");g->alpha_cut=glGetUniformLocation(g->program,"alpha_cut");
 if(g->mvp<0||g->bones<0||!opem_room_lighting_open(&g->lights,g->program,outdoor)){LOGE("Character uniforms unavailable");oa_character_gpu_close(g);return 0;}
 /* A shadow sampler sharing the base texture unit makes every draw invalid, even when shadows are off. */
 glUseProgram(g->program);glUniform1i(glGetUniformLocation(g->program,"room_shadow_map"),3);glUniform1i(glGetUniformLocation(g->program,"room_shadow_on"),0);
 g->lights_open=1;
 for(i=0;i<c->texture_count;i++)upload_texture(g,c,i);
 for(i=0;i<c->part_count;i++)upload_part(g,c,i);
 glBindVertexArray(0);
 if(glGetError()!=GL_NO_ERROR){LOGE("Character upload failed");oa_character_gpu_close(g);return 0;}
 g->ready=1;return 1;
}
void oa_character_gpu_close(oa_character_gpu *g){
 uint32_t i;for(i=0;i<OA_CHAR_MAX_PARTS;i++){if(g->arrays[i])glDeleteVertexArrays(1,&g->arrays[i]);if(g->vertex[i])glDeleteBuffers(1,&g->vertex[i]);if(g->index[i])glDeleteBuffers(1,&g->index[i]);}
 for(i=0;i<OA_CHAR_MAX_TEXTURES;i++)if(g->textures[i])glDeleteTextures(1,&g->textures[i]);
 if(!g->shared){if(g->lights_open)opem_room_lighting_close(&g->lights);if(g->program)glDeleteProgram(g->program);}memset(g,0,sizeof(*g));
}
void oa_character_gpu_draw(oa_character_gpu *g,const oa_character *c,const float mvp[16],int room_lighting,float alpha_cut){
 float rows[OA_CHAR_MAX_PALETTE*12];uint32_t i;if(!g->ready||!c->ready)return;
 glUseProgram(g->program);opem_room_lighting_upload(&g->lights,room_lighting);glUniformMatrix4fv(g->mvp,1,GL_FALSE,mvp);glUniform1i(g->sampler,0);glUniform1f(g->alpha_cut,alpha_cut);
 for(i=0;i<c->part_count;i++){const oa_char_part *p=c->parts+i;uint32_t n;if(c->hidden&(1u<<i))continue;n=oa_character_bones(c,p,rows);
  glUniform4fv(g->bones,(GLsizei)n*3,rows);
  if(p->texture>=0){glActiveTexture(GL_TEXTURE0);glBindTexture(GL_TEXTURE_2D,g->textures[p->texture]);glUniform1i(g->has_texture,1);}else glUniform1i(g->has_texture,0);
  glBindVertexArray(g->arrays[i]);glDrawElements(GL_TRIANGLES,(GLsizei)p->indices,GL_UNSIGNED_INT,0);}
 glBindVertexArray(0);
}
