#include "scene_profile_v08.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static unsigned checks;
static void check(int okay,const char *message){
    if(!okay){fprintf(stderr,"FAIL: %s\n",message);exit(1);}++checks;
}
static int eval(amalur_runtime *r,const char *code,char *error){
    int count;return amalur_runtime_eval_source(r,code,strlen(code),"content-state-test",&count,error,1024);
}
static void query(amalur_runtime *r,unsigned index,int expected,char *error){
    char code[96];int count,status;lua_State *L=amalur_runtime_state(r);
    snprintf(code,sizeof(code),"return captured_content_query(%u)",index);
    status=amalur_runtime_eval_source(r,code,strlen(code),"captured-content-query",&count,error,1024);
    check(!status&&count==1&&lua_type(L,1)==LUA_TBOOLEAN&&lua_toboolean(L,1)==expected,error);
}
static void update(amalur_runtime *r,const scene_content_state_v08 *state,char *error){
    lua_State *L=amalur_runtime_state(r);int top=lua_gettop(L);
    check(!scene_profile_v08_set_content(r,state,error,1024),error);
    check(lua_gettop(L)==top,"content setter preserves caller stack");
}
int main(int argc,char **argv){
    amalur_runtime_config config={0};scene_profile_v08_options options={0};
    scene_content_state_v08 state={0};scene_controller_state_v08 controller={1,15,SCENE_CONTROLLER_DOMAIN_NATIVE_KIND};
    amalur_runtime *runtime,*other;char error[1024];int status,top;unsigned i;
    const char *invalid[]={
        "captured_content_query()", "captured_content_query(nil)",
        "captured_content_query(true)", "captured_content_query('3')",
        "captured_content_query({})", "captured_content_query(function()end)",
        "captured_content_query(-1)", "captured_content_query(32)",
        "captured_content_query(3.5)", "captured_content_query(0/0)",
        "captured_content_query(1/0)", "captured_content_query(-1/0)",
        "captured_content_query(3,nil)"
    };
    if(argc!=2){fprintf(stderr,"content_state_test SIX_NAMESPACE_RUNTIME_DIR\n");return 2;}
    config.runtime_dir=argv[1];options.target_sha256=AMALUR_SCENE_PROFILE_V08_SHA256;
    options.controller=controller;
    runtime=amalur_runtime_create(&config,error,sizeof(error));check(runtime!=NULL,error);
    status=scene_profile_v08_set_content(runtime,&state,error,sizeof(error));
    check(status&&strstr(error,"not installed"),"content setter rejects absent profile");
    options.content.is_set=2;
    check(scene_profile_v08_install(runtime,&options,error,sizeof(error))!=0,"invalid initial content flag rejects before publication");
    options.content.is_set=0;
    top=lua_gettop(amalur_runtime_state(runtime));
    check(!scene_profile_v08_install(runtime,&options,error,sizeof(error)),error);
    check(lua_gettop(amalur_runtime_state(runtime))==top,"install preserves caller stack");
    check(!eval(runtime,"captured_content_query=GAME.is_content_package_active; captured_controller_query=INPUT.is_east_asian_controller_button_swap_required; assert(captured_controller_query()==true); assert(GAME.get_game_engine_version()==1000)",error),error);
    status=eval(runtime,"return captured_content_query(3)",error);
    check(status&&strstr(error,"content state is unset"),"default unknown content fails explicitly");

    state.is_set=1;update(runtime,&state,error);
    for(i=0;i<32;++i)query(runtime,i,0,error); /* Explicit known empty mount set. */
    for(i=0;i<32;++i){
        uint32_t bit=UINT32_C(1)<<i;
        state.registered_mask=bit;state.active_mask=0;update(runtime,&state,error);query(runtime,i,0,error);
        state.registered_mask=0;state.active_mask=bit;update(runtime,&state,error);query(runtime,i,0,error);
        state.registered_mask=bit;state.active_mask=bit;update(runtime,&state,error);
        state.registered_mask=state.active_mask=0; /* Caller buffer no longer has selected bits. */
        query(runtime,i,1,error);query(runtime,(i+1)&31,0,error);
    }
    state.registered_mask=UINT32_C(0xaaaaaaaa);state.active_mask=UINT32_C(0xcccccccc);update(runtime,&state,error);
    for(i=0;i<32;++i)query(runtime,i,(UINT32_C(0x88888888)&(UINT32_C(1)<<i))!=0,error);
    state.registered_mask=state.active_mask=UINT32_MAX;update(runtime,&state,error);
    for(i=0;i<32;++i)query(runtime,i,1,error);
    state.is_set=2;check(scene_profile_v08_set_content(runtime,&state,error,sizeof(error))!=0,"invalid content setter flag rejected");query(runtime,31,1,error);
    state.is_set=-1;check(scene_profile_v08_set_content(runtime,&state,error,sizeof(error))!=0,"negative content setter flag rejected");query(runtime,0,1,error);
    check(scene_profile_v08_set_content(runtime,NULL,error,sizeof(error))!=0,"null content setter state rejected");query(runtime,3,1,error);
    for(i=0;i<sizeof(invalid)/sizeof(invalid[0]);++i){
        status=eval(runtime,invalid[i],error);
        check(status&&strstr(error,"argument domain"),"invalid content query arguments rejected");
    }
    check(!eval(runtime,"assert(captured_controller_query()==true);assert(GAME.get_game_engine_version()==1000)",error),"content setters preserve controller provider/version");
    controller.native_device_kind=7;
    check(!scene_profile_v08_set_controller(runtime,&controller,error,sizeof(error)),error);
    check(!eval(runtime,"assert(captured_controller_query()==false)",error),error);query(runtime,3,1,error);
    state.is_set=0;update(runtime,&state,error);
    status=eval(runtime,"return captured_content_query(3)",error);
    check(status&&strstr(error,"content state is unset"),"unsetting restores unknown rather than false");

    other=amalur_runtime_create(&config,error,sizeof(error));check(other!=NULL,error);
    options.content.is_set=1;options.content.registered_mask=8;options.content.active_mask=8;
    check(!scene_profile_v08_install(other,&options,error,sizeof(error)),error);
    options.content.is_set=0;options.content.registered_mask=options.content.active_mask=0;
    check(!eval(other,"captured_content_query=GAME.is_content_package_active",error),error);query(other,3,1,error);
    status=eval(runtime,"return captured_content_query(3)",error);
    check(status&&strstr(error,"content state is unset"),"content state is realm-local");
    amalur_runtime_destroy(other);amalur_runtime_destroy(runtime);
    printf("{\"ok\":true,\"checks\":%u,\"scope\":\"copied explicit content masks; no DLC entitlement or native mount discovery\"}\n",checks);
    return 0;
}
