#ifndef OA_UI_TEXT_UTF16_INTERNAL_H
#define OA_UI_TEXT_UTF16_INTERNAL_H
#include <stddef.h>
#include <stdint.h>
/* Private, pure C99 decoder used by JNI NewString (NEVER NewStringUTF for text).
   Bounded1024UTF8bytes/256scalars/512UTF16units; no control/surrogate/overlong.
   On failure count remains0; partially written scratch is discarded by caller. */
static int oa_ui_android_utf16(const char*s,uint16_t*out,size_t capacity,size_t*count){
 size_t i=0,n=0;unsigned scalar=0;if(count)*count=0;
 if(!s||!out||!count)return 0;
 while(i<=1024&&s[i]){
  unsigned char c=(unsigned char)s[i++];uint32_t cp,min=0;unsigned more=0,j;
  if(c<128)cp=c;
  else if(c>=0xc2&&c<=0xdf){cp=c&31;more=1;min=0x80;}
  else if(c>=0xe0&&c<=0xef){cp=c&15;more=2;min=0x800;}
  else if(c>=0xf0&&c<=0xf4){cp=c&7;more=3;min=0x10000;}
  else return 0;
  for(j=0;j<more;j++){unsigned char b;if(i>=1024)return 0;b=(unsigned char)s[i++];if((b&0xc0)!=0x80)return 0;cp=(cp<<6)|(b&63);}
  if(cp<min||cp>0x10ffff||(cp>=0xd800&&cp<=0xdfff)||cp<32||cp==127||++scalar>256)return 0;
  if(cp<0x10000){if(n>=capacity)return 0;out[n++]=(uint16_t)cp;}
  else{if(capacity-n<2)return 0;cp-=0x10000;out[n++]=(uint16_t)(0xd800+(cp>>10));out[n++]=(uint16_t)(0xdc00+(cp&1023));}
 }
 if(i>1024||!n)return 0;*count=n;return 1;
}
#endif
