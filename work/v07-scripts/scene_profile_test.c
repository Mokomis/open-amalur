#include "scene_profile.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static unsigned checks;
static void check(int condition,const char *message){if(!condition){fprintf(stderr,"FAIL: %s\n",message);exit(1);}++checks;}
static int eval(amalur_runtime *runtime,const char *source,char *error){int count;return amalur_runtime_eval_source(runtime,source,strlen(source),"profile-test",&count,error,1024);}
int main(int argc,char **argv){
    amalur_runtime_config config={0};amalur_runtime *runtime,*other;lua_State *L;char error[1024];int status,top;
    if(argc!=2){fprintf(stderr,"scene_profile_test RUNTIME_DIR\n");return 2;}config.runtime_dir=argv[1];runtime=amalur_runtime_create(&config,error,sizeof(error));check(runtime!=NULL,error);L=amalur_runtime_state(runtime);
    status=eval(runtime,"return GAME.get_game_engine_version()",error);check(status!=0&&strstr(error,"unimplemented Amalur engine binding"),"default runtime does not invent game engine version");
    status=scene_profile_install(runtime,"wrong-target",error,sizeof(error));check(status!=0&&strstr(error,"SHA256"),"unmatched executable profile rejected");
    top=lua_gettop(L);status=scene_profile_install(runtime,AMALUR_SCENE_PROFILE_SHA256,error,sizeof(error));check(!status,error);check(lua_gettop(L)==top,"profile setup preserves caller stack");
    status=eval(runtime,"local n=select('#',GAME.get_game_engine_version());local v=GAME.get_game_engine_version();assert(n==1 and type(v)=='number' and v==1000);return v",error);check(!status,error);
    status=eval(runtime,"return GAME.get_game_engine_version(1)",error);check(status!=0&&strstr(error,"argument domain"),"unconfirmed argument shapes remain explicit errors");
    status=eval(runtime,"return GAME.is_main_chunk_ready()",error);check(status!=0&&strstr(error,"unimplemented Amalur engine binding"),"unimplemented services remain explicit errors");
    other=amalur_runtime_create(&config,error,sizeof(error));check(other!=NULL,error);status=eval(other,"return GAME.get_game_engine_version()",error);check(status!=0,"profile selection is realm-local");
    amalur_runtime_destroy(other);amalur_runtime_destroy(runtime);printf("{\"ok\":true,\"checks\":%u,\"scope\":\"explicit native-SHA engine version profile via registry provider; static native proof\"}\n",checks);return 0;
}
