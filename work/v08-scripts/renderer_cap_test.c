#include "scene_profile_v08.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static unsigned checks;
static void check(int ok,const char *message){if(!ok){fprintf(stderr,"FAIL: %s\n",message);exit(1);}++checks;}
static void succeeds(amalur_runtime *r,const char *s){int count;char error[1024];int status=amalur_runtime_eval_source(r,s,strlen(s),"renderer-cap-test",&count,error,sizeof(error));check(!status,error);}
static void fails(amalur_runtime *r,const char *s,const char *fragment){int count;char error[1024];int status=amalur_runtime_eval_source(r,s,strlen(s),"renderer-cap-test",&count,error,sizeof(error));check(status&&strstr(error,fragment),error);}
static amalur_runtime *create(const amalur_runtime_config *config){char error[1024];amalur_runtime *r=amalur_runtime_create(config,error,sizeof(error));check(r!=NULL,error);return r;}
int main(int argc,char **argv){
    amalur_runtime_config config={0};scene_profile_v08_options options={0};amalur_runtime *r;char error[1024],source[512];
    const int known[]={1,16},invalid[]={-1,17,INT32_MIN,INT32_MAX};unsigned i;int status;
    if(argc!=2){fprintf(stderr,"renderer_cap_test RUNTIME_DIR\n");return 2;}config.runtime_dir=argv[1];options.target_sha256=AMALUR_SCENE_PROFILE_V08_SHA256;
    r=create(&config);status=scene_profile_v08_install(r,&options,error,sizeof(error));check(!status,error);options.max_anisotropy=1;
    fails(r,"return WINDOW.get_max_anisotrophy()","anisotropy capability is unset");fails(r,"return WINDOW.get_max_anisotrophy(nil)","argument domain");amalur_runtime_destroy(r);
    for(i=0;i<sizeof(known)/sizeof(known[0]);i++){
        memset(&options,0,sizeof(options));options.target_sha256=AMALUR_SCENE_PROFILE_V08_SHA256;options.max_anisotropy=known[i];
        options.platform.is_set=1;options.platform.name_hash=2096549;options.no_language_packs=1;
        r=create(&config);status=scene_profile_v08_install(r,&options,error,sizeof(error));check(!status,error);options.max_anisotropy=0;
        snprintf(source,sizeof(source),"renderer_cap=WINDOW.get_max_anisotrophy;assert(type(renderer_cap())=='number' and renderer_cap()==%d and select('#',renderer_cap())==1)",known[i]);succeeds(r,source);
        fails(r,"return renderer_cap(nil)","argument domain");fails(r,"return renderer_cap(1,2)","argument domain");fails(r,"return WINDOW:get_max_anisotrophy()","argument domain");
        succeeds(r,"assert(WINDOW.get_platform()==2096549 and GAME.get_game_engine_version()==1000 and GAME.get_available_ost_languages()[1]==-1)");amalur_runtime_destroy(r);
    }
    for(i=0;i<sizeof(invalid)/sizeof(invalid[0]);i++){
        memset(&options,0,sizeof(options));options.target_sha256=AMALUR_SCENE_PROFILE_V08_SHA256;options.max_anisotropy=invalid[i];r=create(&config);
        status=scene_profile_v08_install(r,&options,error,sizeof(error));check(status&&strstr(error,"max-anisotropy"),"invalid renderer cap rejected before publication");
        options.max_anisotropy=1;status=scene_profile_v08_install(r,&options,error,sizeof(error));check(!status,error);succeeds(r,"assert(WINDOW.get_max_anisotrophy()==1)");amalur_runtime_destroy(r);
    }
    printf("{\"ok\":true,\"checks\":%u,\"scope\":\"explicit renderer cap mechanics; host preview1 and separate native-value16 fixture, no texture filtering parity\"}\n",checks);return 0;
}
