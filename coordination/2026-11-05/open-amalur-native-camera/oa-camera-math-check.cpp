#include "oa-camera-control.h"
#include <cassert>
#include <cstdio>
int main(){
 const float p[16]={1.311106091287448f,0,0,0,0,2.330855274807898f,0,0,0,0,1.00004996337216f,1,0,0,-26.1875f,0};
 float out[16];oa_camera::Transform(p,out,{});assert(std::memcmp(p,out,sizeof(p))==0);
 auto project=[](const float*m,float x,float y,float z,int c){return x*m[c]+y*m[4+c]+z*m[8+c]+m[12+c];};
 oa_camera::Pose pose;pose.yaw=.1f;oa_camera::Transform(p,out,pose);
 double ratio=project(out,0,0,100,0)/project(out,0,0,100,3);assert(std::abs(ratio+1.311106091287448*std::tan(.1))<1e-6);
 pose={};pose.right=20;oa_camera::Transform(p,out,pose);ratio=project(out,0,0,100,0)/project(out,0,0,100,3);assert(std::abs(ratio+1.311106091287448*.2)<1e-6);
 pose={};pose.forward=20;oa_camera::Transform(p,out,pose);assert(std::abs(project(out,0,0,100,3)-80)<1e-5);
 pose={};pose.pitch=.1f;oa_camera::Transform(p,out,pose);ratio=project(out,0,0,100,1)/project(out,0,0,100,3);assert(std::abs(ratio+2.330855274807898*std::tan(.1))<1e-6);
 std::puts("PASS: exact identity, yaw center ray, pitch center ray, lateral parallax, forward depth");
}
