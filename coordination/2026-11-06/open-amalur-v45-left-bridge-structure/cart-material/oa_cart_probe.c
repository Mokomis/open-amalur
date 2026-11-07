#include "oa_cart_probe.h"
#include <android/asset_manager.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
static uint32_t word(const unsigned char *p){uint32_t v;memcpy(&v,p,4);return v;}
GLuint oa_cart_probe_open(AAssetManager *assets,const char *path,unsigned wanted){
    AAsset *a=AAssetManager_open(assets,path,AASSET_MODE_BUFFER);
    const unsigned char *p;unsigned char *owned=NULL;size_t n,o=16;unsigned nt,k;
    GLuint texture=0;
    if(!a)return 0;
    n=(size_t)AAsset_getLength64(a);p=(const unsigned char*)AAsset_getBuffer(a);
    if(!p){owned=(unsigned char*)malloc(n?n:1);if(!owned||AAsset_read(a,owned,n)!=(int)n)goto done;p=owned;}
    if(n<16||memcmp(p,"OAWP",4)||word(p+4)!=2||word(p+8)>64)goto done;
    nt=word(p+8);
    for(k=0;k<nt;k++){
        unsigned id,faces,w0,h0,levels,total,j;size_t copied=0;
        if(o>n||n-o<24)goto fail;
        id=word(p+o);faces=word(p+o+4);w0=word(p+o+8);h0=word(p+o+12);
        levels=word(p+o+16);total=word(p+o+20);o+=24;
        if(!w0||!h0||levels<1||levels>16||(faces!=1&&faces!=6))goto fail;
        if(id==wanted){if(faces!=6||w0!=h0)goto fail;glGenTextures(1,&texture);glBindTexture(GL_TEXTURE_CUBE_MAP,texture);}
        for(j=0;j<levels;j++){
            unsigned w,h,bytes,face;size_t one,expect;
            if(o>n||n-o<12)goto fail;
            w=word(p+o);h=word(p+o+4);bytes=word(p+o+8);o+=12;
            one=(size_t)w*h*4u;expect=one*faces;
            if(w!=(w0>>j?w0>>j:1)||h!=(h0>>j?h0>>j:1)||expect!=bytes||bytes>n-o)goto fail;
            if(texture)for(face=0;face<6;face++)glTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X+face,(GLint)j,GL_RGBA8,(GLsizei)w,(GLsizei)h,0,GL_RGBA,GL_UNSIGNED_BYTE,p+o+face*one);
            o+=bytes;copied+=bytes;
        }
        if(copied!=total)goto fail;
        if(texture){
            glTexParameteri(GL_TEXTURE_CUBE_MAP,GL_TEXTURE_BASE_LEVEL,0);
            glTexParameteri(GL_TEXTURE_CUBE_MAP,GL_TEXTURE_MAX_LEVEL,(GLint)levels-1);
            glTexParameteri(GL_TEXTURE_CUBE_MAP,GL_TEXTURE_MIN_FILTER,GL_LINEAR_MIPMAP_LINEAR);
            glTexParameteri(GL_TEXTURE_CUBE_MAP,GL_TEXTURE_MAG_FILTER,GL_LINEAR);
            glTexParameteri(GL_TEXTURE_CUBE_MAP,GL_TEXTURE_WRAP_S,GL_CLAMP_TO_EDGE);
            glTexParameteri(GL_TEXTURE_CUBE_MAP,GL_TEXTURE_WRAP_T,GL_CLAMP_TO_EDGE);
            glTexParameteri(GL_TEXTURE_CUBE_MAP,GL_TEXTURE_WRAP_R,GL_CLAMP_TO_EDGE);
            glBindTexture(GL_TEXTURE_CUBE_MAP,0);
            if(glGetError()!=GL_NO_ERROR)goto fail;
            goto done;
        }
    }
    goto done;
fail:
    if(texture){glDeleteTextures(1,&texture);texture=0;}
done:
    free(owned);AAsset_close(a);return texture;
}
