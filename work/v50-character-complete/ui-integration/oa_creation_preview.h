#ifndef OA_CREATION_PREVIEW_H
#define OA_CREATION_PREVIEW_H
#include "oa_creation.h"
#include "oa_character_appearance.h"
#include <android/asset_manager.h>
typedef struct oa_creation_preview{
 oa_ca_renderer *renderer;oa_ca_actor *actor;oa_creation_state shown,failed_profile;
 uint32_t failed_revision;float time;GLuint light_ubo,light_grid;int ready;
 char error[192];
}oa_creation_preview;
void oa_creation_preview_cpu_open(oa_creation_preview*,AAssetManager*);
void oa_creation_preview_gpu_open(oa_creation_preview*);
void oa_creation_preview_gpu_close(oa_creation_preview*);
void oa_creation_preview_cpu_close(oa_creation_preview*);
int oa_creation_preview_available(const oa_creation_preview*,const oa_creation_state*);
const char *oa_creation_preview_error(const oa_creation_preview*);
int oa_creation_preview_draw(oa_creation_preview*,const oa_creation_state*,float angle,float zoom,int face,int width,int height,float dt);
#endif
