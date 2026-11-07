#include "amalur_runtime.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

static int echo_binding(lua_State *L) {
    if(lua_gettop(L)!=4 || lua_type(L,1)!=LUA_TUSERDATA || !lua_isnil(L,2) || lua_tointeger(L,3)!=3 || !lua_isnil(L,4)) {
        lua_pushliteral(L,"provider argument count/type mismatch"); return lua_error(L);
    }
    lua_pushnil(L); lua_pushvalue(L,1); lua_pushinteger(L,7); lua_pushnil(L); return 4;
}
static unsigned checks;
static void require(int condition,const char *message) {
    if(!condition){fprintf(stderr,"FAIL: %s\n",message);exit(1);} ++checks;
}
static int evaluate(amalur_runtime *r,const char *source,int *count,char *error) {
    return amalur_runtime_eval_source(r,source,strlen(source),"api-test",count,error,1024);
}
int main(int argc,char **argv) {
    amalur_runtime_config config={0};amalur_runtime *a,*b;lua_State *L;char error[1024];int count,status;
    if(argc!=2){fprintf(stderr,"runtime_api_test RUNTIME_DIR\n");return 2;}
    config.runtime_dir=argv[1];config.instruction_budget=1000;config.memory_limit_bytes=2*1024*1024;
    a=amalur_runtime_create(&config,error,sizeof(error));require(a!=NULL,error);
    b=amalur_runtime_create(&config,error,sizeof(error));require(b!=NULL,error);
    L=amalur_runtime_state(a);lua_newtable(L);lua_newtable(L);lua_pushcfunction(L,echo_binding);
    lua_setfield(L,-2,"get_stage");lua_setfield(L,-2,"QUEST");
    status=amalur_runtime_set_provider(a,-1,error,sizeof(error));require(status==0,error);require(lua_gettop(L)==1,"provider input stack preserved");
    status=evaluate(a,"local h=__amalur_handles.from_key('quest',4294967295); return QUEST.get_stage(h,nil,3,nil)",&count,error);
    require(status==0,error);require(count==4,"provider trailing nil result count");
    require(lua_isnil(L,1)&&lua_type(L,2)==LUA_TUSERDATA&&lua_tointeger(L,3)==7&&lua_isnil(L,4),"provider result types");
    status=evaluate(b,"return QUEST.get_stage(__amalur_handles.from_key('quest',1))",&count,error);
    require(status!=0&&strstr(error,"unimplemented Amalur engine binding")!=NULL,"second realm has no provider");
    status=evaluate(a,"error({marker=true})",&count,error);
    require(status!=0&&lua_gettop(L)==1&&lua_istable(L,1),"original non-string error retained");
    lua_getfield(L,1,"marker");require(lua_toboolean(L,-1),"error marker retained");
    status=evaluate(a,"error(23,0)",&count,error);require(status!=0&&lua_gettop(L)==1&&lua_type(L,1)==LUA_TNUMBER&&lua_tointeger(L,1)==23,"numeric error object retains its type");
    status=evaluate(a,"return xpcall(function()error(\"original\")end,function(e)return \"transformed\"end)",&count,error);
    require(status==0&&count==2&&!lua_toboolean(L,1)&&!strcmp(lua_tostring(L,2),"transformed"),"ordinary xpcall error transformation");
    status=evaluate(a,"while true do pcall(function()while true do end end)end",&count,error);
    require(status!=0&&strstr(error,"instruction budget exhausted")!=NULL,"pcall cannot swallow budget");
    status=evaluate(a,"while true do xpcall(function()while true do end end,function(e)return e end)end",&count,error);
    require(status!=0&&strstr(error,"instruction budget exhausted")!=NULL,"xpcall cannot swallow budget");
    status=evaluate(a,"return xpcall(function()while true do end end,function()while true do end end)",&count,error);
    require(status!=0&&strstr(error,"instruction budget exhausted")!=NULL,"budget error skips looping xpcall handler");
    status=evaluate(a,"return xpcall(function()error(\"ordinary\")end,function()while true do end end)",&count,error);
    require(status!=0&&strstr(error,"instruction budget exhausted")!=NULL,"ordinary-error handler loop stays budget bounded");
    status=evaluate(a,"return 17,nil",&count,error);require(status==0&&count==2&&lua_tointeger(L,1)==17&&lua_isnil(L,2),"realm recovers after budget error");
    status=evaluate(a,"local t={} while true do t[#t+1]=string.rep('x',65536)..#t end",&count,error);
    require(status==LUA_ERRMEM,"Lua memory cap returns protected error");
    require(amalur_runtime_memory_used(a)<=config.memory_limit_bytes,"allocator within configured cap");
    status=evaluate(a,"return 19,nil",&count,error);require(status==0&&count==2&&lua_tointeger(L,1)==19&&lua_isnil(L,2),"realm recovers after memory error");
    amalur_runtime_destroy(a);amalur_runtime_destroy(b);
    printf("{\"ok\":true,\"checks\":%u,\"scope\":\"portable embedding API contracts, no engine behavior claim\"}\n",checks);return 0;
}
