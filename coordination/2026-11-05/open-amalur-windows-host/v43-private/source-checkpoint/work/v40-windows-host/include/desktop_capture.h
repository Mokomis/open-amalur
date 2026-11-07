#pragma once
int oa_desktop_reference_camera(float output[16],float eye[3]);
int oa_desktop_reference_active(void);
void oa_desktop_scene_state(int world,const float feet[3],float yaw,float pitch,float boom,const float mvp[16],const float eye[3],int clip,float hp,int grounded);
