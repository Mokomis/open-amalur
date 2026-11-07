#ifndef OA_WIN_ACTIVITY_H
#define OA_WIN_ACTIVITY_H
#include "native_window.h"
#include "input.h"
#include "asset_manager.h"
#include <jni.h>
typedef struct ANativeActivity ANativeActivity;
typedef struct ANativeActivityCallbacks{
 void(*onResume)(ANativeActivity*);void(*onPause)(ANativeActivity*);void(*onWindowFocusChanged)(ANativeActivity*,int);void(*onConfigurationChanged)(ANativeActivity*);
 void(*onNativeWindowCreated)(ANativeActivity*,ANativeWindow*);void(*onNativeWindowDestroyed)(ANativeActivity*,ANativeWindow*);
 void(*onInputQueueCreated)(ANativeActivity*,AInputQueue*);void(*onInputQueueDestroyed)(ANativeActivity*,AInputQueue*);void(*onDestroy)(ANativeActivity*);
}ANativeActivityCallbacks;
struct ANativeActivity{ANativeActivityCallbacks *callbacks;JavaVM *vm;AAssetManager *assetManager;void *instance;const char *internalDataPath;};
void ANativeActivity_finish(ANativeActivity*);
void ANativeActivity_onCreate(ANativeActivity*,void*,size_t);
#endif
