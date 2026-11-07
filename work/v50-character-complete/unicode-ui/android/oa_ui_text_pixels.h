#ifndef OA_UI_TEXT_PIXELS_INTERNAL_H
#define OA_UI_TEXT_PIXELS_INTERNAL_H
#include <stddef.h>
#include <stdint.h>
/* AndroidBitmap RGBA8888 rows -> owned tight straight-alpha RGBA.
   Caller validates dimensions/stride/total pixel limit before allocating. */
static void oa_ui_android_straight_rgba(uint8_t*dst,const uint8_t*src,
 unsigned width,unsigned height,size_t stride,int premul,int has_alpha){
 unsigned x,y;
 for(y=0;y<height;y++)for(x=0;x<width;x++){
  const uint8_t*p=src+(size_t)y*stride+x*4;
  uint8_t*d=dst+((size_t)y*width+x)*4;unsigned a=has_alpha?p[3]:255,k;
  d[3]=(uint8_t)a;
  for(k=0;k<3;k++){
   unsigned v=p[k];
   if(premul&&has_alpha)v=a?(v*255+a/2)/a:255;
   d[k]=(uint8_t)(v>255?255:v);
  }
 }
}
#endif
