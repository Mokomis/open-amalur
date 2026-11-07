#include "scene_profile_v08.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static unsigned checks;
static void check(int okay,const char *message){
    if(!okay){fprintf(stderr,"FAIL: %s\n",message);exit(1);}++checks;
}
static int eval(amalur_runtime *r,const char *code,char *error){
    int count;return amalur_runtime_eval_source(r,code,strlen(code),"android-layout-test",&count,error,1024);
}
static void query(amalur_runtime *r,int expected,char *error){
    int count,status;const char *code="return captured_layout_query()";lua_State *L=amalur_runtime_state(r);
    status=amalur_runtime_eval_source(r,code,strlen(code),"captured-layout-query",&count,error,1024);
    check(!status&&count==1&&lua_type(L,1)==LUA_TBOOLEAN&&lua_toboolean(L,1)==expected,error);
}
static void update(amalur_runtime *r,const scene_controller_state_v08 *s,char *error){
    lua_State *L=amalur_runtime_state(r);int top=lua_gettop(L);
    check(!scene_profile_v08_set_controller(r,s,error,1024),error);
    check(lua_gettop(L)==top,"setter preserves stack");
}
int main(int argc,char **argv){
    amalur_runtime_config config={0};scene_profile_v08_options options={0};
    /* Intentional old initializer: trailing domain must default to native. */
    scene_controller_state_v08 legacy={1,13};
    scene_controller_state_v08 state={0};
    amalur_runtime *runtime,*other;char error[1024];int status,domain,kind,i;
    const int kinds[]={INT32_MIN,-1,0,13,15,31,INT32_MAX};
    if(argc!=2){fprintf(stderr,"android_layout_test SIX_NAMESPACE_RUNTIME_DIR\n");return 2;}
    config.runtime_dir=argv[1];options.target_sha256=AMALUR_SCENE_PROFILE_V08_SHA256;
    runtime=amalur_runtime_create(&config,error,sizeof(error));check(runtime!=NULL,error);
    check(legacy.domain==SCENE_CONTROLLER_DOMAIN_NATIVE_KIND,"legacy initializer domain is native");
    options.controller=legacy;check(!scene_profile_v08_install(runtime,&options,error,sizeof(error)),error);
    check(!eval(runtime,"captured_layout_query=INPUT.is_east_asian_controller_button_swap_required",error),error);
    query(runtime,1,error);
    for(domain=0;domain<=2;++domain){
        state.domain=(scene_controller_domain_v08)domain;
        state.is_set=0;state.native_device_kind=13;update(runtime,&state,error);
        status=eval(runtime,"return captured_layout_query()",error);
        check(status&&strstr(error,"state is unset"),"every unset domain raises an error");
        for(i=0;i<(int)(sizeof(kinds)/sizeof(kinds[0]));++i){
            kind=kinds[i];state.is_set=1;state.native_device_kind=kind;
            state.domain=(scene_controller_domain_v08)domain;update(runtime,&state,error);
            /* Mutate caller storage to prove copied state, including domain. */
            state.domain=SCENE_CONTROLLER_DOMAIN_NATIVE_KIND;state.native_device_kind=99;state.is_set=0;
            query(runtime,domain==0?(kind==13||kind==15):domain==2,error);
        }
    }
    state.is_set=1;state.native_device_kind=0;state.domain=SCENE_CONTROLLER_DOMAIN_ANDROID_LOGICAL_REVERSED;
    update(runtime,&state,error);query(runtime,1,error);
    for(i=0;i<2;++i){
        state.domain=(scene_controller_domain_v08)(i?-1:3);
        status=scene_profile_v08_set_controller(runtime,&state,error,sizeof(error));
        check(status!=0,"unknown domain rejected");query(runtime,1,error);
        state.is_set=0;
        status=scene_profile_v08_set_controller(runtime,&state,error,sizeof(error));
        check(status!=0,"unknown unset domain rejected");query(runtime,1,error);state.is_set=1;
    }
    state.domain=SCENE_CONTROLLER_DOMAIN_ANDROID_LOGICAL_STANDARD;state.is_set=2;
    check(scene_profile_v08_set_controller(runtime,&state,error,sizeof(error))!=0,"invalid flag rejected");query(runtime,1,error);
    status=eval(runtime,"return captured_layout_query(true)",error);
    check(status&&strstr(error,"argument domain"),"Android policy query still rejects arguments");
    other=amalur_runtime_create(&config,error,sizeof(error));check(other!=NULL,error);
    options.controller.is_set=1;options.controller.domain=(scene_controller_domain_v08)3;
    check(scene_profile_v08_install(other,&options,error,sizeof(error))!=0,"invalid install domain rejected before publication");
    options.controller.domain=SCENE_CONTROLLER_DOMAIN_ANDROID_LOGICAL_STANDARD;
    options.controller.native_device_kind=15;
    check(!scene_profile_v08_install(other,&options,error,sizeof(error)),error);
    options.controller.domain=SCENE_CONTROLLER_DOMAIN_ANDROID_LOGICAL_REVERSED;
    check(!eval(other,"captured_layout_query=INPUT.is_east_asian_controller_button_swap_required",error),error);
    query(other,0,error);query(runtime,1,error);
    amalur_runtime_destroy(other);amalur_runtime_destroy(runtime);
    printf("{\"ok\":true,\"checks\":%u,\"scope\":\"explicit Android host logical-layout policy; no native-kind mapping\"}\n",checks);
    return 0;
}
