#include "oa_material_probes.h"
#include <android/asset_manager.h>
#include <stdio.h>
#include <string.h>
#include <stdint.h>
static unsigned loads,deletes;static AAsset asset;static uint32_t image;
#define CHECK(c) do{if(!(c)){fprintf(stderr,"FAIL line%d %s\n",__LINE__,#c);return 1;}}while(0)
AAsset *AAssetManager_open(AAssetManager*m,const char*name,int mode){(void)m;(void)name;(void)mode;return &asset;}
off64_t AAsset_getLength64(AAsset*a){return a->size;}
const void *AAsset_getBuffer(AAsset*a){return a->bytes;}
void AAsset_close(AAsset*a){(void)a;}
int __android_log_print(int p,const char*t,const char*f,...){(void)p;(void)t;(void)f;return 0;}
GLuint oa_cart_probe_open(AAssetManager*a,const char*p,unsigned id){(void)a;(void)p;image=id;return ++loads+500;}
void glDeleteTextures(int n,const GLuint*t){(void)t;deletes+=n;}
int main(void){unsigned char bytes[64]={0};uint32_t rows[]={3,2,55,7,66,9,55};oa_material_probes*p;GLuint t;
 memcpy(bytes,"OAPM001",8);memcpy(bytes+8,rows,sizeof(rows));asset.bytes=bytes;asset.size=12+3*8;
 p=oa_material_probes_open(0,31);CHECK(p);
 t=oa_material_probes_get(p,9);CHECK(t&&image==55&&loads==1);
 CHECK(oa_material_probes_get(p,2)==t&&loads==1); /* reverse-order reuse */
 CHECK(oa_material_probes_get(p,123)==0&&loads==1); /* no inherited prior texture */
 CHECK(oa_material_probes_get(p,7)!=t&&image==66&&loads==2);
 oa_material_probes_gpu_close(p);CHECK(deletes==2);
 CHECK(oa_material_probes_get(p,2)!=t&&loads==3);oa_material_probes_gpu_close(p);CHECK(deletes==3);oa_material_probes_close(p);
 rows[2]=0;memcpy(bytes+8,rows,sizeof(rows));CHECK(!oa_material_probes_open(0,31));rows[2]=55;
 rows[3]=2;memcpy(bytes+8,rows,sizeof(rows));CHECK(!oa_material_probes_open(0,31));
 asset.size--;CHECK(!oa_material_probes_open(0,31));oa_material_probes_gpu_close(0);oa_material_probes_close(0);
 puts("PASS per-material ownership: reverse-order shared-cube reuse, no inherited binding, context recreation, single deletion, invalid/zero mapping rejection");return 0;}
