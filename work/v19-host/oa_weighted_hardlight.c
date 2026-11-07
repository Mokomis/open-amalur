#include "oa_weighted_hardlight.h"
#include "oa_character_material.h"
#include "oa_post.h"
#include "oa_render_cache.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <math.h>
#include "opening_sha256.h"
typedef struct SourceTexture {unsigned asset;const char *file;size_t bytes;const char *sha;} SourceTexture;
typedef struct Approved {unsigned part,fab,assembly,material,stride,flags,vertices,indices,palette_count;oa_character_hardlight profile;SourceTexture tex[3];} Approved;
#include "clothing_source_tables.inc"
static const char vertex_source[]=
"#version 300 es\n"
"layout(location=0)in vec3 p;layout(location=1)in ivec4 j;layout(location=2)in vec4 source_weight;layout(location=3)in vec2 source_uv;layout(location=4)in vec4 source_n;layout(location=5)in vec4 source_t;layout(location=6)in vec4 source_b;layout(location=7)in vec4 source_color;"
"uniform mat4 mvp;uniform vec4 char_bones[234];uniform vec2 char_facing_sc;uniform vec2 fog;"
"out vec3 W;out highp vec3 N0;out vec2 UV;out highp float F;out highp float VA;out highp vec4 VC;out highp vec3 TW,BW;out vec2 UV2;flat out highp uint PW;"
"vec3 point_at(int joint,vec3 v){int i=joint*3;vec4 q=vec4(v,1.);return vec3(dot(char_bones[i],q),dot(char_bones[i+1],q),dot(char_bones[i+2],q));}"
"vec3 dir_at(int joint,vec3 v){int i=joint*3;return vec3(dot(char_bones[i].xyz,v),dot(char_bones[i+1].xyz,v),dot(char_bones[i+2].xyz,v));}"
"vec3 skin_point(vec3 v,vec4 w){vec3 r=point_at(j.y,v)*w.y;r=point_at(j.x,v)*w.x+r;r=point_at(j.z,v)*w.z+r;return point_at(j.w,v)*w.w+r;}"
"vec3 skin_dir(vec3 v,vec4 w){vec3 r=dir_at(j.y,v)*w.y;r=dir_at(j.x,v)*w.x+r;r=dir_at(j.z,v)*w.z+r;return dir_at(j.w,v)*w.w+r;}"
"void main(){vec4 w=vec4(source_weight.xyz,dot(vec4(-1.,-1.,-1.,1.),vec4(source_weight.xyz,1.)));W=skin_point(p,w);N0=normalize(skin_dir(source_n.xyz,w));TW=normalize(skin_dir(source_t.xyz,w));"
"vec3 b=source_b.xyz;BW=normalize(vec3(char_facing_sc.y*b.x-char_facing_sc.x*b.y,char_facing_sc.x*b.x+char_facing_sc.y*b.y,b.z));"
"VC=source_color;VA=source_color.a;UV=source_uv;UV2=vec2(0.);PW=0u;gl_Position=mvp*vec4(W,1.);F=1.-min(exp(-(fog.x*gl_Position.w+fog.y)),1.);}";
const char *oa_weighted_hardlight_vertex_source(void){return vertex_source;}
static uint32_t u32(const uint8_t*p){return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;}
static int hash(const uint8_t*p,size_t n,const char *hex){uint8_t d[32];unsigned i;sha256(p,n,d);for(i=0;i<32;i++){unsigned q;if(sscanf(hex+2*i,"%2x",&q)!=1||d[i]!=q)return 0;}return 1;}
static void message(char *e,size_t n,const char*s){if(e&&n&&!e[0])snprintf(e,n,"%s",s);}
static GLint U(GLuint p,const char*n){return oa_cached_uniform(p,n);}
static void I(GLuint p,const char*n,int x){glUniform1i(U(p,n),x);}
static void V3(GLuint p,const char*n,float x,float y,float z){glUniform3f(U(p,n),x,y,z);}
static int find_raw(const uint8_t*b,size_t n,const Approved*a,const uint8_t**raw){
 size_t at=64;unsigned k;int found=0;
 for(k=0;k<12;k++){const uint8_t*r;uint32_t nv,stride;uint64_t ab,rb;
  if(at>n||n-at<128)return 0;r=b+at;at+=128;nv=u32(r+20);stride=u32(r+16);ab=(uint64_t)nv*64u;rb=(uint64_t)nv*stride;
  if(ab>n-at)return 0;at+=(size_t)ab;if(rb>n-at)return 0;
  if(u32(r)==a->part){if(found||u32(r+4)!=a->fab||u32(r+8)!=a->assembly||u32(r+12)!=a->material||stride!=a->stride||nv!=a->vertices||u32(r+24)!=a->indices||u32(r+28)!=a->flags)return 0;*raw=b+at;found=1;}at+=(size_t)rb;
 }
 return found&&at==n;
}
static int raw_valid(const uint8_t*b,const Approved*a){unsigned v,k;for(v=0;v<a->vertices;v++){const uint8_t*s=b+(size_t)v*a->stride;for(k=0;k<4;k++)if(s[12+k]>=a->palette_count||s[12+k]>=78u)return 0;for(k=0;k<3;k++){float p;memcpy(&p,s+4*k,4);if(!isfinite(p))return 0;}for(k=0;k<2;k++){float uv;memcpy(&uv,s+24+4*k,4);if(!isfinite(uv))return 0;}for(k=0;k<3;k++){unsigned c;int nonzero=0;for(c=0;c<3;c++)if(s[32+8*k+2*c]||s[33+8*k+2*c])nonzero=1;if(!nonzero)return 0;}}return 1;}
static GLuint load_texture(const SourceTexture*t,oa_wh_read_malloc read_file,void*user,const char*prefix){
 uint8_t*b=NULL;size_t n=0,at=20;unsigned w,h,levels,k;char path[768];GLuint tex=0;int length=snprintf(path,sizeof(path),"%s%s",prefix?prefix:"",t->file);
 if(length<0||(size_t)length>=sizeof(path)||!read_file(user,path,&b,&n)||!b)goto done;
 if(n!=t->bytes||n<20||!hash(b,n,t->sha)||memcmp(b,"OATX",4)||u32(b+4)!=GL_RGBA8)goto done;
 w=u32(b+8);h=u32(b+12);levels=u32(b+16);if(!w||!h||w>512||h>512||!levels||levels>16)goto done;
 /* Validate ALL extents/bytes before any GL allocation; source mips are retained. */
 for(k=0;k<levels;k++){unsigned mw=w>>k,mh=h>>k;size_t bytes;if(!mw)mw=1;if(!mh)mh=1;bytes=(size_t)mw*mh*4u;if(at>n||n-at<4||u32(b+at)!=bytes||bytes>n-at-4)goto done;at+=4+bytes;}if(at!=n)goto done;
 glGenTextures(1,&tex);glBindTexture(GL_TEXTURE_2D,tex);glPixelStorei(GL_UNPACK_ALIGNMENT,1);at=20;
 for(k=0;k<levels;k++){unsigned mw=w>>k,mh=h>>k,bytes=u32(b+at);if(!mw)mw=1;if(!mh)mh=1;at+=4;glTexImage2D(GL_TEXTURE_2D,(GLint)k,GL_RGBA8,(GLsizei)mw,(GLsizei)mh,0,GL_RGBA,GL_UNSIGNED_BYTE,b+at);at+=bytes;}
 glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_BASE_LEVEL,0);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAX_LEVEL,(GLint)levels-1);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_LINEAR_MIPMAP_LINEAR);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_LINEAR);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,GL_REPEAT);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,GL_REPEAT);
 if(glGetError()!=GL_NO_ERROR){glDeleteTextures(1,&tex);tex=0;}
done:free(b);return tex;
}
static GLuint make_cube(const uint8_t*bgra){uint8_t rgba[1536];GLuint t;unsigned i;for(i=0;i<1536;i+=4){rgba[i]=bgra[i+2];rgba[i+1]=bgra[i+1];rgba[i+2]=bgra[i];rgba[i+3]=bgra[i+3];}
 glGenTextures(1,&t);glBindTexture(GL_TEXTURE_CUBE_MAP,t);for(i=0;i<6;i++)glTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X+i,0,GL_RGBA8,8,8,0,GL_RGBA,GL_UNSIGNED_BYTE,rgba+i*256);
 glTexParameteri(GL_TEXTURE_CUBE_MAP,GL_TEXTURE_BASE_LEVEL,0);glTexParameteri(GL_TEXTURE_CUBE_MAP,GL_TEXTURE_MAX_LEVEL,0);glTexParameteri(GL_TEXTURE_CUBE_MAP,GL_TEXTURE_MIN_FILTER,GL_LINEAR);glTexParameteri(GL_TEXTURE_CUBE_MAP,GL_TEXTURE_MAG_FILTER,GL_LINEAR);glTexParameteri(GL_TEXTURE_CUBE_MAP,GL_TEXTURE_WRAP_S,GL_CLAMP_TO_EDGE);glTexParameteri(GL_TEXTURE_CUBE_MAP,GL_TEXTURE_WRAP_T,GL_CLAMP_TO_EDGE);glTexParameteri(GL_TEXTURE_CUBE_MAP,GL_TEXTURE_WRAP_R,GL_REPEAT);
 if(glGetError()!=GL_NO_ERROR){glDeleteTextures(1,&t);return 0;}return t;
}
static void close_part(oa_wh_part*p){if(p->vao)glDeleteVertexArrays(1,&p->vao);if(p->vbo)glDeleteBuffers(1,&p->vbo);if(p->ibo)glDeleteBuffers(1,&p->ibo);glDeleteTextures(3,p->texture);memset(p,0,sizeof(*p));}
void oa_weighted_hardlight_close(oa_weighted_hardlight*g){unsigned k;if(!g)return;for(k=0;k<4;k++)close_part(g->parts+k);if(g->cube)glDeleteTextures(1,&g->cube);if(g->dummy_ao)glDeleteTextures(1,&g->dummy_ao);if(g->dummy_shadow)glDeleteTextures(1,&g->dummy_shadow);if(g->dummy_grid)glDeleteTextures(1,&g->dummy_grid);if(g->program){glDeleteProgram(g->program);oa_render_cache_reset();}memset(g,0,sizeof(*g));}
static int dummy(oa_weighted_hardlight*g){const uint8_t white[4]={255,255,255,255};const uint16_t ids[8]={65535,65535,65535,65535,65535,65535,65535,65535},depth=65535;
 glGenTextures(1,&g->dummy_ao);glBindTexture(GL_TEXTURE_2D,g->dummy_ao);glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA8,1,1,0,GL_RGBA,GL_UNSIGNED_BYTE,white);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST);
 glGenTextures(1,&g->dummy_shadow);glBindTexture(GL_TEXTURE_2D,g->dummy_shadow);glTexImage2D(GL_TEXTURE_2D,0,GL_DEPTH_COMPONENT16,1,1,0,GL_DEPTH_COMPONENT,GL_UNSIGNED_SHORT,&depth);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_COMPARE_MODE,GL_COMPARE_REF_TO_TEXTURE);
 glGenTextures(1,&g->dummy_grid);glBindTexture(GL_TEXTURE_2D,g->dummy_grid);glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA16UI,2,1,0,GL_RGBA_INTEGER,GL_UNSIGNED_SHORT,ids);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST);return glGetError()==GL_NO_ERROR;
}
GLuint oa_weighted_hardlight_program(const oa_weighted_hardlight*g){return g?g->program:0;}
uint32_t oa_weighted_hardlight_ready_mask(const oa_weighted_hardlight*g){return g?g->ready_mask:0;}
GLuint oa_weighted_hardlight_begin(oa_weighted_hardlight*g,const float eye[3]){GLuint p;unsigned i;if(!g)return 0;g->frame_ready=0;if(!g->ready_mask||!(p=g->program)||!eye||!isfinite(eye[0])||!isfinite(eye[1])||!isfinite(eye[2]))return 0;glUseProgram(p);
 for(i=0;i<8;i++){char n[8];snprintf(n,sizeof(n),"t%u",i);I(p,n,i<3?(int)i:0);}
 I(p,"cube",8);I(p,"native_reflection_cube",8);I(p,"ambient_occlusion",9);I(p,"shadow_map",10);I(p,"light_grid",11);
 glActiveTexture(GL_TEXTURE8);glBindTexture(GL_TEXTURE_CUBE_MAP,g->cube);glActiveTexture(GL_TEXTURE9);glBindTexture(GL_TEXTURE_2D,g->dummy_ao);glActiveTexture(GL_TEXTURE10);glBindTexture(GL_TEXTURE_2D,g->dummy_shadow);glActiveTexture(GL_TEXTURE11);glBindTexture(GL_TEXTURE_2D,g->dummy_grid);
 I(p,"features",128|16|4);I(p,"native_ao_on",0);I(p,"shadow_on",0);I(p,"depth_only",0);I(p,"geometry_kind",0);I(p,"native_alpha_slot",0);I(p,"oa_probe",0);glUniform2i(U(p,"grid_size"),1,1);V3(p,"grid",0,0,1);V3(p,"eye",eye[0],eye[1],eye[2]);V3(p,"sun_dir",0,0,1);V3(p,"sun_color",0,0,0);V3(p,"shadow_color",0,0,0);V3(p,"fog_color",0,0,0);glUniform2f(U(p,"fog"),0,0);glUniform2f(U(p,"ambient_scales"),0,0);glUniform4f(U(p,"sky_light"),0,0,0,1);if(glGetError()!=GL_NO_ERROR)return 0;g->frame_ready=1;return p;
}
uint32_t oa_weighted_hardlight_open(oa_weighted_hardlight*g,const oa_character*c,const uint8_t*attrs,size_t an,const uint8_t*bgra,size_t cn,oa_wh_read_malloc read_file,void*user,const char*prefix,uint32_t mask,unsigned lights,char*e,size_t cap){
 unsigned i,k;const uint8_t*raw[4]={0};if(e&&cap)e[0]=0;if(!g)return 0;memset(g,0,sizeof(*g));
 mask&=OA_WH_ALLOWED_MASK;if(!mask)return 0;
 if(!c||!c->ready||!c->bytes||c->size!=15030356u||c->part_count!=17||!hash(c->bytes,c->size,corrected_pack_sha)){message(e,cap,"requires exact repaired Almain heap pack; old path retained");return 0;}
 if(!attrs||an!=998556u||!hash(attrs,an,"ab02a4a4c87996f5ac5584987455e812f6286c87a563b2bbfbca4b635c7635bf")||memcmp(attrs,"OACAT01",8)){message(e,cap,"source OACAT rejected");return 0;}
 if(!bgra||cn!=1536||!hash(bgra,cn,"a09e463bd738571bf4d19dfb19173ee4ef58972283ddf046ef59f0645ac41836")||!read_file){message(e,cap,"opening character cube/source reader rejected");return 0;}
 if(!lights||lights>2048u){message(e,cap,"invalid light capacity");return 0;}
 for(i=0;i<4;i++)if(mask&(1u<<approved[i].part)){const Approved*a=approved+i;const oa_char_part*part=c->parts+a->part;
  if(part->vertices!=a->vertices||part->indices!=a->indices||part->palette_count!=a->palette_count||a->palette_count>78||!find_raw(attrs,an,a,raw+i)||!raw_valid(raw[i],a)){mask&=~(1u<<a->part);message(e,cap,"source part/layout/palette rejected; part keeps old path");}}
 if(!mask)return 0;
 g->program=oa_world_program_with_vertex(vertex_source,0,lights);if(!g->program){message(e,cap,"weighted HardLight program failed");return 0;}
 g->cube=make_cube(bgra);if(!g->cube||!dummy(g)){message(e,cap,"character shared GPU resources failed");oa_weighted_hardlight_close(g);return 0;}
 for(i=0;i<4;i++)if(mask&(1u<<approved[i].part)){const Approved*a=approved+i;oa_wh_part*part=g->parts+i;const oa_char_part*cp=c->parts+a->part;
  part->part=a->part;part->material=a->material;part->vertices=a->vertices;part->indices=a->indices;part->source_stride=a->stride;part->color_provenance=a->stride==60?OA_WH_COLOR_AUTHORED:OA_WH_COLOR_NATIVE_SHARED_ALL_FF;
  for(k=0;k<3;k++){part->texture[k]=load_texture(a->tex+k,read_file,user,prefix);if(!part->texture[k])break;}
  if(k!=3){message(e,cap,"source material texture failed; part keeps old path");close_part(part);continue;}
  glGenVertexArrays(1,&part->vao);glBindVertexArray(part->vao);glGenBuffers(1,&part->vbo);glBindBuffer(GL_ARRAY_BUFFER,part->vbo);glBufferData(GL_ARRAY_BUFFER,(GLsizeiptr)((size_t)a->vertices*a->stride),raw[i],GL_STATIC_DRAW);glGenBuffers(1,&part->ibo);glBindBuffer(GL_ELEMENT_ARRAY_BUFFER,part->ibo);glBufferData(GL_ELEMENT_ARRAY_BUFFER,(GLsizeiptr)((size_t)a->indices*4),cp->index,GL_STATIC_DRAW);
  glEnableVertexAttribArray(0);glVertexAttribPointer(0,3,GL_FLOAT,GL_FALSE,(GLsizei)a->stride,(const void*)(uintptr_t)0);
  glEnableVertexAttribArray(1);glVertexAttribIPointer(1,4,GL_BYTE,(GLsizei)a->stride,(const void*)(uintptr_t)12);
  glEnableVertexAttribArray(2);glVertexAttribPointer(2,4,GL_SHORT,GL_TRUE,(GLsizei)a->stride,(const void*)(uintptr_t)16);
  glEnableVertexAttribArray(3);glVertexAttribPointer(3,2,GL_FLOAT,GL_FALSE,(GLsizei)a->stride,(const void*)(uintptr_t)24);
  for(k=0;k<3;k++){glEnableVertexAttribArray(4+k);glVertexAttribPointer(4+k,4,GL_SHORT,GL_TRUE,(GLsizei)a->stride,(const void*)(uintptr_t)(32+8*k));}
  if(a->stride==60){glEnableVertexAttribArray(7);glVertexAttribPointer(7,4,GL_UNSIGNED_BYTE,GL_TRUE,60,(const void*)(uintptr_t)56);}else glDisableVertexAttribArray(7);
  if(glGetError()!=GL_NO_ERROR){message(e,cap,"source GPU geometry failed; part keeps old path");close_part(part);continue;}g->ready_mask|=1u<<a->part;
 }
 glBindVertexArray(0);if(!g->ready_mask){oa_weighted_hardlight_close(g);return 0;}g->owner=c;return g->ready_mask;
}
int oa_weighted_hardlight_draw_part(oa_weighted_hardlight*g,const oa_character*c,unsigned pi,const float vp[16]){
 unsigned slot,k,n;float rows[OA_CHAR_MAX_PALETTE*12];GLint f=0;oa_wh_part*p;const Approved*a;
 if(!g||!g->frame_ready||!c||!c->ready||c!=g->owner||!vp||pi>=24||!(g->ready_mask&(1u<<pi))||(c->hidden&(1u<<pi)))return 0;
 if(!isfinite(c->facing))return 0;for(k=0;k<16;k++)if(!isfinite(vp[k]))return 0;
 for(slot=0;slot<4&&approved[slot].part!=pi;slot++){}if(slot==4)return 0;a=approved+slot;p=g->parts+slot;
 n=oa_character_bones(c,c->parts+pi,rows);if(n!=a->palette_count||n>78)return 0;for(k=0;k<n*12;k++)if(!isfinite(rows[k]))return 0;
 glUseProgram(g->program);glGetUniformiv(g->program,U(g->program,"features"),&f);if(!(f&128))return 0;
 if(!oa_character_hardlight_upload(g->program,&a->profile))return 0;
 glUniformMatrix4fv(U(g->program,"mvp"),1,GL_FALSE,vp);glUniform4fv(U(g->program,"char_bones[0]"),(GLsizei)n*3,rows);glUniform2f(U(g->program,"char_facing_sc"),sinf(c->facing),cosf(c->facing));
 for(k=0;k<3;k++){glActiveTexture(GL_TEXTURE0+k);glBindTexture(GL_TEXTURE_2D,p->texture[k]);}glActiveTexture(GL_TEXTURE8);glBindTexture(GL_TEXTURE_CUBE_MAP,g->cube);I(g->program,"cube",8);
 glBindVertexArray(p->vao);if(p->color_provenance==OA_WH_COLOR_NATIVE_SHARED_ALL_FF)glVertexAttrib4f(7,1,1,1,1);glDrawElements(GL_TRIANGLES,(GLsizei)p->indices,GL_UNSIGNED_INT,0);return glGetError()==GL_NO_ERROR?1:-1;
}
