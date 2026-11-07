#ifndef OA_CART_PROBE_H
#define OA_CART_PROBE_H
#include <GLES3/gl3.h>
struct AAssetManager;
// Independently loads one existing OAWP2 cube, without touching water ownership.
// path="world/water-native.bin", image=3594. Caller owns returned GL texture.
GLuint oa_cart_probe_open(struct AAssetManager*,const char *path,unsigned image);
#endif
