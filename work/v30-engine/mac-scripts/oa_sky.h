#ifndef OA_SKY_H
#define OA_SKY_H
#include <GLES3/gl3.h>
#include <stddef.h>
#include <stdint.h>
typedef struct oa_sky{GLuint program,gradient,lower,upper,array,buffer,indices;GLint mvp,eye,radius,time;GLsizei count;float lower_tint[4],upper_tint[4];int ready;}oa_sky;
int oa_sky_open(oa_sky *s,const uint8_t *bytes,size_t size);
void oa_sky_close(oa_sky *s);
void oa_sky_draw(const oa_sky *s,const float mvp[16],const float eye[3],float radius,float seconds,GLuint lut);
#endif
