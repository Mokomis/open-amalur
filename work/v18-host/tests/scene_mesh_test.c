#include "amalur_scene_mesh.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static unsigned checks;
static void require(int condition,const char *s){if(!condition){fprintf(stderr,"FAIL:%s\n",s);exit(1);}checks++;}
static void put(unsigned char *p,uint32_t n){p[0]=(unsigned char)n;p[1]=(unsigned char)(n>>8);p[2]=(unsigned char)(n>>16);p[3]=(unsigned char)(n>>24);}
static void fixture(unsigned char bytes[144]){
    unsigned i;memset(bytes,0,144);memcpy(bytes,"OMSC07\0\0",8);put(bytes+8,3);put(bytes+24,0x3f800000u);put(bytes+28,0x3f800000u);
    put(bytes+36+36,0x3f800000u);put(bytes+36+72+4,0x3f800000u);
    for(i=0;i<3;i++){put(bytes+36+i*36+20,0x3f800000u);put(bytes+36+i*36+24,0x3f000000u);put(bytes+36+i*36+28,0x3f800000u);put(bytes+36+i*36+32,0x3e800000u);}
}
static void reject(unsigned char *bytes,size_t length,const char *fragment){
    amalur_scene_mesh mesh={0};char error[256];int okay=amalur_scene_mesh_parse(bytes,length,&mesh,error,sizeof(error));
    require(!okay&&strstr(error,fragment)!=NULL&&mesh.vertices==NULL,fragment);amalur_scene_mesh_clear(&mesh);
}
int main(void){
    unsigned char bytes[144];char error[256];amalur_scene_mesh mesh={0};
    fixture(bytes);require(amalur_scene_mesh_parse(bytes,sizeof(bytes),&mesh,error,sizeof(error)),error);
    require(mesh.vertex_count==3&&mesh.bounds_min[0]==0&&mesh.bounds_max[0]==1,"decoded count and bounds");
    require(mesh.vertices[9]==1&&mesh.vertices[19]==1&&mesh.vertices[5]==1&&mesh.vertices[6]==0.5f,"exact vertex fields");
    memset(bytes,0,sizeof(bytes));require(mesh.vertices[9]==1,"owned vertex storage survives source mutation");
    require(!amalur_scene_mesh_parse(bytes,sizeof(bytes),&mesh,error,sizeof(error))&&strstr(error,"already owns")!=NULL,"owned output not overwritten");
    amalur_scene_mesh_clear(&mesh);require(mesh.vertices==NULL&&mesh.vertex_count==0,"clear releases and resets");
    fixture(bytes);reject(bytes,35,"truncated");reject(bytes,143,"length differs");
    reject(bytes,AMALUR_SCENE_MAX_BYTES+1u,"admission limit");
    bytes[0]='x';reject(bytes,144,"magic");
    fixture(bytes);put(bytes+8,0);reject(bytes,144,"nonempty");
    fixture(bytes);put(bytes+8,2);reject(bytes,144,"triangle list");
    fixture(bytes);put(bytes+8,0xfffffffcu);reject(bytes,144,"length differs");
    fixture(bytes);put(bytes+12,0x7fc00000u);reject(bytes,144,"bounds");
    fixture(bytes);put(bytes+24,0x7f800000u);reject(bytes,144,"bounds");
    fixture(bytes);put(bytes+12,0x40000000u);reject(bytes,144,"bounds");
    fixture(bytes);put(bytes+24,0);put(bytes+28,0);reject(bytes,144,"no usable extent");
    fixture(bytes);put(bytes+24,0x60ad78ecu);reject(bytes,144,"coordinate range");
    fixture(bytes);put(bytes+36+36,0x40000000u);reject(bytes,144,"outside declared bounds");
    fixture(bytes);put(bytes+36+20,0x7f800000u);reject(bytes,144,"nonfinite");
    fixture(bytes);put(bytes+36+24,0x7fc00000u);reject(bytes,144,"nonfinite");
    printf("{\"ok\":true,\"checks\":%u,\"scope\":\"authored scene interchange parser and malformed-input handling\"}\n",checks);return 0;
}
