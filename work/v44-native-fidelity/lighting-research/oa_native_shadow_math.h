#ifndef OA_NATIVE_SHADOW_MATH_H
#define OA_NATIVE_SHADOW_MATH_H
#include <math.h>
#include <string.h>
typedef struct oa_native_shadow_config {int resolution;float split[4],overlap[3],bias[3],projection_scale[2],bounds_center[3],bounds_half[3];} oa_native_shadow_config;
typedef struct oa_native_shadow_cascade {float vp[16],screen_to_light[16],fade[4],center[3],half_extent,near_z,far_z;} oa_native_shadow_cascade;
static void oa_native_shadow_defaults(oa_native_shadow_config *c){memset(c,0,sizeof(*c));c->resolution=1024;c->split[0]=1;c->split[1]=500;c->split[2]=1500;c->split[3]=10000;c->overlap[0]=60;c->overlap[1]=100;c->overlap[2]=400;c->bias[0]=-7.999999797903001e-5f;c->bias[1]=-.0001500000071246177f;c->bias[2]=-.00039999998989515007f;c->bounds_center[0]=-25;c->bounds_center[1]=-25;c->bounds_center[2]=4921.98388671875f;c->bounds_half[0]=125000;c->bounds_half[1]=125000;c->bounds_half[2]=50000;}
static double oa_ns_dot(const double a[3],const double b[3]){return a[0]*b[0]+a[1]*b[1]+a[2]*b[2];}
static void oa_ns_cross(double o[3],const double a[3],const double b[3]){o[0]=a[1]*b[2]-a[2]*b[1];o[1]=a[2]*b[0]-a[0]*b[2];o[2]=a[0]*b[1]-a[1]*b[0];}
static int oa_ns_normalize(double a[3]){double n=sqrt(oa_ns_dot(a,a));int j;if(!(n>1e-12)||!isfinite(n))return 0;for(j=0;j<3;j++)a[j]/=n;return 1;}
/* Native symmetric-frustum sphere from FUN_00cf2ea0 -> SphereBuilder.
 * Arbitrary rotated/translated perspective camera; non-centred/skew/ortho
 * cameras explicitly rejected. Optional actual eye avoids floatVP precision
 * loss at large translations. GLVP is column-major, sampled depth0..1.
 * ab receives depthA/B for Z=B/(depth-A). vp is GLclip caster matrix;
 * screen_to_light maps native screenNDC*Z to top-left shadowUV+biaseddepth.\n * Optional projection_scale[2]=pureGLProjection[0],[5] preserves native FOV\n * precision before rotation; zero recovers them fromVP (a one-texel snap\n * difference can occur exactly at rounding boundaries). */
static int oa_native_shadow_parameters(oa_native_shadow_cascade out[3],float ab[2],
 const float vp[16],const float eye_in[3],const float sun[3],const oa_native_shadow_config *cfg){
 double rows[4][3],R[3],U[3],F[3],eye[3],D[3],LR[3],LU[3],world_up[3]={0,0,1};double s2,a=0,b,px,py,offx=0,offy=0;int i,j,k,h;
 if(!out||!ab||!vp||!sun||!cfg||cfg->resolution<8)return 0;
 for(i=0;i<4;i++)for(j=0;j<3;j++)rows[i][j]=(double)vp[i+j*4];
 s2=oa_ns_dot(rows[3],rows[3]);if(!(s2>1e-12))return 0;
 a=oa_ns_dot(rows[2],rows[3])/s2;offx=oa_ns_dot(rows[0],rows[3])/s2;offy=oa_ns_dot(rows[1],rows[3])/s2;
 if(fabs(offx)>1e-5||fabs(offy)>1e-5)return 0;
 for(j=0;j<3;j++){R[j]=rows[0][j];U[j]=rows[1][j];F[j]=rows[3][j];D[j]=-(double)sun[j];}
 px=cfg->projection_scale[0]>0?cfg->projection_scale[0]:sqrt(oa_ns_dot(R,R)/s2);py=cfg->projection_scale[1]>0?cfg->projection_scale[1]:sqrt(oa_ns_dot(U,U)/s2);
 if(!(px>0&&py>0)||!oa_ns_normalize(R)||!oa_ns_normalize(U)||!oa_ns_normalize(F)||!oa_ns_normalize(D))return 0;
 if(fabs(oa_ns_dot(R,U))>1e-5)return 0;
 if(eye_in){for(j=0;j<3;j++)eye[j]=eye_in[j];}else{double er=-(double)vp[12]/(px*sqrt(s2)),eu=-(double)vp[13]/(py*sqrt(s2)),ef=-(double)vp[15]/sqrt(s2);for(j=0;j<3;j++)eye[j]=R[j]*er+U[j]*eu+F[j]*ef;}
 b=((double)vp[14]-a*(double)vp[15])/(2*sqrt(s2));if(!(b<0)||!isfinite(b))return 0;ab[0]=(float)((a+1)*.5);ab[1]=(float)b;
 oa_ns_cross(LR,world_up,D);if(!oa_ns_normalize(LR)){world_up[0]=0;world_up[1]=1;world_up[2]=0;oa_ns_cross(LR,world_up,D);if(!oa_ns_normalize(LR))return 0;}oa_ns_cross(LU,D,LR);
 for(i=0;i<3;i++){
  double n=i?(double)cfg->split[i]-cfg->overlap[i-1]:cfg->split[0],f=cfg->split[i+1];double t2=1/(px*px)+1/(py*py),cz=(1+t2)*(n+f)*.5,radius,e,center[3],light_pos[3],bc[3],support=0,zmin,zmax,range,ld[16],map[16];
  if(!(n>0&&f>n&&cfg->overlap[i]>0))return 0;if(cz>f)cz=f;radius=sqrt(t2*f*f+(f-cz)*(f-cz));e=radius*((double)cfg->resolution+4)/cfg->resolution;
  for(j=0;j<3;j++){center[j]=eye[j]+F[j]*cz;if(j<2)center[j]=round(center[j]);light_pos[j]=center[j]-D[j]*(e+.009999999776482582);bc[j]=cfg->bounds_center[j]-light_pos[j];support+=fabs(D[j])*cfg->bounds_half[j];}
  zmin=oa_ns_dot(D,bc)-support;zmax=2*e+.009999999776482582;if(zmin>.009999999776482582)zmin=.009999999776482582;range=zmax-zmin;if(!(range>0))return 0;
  memset(ld,0,sizeof(ld));ld[15]=1;
  for(j=0;j<3;j++){ld[j*4]=LR[j]/e;ld[j*4+1]=LU[j]/e;ld[j*4+2]=D[j]/range;}
  ld[12]=round((-oa_ns_dot(LR,center)/e)*(cfg->resolution*.5))*(2.0/cfg->resolution);ld[13]=round((-oa_ns_dot(LU,center)/e)*(cfg->resolution*.5))*(2.0/cfg->resolution);ld[14]=-(oa_ns_dot(D,light_pos)+zmin)/range;
  for(k=0;k<16;k++)out[i].vp[k]=(float)ld[k];for(j=0;j<4;j++)out[i].vp[j*4+2]=(float)(2*ld[j*4+2]-ld[j*4+3]);
  for(j=0;j<4;j++){map[j*4]=.5*ld[j*4]+.5*ld[j*4+3];map[j*4+1]=-.5*ld[j*4+1]+.5*ld[j*4+3];map[j*4+2]=ld[j*4+2]+cfg->bias[i]*ld[j*4+3];map[j*4+3]=ld[j*4+3];}
  for(k=0;k<4;k++)for(j=0;j<4;j++){
   double v=0;if(k==0)for(h=0;h<3;h++)v+=map[h*4+j]*R[h]/px;
   if(k==1)for(h=0;h<3;h++)v+=map[h*4+j]*U[h]/py;
   if(k==2)for(h=0;h<3;h++)v+=map[h*4+j]*F[h];
   if(k==3){v=map[12+j];for(h=0;h<3;h++)v+=map[h*4+j]*eye[h];}
   out[i].screen_to_light[k*4+j]=(float)v;
  }
  out[i].screen_to_light[15]=1+(i==0?-.0010000000474974513f:(i==1?-.001500000013038516f:-.0020000000949949026f));out[i].fade[0]=1;out[i].fade[1]=-1/cfg->overlap[i];out[i].fade[2]=(float)-n;out[i].fade[3]=(float)(f/cfg->overlap[i]);
  out[i].half_extent=(float)e;out[i].near_z=(float)zmin;out[i].far_z=(float)zmax;for(j=0;j<3;j++)out[i].center[j]=(float)center[j];
 }
 return 1;
}
#endif
