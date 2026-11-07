#ifndef OA_SCENE_PROFILE_H
#define OA_SCENE_PROFILE_H
#include <stdint.h>
#include <stddef.h>
/* Private portable scene envelope, not the original game format.
 * Fields retain authored values; flags explicitly identify preview fallbacks. */
enum{OA_SCENE_INDOOR=1,OA_SCENE_PREVIEW=2,OA_SCENE_AMBIENT_GLOBALS_KNOWN=4};
typedef struct oa_scene_profile{
 int active;unsigned space,region,flags,light_count;
 float spawn[3],yaw,sun_direction[3],sun_color[3],shadow[4],fog_color[3];
 float fog_density,fog_start,post[4],sky[4],ambient_scales[2];
 float (*lights)[8];
 unsigned char cube[1536],lut[16384];
}oa_scene_profile;
struct AAssetManager;
int oa_scene_profile_parse(oa_scene_profile *s,const void *bytes,size_t size);
int oa_scene_profile_load(oa_scene_profile *s,struct AAssetManager *assets);
void oa_scene_profile_close(oa_scene_profile *s);
#endif
