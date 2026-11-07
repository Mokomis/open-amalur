#ifndef OA_NATIVE_AMBIENT_CUBE_CHANNELS_H
#define OA_NATIVE_AMBIENT_CUBE_CHANNELS_H
#include <stdint.h>
#include <stddef.h>
/* Proven current outdoor source-decoder output -> active original cube bytes.
 * This source cube's historical converter swaps R/B relative to runtime.
 * Only use for that same outdoor cube source; indoor/unrelated assets unaudited.
 * Safe for src==dst. Face order/rows/alpha are unchanged. No sRGB conversion. */
static void oa_native_ambient_cube_channels(uint8_t *dst,const uint8_t *src,size_t pixels){
 size_t i;for(i=0;i<pixels;i++){uint8_t r=src[i*4],b=src[i*4+2];dst[i*4]=b;dst[i*4+1]=src[i*4+1];dst[i*4+2]=r;dst[i*4+3]=src[i*4+3];}
}
#endif
