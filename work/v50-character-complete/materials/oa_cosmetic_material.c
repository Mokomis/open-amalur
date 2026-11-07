#include "oa_cosmetic_material.h"
#include "oa_post.h"
#include "oa_render_cache.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <math.h>
#include <limits.h>
/* Generated immutable catalog; shader/source params and slots are preserved. */
#include "cosmetic_source_tables.inc"
#include "cosmetic_tattoo_tables.inc"
static GLint U(GLuint p,const char*n){return oa_cached_uniform(p,n);}
static void I(GLuint p,const char*n,int x){glUniform1i(U(p,n),x);}
static void V3(GLuint p,const char*n,float x,float y,float z){glUniform3f(U(p,n),x,y,z);}
static int finite_array(const float*p,size_t n){size_t i;if(!p)return 0;for(i=0;i<n;i++)if(!isfinite(p[i]))return 0;return 1;}
void oa_cm_packed_color(uint32_t argb,float out[4]){
 const double k=0.0039215688593685626983642578125;
 out[0]=(float)((double)((argb>>16)&255u)*k);
 out[1]=(float)((double)((argb>>8)&255u)*k);
 out[2]=(float)((double)(argb&255u)*k);
 out[3]=(float)((double)(argb>>24)*k);
}
int oa_cm_instance_from_selection(const oa_creation_render_selection*s,uint8_t skin_alpha,oa_cm_instance*out){
 static const unsigned category[8]={OA_CREATION_HAIR_COLOR,OA_CREATION_HAIR_COLOR,
 OA_CREATION_SKIN,OA_CREATION_EYE_COLOR,OA_CREATION_EYEBROW,OA_CREATION_TATTOO_COLOR,
 OA_CREATION_EYELINER,OA_CREATION_LIPSTICK};unsigned k;
 if(!s||!out)return 0;memset(out,0,sizeof(*out));
 for(k=0;k<4;k++){out->probe_instance_tint[k]=1;out->dynamic_tint[k]=1;out->luminance_tint[k]=1;}out->luminance_factors[0]=.2126f;out->luminance_factors[1]=.7152f;out->luminance_factors[2]=.0722f;
 for(k=0;k<8;k++){uint32_t packed;unsigned cat=category[k];
  if(!(s->present_color_mask&(1u<<cat)))return 0;
  packed=s->colors[cat].words[k==1?2:1];
  if(k==2)packed=(packed&0xffffffu)|((uint32_t)skin_alpha<<24);
  if(k>=4){unsigned a=k==4?OA_CREATION_EYEBROW_ALPHA:k==5?OA_CREATION_TATTOO_ALPHA:k==6?OA_CREATION_EYELINER_ALPHA:OA_CREATION_LIPSTICK_ALPHA;
   packed=(packed&0xffffffu)|((uint32_t)s->alphas[a]<<24);}
  oa_cm_packed_color(packed,out->color[k]);
 }
 if(s->present_color_mask&(1u<<OA_CREATION_BEARD_COLOR)){
  oa_cm_packed_color(s->colors[OA_CREATION_BEARD_COLOR].words[1],out->beard[0]);
  oa_cm_packed_color(s->colors[OA_CREATION_BEARD_COLOR].words[2],out->beard[1]);
 }else{memcpy(out->beard,out->color,32);}
 out->head_diffuse=s->head_diffuse_id;out->body_diffuse=s->body_diffuse_id;
 for(k=0;k<sizeof(cm_tattoos)/sizeof(cm_tattoos[0]);k++)if(cm_tattoos[k][0]==s->tattoo_simtype){out->tattoo_texture=cm_tattoos[k][1];break;}
 return out->tattoo_texture>1;
}
int oa_cm_material_find(uint32_t mid,oa_cm_material*out){size_t i;if(!out)return 0;for(i=0;i<sizeof(cm_catalog)/sizeof(cm_catalog[0]);i++)if(cm_catalog[i].material==mid){*out=cm_catalog[i];return 1;}return 0;}
static const char vertex_source[]=
"#version 300 es\n"
"layout(location=0)in vec3 p;layout(location=1)in uvec4 j;layout(location=2)in vec3 source_weight;"
"layout(location=3)in vec2 source_uv;layout(location=4)in vec3 source_n;layout(location=5)in vec3 source_t;layout(location=6)in vec3 source_b;layout(location=7)in vec4 source_color;layout(location=8)in vec2 source_uv1;"
"uniform mat4 mvp;uniform vec4 char_bones[234],char_entity[3];uniform int char_weighted;uniform vec2 fog;"
"out vec3 W;out highp vec3 N0;out vec2 UV;out highp float F;out highp float VA;out highp vec4 VC;out highp vec3 TW,BW;out vec2 UV2;flat out highp uint PW;"
"vec3 point_at(uint joint,vec3 v){int i=int(joint)*3;vec4 q=vec4(v,1.);return vec3(dot(char_bones[i],q),dot(char_bones[i+1],q),dot(char_bones[i+2],q));}"
"vec3 dir_at(uint joint,vec3 v){int i=int(joint)*3;return vec3(dot(char_bones[i].xyz,v),dot(char_bones[i+1].xyz,v),dot(char_bones[i+2].xyz,v));}"
"vec3 skin_point(vec3 v,vec4 w){vec3 r=point_at(j.y,v)*w.y;r=point_at(j.x,v)*w.x+r;r=point_at(j.z,v)*w.z+r;return point_at(j.w,v)*w.w+r;}"
"vec3 skin_dir(vec3 v,vec4 w){vec3 r=dir_at(j.y,v)*w.y;r=dir_at(j.x,v)*w.x+r;r=dir_at(j.z,v)*w.z+r;return dir_at(j.w,v)*w.w+r;}"
"void main(){vec4 w=vec4(source_weight,1.-dot(source_weight,vec3(1.)));"
"W=char_weighted!=0?skin_point(p,w):point_at(0u,p);N0=normalize(char_weighted!=0?skin_dir(source_n,w):dir_at(0u,source_n));TW=normalize(char_weighted!=0?skin_dir(source_t,w):dir_at(0u,source_t));"
"BW=normalize(vec3(dot(char_entity[0].xyz,source_b),dot(char_entity[1].xyz,source_b),dot(char_entity[2].xyz,source_b)));"
"VC=source_color;VA=source_color.a;UV=source_uv;UV2=source_uv1;PW=0u;gl_Position=mvp*vec4(W,1.);F=1.-min(exp(-(fog.x*gl_Position.w+fog.y)),1.);}";
const char *oa_cm_vertex_source(void){return vertex_source;}
static const char declarations[]=
"uniform vec4 cm_colors[8],cm_extra,cm_fresnel,cm_dynamic_tint,cm_lum;uniform vec3 cm_lum_tint,cm_probe_tint;uniform int cm_kind,cm_alpha,cm_normal_policy;uniform float cm_cut;"

"vec3 cm_mapped,cm_eye_add;\n";
static const char coverage[]=
"if(material_family==13&&cm_alpha!=0&&texture(t3,UV).g<cm_cut)discard;"
"if(material_family==13&&cm_kind==7){float keep=min(exp(-(fog.x/gl_FragCoord.w+fog.y)),1.);vec3 c=texture(t0,UV).rgb*VC.rgb*cm_dynamic_tint.rgb;c=mix(c,cm_lum_tint*dot(c,cm_lum.xyz),cm_lum.w);o=vec4(c,texture(t3,UV).g*VC.a*cm_dynamic_tint.a*keep);return;}\n";
static const char cases[]=
"else if(material_family==13&&(features&128)!=0){"
"vec3 vv=normalize(eye-W);cm_eye_add=vec3(0.);"
"if(cm_kind==4){N=normalize(N0);cm_mapped=N;vec3 vref=reflect(vv,N);vec3 eyeBase=d.rgb+texture(t3,UV).g*cm_colors[3].rgb+texture(native_reflection_cube,vref).rgb;"
"base=eyeBase*VC.rgb*VC.a;cm_eye_add=eyeBase*VC.rgb*texture(t3,UV).g*cm_extra.x;spec=0.;spec_gain=0.;spec_power=0.;}"
"else{vec3 nm=unpack(texture(t1,UV));cm_mapped=normalize(TW*nm.x+BW*nm.y+N0*nm.z);N=cm_normal_policy!=0?normalize(N0):cm_mapped;"
"float rim=clamp(cm_fresnel.x*pow(1.-clamp(dot(cm_mapped,vv),0.,1.),cm_fresnel.y),0.,1.);"
"vec3 cosmetic=cm_kind==3?mix(cm_colors[0].rgb,cm_colors[1].rgb,texture(t6,UV).g):(cm_kind==6?d.rgb:mix(d.rgb,d.rgb*cm_colors[2].rgb,cm_colors[2].a));cosmetic+=vec3(cm_extra.x*rim);"
"if(cm_kind==2){vec4 makeup=texture(t4,UV2);cosmetic=mix(cosmetic,cm_colors[5].rgb,texture(t5,UV2).g*cm_colors[5].a);cosmetic=mix(cosmetic,cm_colors[4].rgb,makeup.r*cm_colors[4].a);cosmetic=mix(cosmetic,cm_colors[6].rgb,makeup.g*cm_colors[6].a);cosmetic=mix(cosmetic,cm_colors[7].rgb,makeup.b*cm_colors[7].a);}"
"if(cm_kind==6)cm_eye_add=texture(t3,UV).g*texture(native_reflection_cube,reflect(-vv,cm_mapped).xzy).rgb*cm_probe_tint*reflection_environment_tint;"
"base=cosmetic*VC.rgb*VC.a;spec=texture(t2,UV).g*material_specular.x;spec_gain=clamp(spec*VC.a,0.,1.);spec_power=material_specular.y*.25;}}\n";
static const char ambient[]=
"if(material_family==13)amb=oa_half3(clamp(texture(cube,cm_mapped.xzy).rgb*VC.a*materialBase+cm_eye_add,0.,1.));\n";
static char *replace_once(char*s,const char*key,const char*value){char*at,*out;size_t a,b,c;if(!s)return NULL;at=strstr(s,key);if(!at||strstr(at+strlen(key),key)){free(s);return NULL;}a=(size_t)(at-s);b=strlen(value);c=strlen(at+strlen(key));if(a>SIZE_MAX-b-c-1){free(s);return NULL;}out=(char*)malloc(a+b+c+1);if(out){memcpy(out,s,a);memcpy(out+a,value,b);memcpy(out+a+b,at+strlen(key),c+1);}free(s);return out;}
char *oa_cm_fragment_source(unsigned lights){char*s=oa_world_fragment_source(0,lights,1);s=replace_once(s,"/*OA_CHARACTER_DECLARATIONS*/",declarations);s=replace_once(s,"/*OA_CHARACTER_COVERAGE*/",coverage);s=replace_once(s,"/*OA_CHARACTER_CASES*/",cases);return replace_once(s,"/*OA_CHARACTER_AMBIENT*/",ambient);}
static int dummy(oa_cm_context*g){const uint8_t white[4]={255,255,255,255};const uint16_t ids[8]={65535,65535,65535,65535,65535,65535,65535,65535},depth=65535;
 glGenTextures(1,&g->dummy_ao);glBindTexture(GL_TEXTURE_2D,g->dummy_ao);glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA8,1,1,0,GL_RGBA,GL_UNSIGNED_BYTE,white);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST);
 glGenTextures(1,&g->dummy_shadow);glBindTexture(GL_TEXTURE_2D,g->dummy_shadow);glTexImage2D(GL_TEXTURE_2D,0,GL_DEPTH_COMPONENT16,1,1,0,GL_DEPTH_COMPONENT,GL_UNSIGNED_SHORT,&depth);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_COMPARE_MODE,GL_COMPARE_REF_TO_TEXTURE);
 glGenTextures(1,&g->dummy_grid);glBindTexture(GL_TEXTURE_2D,g->dummy_grid);glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA16UI,2,1,0,GL_RGBA_INTEGER,GL_UNSIGNED_SHORT,ids);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,GL_NEAREST);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_NEAREST);return glGetError()==GL_NO_ERROR;
}
int oa_cm_open(oa_cm_context*g,GLuint cc,GLuint wc,oa_cm_texture_lookup fn,void*user,unsigned lights){char*fs;GLuint block;if(!g||!cc||!wc||!fn||g->program||!lights||lights>2048)return 0;memset(g,0,sizeof(*g));fs=oa_cm_fragment_source(lights);if(!fs)return 0;g->program=oa_post_program(vertex_source,fs);free(fs);if(!g->program)return 0;block=glGetUniformBlockIndex(g->program,"Lights");if(block!=GL_INVALID_INDEX)glUniformBlockBinding(g->program,block,0);g->character_cube=cc;g->world_cube=wc;g->texture=fn;g->texture_user=user;if(!dummy(g)){oa_cm_close(g);return 0;}return 1;}
void oa_cm_close(oa_cm_context*g){if(!g)return;if(g->program)glDeleteProgram(g->program);if(g->dummy_ao)glDeleteTextures(1,&g->dummy_ao);if(g->dummy_shadow)glDeleteTextures(1,&g->dummy_shadow);if(g->dummy_grid)glDeleteTextures(1,&g->dummy_grid);memset(g,0,sizeof(*g));oa_render_cache_reset();}
void oa_cm_environment_probe(oa_cm_context*g,GLuint p){if(g)g->environment_probe=p;}
GLuint oa_cm_program(const oa_cm_context*g){return g?g->program:0;}
GLuint oa_cm_begin(oa_cm_context*g,const float eye[3]){GLuint p;unsigned i;if(!g)return 0;g->frame_ready=0;if(!(p=g->program)||!finite_array(eye,3))return 0;glUseProgram(p);for(i=0;i<8;i++){char n[8];snprintf(n,sizeof(n),"t%u",i);I(p,n,i<3?(int)i:0);}I(p,"t3",3);I(p,"t4",4);I(p,"t5",5);I(p,"t6",6);I(p,"native_reflection_cube",14);I(p,"cube",8);I(p,"ambient_occlusion",9);I(p,"shadow_map",10);I(p,"light_grid",11);I(p,"native_reflection_cube",14);I(p,"terrain_selector",11);I(p,"terrain_paint",0);
 I(p,"features",128|16|4);I(p,"material_family",13);I(p,"geometry_kind",0);I(p,"depth_only",0);I(p,"native_alpha_slot",0);I(p,"native_ao_on",0);I(p,"shadow_on",0);I(p,"light_count",0);I(p,"terrain_draw_set",-1);I(p,"oa_probe",0);
 glUniform3fv(U(p,"eye"),1,eye);V3(p,"sun_dir",0,0,1);V3(p,"sun_color",0,0,0);V3(p,"shadow_color",0,0,0);V3(p,"fog_color",0,0,0);glUniform2f(U(p,"fog"),0,0);glUniform2f(U(p,"ambient_scales"),5,.9f);glUniform4f(U(p,"sky_light"),.5f,.5f,.6f,1);glUniform3f(U(p,"reflection_environment_tint"),1,1,1);
 glActiveTexture(GL_TEXTURE8);glBindTexture(GL_TEXTURE_CUBE_MAP,g->character_cube);glActiveTexture(GL_TEXTURE9);glBindTexture(GL_TEXTURE_2D,g->dummy_ao);glActiveTexture(GL_TEXTURE10);glBindTexture(GL_TEXTURE_2D,g->dummy_shadow);glActiveTexture(GL_TEXTURE11);glBindTexture(GL_TEXTURE_2D,g->dummy_grid);glActiveTexture(GL_TEXTURE14);glBindTexture(GL_TEXTURE_CUBE_MAP,g->character_cube);g->frame_ready=glGetError()==GL_NO_ERROR;return g->frame_ready?p:0;
}
int oa_cm_surface_open(oa_cm_surface*s,const oa_cm_vertex*v,uint32_t nv,const uint32_t*ix,uint32_t ni,uint32_t pc,int weighted){unsigned k,a;uint32_t flags=~0u;if(!s||s->vao||!v||!ix||!nv||!ni||ni%3||ni>INT_MAX||!pc||pc>OA_CM_MAX_PALETTE||sizeof(*v)!=96)return 0;
 for(k=0;k<nv;k++){const oa_cm_vertex*q=v+k;flags&=q->flags;if(!finite_array(q->p,3)||!finite_array(q->weight,3)||!finite_array(q->uv0,2)||!finite_array(q->uv1,2)||!finite_array(q->n,3)||!finite_array(q->t,3)||!finite_array(q->b,3))return 0;if((q->flags&15u)!=15u||!(q->flags&(OA_CM_HAS_COLOR|OA_CM_NATIVE_DEFAULT_COLOR)))return 0;if(!(q->flags&OA_CM_HAS_COLOR)&&memcmp(q->rgba,"\xff\xff\xff\xff",4))return 0;for(a=0;a<4;a++)if(weighted&&q->joints[a]>=pc)return 0;}for(k=0;k<ni;k++)if(ix[k]>=nv)return 0;
 memset(s,0,sizeof(*s));glGenVertexArrays(1,&s->vao);glBindVertexArray(s->vao);glGenBuffers(1,&s->vbo);glBindBuffer(GL_ARRAY_BUFFER,s->vbo);glBufferData(GL_ARRAY_BUFFER,(GLsizeiptr)((size_t)nv*96),v,GL_STATIC_DRAW);glGenBuffers(1,&s->ibo);glBindBuffer(GL_ELEMENT_ARRAY_BUFFER,s->ibo);glBufferData(GL_ELEMENT_ARRAY_BUFFER,(GLsizeiptr)((size_t)ni*4),ix,GL_STATIC_DRAW);
 glVertexAttribPointer(0,3,GL_FLOAT,GL_FALSE,96,(void*)0);glVertexAttribIPointer(1,4,GL_UNSIGNED_BYTE,96,(void*)12);glVertexAttribPointer(2,3,GL_FLOAT,GL_FALSE,96,(void*)16);glVertexAttribPointer(3,2,GL_FLOAT,GL_FALSE,96,(void*)28);glVertexAttribPointer(4,3,GL_FLOAT,GL_FALSE,96,(void*)44);glVertexAttribPointer(5,3,GL_FLOAT,GL_FALSE,96,(void*)56);glVertexAttribPointer(6,3,GL_FLOAT,GL_FALSE,96,(void*)68);glVertexAttribPointer(7,4,GL_UNSIGNED_BYTE,GL_TRUE,96,(void*)80);glVertexAttribPointer(8,2,GL_FLOAT,GL_FALSE,96,(void*)36);for(k=0;k<9;k++)glEnableVertexAttribArray(k);
 if(glGetError()!=GL_NO_ERROR){oa_cm_surface_close(s);return 0;}s->vertices=nv;s->indices=ni;s->palette_count=pc;s->weighted=weighted!=0;s->flags=flags;return 1;
}
void oa_cm_surface_close(oa_cm_surface*s){if(!s)return;if(s->vao)glDeleteVertexArrays(1,&s->vao);if(s->vbo)glDeleteBuffers(1,&s->vbo);if(s->ibo)glDeleteBuffers(1,&s->ibo);memset(s,0,sizeof(*s));}
static int resolve_textures(oa_cm_context*g,const oa_cm_material*m,const oa_cm_instance*in,GLuint tex[8]){uint32_t ids[8];unsigned k;if(!g||!g->program||!m||m->kind>OA_CM_FOG_ADDITIVE||!in)return 0;if(m->kind==OA_CM_HEAD&&in->tattoo_texture<=1)return 0;
 memset(ids,0,sizeof(ids));ids[0]=m->source_slots[0];ids[1]=m->source_slots[3];ids[2]=m->source_slots[2];ids[3]=m->source_slots[1];ids[4]=m->source_slots[7];ids[5]=in->tattoo_texture?in->tattoo_texture:m->source_slots[9];ids[6]=m->source_slots[7];ids[7]=m->source_slots[12];
 if(m->kind==OA_CM_SKIN&&in->body_diffuse>1)ids[0]=in->body_diffuse;if(m->kind==OA_CM_HEAD&&in->head_diffuse>1)ids[0]=in->head_diffuse;
 /* Optimized-out source maps are NOT fabricated white: use a real required map
  * solely as inactive sampler completeness binding. Family resources validated. */
 for(k=0;k<8;k++){int needed=k<3;if(m->kind==OA_CM_HAIR)needed=k==1||k==2||k==3||k==6;if(m->kind==OA_CM_HEAD)needed=k<3||k==4||k==5;if(m->kind==OA_CM_SKIN)needed=k<3||k==3;if(m->kind==OA_CM_EYE)needed=k==0||k==7;
  if(m->kind==OA_CM_EYE&&k==3){ids[k]=m->source_slots[6];needed=1;}if(m->kind==OA_CM_DOT3)needed=k<3;
  if(m->kind==OA_CM_REFLECT)needed=k<4;
  if(m->kind==OA_CM_FOG_ADDITIVE)needed=k==0||k==3;
  tex[k]=0;if(needed){if(ids[k]<=1)return 0;tex[k]=g->texture(g->texture_user,ids[k],k==7?GL_TEXTURE_CUBE_MAP:GL_TEXTURE_2D);if(!tex[k])return 0;}
 }
 if(m->kind==OA_CM_REFLECT){if(!g->environment_probe)return 0;tex[7]=g->environment_probe;}
 for(k=0;k<7;k++)if(!tex[k])tex[k]=tex[0]?tex[0]:tex[1];if(!tex[7])tex[7]=g->character_cube;
 return 1;
}
int oa_cm_resources_ready(oa_cm_context*g,const oa_cm_material*m,const oa_cm_instance*in){GLuint t[8];return resolve_textures(g,m,in,t);}
int oa_cm_draw(oa_cm_context*g,const oa_cm_surface*s,const oa_cm_material*m,const oa_cm_instance*in,int beard,const float vp[16],const float*bones,const float entity[12]){
 GLuint tex[8],p;unsigned k;float colors[8][4];int family;
 if(!g||!g->frame_ready||!(p=g->program)||!s||!s->vao||!m||m->kind>OA_CM_FOG_ADDITIVE||!in||!finite_array(vp,16)||!finite_array(bones,(size_t)s->palette_count*12)||!finite_array(entity,12)||!finite_array(&in->color[0][0],32))return 0;
 if(m->kind==OA_CM_HEAD&&(!(s->flags&OA_CM_HAS_UV1)||in->tattoo_texture<=1))return 0;
 if(!resolve_textures(g,m,in,tex))return 0;
 glUseProgram(p);family=m->kind==OA_CM_HARDLIGHT?12:m->kind==OA_CM_DOT3?1:13;I(p,"material_family",family);I(p,"cm_kind",(int)m->kind);I(p,"cm_alpha",m->alpha_test&&(m->kind==OA_CM_SKIN||m->kind==OA_CM_HAIR));I(p,"cm_normal_policy",(int)m->normal_policy);glUniform1f(U(p,"cm_cut"),(float)m->cutoff_byte/255.f);
 glUniform4fv(U(p,"material_color"),1,m->constant);glUniform4f(U(p,"material_specular"),m->specular[0],m->specular[1],m->extra[0],m->fresnel[0]);glUniform4f(U(p,"material_tiling"),1,1,m->fresnel[1],0);glUniform4fv(U(p,"cm_extra"),1,m->kind==OA_CM_EYE?m->constant:m->extra);glUniform4fv(U(p,"cm_fresnel"),1,m->fresnel);
 glUniform3fv(U(p,"cm_probe_tint"),1,in->probe_instance_tint);glUniform4fv(U(p,"cm_dynamic_tint"),1,in->dynamic_tint);glUniform4fv(U(p,"cm_lum"),1,in->luminance_factors);glUniform3fv(U(p,"cm_lum_tint"),1,in->luminance_tint);
 memcpy(colors,in->color,sizeof(colors));if(beard)memcpy(colors,in->beard,32);glUniform4fv(U(p,"cm_colors"),8,&colors[0][0]);I(p,"char_weighted",s->weighted);glUniform4fv(U(p,"char_bones"),(GLsizei)s->palette_count*3,bones);glUniform4fv(U(p,"char_entity"),3,entity);glUniformMatrix4fv(U(p,"mvp"),1,GL_FALSE,vp);
 for(k=0;k<8;k++){glActiveTexture(k==7?GL_TEXTURE14:GL_TEXTURE0+k);glBindTexture(k==7?GL_TEXTURE_CUBE_MAP:GL_TEXTURE_2D,tex[k]);}glActiveTexture(GL_TEXTURE8);glBindTexture(GL_TEXTURE_CUBE_MAP,m->kind==OA_CM_DOT3?g->world_cube:g->character_cube);glBindVertexArray(s->vao);glDrawElements(GL_TRIANGLES,(GLsizei)s->indices,GL_UNSIGNED_INT,(void*)0);return glGetError()==GL_NO_ERROR?1:-1;
}
