#ifndef OPEM_INTERACTION_ANDROID_H
#define OPEM_INTERACTION_ANDROID_H
#include "interaction_lua.h"
#include <android/asset_manager.h>
#include <android/input.h>
int oa_android_start(oa_interaction *,amalur_runtime *,AAssetManager *,const char *inventory_path);
void oa_android_close(oa_interaction *);
/* Only called for an open modal; captures all input to freeze walking. */
int oa_android_modal_event(oa_interaction *,AInputEvent *,int width,int height,const char *inventory_path);
#endif
