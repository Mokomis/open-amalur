#include "scene_profile_v08.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static unsigned checks;
static void check(int okay,const char *message){if(!okay){fprintf(stderr,"FAIL: %s\n",message);exit(1);}++checks;}
static int eval(amalur_runtime *r,const char *code,char *error){int n;return amalur_runtime_eval_source(r,code,strlen(code),"quick-save-state-test",&n,error,1024);}
static void capability(amalur_runtime *r,int expected,char *error){
    const char *code="return saved_capability()";int n,status;lua_State *L=amalur_runtime_state(r);
    status=amalur_runtime_eval_source(r,code,strlen(code),"captured-quick-save",&n,error,1024);
    check(!status&&n==1&&lua_type(L,1)==LUA_TBOOLEAN&&lua_toboolean(L,1)==expected,error);
}
int main(int argc,char **argv){
    amalur_runtime_config config={0};scene_profile_v08_options options={0};
    amalur_runtime *unknown,*unsupported,*supported;char error[1024];int status,top;unsigned i;
    const scene_quick_save_state_v08 invalid[]={{2,0},{-1,0},{1,2},{1,-1},{0,2}};
    if(argc!=2){fprintf(stderr,"quick_save_state_test RUNTIME_DIR_WITH_SAVE_RESTORE\n");return 2;}
    config.runtime_dir=argv[1];options.target_sha256=AMALUR_SCENE_PROFILE_V08_SHA256;
    options.controller.is_set=1;options.controller.native_device_kind=15;
    options.content.is_set=1;options.platform.is_set=1;options.platform.name_hash=2096549;options.fresh_profile=1;
    unknown=amalur_runtime_create(&config,error,sizeof(error));check(unknown!=NULL,error);
    for(i=0;i<sizeof(invalid)/sizeof(invalid[0]);++i){options.quick_save=invalid[i];check(scene_profile_v08_install(unknown,&options,error,sizeof(error))!=0,"non-boolean capability flags rejected before publication");}
    options.quick_save.is_set=0;options.quick_save.supported=1;
    check(!scene_profile_v08_install(unknown,&options,error,sizeof(error)),error);
    check(!eval(unknown,"saved_capability=SAVE_RESTORE.does_platform_support_quick_save",error),error);
    status=eval(unknown,"return saved_capability()",error);check(status&&strstr(error,"quick-save state is unset"),"supported value cannot override unknown state");

    unsupported=amalur_runtime_create(&config,error,sizeof(error));check(unsupported!=NULL,error);
    options.quick_save.is_set=1;options.quick_save.supported=0;
    top=lua_gettop(amalur_runtime_state(unsupported));check(!scene_profile_v08_install(unsupported,&options,error,sizeof(error)),error);
    check(lua_gettop(amalur_runtime_state(unsupported))==top,"capability install preserves caller stack");
    options.quick_save.supported=1;options.quick_save.is_set=0;
    check(!eval(unsupported,"saved_capability=SAVE_RESTORE.does_platform_support_quick_save;collectgarbage('collect')",error),error);capability(unsupported,0,error);
    status=eval(unsupported,"return saved_capability(nil)",error);check(status&&strstr(error,"argument domain"),"explicit nil argument rejected");
    status=eval(unsupported,"return saved_capability(1,2)",error);check(status&&strstr(error,"argument domain"),"multiple arguments rejected");
    check(!eval(unsupported,"PROFILE.set_variable(123,7);assert(PROFILE.get_variable(123)==7);assert(GAME.get_game_engine_version()==1000);assert(not GAME.is_content_package_active(3));assert(WINDOW.get_platform()==2096549);assert(INPUT.is_east_asian_controller_button_swap_required())",error),error);capability(unsupported,0,error);

    supported=amalur_runtime_create(&config,error,sizeof(error));check(supported!=NULL,error);
    options.quick_save.is_set=1;options.quick_save.supported=1;
    check(!scene_profile_v08_install(supported,&options,error,sizeof(error)),error);
    options.quick_save.supported=0;
    check(!eval(supported,"saved_capability=SAVE_RESTORE.does_platform_support_quick_save",error),error);capability(supported,1,error);capability(unsupported,0,error);
    status=eval(unknown,"return saved_capability()",error);check(status&&strstr(error,"quick-save state is unset"),"capability is realm-local");
    amalur_runtime_destroy(supported);amalur_runtime_destroy(unsupported);amalur_runtime_destroy(unknown);
    printf("{\"ok\":true,\"checks\":%u,\"scope\":\"copied explicit quick-save capability only; no save operations\"}\n",checks);return 0;
}
