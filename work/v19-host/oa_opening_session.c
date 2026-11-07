#include "oa_opening_session.h"
#include <GLES3/gl3.h>
#include "oa_stream.h"
#include <android/asset_manager.h>
#include <android/log.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <math.h>
#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#endif
#define LOGI(...) __android_log_print(ANDROID_LOG_INFO,"OpemAmalurScene",__VA_ARGS__)
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR,"OpemAmalurScene",__VA_ARGS__)
struct oa_opening_session {
 AAssetManager *assets;
 oa_movement_host *host;
 char path[1024];
 oa_movement_stats observed;
 int file_present;
 oa_stream *load_stream;
 opem_controller_config load_config;
 opem_collision_world *staged_world;
 opem_controller staged_controller;
 oa_movement_pose staged_pose;
};
static int fail(char *e,size_t n,const char *s){if(e&&n)snprintf(e,n,"%s",s);return 1;}
static AAsset *asset_open(oa_opening_session *s,const char *name){
 char path[512];int n;if(!name||strstr(name,"..")||strchr(name,':')||name[0]=='/'||name[0]=='\\')return NULL;
 n=snprintf(path,sizeof(path),"opening-runtime/%s",name);if(n<0||(size_t)n>=sizeof(path))return NULL;
 return AAssetManager_open(s->assets,path,AASSET_MODE_BUFFER);
}
static int asset_size(void *ctx,const char *name,size_t *n,char *e,size_t cap){
 AAsset *a=asset_open(ctx,name);int64_t bytes;if(!a)return fail(e,cap,"pinned opening asset missing");
 bytes=AAsset_getLength64(a);AAsset_close(a);if(bytes<0||bytes>1048576)return fail(e,cap,"pinned opening asset size rejected");
 *n=(size_t)bytes;return 0;
}
static int asset_read(void *ctx,const char *name,void *p,size_t n,char *e,size_t cap){
 AAsset *a=asset_open(ctx,name);size_t at=0;if(!a)return fail(e,cap,"pinned opening asset missing");
 if(AAsset_getLength64(a)!=(int64_t)n){AAsset_close(a);return fail(e,cap,"pinned opening asset changed size");}
 while(at<n){int k=AAsset_read(a,(unsigned char*)p+at,n-at);if(k<=0){AAsset_close(a);return fail(e,cap,"pinned opening asset short read");}at+=(size_t)k;}
 AAsset_close(a);return 0;
}
static void report(void *ctx,const char *why){(void)ctx;LOGE("Opening source event latched; movement paused: %s",why);}
static int checkpoint_exists(const oa_opening_session *s);
static void observe(oa_opening_session *s,const char *reason,int force){
 oa_movement_stats st;oa_movement_tutorial a={0},b={0};oa_movement_host_get_stats(s->host,&st);
 if(st.checkpoint_writes)s->file_present=1;
 if(!force&&st.inside_mask==s->observed.inside_mask&&st.checkpoint_writes==s->observed.checkpoint_writes&&st.latched==s->observed.latched)return;
 oa_movement_host_tutorial_get(s->host,17524338u,&a);oa_movement_host_tutorial_get(s->host,26339831u,&b);
 LOGI("Opening source state reason=%s scene=%u region=%u inside=%u skipped=%u checkpoint_writes=%llu tutorial_kills=%u,%u latched=%u lua_calls=%llu lua_bytes=%zu services=%u",
 reason,st.scene,st.region,st.inside_mask,st.cinematic_skipped,(unsigned long long)st.checkpoint_writes,a.kills,b.kills,st.latched,
 (unsigned long long)st.runtime.calls,st.runtime.lua_bytes,oa_movement_host_services(s->host));s->observed=st;
}
static void discard_staged(oa_opening_session *s){opem_collision_destroy(s->staged_world);s->staged_world=NULL;s->load_stream=NULL;}
static int validate_pose(void *ctx,const oa_movement_pose *p,char *e,size_t n){
 oa_opening_session *s=ctx;unsigned i;
 if(!s->load_stream)return fail(e,n,"opening load requires the current collision stream");
 s->staged_world=oa_stream_collision_now(s->load_stream,p->feet,e,n);if(!s->staged_world)return 1;
 if(!opem_controller_spawn(s->staged_world,&s->load_config,p->feet,&s->staged_controller,e,n))return 1;
 /* A loader cannot silently relocate a saved capsule out of a newly blocked area. */
 for(i=0;i<3;i++)if(fabsf(s->staged_controller.feet[i]-p->feet[i])>2.f)return fail(e,n,"saved pose requires relocation; checkpoint preserved");
 if(!opem_controller_clear(s->staged_world,&s->load_config,p->feet,e,n))return 1;
 /* Keep the exact checkpoint pose after validation; spawn's rest state/velocity
  * is intentional for this movement-only checkpoint. */
 memcpy(s->staged_controller.feet,p->feet,sizeof(p->feet));
 memcpy(s->staged_controller.last_safe_feet,p->feet,sizeof(p->feet));s->staged_pose=*p;return 0;
}
oa_opening_session *oa_opening_session_open(AAssetManager *assets,const char *dir,unsigned space,unsigned region,const oa_movement_pose *pose,int explicit_skip,char *e,size_t cap){
 oa_opening_session *s;oa_movement_config cfg={0};oa_opening_assets io;int n;
 if(!assets||!dir||!pose||space!=1417252u||region!=1262814u){fail(e,cap,"opening source scene identity required");return NULL;}
 s=calloc(1,sizeof(*s));if(!s){fail(e,cap,"opening session allocation failed");return NULL;}s->assets=assets;
 n=snprintf(s->path,sizeof(s->path),"%s/wellofsouls.opening-checkpoint-v1.bin",dir);
 if(n<0||(size_t)n>=sizeof(s->path)){free(s);fail(e,cap,"opening checkpoint path too long");return NULL;}
 /* Authored prototype slot generation, not a native persistent object identity. */
 cfg.generation=1;cfg.checkpoint_path=s->path;cfg.report_context=s;cfg.report_failure=report;
 cfg.pose_validation_context=s;cfg.validate_load_pose=validate_pose;
 io.context=s;io.size=asset_size;io.read=asset_read;s->host=oa_movement_host_create(&io,&cfg,e,cap);
 if(!s->host||oa_movement_host_update_pose(s->host,pose,e,cap)||(explicit_skip&&oa_movement_host_cinematic_skipped(s->host,e,cap))){
  oa_opening_session_close(s);return NULL;}
 if(explicit_skip)LOGI("Opening cinematic explicitly skipped by development setting; playback/creator unavailable");
 s->file_present=checkpoint_exists(s);observe(s,"open",1);return s;
}
void oa_opening_session_close(oa_opening_session *s){if(!s)return;discard_staged(s);oa_movement_host_close(s->host);free(s);}
int oa_opening_session_update(oa_opening_session *s,const oa_movement_pose *p,char *e,size_t n){
 int r;if(!s)return fail(e,n,"opening session unavailable");r=oa_movement_host_update_pose(s->host,p,e,n);observe(s,"accepted_pose",0);return r;
}
int oa_opening_session_save(oa_opening_session *s,char *e,size_t n){
 int r;if(!s)return fail(e,n,"opening session unavailable");r=oa_movement_host_save_checkpoint(s->host,e,n);observe(s,"manual_checkpoint",1);return r;
}
static int checkpoint_exists(const oa_opening_session *s){
 FILE *f;if(!s)return 0;
#ifdef _WIN32
 wchar_t path[1024];if(!MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,s->path,-1,path,1024))return 0;f=_wfopen(path,L"rb");
#else
 f=fopen(s->path,"rb");
#endif
 if(!f)return 0;fclose(f);return 1;
}
int oa_opening_session_has_checkpoint(const oa_opening_session *s){return s?s->file_present:0;}
int oa_opening_session_load(oa_opening_session *s,oa_stream *stream,const opem_controller_config *cfg,opem_collision_world **world,opem_controller *body,oa_movement_pose *p,char *e,size_t n){
 int r;if(!s||!stream||!cfg||!world||!body||!p)return fail(e,n,"opening load requires a current stream/controller");
 discard_staged(s);s->load_stream=stream;s->load_config=*cfg;r=oa_movement_host_load_checkpoint(s->host,e,n);
 if(r){discard_staged(s);return r;}
 /* No fallible work after the source host commit. */
 opem_collision_destroy(*world);*world=s->staged_world;s->staged_world=NULL;*body=s->staged_controller;*p=s->staged_pose;s->load_stream=NULL;
 s->file_present=1;observe(s,"checkpoint_loaded",1);return 0;
}
