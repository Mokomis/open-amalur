#include <stdio.h>
#include <string.h>
#include "oa_ui_text_utf16.h"
#include "oa_ui_text_pixels.h"
#define CK(x) do{if(!(x)){fprintf(stderr,"FAIL line%d\n",__LINE__);return 2;}}while(0)
int main(void){
 uint16_t out[512];size_t n;unsigned i;char longtext[1026];
 const char*bad[]={"\xc0\xaf","\xed\xa0\x80","\xf4\x90\x80\x80","\xe2\x82","\x80","\xf8\x88\x80\x80\x80","a\nb","\xc2","\xe0\x80\xaf","\xf0\x80\x80\xaf","\xf5\x80\x80\x80","\xff",""};
 CK(oa_ui_android_utf16("Elrid",out,512,&n)&&n==5&&out[0]=='E'&&out[4]=='d');
 CK(oa_ui_android_utf16("\xc3\xa9",out,512,&n)&&n==1&&out[0]==0xe9);
 CK(oa_ui_android_utf16("e\xcc\x81",out,512,&n)&&n==2&&out[0]=='e'&&out[1]==0x301);
 CK(oa_ui_android_utf16("\xe4\xb8\xad\xe6\x96\x87",out,512,&n)&&n==2&&out[0]==0x4e2d&&out[1]==0x6587);
 CK(oa_ui_android_utf16("\xf0\x9f\x98\x80",out,512,&n)&&n==2&&out[0]==0xd83d&&out[1]==0xde00);
 CK(oa_ui_android_utf16("\xf4\x8f\xbf\xbf",out,512,&n)&&n==2&&out[0]==0xdbff&&out[1]==0xdfff);
 for(i=0;i<sizeof(bad)/sizeof(*bad);i++){n=999;CK(!oa_ui_android_utf16(bad[i],out,512,&n)&&n==0);}
 CK(!oa_ui_android_utf16(NULL,out,512,&n)&&n==0);
 CK(!oa_ui_android_utf16("\xf0\x9f\x98\x80",out,1,&n)&&n==0);
 CK(!oa_ui_android_utf16("ab",out,1,&n)&&n==0);
 for(i=0;i<256;i++)memcpy(longtext+4*i,"\xf0\x9f\x98\x80",4);longtext[1024]=0;
 CK(oa_ui_android_utf16(longtext,out,512,&n)&&n==512);
 memset(longtext,'a',257);longtext[257]=0;
 CK(!oa_ui_android_utf16(longtext,out,512,&n)&&n==0);
 {
  const uint8_t src[24]={64,32,16,128,0,0,0,0,99,99,99,99,25,50,75,255,128,64,0,128,99,99,99,99};
  const uint8_t expected[16]={128,64,32,128,255,255,255,0,25,50,75,255,255,128,0,128};
  uint8_t dst[16];
  oa_ui_android_straight_rgba(dst,src,2,2,12,1,1);CK(!memcmp(dst,expected,16));
  oa_ui_android_straight_rgba(dst,src,2,2,12,0,1);CK(!memcmp(dst,src,8)&&!memcmp(dst+8,src+12,8));
  oa_ui_android_straight_rgba(dst,src,2,2,12,1,0);CK(dst[3]==255&&dst[7]==255&&dst[11]==255&&dst[15]==255&&dst[0]==64);
  puts("PASS stride-aware premultiplied->straight RGBA including0/128/255alpha, saturation, color channels, already-straight and opaque rows");
 }
 puts("PASS exact UTF8->UTF16: ASCII/composed/decomposed/CJK/nonBMP/maxscalar;13invalid encodings +NULL/control/empty/capacity/257scalar reject;256nonBMP=512UTF16units");
 return 0;
}
