#include "scene_profile_v08.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static unsigned checks;
static void check(int condition,const char *message){if(!condition){fprintf(stderr,"FAIL: %s\n",message);exit(1);}++checks;}
static int eval(amalur_runtime *runtime,const char *source,char *error){int count;return amalur_runtime_eval_source(runtime,source,strlen(source),"controller-state-test",&count,error,1024);}
static void result(amalur_runtime *runtime,int expected,char *error){
    int count,status;const char *code="return saved_input_query()";lua_State *L=amalur_runtime_state(runtime);
    status=amalur_runtime_eval_source(runtime,code,strlen(code),"captured-controller-query",&count,error,1024);
    check(!status&&count==1&&lua_type(L,1)==LUA_TBOOLEAN&&lua_toboolean(L,1)==expected,error);
}
int main(int argc,char **argv){
    amalur_runtime_config config={0};scene_profile_v08_options options={0};scene_controller_state_v08 state={0};
    amalur_runtime *runtime,*other;lua_State *L;char error[1024];int status,kind,top;
    if(argc!=2){fprintf(stderr,"controller_state_test SIX_NAMESPACE_RUNTIME_DIR\n");return 2;}config.runtime_dir=argv[1];
    runtime=amalur_runtime_create(&config,error,sizeof(error));check(runtime!=NULL,error);L=amalur_runtime_state(runtime);
    status=scene_profile_v08_set_controller(runtime,&state,error,sizeof(error));check(status&&strstr(error,"not installed"),"updating absent state fails explicitly");
    options.target_sha256="wrong-sha";status=scene_profile_v08_install(runtime,&options,error,sizeof(error));check(status!=0,"wrong executable profile rejected");
    options.target_sha256=AMALUR_SCENE_PROFILE_V08_SHA256;top=lua_gettop(L);status=scene_profile_v08_install(runtime,&options,error,sizeof(error));check(!status,error);check(lua_gettop(L)==top,"install preserves caller stack");
    status=eval(runtime,"saved_input_query=INPUT.is_east_asian_controller_button_swap_required; assert(GAME.get_game_engine_version()==1000);return saved_input_query()",error);check(status&&strstr(error,"state is unset"),"initial unset state fails rather than inventing false");
    for(kind=0;kind<=31;kind++){
        state.is_set=1;state.native_device_kind=kind;top=lua_gettop(L);status=scene_profile_v08_set_controller(runtime,&state,error,sizeof(error));check(!status,error);check(lua_gettop(L)==top,"state update preserves stack");
        state.native_device_kind=-999;result(runtime,kind==13||kind==15,error);
    }
    state.native_device_kind=INT32_MIN;status=scene_profile_v08_set_controller(runtime,&state,error,sizeof(error));check(!status,error);result(runtime,0,error);
    state.native_device_kind=INT32_MAX;status=scene_profile_v08_set_controller(runtime,&state,error,sizeof(error));check(!status,error);result(runtime,0,error);
    state.native_device_kind=13;status=scene_profile_v08_set_controller(runtime,&state,error,sizeof(error));check(!status,error);result(runtime,1,error);
    state.is_set=2;status=scene_profile_v08_set_controller(runtime,&state,error,sizeof(error));check(status!=0,"invalid setter state rejected");result(runtime,1,error);
    status=eval(runtime,"return saved_input_query(nil)",error);check(status&&strstr(error,"argument domain"),"unexpected input-query arguments rejected");
    status=eval(runtime,"return INPUT.get_version()",error);check(status&&strstr(error,"unimplemented Amalur engine binding"),"other input methods remain explicit errors");
    state.is_set=0;status=scene_profile_v08_set_controller(runtime,&state,error,sizeof(error));check(!status,error);
    status=eval(runtime,"return saved_input_query()",error);check(status&&strstr(error,"state is unset"),"disconnect/unset restores explicit error");
    other=amalur_runtime_create(&config,error,sizeof(error));check(other!=NULL,error);options.controller.is_set=1;options.controller.native_device_kind=15;
    status=scene_profile_v08_install(other,&options,error,sizeof(error));check(!status,error);options.controller.native_device_kind=0;
    status=eval(other,"saved_input_query=INPUT.is_east_asian_controller_button_swap_required",error);check(!status,error);result(other,1,error);
    status=eval(runtime,"return saved_input_query()",error);check(status&&strstr(error,"state is unset"),"controller state is realm-local");
    amalur_runtime_destroy(other);amalur_runtime_destroy(runtime);printf("{\"ok\":true,\"checks\":%u,\"scope\":\"mutable explicit native device-kind state; no Android kind mapping or native runtime parity claim\"}\n",checks);return 0;
}
