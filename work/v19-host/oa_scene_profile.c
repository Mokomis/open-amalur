#include "oa_scene_profile.h"
#include <android/asset_manager.h>
#include <android/log.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
void oa_scene_profile_close(oa_scene_profile *s){if(s){free(s->lights);memset(s,0,sizeof(*s));}}
int oa_scene_profile_parse(oa_scene_profile *s,const void *bytes,size_t size){
 const unsigned char *b=(const unsigned char*)bytes;uint32_t u[7];float v[29];unsigned i;oa_scene_profile q={0};size_t pos=152,expected;
 if(!s||!b||size<152||memcmp(b,"OASCENV1",8))return 0;
 memcpy(u,b+8,sizeof(u));memcpy(v,b+36,sizeof(v));
 if(u[0]!=1||!u[1]||!u[2]||(u[3]&~7u)||u[4]>512||u[5]!=1536||u[6]!=16384)return 0;
 if(!(u[3]&OA_SCENE_AMBIENT_GLOBALS_KNOWN)&&!(u[3]&OA_SCENE_PREVIEW))return 0;
 expected=152+(size_t)u[4]*32+1536+16384;if(size!=expected)return 0;
 for(i=0;i<29;i++)if(!isfinite(v[i])||fabsf(v[i])>10000000.f)return 0;
 {float n=v[4]*v[4]+v[5]*v[5]+v[6]*v[6];if(n<.9f||n>1.1f)return 0;}
 if(v[17]<0||v[19]<0||v[20]<=0||v[21]<=0||v[22]<0)return 0;
 q.space=u[1];q.region=u[2];q.flags=u[3];q.light_count=u[4];
 memcpy(q.spawn,v,12);q.yaw=v[3];memcpy(q.sun_direction,v+4,12);memcpy(q.sun_color,v+7,12);memcpy(q.shadow,v+10,16);memcpy(q.fog_color,v+14,12);
 q.fog_density=v[17];q.fog_start=v[18];memcpy(q.post,v+19,16);memcpy(q.sky,v+23,16);memcpy(q.ambient_scales,v+27,8);
 q.lights=(float(*)[8])malloc((size_t)(q.light_count?q.light_count:1)*32);if(!q.lights)return 0;
 memcpy(q.lights,b+pos,(size_t)q.light_count*32);pos+=(size_t)q.light_count*32;
 for(i=0;i<q.light_count;i++){unsigned j;for(j=0;j<8;j++)if(!isfinite(q.lights[i][j])||fabsf(q.lights[i][j])>10000000.f)goto invalid;
  if(q.lights[i][3]<0||q.lights[i][7]<=q.lights[i][3])goto invalid;}
 memcpy(q.cube,b+pos,1536);memcpy(q.lut,b+pos+1536,16384);q.active=1;
 oa_scene_profile_close(s);*s=q;return 1;
 invalid:free(q.lights);return 0;
}
int oa_scene_profile_load(oa_scene_profile *s,AAssetManager *assets){
 AAsset *a=AAssetManager_open(assets,"scene-profile.bin",AASSET_MODE_BUFFER);int ok=0;off64_t n;
 if(!a)return 0;n=AAsset_getLength64(a);if(n>0&&n<1024*1024)ok=oa_scene_profile_parse(s,AAsset_getBuffer(a),(size_t)n);AAsset_close(a);
 if(ok)__android_log_print(ANDROID_LOG_INFO,"OpemAmalurScene","SCENE_PROFILE space=%u region=%u lights=%u indoor=%d preview=%d ambient_globals_known=%d",s->space,s->region,s->light_count,!!(s->flags&1),!!(s->flags&2),!!(s->flags&4));
 else __android_log_print(ANDROID_LOG_ERROR,"OpemAmalurScene","Scene profile rejected; preserve existing scene path");
 return ok;
}
