// Open Amalur captured-scene camera experiment. Disabled unless explicitly enabled.
#pragma once
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
namespace oa_camera {
struct Pose { float yaw=0, pitch=0, right=0, forward=0; };
inline Pose pose;
inline bool Enabled() { const char* p=std::getenv("OA_CAMERA"); return p && p[0]=='1'; }
inline void Clamp() {
 pose.yaw=std::clamp(pose.yaw,-0.2f,0.2f); pose.pitch=std::clamp(pose.pitch,-0.13f,0.13f);
 pose.right=std::clamp(pose.right,-300.f,300.f); pose.forward=std::clamp(pose.forward,-300.f,300.f);
}
inline Pose Read() {
 // Local private control file is optional; a changed line overrides touch state once.
 static char previous[192]={};char line[192]={};
 FILE* f=std::fopen("/data/user/0/org.openamalur.nativebenchmark/files/camera.txt","r");
 if(f) { if(std::fgets(line,sizeof(line),f) && std::strcmp(line,previous)) {
  Pose next; if(std::sscanf(line,"%f %f %f %f",&next.yaw,&next.pitch,&next.right,&next.forward)==4 &&
   std::isfinite(next.yaw)&&std::isfinite(next.pitch)&&std::isfinite(next.right)&&std::isfinite(next.forward)) {pose=next;Clamp();}
  std::strncpy(previous,line,sizeof(previous)-1);
 } std::fclose(f); }
 return pose;
}
// Row-vector clip -> view -> camera delta -> clip. Projection measured from captured shader inputs.
inline void Transform(const float* src,float* dst,const Pose& p) {
 if(p.yaw==0 && p.pitch==0 && p.right==0 && p.forward==0) {std::memcpy(dst,src,64);return;}
 constexpr double fx=1.311106091287448, fy=2.330855274807898, q=1.00004996337216, nearTerm=-26.1875;
 const double cy=std::cos(p.yaw),sy=std::sin(p.yaw),cp=std::cos(p.pitch),sp=std::sin(p.pitch);
 for(int row=0;row<4;++row) {
  const float* a=src+4*row;
  const double h=(a[2]-q*a[3])/nearTerm;
  const double x=a[0]/fx-p.right*h,y=a[1]/fy,z=a[3]-p.forward*h;
  const double rx=cy*x-sy*z,rz=sy*x+cy*z;
  const double ry=cp*y-sp*rz,zz=sp*y+cp*rz;
  dst[row*4]=static_cast<float>(fx*rx);dst[row*4+1]=static_cast<float>(fy*ry);
  dst[row*4+2]=static_cast<float>(q*zz+nearTerm*h);dst[row*4+3]=static_cast<float>(zz);
 }
}
}
