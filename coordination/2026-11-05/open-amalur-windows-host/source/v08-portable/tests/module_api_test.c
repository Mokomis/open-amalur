#include "amalur_runtime.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

static unsigned checks;
static void check(int condition,const char *message) {
    if(!condition){fprintf(stderr,"FAIL: %s\n",message);exit(1);} ++checks;
}
static int eval(amalur_runtime *r,const char *source,int *count,char *error) {
    return amalur_runtime_eval_source(r,source,strlen(source),"module-test",count,error,1024);
}
static int add(amalur_runtime *r,const char *name,const char *source,char *error) {
    return amalur_runtime_register_module_source(r,name,source,strlen(source),error,1024);
}
int main(int argc,char **argv) {
    amalur_runtime_config config={0}; amalur_runtime *r,*other; lua_State *L;
    char error[1024];int count,status;
    if(argc!=2){fprintf(stderr,"module_api_test RUNTIME_DIR\n");return 2;}
    config.runtime_dir=argv[1];config.instruction_budget=1000000;
    r=amalur_runtime_create(&config,error,sizeof(error));check(r!=NULL,error);L=amalur_runtime_state(r);
    status=add(r,"A","module('A',package.seeall); loads=(loads or 0)+1; function get() return shared_value end",error);check(status==0,error);
    check(lua_gettop(L)==0,"registration does not execute or pollute stack");
    status=eval(r,"assert(A==nil); shared_value=11; local a=require('A'); local b=require('A'); assert(a==b and a.loads==1); assert(a.get()==11); shared_value=12; assert(a.get()==12); assert(a._M==a and a._NAME=='A' and a._PACKAGE==''); assert(getmetatable(a).__index==_G); return __amalur_module_table_allowed(a)",&count,error);
    check(status==0&&count==1&&lua_toboolean(L,1),error);
    status=eval(r,"return __amalur_module_table_allowed(setmetatable({}, {__index=_G}))",&count,error);
    check(status==0&&count==1&&!lua_toboolean(L,1),"unregistered fallback table rejected");
    status=eval(r,"local mt=getmetatable(A); mt.extra=true; local no=not __amalur_module_table_allowed(A); mt.extra=nil; return no and __amalur_module_table_allowed(A)",&count,error);
    check(status==0&&lua_toboolean(L,1),"changed marked metatable rejected and exact shape restored");
    status=eval(r,"local mt=getmetatable(A); setmetatable(A,{__index=_G}); local no=not __amalur_module_table_allowed(A); setmetatable(A,mt); return no and __amalur_module_table_allowed(A)",&count,error);
    check(status==0&&lua_toboolean(L,1),"replacement metatable rejected by identity");
    status=eval(r,"setmetatable(_G,{__index=function() return 99 end}); local no=not __amalur_module_table_allowed(A); setmetatable(_G,nil); return no and __amalur_module_table_allowed(A)",&count,error);
    check(status==0&&lua_toboolean(L,1),"module fallback requires plain realm globals");
    status=add(r,"A","return {}",error);check(status!=0&&strstr(error,"Duplicate")!=NULL,"duplicate source rejected");
    status=add(r,"B","module('B',package.seeall); local a=require('A'); result=a.get()",error);check(status==0,error);
    status=eval(r,"return require('B').result",&count,error);check(status==0&&lua_tointeger(L,1)==12,error);
    status=add(r,"ReturnsFalse","return false",error);check(status==0,error);
    status=eval(r,"return require('ReturnsFalse')",&count,error);check(status==0&&count==1&&lua_type(L,1)==LUA_TBOOLEAN&&!lua_toboolean(L,1),"false module return preserved");
    status=add(r,"ReturnsNothing","",error);check(status==0,error);
    status=eval(r,"return require('ReturnsNothing')",&count,error);check(status==0&&count==1&&lua_toboolean(L,1),"nil module defaults to true per Lua5.1");
    status=add(r,"Cycle","require('Cycle')",error);check(status==0,error);
    status=eval(r,"return require('Cycle')",&count,error);check(status!=0&&strstr(error,"loop or previous error")!=NULL,"require cycle fails explicitly");
    status=eval(r,"return require('io')",&count,error);check(status!=0,"removed I/O cannot be required from old loaded registry");
    status=eval(r,"return require('C:/not-a-module')",&count,error);check(status!=0,"no file search fallback");
    status=eval(r,"assert(package.path==nil and package.cpath==nil and package.loadlib==nil and package.loaders==nil and package.preload==nil); return 1",&count,error);check(status==0,error);
    status=add(r,"SyntaxError","this is not lua",error);check(status!=0,"syntax error rejected at registration");
    status=add(r,"SyntaxError","return 23",error);check(status==0,"failed registration leaves no half module");
    status=eval(r,"return require('SyntaxError')",&count,error);check(status==0&&lua_tointeger(L,1)==23,error);
    {
        const char *source="assert((...)=='Lazy'); module('Lazy',package.seeall); value=31";
        char *copy=(char*)malloc(strlen(source)+1);check(copy!=NULL,"source copy allocated");strcpy(copy,source);
        status=amalur_runtime_register_module_source_lazy(r,"Lazy",copy,strlen(copy),error,sizeof(error));
        memset(copy,'x',strlen(copy));free(copy);check(status==0,error);
        status=eval(r,"assert(Lazy==nil); local x=require('Lazy'); assert(__amalur_module_table_allowed(x)); assert(x==require('Lazy')); return x.value",&count,error);
        check(status==0&&lua_tointeger(L,1)==31,"lazy source copies bytes, receives module name, and preserves tracked module semantics");
        status=amalur_runtime_register_module_source_lazy(r,"LazySyntax","this is not lua",15,error,sizeof(error));check(status==0,"lazy syntax check deferred");
        status=eval(r,"return require('LazySyntax')",&count,error);check(status!=0,"lazy source syntax fails at require");
        status=amalur_runtime_register_module_file_lazy(r,"LazyMissing","nonexistent-explicit-module-41f6d1.lua",error,sizeof(error));check(status==0,"lazy file reading deferred");
        status=eval(r,"return require('LazyMissing')",&count,error);check(status!=0&&strstr(error,"cannot open")!=NULL,"lazy missing file fails at require");
    }
    other=amalur_runtime_create(&config,error,sizeof(error));check(other!=NULL,error);
    status=eval(other,"return require('A')",&count,error);check(status!=0,"module registration is realm-local");
    amalur_runtime_destroy(other);amalur_runtime_destroy(r);
    printf("{\"ok\":true,\"checks\":%u,\"scope\":\"portable Lua5.1 module contract; not native game equivalence\"}\n",checks);
    return 0;
}
