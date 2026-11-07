#include "amalur_runtime.h"
#include "lauxlib.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static unsigned checks;
static void check(int ok,const char *message){if(!ok){fprintf(stderr,"FAIL: %s\n",message);exit(1);}++checks;}
static int eval(amalur_runtime *r,const char *s,char *error){int count;return amalur_runtime_eval_source(r,s,strlen(s),"save-restore-registry-test",&count,error,1024);}
static void check_registry_methods(amalur_runtime *runtime,const char *directory){
    static const struct {const char *name;unsigned count;} expected[]={
        {"QUEST",48},{"GAME",165},{"ACTOR",611},{"TIME",6},{"WINDOW",232},{"INPUT",42},{"PROFILE",123},{"SAVE_RESTORE",41}};
    lua_State *L=amalur_runtime_state(runtime);char path[2048],message[512];unsigned namespaces=0,i,n;const char *name;int size,status;
    size=snprintf(path,sizeof(path),"%s/engine_binding_registry.lua",directory);
    check(size>0&&(size_t)size<sizeof(path),"registry path fits test buffer");
    status=luaL_loadfile(L,path);if(!status)status=lua_pcall(L,0,1,0);
    check(!status,status?lua_tostring(L,-1):"registry loaded");check(lua_istable(L,-1),"registry source returns table");
    lua_pushnil(L);
    while(lua_next(L,1)){
        check(lua_type(L,2)==LUA_TSTRING&&lua_istable(L,3),"registry namespace entry shape");
        name=lua_tostring(L,2);for(i=0;i<8&&strcmp(expected[i].name,name);++i){}
        snprintf(message,sizeof(message),"unexpected registry namespace: %s",name);check(i<8,message);
        lua_getglobal(L,name);snprintf(message,sizeof(message),"runtime namespace missing: %s",name);check(lua_istable(L,4),message);
        n=0;lua_pushnil(L);
        while(lua_next(L,3)){
            check(lua_type(L,5)==LUA_TSTRING&&lua_type(L,6)==LUA_TSTRING,"registry method entry shape");
            lua_getfield(L,4,lua_tostring(L,5));
            snprintf(message,sizeof(message),"registered method unreachable: %s.%s",name,lua_tostring(L,5));
            check(lua_isfunction(L,7),message);lua_pop(L,2);++n;
        }
        snprintf(message,sizeof(message),"registry count mismatch: %s expected=%u actual=%u",name,expected[i].count,n);
        check(n==expected[i].count,message);lua_pop(L,2);++namespaces;
    }
    check(namespaces==8,"all eight registry namespaces loaded");lua_pop(L,1);
}
int main(int argc,char **argv){
    amalur_runtime_config config={0};amalur_runtime *runtime;char error[1024];int status;
    if(argc!=2){fprintf(stderr,"save_restore_registry_test RUNTIME_DIR\n");return 2;}
    config.runtime_dir=argv[1];runtime=amalur_runtime_create(&config,error,sizeof(error));check(runtime!=NULL,error);
    check_registry_methods(runtime,argv[1]);
    status=eval(runtime,"return PROFILE.get_variable(1)",error);check(status&&strstr(error,"unimplemented Amalur engine binding: PROFILE.get_variable"),"missing profile read provider remains explicit");
    status=eval(runtime,"return PROFILE.set_variable(1,2)",error);check(status&&strstr(error,"unimplemented Amalur engine binding: PROFILE.set_variable"),"missing profile write provider remains explicit");
    status=eval(runtime,"assert(PROFILE.__unregistered_method==nil and type(WINDOW.get_platform)=='function')",error);check(!status,error);
    status=eval(runtime,"return SAVE_RESTORE.does_platform_support_quick_save()",error);check(status&&strstr(error,"unimplemented Amalur engine binding: SAVE_RESTORE.does_platform_support_quick_save"),"missing quick-save capability remains explicit");
    amalur_runtime_destroy(runtime);printf("{\"ok\":true,\"checks\":%u,\"scope\":\"41 proven SAVE_RESTORE registrations; save capability and persistence remain unimplemented\"}\n",checks);return 0;
}
