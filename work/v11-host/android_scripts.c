/* Recovered scene bootstrap. A complete realm belongs to the render worker;
 * it remains idle after initialization until actual engine events are modeled. */
#include "android_scripts.h"
#include "scene_script_bootstrap.h"
#include "scene_asset_keys.h"
#include "scene_asset_macros_v08.h"
#include "scene_enums_v08.h"
#include <android/log.h>
#include <stdlib.h>
#include <stdio.h>
#include <stdint.h>

#define SCRIPT_LOG(level,...) __android_log_print(level,"OpemAmalurScripts",__VA_ARGS__)
#define SNAPSHOT_MAX_BYTES (8u + 65536u * 8u)
#define SNAPSHOT_TOTAL_MAX_BYTES (16u * 1024u * 1024u)

typedef struct snapshot_descriptor {
    const char *asset;
    const char *macro_name; /* NULL uses the separate input-key installer. */
    uint32_t category;
} snapshot_descriptor;
/* CMake generates this from the same explicit manifest used by APK packaging.
 * Every association still requires native evidence; none is inferred here. */
#include "android_asset_macros.inc"
static const char macro_manifest_id[]="opem-android-macro-manifest-sha256:" OPEM_ANDROID_MACRO_MANIFEST_SHA256;
#define SNAPSHOT_COUNT (sizeof(snapshot_descriptors)/sizeof(snapshot_descriptors[0]))
typedef struct asset_snapshot {char *bytes;size_t length;} asset_snapshot;
typedef struct android_setup {
    asset_snapshot snapshots[SNAPSHOT_COUNT];
    asset_snapshot enums;
    scene_controller_state_v08 controller;
} android_setup;

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
    if(AAsset_getLength64(a)!=(off64_t)size){AAsset_close(a);snprintf(error,cap,"APK asset size changed: %s",path);return 1;}
    while(offset<size){size_t want=size-offset;int n;if(want>1048576)want=1048576;
        n=AAsset_read(a,dest+offset,want);
        if(n<=0){AAsset_close(a);snprintf(error,cap,"Incomplete APK asset: %s",path);return 1;}offset+=(size_t)n;
    }
    AAsset_close(a);return 0;
}
static int setup_services(amalur_runtime *runtime,void *context,char *error,size_t cap){
    android_setup *setup=(android_setup*)context;
    scene_profile_v08_options profile={0};size_t i;
    profile.target_sha256=AMALUR_SCENE_PROFILE_V08_SHA256;
    profile.controller=setup->controller;
    /* This port has mounted no optional content packages. This is host mount
     * policy, not a native installation, licensing, or DLC ownership report. */
    profile.content.is_set=1;profile.content.registered_mask=0;profile.content.active_mask=0;
    /* Verified SH("android"), explicit new port platform; never native win32. */
    profile.platform.is_set=1;profile.platform.name_hash=2096549;
    profile.fresh_profile=1; /* New empty Android session; no user profile import. */
    profile.quick_save.is_set=1;profile.quick_save.supported=0; /* No Android save system. */
    profile.max_anisotropy=1; /* Explicit preview capability: no anisotropic filtering. */
    profile.no_language_packs=1; /* Explicit empty Android pack catalog. */
    if(scene_profile_v08_install(runtime,&profile,error,cap))return 1;
    SCRIPT_LOG(ANDROID_LOG_INFO,"Platform policy known: name=android name_hash=2096549 scope=new_Android_host_platform native_enum_unassigned=1");
    SCRIPT_LOG(ANDROID_LOG_INFO,"Content policy known: optional_packages_mounted=0 registered_mask=0x0 active_mask=0x0 scope=Android_port_mounts");
    SCRIPT_LOG(ANDROID_LOG_INFO,"Preference policy: scope=fresh_session_in_memory initial_entries=0 imported_user_profile=0 persistence=0");
    SCRIPT_LOG(ANDROID_LOG_INFO,"Quick-save capability known: supported=0 scope=Android_preview_no_save_system");
    SCRIPT_LOG(ANDROID_LOG_INFO,"Language catalog known: installed_packs=0 automatic_id=-1 label=Automatic scope=new_Android_host_label");
    if(scene_enums_v08_install(runtime,setup->enums.bytes,setup->enums.length,error,cap))return 1;
    SCRIPT_LOG(ANDROID_LOG_INFO,"Installed enum snapshot asset=compiled_enums.bin bytes=%zu entries=%zu",setup->enums.length,(setup->enums.length-12u)/12u);
    for(i=0;i<SNAPSHOT_COUNT;++i){
        const snapshot_descriptor *desc=&snapshot_descriptors[i];
        const asset_snapshot *snapshot=&setup->snapshots[i];
        int status=desc->macro_name?
            scene_asset_macro_v08_install(runtime,desc->macro_name,desc->category,
                                         snapshot->bytes,snapshot->length,error,cap):
            scene_asset_keys_install(runtime,snapshot->bytes,snapshot->length,error,cap);
        if(status)return 1;
        SCRIPT_LOG(ANDROID_LOG_INFO,"Installed snapshot asset=%s macro=%s category=0x%x bytes=%zu",
                   desc->asset,desc->macro_name?desc->macro_name:"input-key adapter",desc->category,snapshot->length);
    }
    return 0;
}
amalur_runtime *opem_android_scripts_start(const amalur_scene_mesh *mesh,AAssetManager *assets,
                                         const scene_controller_state_v08 *controller){
    scene_script_resources resources={0};scene_script_options options={0};scene_script_result result;
    amalur_runtime *runtime=NULL;android_setup setup={0};char error[256];size_t i,total_bytes=0;
    if(!mesh||!assets||!controller){SCRIPT_LOG(ANDROID_LOG_ERROR,"Scene script arguments are absent");return NULL;}
    setup.controller=*controller;
    SCRIPT_LOG(ANDROID_LOG_INFO,"%s macros=%zu",macro_manifest_id,SNAPSHOT_COUNT-1);
    if(asset_size(assets,"compiled_enums.bin",&setup.enums.length,error,sizeof(error))){
        SCRIPT_LOG(ANDROID_LOG_ERROR,"%s",error);goto done;
    }
    if(setup.enums.length<12||setup.enums.length>SCENE_ENUMS_V08_MAX_BYTES){
        SCRIPT_LOG(ANDROID_LOG_ERROR,"Enum snapshot length outside admitted range: %zu",setup.enums.length);goto done;
    }
    total_bytes=setup.enums.length;
    setup.enums.bytes=(char*)malloc(setup.enums.length);
    if(!setup.enums.bytes){SCRIPT_LOG(ANDROID_LOG_ERROR,"Enum snapshot allocation failed");goto done;}
    if(asset_read(assets,"compiled_enums.bin",setup.enums.bytes,setup.enums.length,error,sizeof(error))){
        SCRIPT_LOG(ANDROID_LOG_ERROR,"%s",error);goto done;
    }
    for(i=0;i<SNAPSHOT_COUNT;++i){
        const snapshot_descriptor *desc=&snapshot_descriptors[i];asset_snapshot *snapshot=&setup.snapshots[i];
        if(asset_size(assets,desc->asset,&snapshot->length,error,sizeof(error))){
            SCRIPT_LOG(ANDROID_LOG_ERROR,"%s",error);goto done;
        }
        if(snapshot->length<8||snapshot->length>SNAPSHOT_MAX_BYTES){
            SCRIPT_LOG(ANDROID_LOG_ERROR,"Snapshot length outside admitted range: %s bytes=%zu",desc->asset,snapshot->length);goto done;
        }
        if(snapshot->length>SNAPSHOT_TOTAL_MAX_BYTES-total_bytes){
            SCRIPT_LOG(ANDROID_LOG_ERROR,"Snapshot total exceeds16MiB at %s",desc->asset);goto done;
        }
        total_bytes+=snapshot->length;
        snapshot->bytes=(char*)malloc(snapshot->length);
        if(!snapshot->bytes){SCRIPT_LOG(ANDROID_LOG_ERROR,"Snapshot allocation failed: %s",desc->asset);goto done;}
        if(asset_read(assets,desc->asset,snapshot->bytes,snapshot->length,error,sizeof(error))){
            SCRIPT_LOG(ANDROID_LOG_ERROR,"%s",error);goto done;
        }
    }
    options.setup=setup_services;options.setup_context=&setup;
    resources.context=assets;resources.size=asset_size;resources.read=asset_read;
    options.bootstrap_module="ParentUtils";options.root_module="SpaceCommon";options.event="on_object_creation_complete";
    options.lua_memory_limit=256u*1024u*1024u;options.instruction_budget=30000000u;
    options.maximum_total_bytes=128u*1024u*1024u;
    runtime=scene_script_bootstrap(&resources,&options,&result);
    SCRIPT_LOG(result.ok?ANDROID_LOG_INFO:ANDROID_LOG_WARN,
        "scene_vertices=%u phase=%s bootstrap_loaded=%d root_loaded=%d event_invoked=%d registered_modules=%u resource_bytes=%zu lua_bytes=%zu retained=%d error=%s",
        mesh->vertex_count,result.phase,result.bootstrap_loaded,result.root_loaded,result.event_invoked,result.registered_modules,
        result.resource_bytes,result.lua_memory_bytes,runtime!=NULL,result.error);
    /* Bootstrap destroys failed realms. A retained realm has completed the
     * requested root/event, but no per-frame gameplay behavior is supplied. */
done:
    for(i=0;i<SNAPSHOT_COUNT;++i)free(setup.snapshots[i].bytes);
    free(setup.enums.bytes);
    return runtime;
}
void opem_android_scripts_stop(amalur_runtime *runtime){
    if(runtime){amalur_runtime_destroy(runtime);SCRIPT_LOG(ANDROID_LOG_INFO,"Retained scene realm destroyed on owner worker");}
}
