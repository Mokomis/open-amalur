#define GL_APICALL
#include "oa_cart_probe.h"
#include <android/asset_manager.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
struct AAsset{unsigned char *p;size_t n;};
static const char *input;
AAsset *AAssetManager_open(AAssetManager *m,const char *p,int mode){FILE*f;AAsset*a;(void)m;(void)p;(void)mode;f=fopen(input,"rb");if(!f)return NULL;a=(AAsset*)calloc(1,sizeof(*a));if(!a){fclose(f);return NULL;}fseek(f,0,SEEK_END);a->n=(size_t)ftell(f);fseek(f,0,SEEK_SET);a->p=(unsigned char*)malloc(a->n);if(!a->p||fread(a->p,1,a->n,f)!=a->n){free(a->p);free(a);fclose(f);return NULL;}fclose(f);return a;}
const void *AAsset_getBuffer(AAsset *a){return a->p;}
off64_t AAsset_getLength64(AAsset *a){return(off64_t)a->n;}
int AAsset_read(AAsset *a,void *b,size_t n){if(n>a->n)return -1;memcpy(b,a->p,n);return(int)n;}
void AAsset_close(AAsset *a){free(a->p);free(a);}
static unsigned calls;static int bad_order;static size_t bytes;static uint64_t fnv=UINT64_C(14695981039346656037);static int maxlevel=-1;
void GL_APIENTRY glGenTextures(GLsizei n,GLuint *t){int i;for(i=0;i<n;i++)t[i]=123;}
void GL_APIENTRY glBindTexture(GLenum t,GLuint x){(void)t;(void)x;}
void GL_APIENTRY glTexImage2D(GLenum target,GLint level,GLint format,GLsizei w,GLsizei h,GLint border,GLenum f,GLenum type,const void *p){size_t i,n=(size_t)w*h*4u;const unsigned char*b=(const unsigned char*)p;(void)target;(void)level;(void)format;(void)border;(void)f;(void)type;if(target!=GL_TEXTURE_CUBE_MAP_POSITIVE_X+calls%6u||level!=(GLint)(calls/6u)||w!=(128>>(calls/6u))||h!=w)bad_order=1;calls++;bytes+=n;for(i=0;i<n;i++){fnv^=b[i];fnv*=UINT64_C(1099511628211);}}
void GL_APIENTRY glTexParameteri(GLenum t,GLenum name,GLint value){(void)t;if(name==GL_TEXTURE_MAX_LEVEL)maxlevel=value;}
GLenum GL_APIENTRY glGetError(void){return GL_NO_ERROR;}
void GL_APIENTRY glDeleteTextures(GLsizei n,const GLuint *t){(void)n;(void)t;}
int main(int argc,char **argv){GLuint t;struct AAssetManager assets={0};if(argc!=3)return 2;input=argv[1];t=oa_cart_probe_open(&assets,"glassmetalprobe-probes.bin",(unsigned)strtoul(argv[2],0,10));printf("{\"texture\":%u,\"face_mip_uploads\":%u,\"rgba_bytes\":%zu,\"max_level\":%d,\"fnv1a64\":\"%016llx\"}\n",t,calls,bytes,maxlevel,(unsigned long long)fnv);return(!bad_order&&t==123&&calls==36&&bytes==524160&&maxlevel==5)?0:1;}
