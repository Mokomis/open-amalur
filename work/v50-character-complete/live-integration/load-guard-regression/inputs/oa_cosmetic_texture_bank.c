#include "oa_cosmetic_texture_bank.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include "opening_sha256.h"
#include "cosmetic_texture_pins.inc"
static int pinned(const uint8_t*b,size_t n,const CMBankPin*p){uint8_t d[32];unsigned i;if(n!=p->bytes)return 0;sha256(b,n,d);for(i=0;i<32;i++){unsigned x;if(sscanf(p->sha+2*i,"%2x",&x)!=1||d[i]!=x)return 0;}return 1;}
static uint32_t u32(const uint8_t*p){return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;}
int oa_cm_bank_open(oa_cm_texture_bank*b,oa_cm_read_file r,void*u,const char*prefix){size_t n=prefix?strlen(prefix):0;if(!b||!r||n>=sizeof(b->prefix)||b->count)return 0;memset(b,0,sizeof(*b));b->read=r;b->user=u;if(n)memcpy(b->prefix,prefix,n+1);return 1;}
void oa_cm_bank_close(oa_cm_texture_bank*b){unsigned i;if(!b)return;for(i=0;i<b->count;i++)if(b->entries[i].texture)glDeleteTextures(1,&b->entries[i].texture);memset(b,0,sizeof(*b));}
GLuint oa_cm_bank_texture(void*context,uint32_t asset,GLenum target){oa_cm_texture_bank*b=(oa_cm_texture_bank*)context;uint8_t*data=NULL;size_t n=0,at,start;uint32_t w,h,levels,k,faces,fmt;GLuint t=0;char path[640];int z;unsigned i;const CMBankPin*pin=NULL;
 if(!b||!b->read||asset<=1||(target!=GL_TEXTURE_2D&&target!=GL_TEXTURE_CUBE_MAP))return 0;
 for(i=0;i<b->count;i++)if(b->entries[i].asset==asset&&b->entries[i].target==target)return b->entries[i].texture;
 for(i=0;i<sizeof(cm_bank_pins)/sizeof(cm_bank_pins[0]);i++)if(cm_bank_pins[i].asset==asset&&cm_bank_pins[i].target==target){pin=cm_bank_pins+i;break;}if(!pin)return 0;
 if(b->count>=512)return 0;z=snprintf(path,sizeof(path),"%s%u.%s",b->prefix,asset,target==GL_TEXTURE_2D?"oatx":"oacube");if(z<0||(size_t)z>=sizeof(path)||!b->read(b->user,path,&data,&n)||!data)goto done;
 if(!pinned(data,n,pin))goto done;
 if(target==GL_TEXTURE_2D){if(n<20||memcmp(data,"OATX",4)||(u32(data+4)!=GL_RGBA8&&u32(data+4)!=GL_SRGB8_ALPHA8))goto done;w=u32(data+8);h=u32(data+12);levels=u32(data+16);faces=1;start=20;fmt=u32(data+4);}
 else{if(n<24||memcmp(data,"OACUBE1\0",8)||u32(data+20)!=GL_RGBA8)goto done;w=u32(data+8);h=u32(data+12);levels=u32(data+16);faces=6;start=24;fmt=GL_RGBA8;if(w!=h)goto done;}
 if(!w||!h||w>512||h>512||!levels||levels>10)goto done;
 at=start;for(k=0;k<levels;k++){uint32_t ww=w>>k,hh=h>>k;size_t bytes;if(!ww)ww=1;if(!hh)hh=1;bytes=(size_t)ww*hh*4*faces;if(at>n||n-at<4||u32(data+at)!=bytes||bytes>n-at-4)goto done;at+=4+bytes;}if(at!=n)goto done;
 glGenTextures(1,&t);glBindTexture(target,t);glPixelStorei(GL_UNPACK_ALIGNMENT,1);at=start;
 for(k=0;k<levels;k++){uint32_t ww=w>>k,hh=h>>k;size_t bytes;if(!ww)ww=1;if(!hh)hh=1;bytes=(size_t)ww*hh*4;at+=4;for(i=0;i<faces;i++)glTexImage2D(faces==6?GL_TEXTURE_CUBE_MAP_POSITIVE_X+i:target,(GLint)k,(GLint)fmt,(GLsizei)ww,(GLsizei)hh,0,GL_RGBA,GL_UNSIGNED_BYTE,data+at+bytes*i);at+=bytes*faces;}
 glTexParameteri(target,GL_TEXTURE_BASE_LEVEL,0);glTexParameteri(target,GL_TEXTURE_MAX_LEVEL,(GLint)levels-1);glTexParameteri(target,GL_TEXTURE_MIN_FILTER,GL_LINEAR_MIPMAP_LINEAR);glTexParameteri(target,GL_TEXTURE_MAG_FILTER,GL_LINEAR);glTexParameteri(target,GL_TEXTURE_WRAP_S,faces==6?GL_CLAMP_TO_EDGE:GL_REPEAT);glTexParameteri(target,GL_TEXTURE_WRAP_T,faces==6?GL_CLAMP_TO_EDGE:GL_REPEAT);if(faces==6)glTexParameteri(target,GL_TEXTURE_WRAP_R,GL_CLAMP_TO_EDGE);
 if(glGetError()!=GL_NO_ERROR){glDeleteTextures(1,&t);t=0;goto done;}b->entries[b->count].asset=asset;b->entries[b->count].target=target;b->entries[b->count++].texture=t;
done:free(data);return t;
}
