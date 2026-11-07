#ifndef OA_NATIVE_AO_MATH_H
#define OA_NATIVE_AO_MATH_H
#include <math.h>
#include <string.h>
/* Derive current AO projection from a column-major GL VP. Perspective camera
 * only. Out contains native128-byte block. Depth input is stored hardware0..1.
 * This keeps the measured physical radius120/fade5800..6000. projScale=.15*h*py
 * comes from FUN_00c74280: height/(2*tan(FOV*.5))*radiusScale, where
 * FUN_00c982f0 sets radiusScale=.30000001192092896. Projected-matrix recovery
 * agrees with the reference FOV producer within1.1ppm. Explicit constants
 * may instead be supplied to oa_native_ao_render_constants for that reference.
 */
static int oa_native_ao_parameters(float out[32],float *depth_cut,
 const float gl_vp[16],int w,int h){
 double row[4][3],s2=0,s,a=0,b,px2=0,py2=0,xy=0,offx=0,offy=0;int i,j;
 if(!out||!depth_cut||!gl_vp||w<=0||h<=0)return 0;
 for(i=0;i<4;i++)for(j=0;j<3;j++)row[i][j]=(double)gl_vp[i+j*4];
 for(j=0;j<3;j++){s2+=row[3][j]*row[3][j];a+=row[2][j]*row[3][j];offx+=row[0][j]*row[3][j];offy+=row[1][j]*row[3][j];}
 if(!(s2>1e-12)||!isfinite(s2))return 0;s=sqrt(s2);a/=s2;offx/=s2;offy/=s2;
 for(j=0;j<3;j++){double x=row[0][j]-offx*row[3][j],y=row[1][j]-offy*row[3][j];px2+=x*x;py2+=y*y;xy+=x*y;}
 if(!(px2>0&&py2>0)||fabs(xy)>1e-4*sqrt(px2*py2))return 0;
 b=((double)gl_vp[14]-a*(double)gl_vp[15])/(2*s);
 if(!(b<0)||!isfinite(b))return 0;
 {double px=sqrt(px2)/s,py=sqrt(py2)/s,A=(a+1)*.5;
 memset(out,0,32*sizeof(float));
 out[0]=8;out[1]=1.3999999761581421f;out[2]=2;out[3]=.4000000059604645f;
 out[4]=0;out[5]=1;out[6]=(float)(.30000001192092896*.5*(double)h*py);out[7]=1;
 out[8]=1;out[9]=1.9073486328125e-6f;out[10]=5800;out[11]=.004999999888241291f;
 out[12]=120;out[13]=14400;out[14]=2985984000000.f;out[15]=2.6791839146528273e-12f;
 out[16]=(float)((-1-offx)/px);out[17]=(float)((1-offy)/py);out[18]=(float)(2/((double)w*px));out[19]=(float)(-2/((double)h*py));
 out[20]=(float)A;out[21]=(float)b;
 out[24]=(float)w;out[25]=(float)h;out[26]=1.f/w;out[27]=1.f/h;
 out[28]=(float)w;out[29]=(float)h;out[30]=1.f/w;out[31]=1.f/h;
 *depth_cut=(float)(A+b/6000.0);return isfinite(*depth_cut);}
}
#endif
