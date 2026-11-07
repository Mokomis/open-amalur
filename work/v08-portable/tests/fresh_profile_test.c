#include "scene_profile_v08.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static unsigned checks;
static void check(int okay,const char *message){if(!okay){fprintf(stderr,"FAIL: %s\n",message);exit(1);}++checks;}
static int eval(amalur_runtime *r,const char *code,char *error){int n;return amalur_runtime_eval_source(r,code,strlen(code),"fresh-profile-test",&n,error,1024);}
static void missing(amalur_runtime *r,int32_t hash,char *error){
    char code[96];int n,status;lua_State *L=amalur_runtime_state(r);
    snprintf(code,sizeof(code),"return saved_preference_query(%d)",(int)hash);
    status=amalur_runtime_eval_source(r,code,strlen(code),"missing-preference",&n,error,1024);
    check(!status&&n==1&&lua_type(L,1)==LUA_TNIL,error);
}
static void stored(amalur_runtime *r,int32_t hash,int32_t value,char *error){
    char code[96];int n,status;lua_State *L=amalur_runtime_state(r);
    snprintf(code,sizeof(code),"return saved_preference_query(%d)",(int)hash);
    status=amalur_runtime_eval_source(r,code,strlen(code),"stored-preference",&n,error,1024);
    check(!status&&n==1&&lua_type(L,1)==LUA_TNUMBER&&lua_tonumber(L,1)==(lua_Number)value,error);
}
static void write_value(amalur_runtime *r,int32_t hash,int32_t value,char *error){
    char code[128];int n,status;
    snprintf(code,sizeof(code),"return saved_preference_write(%d,%d)",(int)hash,(int)value);
    status=amalur_runtime_eval_source(r,code,strlen(code),"write-preference",&n,error,1024);
    check(!status&&n==0,"valid preference setter returns zero values");
}
int main(int argc,char **argv){
    amalur_runtime_config config={0};scene_profile_v08_options options={0};
    scene_content_state_v08 content={1,8,8};
    scene_controller_state_v08 controller={1,15,SCENE_CONTROLLER_DOMAIN_NATIVE_KIND};
    amalur_runtime *unknown,*fresh,*other;char error[1024];int status,top;unsigned i;
    const int32_t keys[]={INT32_MIN,INT32_MIN+1,-1,0,1,585298,2096549,INT32_MAX};
    const char *invalid[]={
        "saved_preference_query()", "saved_preference_query(nil)",
        "saved_preference_query(true)", "saved_preference_query('1')",
        "saved_preference_query({})", "saved_preference_query(function()end)",
        "saved_preference_query(-2147483649)", "saved_preference_query(2147483648)",
        "saved_preference_query(1.5)", "saved_preference_query(0/0)",
        "saved_preference_query(1/0)", "saved_preference_query(-1/0)",
        "saved_preference_query(1,nil)"
    };
    const char *invalid_writes[]={
        "saved_preference_write()", "saved_preference_write(5)",
        "saved_preference_write(5,8,nil)", "saved_preference_write('5',8)",
        "saved_preference_write(nil,8)", "saved_preference_write(true,8)",
        "saved_preference_write({},8)", "saved_preference_write(1.5,8)",
        "saved_preference_write(-2147483649,8)", "saved_preference_write(2147483648,8)",
        "saved_preference_write(0/0,8)", "saved_preference_write(1/0,8)",
        "saved_preference_write(5,nil)", "saved_preference_write(5,true)",
        "saved_preference_write(5,'8')", "saved_preference_write(5,{})",
        "saved_preference_write(5,function()end)", "saved_preference_write(5,8.5)",
        "saved_preference_write(5,-2147483649)", "saved_preference_write(5,2147483648)",
        "saved_preference_write(5,0/0)", "saved_preference_write(5,1/0)",
        "saved_preference_write(5,-1/0)"
    };
    if(argc!=2){fprintf(stderr,"fresh_profile_test RUNTIME_DIR_WITH_PROFILE\n");return 2;}
    config.runtime_dir=argv[1];options.target_sha256=AMALUR_SCENE_PROFILE_V08_SHA256;
    options.controller=controller;options.content.is_set=1;
    options.platform.is_set=1;options.platform.name_hash=2096549;
    unknown=amalur_runtime_create(&config,error,sizeof(error));check(unknown!=NULL,error);
    options.fresh_profile=2;check(scene_profile_v08_install(unknown,&options,error,sizeof(error))!=0,"invalid positive fresh flag rejected");
    options.fresh_profile=-1;check(scene_profile_v08_install(unknown,&options,error,sizeof(error))!=0,"invalid negative fresh flag rejected");
    options.fresh_profile=0;check(!scene_profile_v08_install(unknown,&options,error,sizeof(error)),error);
    check(!eval(unknown,"saved_preference_query=PROFILE.get_variable;saved_preference_write=PROFILE.set_variable",error),error);
    status=eval(unknown,"return saved_preference_query(585298)",error);
    check(status&&strstr(error,"preference state is unset"),"unset preference session fails explicitly");
    status=eval(unknown,"saved_preference_write(5,7)",error);
    check(status&&strstr(error,"preference state is unset"),"unset preference session rejects writes");

    fresh=amalur_runtime_create(&config,error,sizeof(error));check(fresh!=NULL,error);
    options.fresh_profile=1;top=lua_gettop(amalur_runtime_state(fresh));
    check(!scene_profile_v08_install(fresh,&options,error,sizeof(error)),error);
    check(lua_gettop(amalur_runtime_state(fresh))==top,"fresh profile install preserves caller stack");
    options.fresh_profile=0; /* Caller mutation cannot change copied state. */
    check(!eval(fresh,"saved_preference_query=PROFILE.get_variable;saved_preference_write=PROFILE.set_variable;collectgarbage('collect')",error),error);
    for(i=0;i<sizeof(keys)/sizeof(keys[0]);++i)missing(fresh,keys[i],error);
    for(i=0;i<sizeof(invalid)/sizeof(invalid[0]);++i){
        status=eval(fresh,invalid[i],error);
        check(status&&strstr(error,"argument domain"),"invalid preference arguments rejected");
    }
    write_value(fresh,INT32_MIN,INT32_MAX,error);stored(fresh,INT32_MIN,INT32_MAX,error);
    write_value(fresh,INT32_MAX,INT32_MIN,error);stored(fresh,INT32_MAX,INT32_MIN,error);
    write_value(fresh,INT32_MIN,-1,error);stored(fresh,INT32_MIN,-1,error);stored(fresh,INT32_MAX,INT32_MIN,error);
    write_value(fresh,0,0,error);stored(fresh,0,0,error);missing(fresh,1,error);
    write_value(fresh,5,7,error);
    for(i=0;i<sizeof(invalid_writes)/sizeof(invalid_writes[0]);++i){
        status=eval(fresh,invalid_writes[i],error);
        check(status&&strstr(error,"argument domain"),"invalid preference write rejected");
        stored(fresh,5,7,error); /* Rejected writes must not replace valid state. */
    }
    check(!eval(fresh,"PROFILE.set_variable(42,10);assert(saved_preference_query(42)==10);saved_preference_write(42,11);assert(PROFILE.get_variable(42)==11);collectgarbage('collect')",error),error);
    stored(fresh,42,11,error);stored(fresh,INT32_MIN,-1,error);stored(fresh,INT32_MAX,INT32_MIN,error);
    check(!scene_profile_v08_set_content(fresh,&content,error,sizeof(error)),error);
    controller.native_device_kind=7;check(!scene_profile_v08_set_controller(fresh,&controller,error,sizeof(error)),error);
    check(!eval(fresh,"assert(GAME.get_game_engine_version()==1000);assert(GAME.is_content_package_active(3));assert(WINDOW.get_platform()==2096549);assert(not INPUT.is_east_asian_controller_button_swap_required())",error),error);
    stored(fresh,INT32_MAX,INT32_MIN,error);
    status=eval(unknown,"return saved_preference_query(585298)",error);
    check(status&&strstr(error,"preference state is unset"),"fresh-session configuration is realm-local");
    other=amalur_runtime_create(&config,error,sizeof(error));check(other!=NULL,error);
    options.fresh_profile=1;check(!scene_profile_v08_install(other,&options,error,sizeof(error)),error);
    check(!eval(other,"saved_preference_query=PROFILE.get_variable;saved_preference_write=PROFILE.set_variable",error),error);
    missing(other,5,error);write_value(other,5,99,error);stored(other,5,99,error);stored(fresh,5,7,error);
    amalur_runtime_destroy(other);amalur_runtime_destroy(fresh);amalur_runtime_destroy(unknown);
    printf("{\"ok\":true,\"checks\":%u,\"scope\":\"fresh in-memory preference dictionary; no user profile import or persistence\"}\n",checks);return 0;
}
