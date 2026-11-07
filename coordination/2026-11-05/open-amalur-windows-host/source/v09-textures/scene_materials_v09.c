#include "scene_materials_v09.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static uint32_t u32(const unsigned char *p){return (uint32_t)p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24);}
static float f32(const unsigned char *p){uint32_t bits=u32(p);float value;memcpy(&value,&bits,4);return value;}
static int fail(char *error,size_t capacity,const char *message){if(error&&capacity)snprintf(error,capacity,"%s",message);return 0;}
void scene_materials_v09_free(scene_materials_v09 *m){uint32_t i;if(!m)return;if(m->textures)for(i=0;i<m->texture_count;i++)free(m->textures[i].rgba);free(m->textures);free(m->draws);free(m->uv);memset(m,0,sizeof(*m));}
int scene_materials_v09_load(const void *data,size_t length,uint32_t expected_vertices,const unsigned char expected_sha[32],scene_materials_v09 *out,char *error,size_t capacity){
    const unsigned char *bytes=(const unsigned char*)data;size_t at,uv_bytes,draw_bytes,owned;uint32_t vertices,draws,textures,i,next=0;scene_materials_v09 m={0};
    if(error&&capacity)*error=0;
    if(!bytes||!out||!expected_sha||sizeof(float)!=4)return fail(error,capacity,"Material package arguments or float32 host invalid");
    if(out->uv||out->draws||out->textures||out->vertex_count||out->draw_count||out->texture_count||out->owned_bytes)return fail(error,capacity,"Material output must be zero initialized");
    if(length<56||length>SCENE_MATERIALS_V09_MAX_BYTES||memcmp(bytes,"OMAT09\0\0",8)||u32(bytes+8)!=1)return fail(error,capacity,"Material package magic/version/length invalid");
    vertices=u32(bytes+12);draws=u32(bytes+16);textures=u32(bytes+20);
    if(!vertices||vertices!=expected_vertices||vertices>SCENE_MATERIALS_V09_MAX_VERTICES||vertices%3||!draws||draws>SCENE_MATERIALS_V09_MAX_DRAWS||textures>SCENE_MATERIALS_V09_MAX_TEXTURES)return fail(error,capacity,"Material package count outside selected scene bounds");
    if(memcmp(bytes+24,expected_sha,32))return fail(error,capacity,"Material package scene SHA256 mismatch");
    uv_bytes=(size_t)vertices*8;draw_bytes=(size_t)draws*16;at=56;
    if(uv_bytes>length-at)return fail(error,capacity,"Material UV payload truncated");
    for(i=0;i<vertices*2;i++)if(!isfinite(f32(bytes+at+(size_t)i*4)))return fail(error,capacity,"Material UV is nonfinite");
    at+=uv_bytes;if(draw_bytes>length-at)return fail(error,capacity,"Material draw table truncated");
    for(i=0;i<draws;i++){
        const unsigned char *d=bytes+at+(size_t)i*16;uint32_t first=u32(d),count=u32(d+4),texture=u32(d+8);
        if(first!=next||!count||count%3||count>vertices-next||u32(d+12)||(texture!=SCENE_MATERIALS_V09_FALLBACK&&texture>=textures))return fail(error,capacity,"Material draw coverage or texture reference invalid");
        next+=count;
    }
    if(next!=vertices)return fail(error,capacity,"Material draws do not cover the complete scene");
    at+=draw_bytes;owned=uv_bytes+(size_t)draws*sizeof(*m.draws)+(size_t)textures*sizeof(*m.textures);
    for(i=0;i<textures;i++){
        uint32_t w,h,n;
        if(length-at<16)return fail(error,capacity,"Material texture header truncated");
        w=u32(bytes+at);h=u32(bytes+at+4);n=u32(bytes+at+8);
        if(!w||!h||w>SCENE_MATERIALS_V09_MAX_DIMENSION||h>SCENE_MATERIALS_V09_MAX_DIMENSION||n!=(uint64_t)w*h*4||u32(bytes+at+12))return fail(error,capacity,"Material texture RGBA8 shape/flags invalid");
        at+=16;if(n>length-at)return fail(error,capacity,"Material texture pixels truncated");at+=n;
        if(n>SCENE_MATERIALS_V09_MAX_BYTES-owned)return fail(error,capacity,"Material owned CPU byte budget exceeded");owned+=n;
    }
    if(at!=length)return fail(error,capacity,"Material package trailing bytes rejected");
    m.vertex_count=vertices;m.draw_count=draws;m.texture_count=textures;m.owned_bytes=owned;memcpy(m.scene_sha256,bytes+24,32);
    m.uv=(float*)malloc(uv_bytes);m.draws=(scene_material_draw_v09*)calloc(draws,sizeof(*m.draws));
    if(textures)m.textures=(scene_material_texture_v09*)calloc(textures,sizeof(*m.textures));
    if(!m.uv||!m.draws||(textures&&!m.textures))goto oom;
    at=56;for(i=0;i<vertices*2;i++)m.uv[i]=f32(bytes+at+(size_t)i*4);at+=uv_bytes;
    for(i=0;i<draws;i++){m.draws[i].first_vertex=u32(bytes+at);m.draws[i].vertex_count=u32(bytes+at+4);m.draws[i].texture_index=u32(bytes+at+8);at+=16;}
    for(i=0;i<textures;i++){
        scene_material_texture_v09 *t=m.textures+i;t->width=u32(bytes+at);t->height=u32(bytes+at+4);t->rgba_bytes=u32(bytes+at+8);at+=16;
        t->rgba=(unsigned char*)malloc(t->rgba_bytes);if(!t->rgba)goto oom;memcpy(t->rgba,bytes+at,t->rgba_bytes);at+=t->rgba_bytes;
    }
    *out=m;return 1;
oom:scene_materials_v09_free(&m);return fail(error,capacity,"Material package allocation failed");
}
