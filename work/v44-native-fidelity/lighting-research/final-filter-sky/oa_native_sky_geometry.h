#ifndef OA_NATIVE_SKY_GEOMETRY_H
#define OA_NATIVE_SKY_GEOMETRY_H
#include <math.h>
#include <stdint.h>
enum{OA_NATIVE_SKY_VERTICES=576,OA_NATIVE_SKY_INDICES=1722};
/* FUN_00d1f6f0: fixed global sky geometry, independent of camera/room/save.
 * Original radians approximation, accumulated float angles, and double radii. */
static void oa_native_sky_geometry(float vertices[576][5],uint16_t indices[1722]){
 const double radians=.017453279346227646;const float radius=420000,shift=-210000;
 int ring,segment,i=0,j,k;float step=(float)(15.0*radians),a=0,b=(float)(15.0*radians);
 for(ring=0;ring<6;ring++){float u=0,v=step;for(segment=0;segment<24;segment++){
  float ca=(float)cos((double)a),cb=(float)cos((double)b),sa=(float)sin((double)a),sb=(float)sin((double)b);
  float cu=(float)cos((double)u),cv=(float)cos((double)v),su=(float)sin((double)u),sv=(float)sin((double)v);
  double r0=(double)radius*sa,r1=(double)radius*sb;float z0=(float)((double)shift+(double)radius*ca),z1=(float)((double)shift+(double)radius*cb);
  float q[4][5]={{(float)(cu*r0),(float)(su*r0),z0,ca,0},{(float)(cu*r1),(float)(su*r1),z1,cb,0},{(float)(cv*r0),(float)(sv*r0),z0,ca,0},{(float)(cv*r1),(float)(sv*r1),z1,cb,0}};
  for(j=0;j<4;j++,i++)for(k=0;k<5;k++)vertices[i][k]=q[j][k];
  u=v;v=(float)((double)v+(double)step);
 }a=b;b=(float)((double)b+(double)step);}
 for(i=0;i<574;i++){indices[i*3]=(uint16_t)i;indices[i*3+1]=(uint16_t)(i+(i&1)+1);indices[i*3+2]=(uint16_t)(i-(i&1)+2);}
}
#endif
