#include "scene_profile.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static unsigned checks;
static void check(int condition,const char *message){if(!condition){fprintf(stderr,"FAIL: %s\n",message);exit(1);}++checks;}
static int eval(amalur_runtime *runtime,const char *source,char *error){int count;return amalur_runtime_eval_source(runtime,source,strlen(source),"input-registry-test",&count,error,1024);}
int main(int argc,char **argv){
    amalur_runtime_config config={0};amalur_runtime *runtime;char error[1024];int status;
    if(argc!=2){fprintf(stderr,"input_registry_test V07_RUNTIME_DIR\n");return 2;}
    config.runtime_dir=argv[1];runtime=amalur_runtime_create(&config,error,sizeof(error));check(runtime!=NULL,error);
    status=eval(runtime,"local expected={QUEST=48,GAME=165,ACTOR=611,TIME=6,WINDOW=232,INPUT=42};for name,count in pairs(expected)do local ns=_G[name];assert(type(ns)=='table' and getmetatable(ns)==nil);local n=0;for k,v in pairs(ns)do assert(type(k)=='string' and type(v)=='function');n=n+1 end;assert(n==count)end",error);check(!status,error);
    status=eval(runtime,"return INPUT.is_east_asian_controller_button_swap_required()",error);check(status&&strstr(error,"unimplemented Amalur engine binding: INPUT.is_east_asian_controller_button_swap_required"),"missing INPUT behavior is explicit binding error");
    status=scene_profile_install(runtime,AMALUR_SCENE_PROFILE_SHA256,error,sizeof(error));check(!status,error);
    status=eval(runtime,"assert(GAME.get_game_engine_version()==1000);local n=0;for k,v in pairs(INPUT)do n=n+1 end;assert(n==42)",error);check(!status,error);
    status=eval(runtime,"return INPUT.is_east_asian_controller_button_swap_required()",error);check(status&&strstr(error,"unimplemented Amalur engine binding: INPUT.is_east_asian_controller_button_swap_required"),"GAME profile does not invent INPUT state");
    amalur_runtime_destroy(runtime);printf("{\"ok\":true,\"checks\":%u,\"scope\":\"42 proven INPUT registrations; missing native controller state remains explicit\"}\n",checks);return 0;
}
