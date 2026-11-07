#include "scene_profile.h"
#include "lauxlib.h"
#include <stdio.h>
#include <string.h>
typedef struct profile_setup {amalur_runtime *runtime;char *error;size_t cap;} profile_setup;
/* Static original callback00e267f0 calls00aa18e0(1000). Constructor stores
 * LuaParameter kind6 and payload1000;00aadd20 case6 pushes numeric tag3 with
 * that payload. This is executable-specific evidence, not a guessed version. */
static int game_engine_version(lua_State *L){
    if(lua_gettop(L)!=0)return luaL_error(L,"Unmodeled GAME.get_game_engine_version argument domain");
    lua_pushinteger(L,1000);return 1;
}
static int install(lua_State *L){
    profile_setup *setup=(profile_setup*)lua_touserdata(L,1);int status;
    lua_newtable(L);lua_newtable(L);lua_pushcfunction(L,game_engine_version);
    lua_setfield(L,-2,"get_game_engine_version");lua_setfield(L,-2,"GAME");
    status=amalur_runtime_set_provider(setup->runtime,-1,setup->error,setup->cap);
    if(status)return lua_error(L);
    return 0;
}
int scene_profile_install(amalur_runtime *runtime,const char *target_sha256,char *error,size_t cap){
    profile_setup setup={runtime,error,cap};lua_State *L;int status;
    if(error&&cap)*error=0;
    if(!runtime||!target_sha256||strcmp(target_sha256,AMALUR_SCENE_PROFILE_SHA256)){
        if(error&&cap)snprintf(error,cap,"Explicit supported native executable SHA256 required for scene profile");return LUA_ERRRUN;
    }
    L=amalur_runtime_state(runtime);status=lua_cpcall(L,install,&setup);
    if(status&&error&&cap)snprintf(error,cap,"%s",lua_type(L,-1)==LUA_TSTRING?lua_tostring(L,-1):"Non-string scene profile setup error");
    return status;
}
