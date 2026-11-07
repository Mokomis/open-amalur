#include "native_light_volume_weights.h"
#include <assert.h>
#include <math.h>
#include <stdio.h>
static const oa_light_volume source_volumes[2]={
 {{4104.50244140625f,2541.97900390625f,12.481781005859375f},
  {0,0,0,1},{9.918001174926758f,8.458000183105469f,5.296000003814697f},2000},
 {{38989.69921875f,-1308.2301025390625f,55.30353546142578f},
  {0,0,0,1},{20,50,30},1000}
};
static int checks=0;
static void near_value(float actual,float expected,float tolerance)
{assert(fabsf(actual-expected)<=tolerance);checks++;}
static void normal(oa_light_volume *v,size_t n,const float p[3],float sw,
                   float *w,oa_light_volume_result *r)
{assert(oa_light_volume_weights(v,n,p,sw,OA_LIGHT_NORMAL,w,r)==OA_LIGHT_NORMAL_READY);checks++;}
int main(void)
{
 float spawn[3]={4312,2806,-314},eye[3]={4547.2138671875f,2805.9921875f,-116.858306884765625f};
 float point[3],weights[2],dist,half;
 oa_light_volume_result result;
 oa_light_volume v[2]={source_volumes[0],source_volumes[1]},rotated;
 normal(v,2,spawn,1,weights,&result);near_value(weights[0],1,0);near_value(weights[1],0,0);near_value(result.normalized_base,0,0);
 assert(oa_light_volume_distance(v+1,spawn,&dist));near_value(dist,24677.69921875f,0.001f);
 printf("spawn weights=(%.8f,%.8f) base=%.8f secondDistance=%.8f\n",weights[0],weights[1],result.normalized_base,dist);
 normal(v,2,eye,1,weights,&result);near_value(weights[0],1,0);near_value(weights[1],0,0);near_value(result.normalized_base,0,0);
 assert(oa_light_volume_distance(v+1,eye,&dist));near_value(dist,24442.484375f,0.001f);
 printf("camera weights=(%.8f,%.8f) base=%.8f secondDistance=%.8f\n",weights[0],weights[1],result.normalized_base,dist);
 point[0]=v[0].translation[0];point[1]=v[0].translation[1];point[2]=v[0].translation[2];
 normal(v,1,point,1,weights,&result);near_value(weights[0],1,0);
 half=(float)((double)v[0].scale[0]*1000.0)*.5f;
 point[0]=v[0].translation[0]+half;
 normal(v,1,point,1,weights,&result);near_value(weights[0],1,.00001f);
 point[0]=v[0].translation[0]+half+1000;
 normal(v,1,point,1,weights,&result);near_value(weights[0],.5f,.00001f);near_value(result.normalized_base,.5f,.00001f);
 point[0]=v[0].translation[0]+half+2000;
 normal(v,1,point,1,weights,&result);near_value(weights[0],0,.00001f);near_value(result.normalized_base,1,.00001f);
 point[0]+=1000;
 normal(v,1,point,1,weights,&result);near_value(weights[0],0,0);near_value(result.normalized_base,1,0);
 v[1]=v[0];
 normal(v,2,spawn,1,weights,&result);near_value(weights[0],.5f,0);near_value(weights[1],.5f,0);near_value(result.raw_local_total,2,0);near_value(result.normalized_base,0,0);
 normal(v,1,spawn,.25f,weights,&result);near_value(weights[0],.25f,0);near_value(result.normalized_base,.75f,0);
 v[0].fade=0;
 normal(v,1,spawn,1,weights,&result);near_value(weights[0],1,0);
 normal(v,1,point,1,weights,&result);near_value(weights[0],0,0);
 v[0]=source_volumes[0];
 assert(oa_light_volume_weights(v,1,spawn,1,OA_LIGHT_ADDITIONAL_OVERRIDE,weights,&result)==OA_LIGHT_ADDITIONAL_INPUT_REQUIRED);checks++;
 near_value(weights[0],1,0); /* Ordinary part only; no invented override. */
 weights[0]=123;result.normalized_base=456;
 assert(oa_light_volume_weights(v,1,spawn,1,OA_LIGHT_HARD_OVERRIDE,weights,&result)==OA_LIGHT_HARD_INPUT_REQUIRED);checks++;
 near_value(weights[0],123,0);near_value(result.normalized_base,456,0);
 rotated=v[0];rotated.translation[0]=rotated.translation[1]=rotated.translation[2]=0;
 rotated.scale[0]=2;rotated.scale[1]=rotated.scale[2]=1;
 rotated.quaternion[2]=.7071067690849304f;rotated.quaternion[3]=.7071067690849304f;rotated.fade=1000;
 point[0]=0;point[1]=-1250;point[2]=0;
 assert(oa_light_volume_distance(&rotated,point,&dist));near_value(dist,250,.001f);
 normal(&rotated,1,point,1,weights,&result);near_value(weights[0],.75f,.00001f);
 rotated.scale[0]=-1;assert(!oa_light_volume_distance(&rotated,point,&dist));checks++;
 rotated.scale[0]=1;rotated.quaternion[3]=3;assert(!oa_light_volume_distance(&rotated,point,&dist));checks++;
 normal(NULL,0,spawn,1,weights,&result);near_value(result.normalized_base,1,0);
 printf("PASS %d checks: spawn/camera/boundary/fade/outside/overlap/SpaceWeight/zeroFade/rotated/overrideModes/invalid/empty\n",checks);
 return 0;
}
