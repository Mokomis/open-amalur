#include "scene_profile_v08.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static unsigned checks;
static void check(int ok,const char *message){if(!ok){fprintf(stderr,"FAIL: %s\n",message);exit(1);}++checks;}
static void succeeds(amalur_runtime *r,const char *s){int count;char error[1024];int status=amalur_runtime_eval_source(r,s,strlen(s),"empty-object-handle-test",&count,error,sizeof(error));check(!status,error);}
static void fails(amalur_runtime *r,const char *s,const char *fragment){int count;char error[1024];int status=amalur_runtime_eval_source(r,s,strlen(s),"empty-object-handle-test",&count,error,sizeof(error));check(status&&strstr(error,fragment),error);}
static amalur_runtime *create(const amalur_runtime_config *config){char error[1024];amalur_runtime *r=amalur_runtime_create(config,error,sizeof(error));check(r!=NULL,error);return r;}
int main(int argc,char **argv){
    amalur_runtime_config config={0};scene_profile_v08_options options={0};amalur_runtime *r;char error[1024];int status;
    if(argc!=2){fprintf(stderr,"empty_object_handle_test RUNTIME_DIR\n");return 2;}
    config.runtime_dir=argv[1];options.target_sha256=AMALUR_SCENE_PROFILE_V08_SHA256;
    r=create(&config);
    succeeds(r,"expected_empty=__amalur_handles.from_words(0xfb,0);check_words=__amalur_handles.to_words;check_hex=__amalur_uint64.hex;check_member=__amalur_type11_key_allowed");
    status=scene_profile_v08_install(r,&options,error,sizeof(error));check(!status,error);
    succeeds(r,"empty_fn=GAME.get_empty_object_handle;local h=empty_fn();assert(type(h)=='userdata' and check_member(h));assert(rawequal(h,expected_empty));local low,high=check_words(h);assert(low==0xfb and high==0 and check_hex(h)=='00000000000000fb');assert(select('#',empty_fn())==1)");
    succeeds(r,"for i=1,200 do assert(rawequal(empty_fn(),expected_empty)) end;assert(not rawequal(expected_empty,__amalur_handles.from_words(0xb,0)));assert(not rawequal(expected_empty,__amalur_handles.from_words(0xfb,1)))");
    fails(r,"return empty_fn(nil)","argument domain");
    fails(r,"return empty_fn(1)","argument domain");
    fails(r,"return empty_fn(false,{})","argument domain");
    fails(r,"return GAME:get_empty_object_handle()","argument domain");
    succeeds(r,"__amalur_handles.from_words=function()error('public constructor invoked')end;__amalur_uint64.from_hex=function()error('public carrier constructor invoked')end;__amalur_uint64.is=function()return false end;assert(rawequal(empty_fn(),expected_empty));assert(check_member(empty_fn()))");
    succeeds(r,"__amalur_handles=nil;__amalur_uint64=nil;assert(rawequal(empty_fn(),expected_empty));local low,high=check_words(empty_fn());assert(low==0xfb and high==0)");
    succeeds(r,"assert(GAME.get_game_engine_version()==1000)");
    fails(r,"return GAME.is_content_package_active(0)","content state is unset");
    amalur_runtime_destroy(r);
    /* A new realm creates its own canonical carrier, independent of mutation
       in a previously destroyed realm. */
    r=create(&config);status=scene_profile_v08_install(r,&options,error,sizeof(error));check(!status,error);
    succeeds(r,"assert(rawequal(GAME.get_empty_object_handle(),__amalur_handles.from_words(0xfb,0)))");
    amalur_runtime_destroy(r);
    /* Constructor availability is validated before provider publication. */
    r=create(&config);succeeds(r,"__amalur_handles.from_words=nil");
    status=scene_profile_v08_install(r,&options,error,sizeof(error));check(status&&strstr(error,"from_words"),"missing constructor rejected");
    amalur_runtime_destroy(r);
    r=create(&config);succeeds(r,"__amalur_handles.from_words=function()return 7 end");
    status=scene_profile_v08_install(r,&options,error,sizeof(error));check(status&&strstr(error,"Canonical empty object handle"),"non-userdata constructor result rejected");
    amalur_runtime_destroy(r);
    printf("{\"ok\":true,\"checks\":%u,\"scope\":\"exact canonical empty object token low0xfb high0; zero arity, repeated identity and post-install constructor mutation resistance only\"}\n",checks);return 0;
}
