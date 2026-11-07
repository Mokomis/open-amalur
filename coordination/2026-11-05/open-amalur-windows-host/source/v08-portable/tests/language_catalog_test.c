#include "scene_profile_v08.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static unsigned checks;
static const char *methods[]={"get_available_ost_languages","get_available_audio_languages","get_available_ost_language_names","get_available_audio_language_names"};
static void check(int ok,const char *message){if(!ok){fprintf(stderr,"FAIL: %s\n",message);exit(1);}++checks;}
static void succeeds(amalur_runtime *r,const char *s){int count;char error[1024];int status=amalur_runtime_eval_source(r,s,strlen(s),"language-catalog-test",&count,error,sizeof(error));check(!status,error);}
static void fails(amalur_runtime *r,const char *s,const char *fragment){int count;char error[1024];int status=amalur_runtime_eval_source(r,s,strlen(s),"language-catalog-test",&count,error,sizeof(error));check(status&&strstr(error,fragment),error);}
static amalur_runtime *create(const amalur_runtime_config *config){char error[1024];amalur_runtime *r=amalur_runtime_create(config,error,sizeof(error));check(r!=NULL,error);return r;}
int main(int argc,char **argv){
    amalur_runtime_config config={0};scene_profile_v08_options options={0};amalur_runtime *runtime;
    scene_controller_state_v08 controller={1,1,SCENE_CONTROLLER_DOMAIN_NATIVE_KIND};scene_content_state_v08 content={1,2,2};
    const int invalid_flags[]={-1,2,INT32_MIN,INT32_MAX};char error[1024],source[1024];int status;unsigned i;
    if(argc!=2){fprintf(stderr,"language_catalog_test RUNTIME_DIR\n");return 2;}config.runtime_dir=argv[1];
    options.target_sha256=AMALUR_SCENE_PROFILE_V08_SHA256;
    runtime=create(&config);status=scene_profile_v08_install(runtime,&options,error,sizeof(error));check(!status,error);
    options.no_language_packs=1; /* Unknown installation cannot borrow this later change. */
    for(i=0;i<4;i++){
        snprintf(source,sizeof(source),"return GAME.%s()",methods[i]);fails(runtime,source,"language catalog is unset");
        snprintf(source,sizeof(source),"return GAME.%s(nil)",methods[i]);fails(runtime,source,"argument domain");
    }
    amalur_runtime_destroy(runtime);
    options.controller.is_set=1;options.controller.native_device_kind=13;
    options.content.is_set=1;options.content.registered_mask=1;options.content.active_mask=1;
    options.platform.is_set=1;options.platform.name_hash=2096549;options.fresh_profile=1;
    options.quick_save.is_set=1;options.quick_save.supported=0;
    runtime=create(&config);status=scene_profile_v08_install(runtime,&options,error,sizeof(error));check(!status,error);
    memset(&options,0,sizeof(options)); /* All options were copied into Lua-owned state. */
    succeeds(runtime,"captured_language_methods={GAME.get_available_ost_languages,GAME.get_available_audio_languages,GAME.get_available_ost_language_names,GAME.get_available_audio_language_names};for i,fn in ipairs(captured_language_methods)do local a=fn();local b=fn();assert(type(a)=='table' and getmetatable(a)==nil and not rawequal(a,b));assert(#a==1 and a[0]==nil and a[2]==nil and select('#',fn())==1);local n=0;for k,v in pairs(a)do n=n+1;assert(k==1)end;assert(n==1);if i<=2 then assert(a[1]==-1 and type(a[1])=='number')else assert(a[1]=='Automatic')end;a[1]='changed';a[2]='extra';a.extra=17;assert(#fn()==1 and fn()[1]==b[1] and fn().extra==nil)end");
    for(i=0;i<4;i++){
        snprintf(source,sizeof(source),"return GAME.%s(nil)",methods[i]);fails(runtime,source,"argument domain");
        snprintf(source,sizeof(source),"return GAME.%s(1,2)",methods[i]);fails(runtime,source,"argument domain");
        snprintf(source,sizeof(source),"return GAME:%s()",methods[i]);fails(runtime,source,"argument domain");
    }
    succeeds(runtime,"assert(GAME.get_game_engine_version()==1000 and INPUT.is_east_asian_controller_button_swap_required()==true and GAME.is_content_package_active(0)==true and WINDOW.get_platform()==2096549 and SAVE_RESTORE.does_platform_support_quick_save()==false);assert(PROFILE.get_variable(123)==nil);PROFILE.set_variable(123,456);assert(PROFILE.get_variable(123)==456)");
    status=scene_profile_v08_set_controller(runtime,&controller,error,sizeof(error));check(!status,error);
    status=scene_profile_v08_set_content(runtime,&content,error,sizeof(error));check(!status,error);
    succeeds(runtime,"assert(INPUT.is_east_asian_controller_button_swap_required()==false and GAME.is_content_package_active(0)==false and GAME.is_content_package_active(1)==true);assert(GAME.get_available_ost_languages==captured_language_methods[1] and GAME.get_available_audio_languages==captured_language_methods[2] and GAME.get_available_ost_language_names==captured_language_methods[3] and GAME.get_available_audio_language_names==captured_language_methods[4]);for i,fn in ipairs(captured_language_methods)do local a=fn();assert(#a==1 and a[1]==(i<=2 and -1 or 'Automatic'))end");
    fails(runtime,"return GAME.get_active_ost_language_id()","unimplemented Amalur engine binding: GAME.get_active_ost_language_id");
    fails(runtime,"return GAME.set_ost_to_language_id(-1)","unimplemented Amalur engine binding: GAME.set_ost_to_language_id");
    fails(runtime,"return GAME.set_audio_to_language_id(-1)","unimplemented Amalur engine binding: GAME.set_audio_to_language_id");
    amalur_runtime_destroy(runtime);
    for(i=0;i<sizeof(invalid_flags)/sizeof(invalid_flags[0]);i++){
        memset(&options,0,sizeof(options));options.target_sha256=AMALUR_SCENE_PROFILE_V08_SHA256;options.no_language_packs=invalid_flags[i];
        runtime=create(&config);status=scene_profile_v08_install(runtime,&options,error,sizeof(error));check(status&&strstr(error,"no-language-packs"),"invalid catalog flag rejected before provider publication");
        fails(runtime,"return GAME.get_game_engine_version()","unimplemented Amalur engine binding");
        options.no_language_packs=1;status=scene_profile_v08_install(runtime,&options,error,sizeof(error));check(!status,error);
        succeeds(runtime,"assert(GAME.get_available_ost_languages()[1]==-1 and GAME.get_available_audio_language_names()[1]=='Automatic')");amalur_runtime_destroy(runtime);
    }
    printf("{\"ok\":true,\"checks\":%u,\"scope\":\"explicit no-mounted-language-packs ID lists and host Automatic labels; not native localized label or audio parity\"}\n",checks);return 0;
}
