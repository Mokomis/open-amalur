#ifndef OPEM_ANDROID_SCRIPTS_V08_H
#define OPEM_ANDROID_SCRIPTS_V08_H
#include "amalur_scene_mesh.h"
#include "scene_profile_v08.h"
#include <android/asset_manager.h>

/* Called only by the scene worker after mesh validation. Returns a worker-owned
 * realm only after complete bootstrap success, otherwise NULL with log detail.
 * All asset snapshots and setup context are copied before this returns.
 * No mesh pointer, input-event pointer, or JNI reference is retained by Lua. */
amalur_runtime *opem_android_scripts_start(const amalur_scene_mesh *, AAssetManager *,
                                         const scene_controller_state_v08 *);
/* Call on the same worker before the Activity is released; NULL is accepted. */
void opem_android_scripts_stop(amalur_runtime *);
#endif
