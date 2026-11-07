#include "interaction_pick.h"
#include <math.h>
#include <stddef.h>
int oa_mesh_pick(const float *v,uint32_t total,uint32_t first,uint32_t count,const float eye[3],const float d[3],float reach,float hit[3],float *distance){
 uint32_t i;double best=reach,n;int found=0;
 if(!v||!eye||!d||!hit||!distance||first>total||count>total-first||count%3||!isfinite(reach)||reach<=0||reach>1000)return 0;
 for(i=0;i<3;i++)if(!isfinite(eye[i])||!isfinite(d[i]))return 0;n=(double)d[0]*d[0]+(double)d[1]*d[1]+(double)d[2]*d[2];if(fabs(n-1)>.002)return 0;
 for(i=first;i<first+count;i+=3){const float *a=v+(size_t)i*9,*b=a+9,*c=b+9;double e1[3],e2[3],p[3],t[3],q[3],det,u,w,at;unsigned j;
  for(j=0;j<3;j++){e1[j]=b[j]-a[j];e2[j]=c[j]-a[j];t[j]=eye[j]-a[j];}
  p[0]=d[1]*e2[2]-d[2]*e2[1];p[1]=d[2]*e2[0]-d[0]*e2[2];p[2]=d[0]*e2[1]-d[1]*e2[0];det=e1[0]*p[0]+e1[1]*p[1]+e1[2]*p[2];if(fabs(det)<1e-10)continue;
  u=(t[0]*p[0]+t[1]*p[1]+t[2]*p[2])/det;if(u<0||u>1)continue;q[0]=t[1]*e1[2]-t[2]*e1[1];q[1]=t[2]*e1[0]-t[0]*e1[2];q[2]=t[0]*e1[1]-t[1]*e1[0];w=(d[0]*q[0]+d[1]*q[1]+d[2]*q[2])/det;if(w<0||u+w>1)continue;at=(e2[0]*q[0]+e2[1]*q[1]+e2[2]*q[2])/det;if(at>.01&&at<=best){best=at;found=1;}
 }if(!found)return 0;for(i=0;i<3;i++)hit[i]=(float)(eye[i]+d[i]*best);*distance=(float)best;return 1;
}
