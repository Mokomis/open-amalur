#include "scene_materials_v09.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static unsigned checks;
static void check(int ok,const char *msg){if(!ok){fprintf(stderr,"FAIL %s\n",msg);exit(1);}checks++;}
static void w32(unsigned char*p,uint32_t v){p[0]=(unsigned char)v;p[1]=(unsigned char)(v>>8);p[2]=(unsigned char)(v>>16);p[3]=(unsigned char)(v>>24);}
static void make(unsigned char b[176],unsigned char sha[32]){
    unsigned i;memset(b,0,176);for(i=0;i<32;i++)sha[i]=(unsigned char)i;
    memcpy(b,"OMAT09\0\0",8);w32(b+8,1);w32(b+12,6);w32(b+16,2);w32(b+20,2);memcpy(b+24,sha,32);
    w32(b+56,0x3f800000);w32(b+60,0xbf800000); /* UV1,-1 */
    w32(b+104,0);w32(b+108,3);w32(b+112,0);
    w32(b+120,3);w32(b+124,3);w32(b+128,SCENE_MATERIALS_V09_FALLBACK);
    w32(b+136,1);w32(b+140,1);w32(b+144,4);b[152]=255;b[155]=255;
    w32(b+156,1);w32(b+160,1);w32(b+164,4);b[173]=255;b[175]=255;
}
static void rejected(const unsigned char*b,size_t n,uint32_t count,const unsigned char sha[32]){
    scene_materials_v09 m={0};char error[256];int ok=scene_materials_v09_load(b,n,count,sha,&m,error,sizeof(error));
    check(!ok&&error[0]&&!m.uv&&!m.draws&&!m.textures&&!m.owned_bytes,"invalid package rejected without output publication");scene_materials_v09_free(&m);
}
int main(void){
    unsigned char b[176],copy[176],sha[32],other[32];unsigned i;scene_materials_v09 m={0};char error[256];
    make(b,sha);check(scene_materials_v09_load(b,sizeof(b),6,sha,&m,error,sizeof(error)),error);
    check(m.vertex_count==6&&m.draw_count==2&&m.texture_count==2,"counts retained");
    check(m.uv[0]==1&&m.uv[1]==-1,"UV signs/values unchanged");
    check(m.draws[1].first_vertex==3&&m.draws[1].texture_index==SCENE_MATERIALS_V09_FALLBACK,"explicit fallback retained");
    check(m.textures[0].rgba[0]==255&&m.textures[1].rgba[1]==255,"RGBA bytes retained");
    memset(b,0,sizeof(b));check(m.uv[0]==1&&m.textures[0].rgba[0]==255,"loader owns copies");
    make(b,sha);check(!scene_materials_v09_load(b,sizeof(b),6,sha,&m,error,sizeof(error)),"nonempty output rejected");
    check(m.uv[0]==1,"failed reuse preserves loaded output");scene_materials_v09_free(&m);scene_materials_v09_free(&m);
    check(!m.uv&&!m.draws&&!m.textures&&!m.vertex_count,"free resets and tolerates repeat");
    for(i=0;i<sizeof(b);i++)rejected(b,i,6,sha);
    memcpy(other,sha,32);other[31]^=1;rejected(b,sizeof(b),6,other);rejected(b,sizeof(b),3,sha);
    rejected(NULL,sizeof(b),6,sha);rejected(b,sizeof(b),6,NULL);
#define BAD32(offset,value) do{memcpy(copy,b,sizeof(b));w32(copy+(offset),(value));rejected(copy,sizeof(copy),6,sha);}while(0)
    BAD32(0,0);BAD32(8,2);BAD32(12,0);BAD32(12,7);BAD32(16,0);BAD32(16,4097);BAD32(20,257);
    BAD32(56,0x7fc00000);BAD32(60,0x7f800000);BAD32(60,0xff800000);
    BAD32(104,3);BAD32(108,0);BAD32(108,4);BAD32(108,9);BAD32(112,2);BAD32(116,1);
    BAD32(120,0);BAD32(124,6);BAD32(132,1);
    BAD32(136,0);BAD32(136,4097);BAD32(140,4097);BAD32(144,3);BAD32(148,1);
    BAD32(156,0);BAD32(164,0);BAD32(168,1);
#undef BAD32
    /* A deliberately all-fallback package is valid and contains no textures. */
    make(b,sha);w32(b+16,1);w32(b+20,0);w32(b+108,6);w32(b+112,SCENE_MATERIALS_V09_FALLBACK);
    check(scene_materials_v09_load(b,120,6,sha,&m,error,sizeof(error)),error);
    check(m.texture_count==0&&m.textures==NULL&&m.draws[0].vertex_count==6,"all-fallback scope explicit");
    scene_materials_v09_free(&m);rejected(b,121,6,sha);
    printf("{\"ok\":true,\"checks\":%u,\"scope\":\"authored material package bounds, exact scene identity, payload copy and explicit fallback only\"}\n",checks);return 0;
}
