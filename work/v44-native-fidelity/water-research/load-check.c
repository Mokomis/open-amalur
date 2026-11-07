#include "oa_native_water.h"
#include <stdio.h>
#include <stdlib.h>
struct AAsset{FILE*f;long bytes;};
AAsset*AAssetManager_open(AAssetManager*a,const char*p,int mode){AAsset*x=(AAsset*)calloc(1,sizeof(*x));(void)a;(void)mode;x->f=fopen(p,"rb");if(!x->f){free(x);return NULL;}fseek(x->f,0,SEEK_END);x->bytes=ftell(x->f);fseek(x->f,0,SEEK_SET);return x;}
int AAsset_read(AAsset*a,void*p,size_t n){return (int)fread(p,1,n,a->f);}
off_t AAsset_getLength(AAsset*a){return (off_t)a->bytes;}
void AAsset_close(AAsset*a){fclose(a->f);free(a);}
int main(int argc,char**argv){oa_native_water w={0};AAssetManager am={0};float p[3]={-2629.17f,-88219.7f,6976.69f};if(argc!=2||!oa_native_water_open(&w,&am,argv[1]))return 2;if(!oa_native_water_contains(&w,404112,p,1))return 3;oa_native_water_gpu_close(&w);oa_native_water_close(&w);if(w.state)return 4;puts("Native water pack read/mesh bounds/context lifecycle PASS");return 0;}
