/* One-shot recovered scene bootstrap diagnostic, shared with Windows inspector. */
#include "scene_script_bootstrap.h"
#include "scene_asset_keys.h"
#include "scene_profile.h"
#include <stdlib.h>
#include "amalur_scene_mesh.h"
#include <android/asset_manager.h>
#include <android/log.h>
#include <stdio.h>
#include <stdint.h>
static int asset_size(void *context,const char *path,size_t *size,char *error,size_t cap){
 AAsset *a=AAssetManager_open((AAssetManager*)context,path,AASSET_MODE_STREAMING);off64_t n;
 if(!a){snprintf(error,cap,"Missing APK asset: %s",path);return 1;}
 n=AAsset_getLength64(a);AAsset_close(a);
 if(n<0||(uint64_t)n>SIZE_MAX){snprintf(error,cap,"Invalid APK asset size: %s",path);return 1;}
 *size=(size_t)n;return 0;
}
static int asset_read(void *context,const char *path,char *dest,size_t size,char *error,size_t cap){
 AAsset *a=AAssetManager_open((AAssetManager*)context,path,AASSET_MODE_STREAMING);size_t offset=0;
 if(!a){snprintf(error,cap,"Missing APK asset: %s",path);return 1;}
 if(AAsset_getLength64(a)!=(off64_t)size){AAsset_close(a);snprintf(error,cap,"APK asset size changed");return 1;}
 while(offset<size){size_t want=size-offset;int n;if(want>1048576)want=1048576;
  n=AAsset_read(a,dest+offset,want);if(n<=0){AAsset_close(a);snprintf(error,cap,"Incomplete APK asset: %s",path);return 1;}offset+=(size_t)n;}
 AAsset_close(a);return 0;
}
typedef struct key_snapshot {char *bytes;size_t length;} key_snapshot;
static int setup_keys(amalur_runtime *runtime,void *context,char *error,size_t cap){
 key_snapshot *snapshot=(key_snapshot*)context;
 if(scene_asset_keys_install(runtime,snapshot->bytes,snapshot->length,error,cap))return 1;
 return scene_profile_install(runtime,AMALUR_SCENE_PROFILE_SHA256,error,cap);
}
void amalur_scene_script_hook(const amalur_scene_mesh *mesh,AAssetManager *assets){
 scene_script_resources resources={0};scene_script_options options={0};scene_script_result result;amalur_runtime *runtime;
 key_snapshot snapshot={0};char error[256];
 if(asset_size(assets,"inputdeviceaction_init.bin",&snapshot.length,error,sizeof(error))||snapshot.length>524296u){
  __android_log_print(ANDROID_LOG_ERROR,"OpemAmalurScripts","Missing or oversized input action snapshot");return;
 }
 snapshot.bytes=(char*)malloc(snapshot.length?snapshot.length:1);
 if(!snapshot.bytes){__android_log_print(ANDROID_LOG_ERROR,"OpemAmalurScripts","Input action allocation failed");return;}
 if(asset_read(assets,"inputdeviceaction_init.bin",snapshot.bytes,snapshot.length,error,sizeof(error))){
  __android_log_print(ANDROID_LOG_ERROR,"OpemAmalurScripts","%s",error);free(snapshot.bytes);return;
 }
 options.setup=setup_keys;options.setup_context=&snapshot;
 resources.context=assets;resources.size=asset_size;resources.read=asset_read;
 options.root_module="SpaceCommon";options.event="on_object_creation_complete";options.lua_memory_limit=128u*1024u*1024u;options.instruction_budget=10000000u;
 runtime=scene_script_bootstrap(&resources,&options,&result);
 free(snapshot.bytes);
 __android_log_print(result.ok?ANDROID_LOG_INFO:ANDROID_LOG_WARN,"OpemAmalurScripts",
  "scene_vertices=%u phase=%s root_loaded=%d event_invoked=%d registered_modules=%u resource_bytes=%zu lua_bytes=%zu error=%s",
  mesh->vertex_count,result.phase,result.root_loaded,result.event_invoked,result.registered_modules,result.resource_bytes,result.lua_memory_bytes,result.error);
 /* A failed bootstrap never becomes a gameplay realm. The preview currently
    runs one initialization probe only; no frame events or invented providers. */
 amalur_runtime_destroy(runtime);
}
