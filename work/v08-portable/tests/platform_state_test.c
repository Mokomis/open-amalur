#include "scene_profile_v08.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static unsigned checks;
static void check(int okay,const char *message){if(!okay){fprintf(stderr,"FAIL: %s\n",message);exit(1);}++checks;}
static int eval(amalur_runtime *r,const char *code,char *error){int n;return amalur_runtime_eval_source(r,code,strlen(code),"platform-state-test",&n,error,1024);}
static void platform(amalur_runtime *r,int32_t hash,char *error){
    const char *code="return captured_platform()";int n,status;lua_State *L=amalur_runtime_state(r);
    status=amalur_runtime_eval_source(r,code,strlen(code),"copied-platform-query",&n,error,1024);
    check(!status&&n==1&&lua_type(L,1)==LUA_TNUMBER&&lua_tonumber(L,1)==(lua_Number)hash,error);
}
int main(int argc,char **argv){
    amalur_runtime_config config={0};scene_profile_v08_options options={0};
    scene_content_state_v08 content={1,8,8};
    scene_controller_state_v08 controller={1,15,SCENE_CONTROLLER_DOMAIN_NATIVE_KIND};
    amalur_runtime *unknown,*android,*native;char error[1024];int status,top;
    if(argc!=2){fprintf(stderr,"platform_state_test SIX_NAMESPACE_RUNTIME_DIR\n");return 2;}
    config.runtime_dir=argv[1];options.target_sha256=AMALUR_SCENE_PROFILE_V08_SHA256;
    options.controller=controller;options.content.is_set=1;
    unknown=amalur_runtime_create(&config,error,sizeof(error));check(unknown!=NULL,error);
    options.platform.is_set=2;check(scene_profile_v08_install(unknown,&options,error,sizeof(error))!=0,"invalid positive platform flag rejected");
    options.platform.is_set=-1;check(scene_profile_v08_install(unknown,&options,error,sizeof(error))!=0,"invalid negative platform flag rejected");
    options.platform.is_set=0;options.platform.name_hash=2096549;
    check(!scene_profile_v08_install(unknown,&options,error,sizeof(error)),error);
    check(!eval(unknown,"captured_platform=WINDOW.get_platform",error),error);
    status=eval(unknown,"return captured_platform()",error);check(status&&strstr(error,"platform state is unset"),"known-looking hash never overrides unset state");
    check(!eval(unknown,"assert(INPUT.is_east_asian_controller_button_swap_required()==true); assert(not GAME.is_content_package_active(3)); assert(GAME.get_game_engine_version()==1000)",error),error);

    android=amalur_runtime_create(&config,error,sizeof(error));check(android!=NULL,error);
    options.platform.is_set=1;options.platform.name_hash=2096549;
    top=lua_gettop(amalur_runtime_state(android));check(!scene_profile_v08_install(android,&options,error,sizeof(error)),error);
    check(lua_gettop(amalur_runtime_state(android))==top,"platform installation preserves caller stack");
    options.platform.name_hash=585298;options.platform.is_set=0;
    check(!eval(android,"captured_platform=WINDOW.get_platform;collectgarbage('collect')",error),error);platform(android,2096549,error);
    status=eval(android,"return captured_platform(nil)",error);check(status&&strstr(error,"argument domain"),"explicit nil argument rejected");
    status=eval(android,"return captured_platform(1,2)",error);check(status&&strstr(error,"argument domain"),"multiple arguments rejected");
    check(!scene_profile_v08_set_content(android,&content,error,sizeof(error)),error);
    controller.native_device_kind=7;check(!scene_profile_v08_set_controller(android,&controller,error,sizeof(error)),error);
    check(!eval(android,"assert(GAME.is_content_package_active(3));assert(not INPUT.is_east_asian_controller_button_swap_required());assert(GAME.get_game_engine_version()==1000)",error),error);platform(android,2096549,error);

    native=amalur_runtime_create(&config,error,sizeof(error));check(native!=NULL,error);
    options.platform.is_set=1;options.platform.name_hash=585298;
    check(!scene_profile_v08_install(native,&options,error,sizeof(error)),error);
    check(!eval(native,"captured_platform=WINDOW.get_platform",error),error);platform(native,585298,error);platform(android,2096549,error);
    status=eval(unknown,"return captured_platform()",error);check(status&&strstr(error,"platform state is unset"),"platform state is realm-local");
    amalur_runtime_destroy(native);amalur_runtime_destroy(android);amalur_runtime_destroy(unknown);
    printf("{\"ok\":true,\"checks\":%u,\"scope\":\"copied immutable platform name hash; Android is explicit new host platform\"}\n",checks);return 0;
}
