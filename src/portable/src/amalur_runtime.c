#include "amalur_runtime.h"
#include "lauxlib.h"
#include "lualib.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

struct amalur_runtime {
    lua_State *L;
    const char *runtime_dir; /* Used only during protected initialization. */
    size_t used, limit;
    uint64_t budget, remaining;
    int hook_step, budget_exhausted;
    int carrier_ref, registry_ref, bridge_ref;
};
static char runtime_key;

static void diagnostic(char *dst, size_t cap, const char *message) {
    size_t n;
    if (!dst || !cap) return;
    if (!message) message="non-string Lua error";
    n=strlen(message); if (n>=cap) n=cap-1;
    memcpy(dst,message,n); dst[n]=0;
}
static void *limited_alloc(void *ud, void *ptr, size_t old_size, size_t new_size) {
    amalur_runtime *r=(amalur_runtime*)ud;
    void *next;
    if (!ptr) old_size=0;
    if (!new_size) { free(ptr); r->used-=old_size; return NULL; }
    if (old_size>r->used || new_size>r->limit-(r->used-old_size)) return NULL;
    next=realloc(ptr,new_size);
    if (next) r->used=r->used-old_size+new_size;
    return next;
}
static amalur_runtime *owner(lua_State *L) {
    amalur_runtime *r;
    lua_pushlightuserdata(L,&runtime_key); lua_rawget(L,LUA_REGISTRYINDEX);
    r=(amalur_runtime*)lua_touserdata(L,-1); lua_pop(L,1); return r;
}
static int budget_error(lua_State *L) {
    return luaL_error(L,"Amalur Lua instruction budget exhausted");
}
static void instruction_hook(lua_State *L, lua_Debug *ar) {
    amalur_runtime *r=owner(L); (void)ar;
    if (r->budget_exhausted || r->remaining<=(uint64_t)r->hook_step) {
        r->budget_exhausted=1; budget_error(L); return;
    }
    r->remaining-=(uint64_t)r->hook_step;
    if (r->remaining<(uint64_t)r->hook_step) {
        r->hook_step=(int)r->remaining; lua_sethook(L,instruction_hook,LUA_MASKCOUNT,r->hook_step);
    }
}
static void begin_budget(amalur_runtime *r) {
    r->remaining=r->budget; r->budget_exhausted=0;
    r->hook_step=(int)(r->remaining<1000?r->remaining:1000);
    lua_sethook(r->L,instruction_hook,LUA_MASKCOUNT,r->hook_step);
}
/* Protected calls propagate exhausted host budgets instead of allowing a Lua
 * loop to swallow the hook error indefinitely. Ordinary Lua errors are intact. */
static int bounded_pcall(lua_State *L) {
    int status; amalur_runtime *r=owner(L);
    luaL_checkany(L,1);
    status=lua_pcall(L,lua_gettop(L)-1,LUA_MULTRET,0);
    if (r->budget_exhausted) return budget_error(L);
    lua_pushboolean(L,status==0); lua_insert(L,1); return lua_gettop(L);
}
static int bounded_error_handler(lua_State *L) {
    amalur_runtime *r=owner(L);
    /* Lua 5.1 disables hooks while handling a hook-raised error. Never enter
     * a script error handler once that hook has exhausted the host budget. */
    if (r->budget_exhausted) return budget_error(L);
    lua_pushvalue(L,lua_upvalueindex(1)); lua_pushvalue(L,1); lua_call(L,1,1);
    if (r->budget_exhausted) return budget_error(L);
    return 1;
}
static int bounded_xpcall(lua_State *L) {
    int status; amalur_runtime *r=owner(L);
    luaL_checkany(L,1); luaL_checkany(L,2); lua_settop(L,2);
    lua_pushvalue(L,2); lua_pushcclosure(L,bounded_error_handler,1); lua_replace(L,2);
    lua_pushvalue(L,1); lua_remove(L,1); /* handler, function */
    status=lua_pcall(L,0,LUA_MULTRET,1); lua_remove(L,1);
    if (r->budget_exhausted) return budget_error(L);
    lua_pushboolean(L,status==0); lua_insert(L,1); return lua_gettop(L);
}
static void load_module(lua_State *L, const char *directory, const char *name) {
    size_t a=strlen(directory),b=strlen(name); char *path; int status;
    if (a>4096 || b>256) luaL_error(L,"Runtime module path too long");
    path=(char*)malloc(a+b+2);
    if (!path) luaL_error(L,"Runtime module path allocation failed");
    memcpy(path,directory,a); path[a]='/'; memcpy(path+a+1,name,b+1);
    status=luaL_loadfile(L,path); free(path);
    if (status) lua_error(L);
    lua_call(L,0,1);
    if (!lua_istable(L,-1)) luaL_error(L,"Runtime module %s must return a table",name);
}
static int absolute_index(lua_State *L, int index) {
    return index>0 || index<=LUA_REGISTRYINDEX ? index : lua_gettop(L)+index+1;
}
static void install_provider(lua_State *L, amalur_runtime *r, int provider) {
    provider=absolute_index(L,provider);
    lua_rawgeti(L,LUA_REGISTRYINDEX,r->bridge_ref); lua_getfield(L,-1,"new"); lua_remove(L,-2);
    lua_rawgeti(L,LUA_REGISTRYINDEX,r->registry_ref); lua_pushvalue(L,provider);
    lua_call(L,2,1); /* bridge owns strict registry/provider validation */
    lua_pushnil(L);
    while (lua_next(L,-2)) {
        lua_pushvalue(L,-2); lua_pushvalue(L,-2); lua_rawset(L,LUA_GLOBALSINDEX);
        lua_pop(L,1);
    }
    lua_pop(L,1);
}
static int initialize(lua_State *L) {
    amalur_runtime *r=(amalur_runtime*)lua_touserdata(L,1);
    const char *remove_names[]={"io","os","debug","package","coroutine","require",
        "dofile","loadfile","load","loadstring",NULL};
    const char **name;
    lua_pushlightuserdata(L,&runtime_key); lua_pushlightuserdata(L,r); lua_rawset(L,LUA_REGISTRYINDEX);
    luaL_openlibs(L);
    lua_pushcfunction(L,bounded_pcall); lua_setglobal(L,"pcall");
    lua_pushcfunction(L,bounded_xpcall); lua_setglobal(L,"xpcall");
    begin_budget(r);
    load_module(L,r->runtime_dir,"amalur_uint64.lua");
    lua_pushvalue(L,-1); lua_setglobal(L,"__amalur_uint64"); r->carrier_ref=luaL_ref(L,LUA_REGISTRYINDEX);
    load_module(L,r->runtime_dir,"amalur_engine_handles.lua"); lua_getfield(L,-1,"new");
    lua_rawgeti(L,LUA_REGISTRYINDEX,r->carrier_ref); lua_call(L,1,1); lua_setglobal(L,"__amalur_handles"); lua_pop(L,1);
    load_module(L,r->runtime_dir,"engine_binding_registry.lua"); r->registry_ref=luaL_ref(L,LUA_REGISTRYINDEX);
    load_module(L,r->runtime_dir,"amalur_engine_bindings.lua"); r->bridge_ref=luaL_ref(L,LUA_REGISTRYINDEX);
    load_module(L,r->runtime_dir,"amalur_native_math.lua"); lua_setglobal(L,"math");
    lua_newtable(L); install_provider(L,r,-1); lua_pop(L,1);
    for (name=remove_names;*name;name++) { lua_pushnil(L); lua_setglobal(L,*name); }
    lua_settop(L,0); return 0;
}
amalur_runtime *amalur_runtime_create(const amalur_runtime_config *config, char *error, size_t cap) {
    amalur_runtime *r; int status; uint64_t evaluation_budget;
    diagnostic(error,cap,"");
    if (!config || !config->runtime_dir || !*config->runtime_dir) {
        diagnostic(error,cap,"An explicit runtime directory is required"); return NULL;
    }
    r=(amalur_runtime*)calloc(1,sizeof(*r));
    if (!r) { diagnostic(error,cap,"Host allocation failed"); return NULL; }
    r->runtime_dir=config->runtime_dir;
    r->budget=config->instruction_budget?config->instruction_budget:1000000;
    r->limit=config->memory_limit_bytes?config->memory_limit_bytes:64u*1024u*1024u;
    r->L=lua_newstate(limited_alloc,r);
    if (!r->L) { diagnostic(error,cap,"Lua state allocation failed"); free(r); return NULL; }
    evaluation_budget=r->budget; r->budget=1000000; /* Separate bounded bootstrap budget. */
    status=lua_cpcall(r->L,initialize,r); lua_sethook(r->L,NULL,0,0); r->runtime_dir=NULL;
    r->budget=evaluation_budget;
    if (status) { diagnostic(error,cap,lua_type(r->L,-1)==LUA_TSTRING?lua_tostring(r->L,-1):NULL); amalur_runtime_destroy(r); return NULL; }
    lua_settop(r->L,0); return r;
}
void amalur_runtime_destroy(amalur_runtime *r) { if(r){if(r->L)lua_close(r->L);free(r);} }
lua_State *amalur_runtime_state(amalur_runtime *r) { return r?r->L:NULL; }
size_t amalur_runtime_memory_used(const amalur_runtime *r) { return r?r->used:0; }
static int provider_call(lua_State *L) {
    amalur_runtime *r=(amalur_runtime*)lua_touserdata(L,lua_upvalueindex(1));
    install_provider(L,r,1); return 0;
}
int amalur_runtime_set_provider(amalur_runtime *r,int index,char *error,size_t cap) {
    int status; lua_State *L; uint64_t evaluation_budget;
    diagnostic(error,cap,"");
    if (!r) { diagnostic(error,cap,"Null runtime"); return LUA_ERRRUN; }
    L=r->L; index=absolute_index(L,index);
    if (lua_type(L,index)!=LUA_TTABLE) { diagnostic(error,cap,"Provider must be a table"); lua_pushliteral(L,"Provider must be a table"); return LUA_ERRRUN; }
    lua_pushlightuserdata(L,r); lua_pushcclosure(L,provider_call,1); lua_pushvalue(L,index);
    evaluation_budget=r->budget; r->budget=1000000; /* Provider installation is host setup, not script evaluation. */
    begin_budget(r); status=lua_pcall(L,1,0,0); lua_sethook(L,NULL,0,0); r->budget=evaluation_budget;
    if(status) diagnostic(error,cap,lua_type(L,-1)==LUA_TSTRING?lua_tostring(L,-1):NULL);
    return status;
}
static int finish_eval(amalur_runtime *r,int status,int *count,char *error,size_t cap) {
    lua_State *L=r->L;
    if (!status) { begin_budget(r); status=lua_pcall(L,0,LUA_MULTRET,0); }
    lua_sethook(L,NULL,0,0);
    if (status) { diagnostic(error,cap,lua_type(L,-1)==LUA_TSTRING?lua_tostring(L,-1):NULL); if(count)*count=0; }
    else { diagnostic(error,cap,""); if(count)*count=lua_gettop(L); }
    return status;
}
int amalur_runtime_eval_file(amalur_runtime *r,const char *path,int *count,char *error,size_t cap) {
    if(count)*count=0;
    if(!r || !path){diagnostic(error,cap,"Runtime and script path required");return LUA_ERRRUN;}
    lua_settop(r->L,0); return finish_eval(r,luaL_loadfile(r->L,path),count,error,cap);
}
int amalur_runtime_eval_source(amalur_runtime *r,const char *source,size_t length,const char *name,int *count,char *error,size_t cap) {
    if(count)*count=0;
    if(!r || !source){diagnostic(error,cap,"Runtime and source required");return LUA_ERRRUN;}
    lua_settop(r->L,0); return finish_eval(r,luaL_loadbuffer(r->L,source,length,name?name:"recovered-script"),count,error,cap);
}
