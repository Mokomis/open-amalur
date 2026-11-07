#include "amalur_runtime.h"
#include "lauxlib.h"
#include "lualib.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

struct amalur_runtime {
    lua_State *L;
    const char *runtime_dir; /* Used only during protected initialization. */
    const amalur_runtime_source *runtime_sources;
    size_t runtime_source_count;
    size_t used, limit;
    uint64_t budget, remaining;
    int hook_step, budget_exhausted;
    int carrier_ref, registry_ref, bridge_ref;
    int preload_ref, module_marks_ref;
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
/* Static native contract: SL callback00aaf2d0 -> table reader00aa70e0 ->
 * LuaParameter kind0x10 constructor00aa18b0 -> pusher00aadd20. Raw native
 * strings01730a1c="SL1",01730a18="SL2". This table form normalizes an ID;
 * it does not perform localization. String lookup remains unsupported. */
static int native_sl_identifier(lua_State *L) {
    lua_Number high,low;
    if(lua_gettop(L)!=1){lua_pushnil(L);return 1;}
    if(lua_type(L,1)==LUA_TSTRING)
        return luaL_error(L,"Amalur SL string form requires an unimplemented localization service");
    if(lua_type(L,1)!=LUA_TTABLE){lua_pushnil(L);return 1;}
    if(lua_getmetatable(L,1))return luaL_error(L,"Unmodeled Amalur SL table metatable");
    lua_pushliteral(L,"SL1");lua_rawget(L,1);
    if(lua_type(L,-1)!=LUA_TNUMBER){lua_pushnil(L);return 1;}
    lua_pushliteral(L,"SL2");lua_rawget(L,1);
    if(lua_type(L,-1)!=LUA_TNUMBER){lua_pushnil(L);return 1;}
    high=lua_tonumber(L,-2);low=lua_tonumber(L,-1);
    if(high!=high||high<(-2147483647.0-1.0)||high>2147483647.0||
       low!=low||low<(-2147483647.0-1.0)||low>2147483647.0)
        return luaL_error(L,"Unmodeled Amalur SL signed-int32 numeric domain");
    if(high!=(lua_Number)(int32_t)high||low!=(lua_Number)(int32_t)low)
        return luaL_error(L,"Unmodeled Amalur SL signed-int32 numeric domain");
    if(high==0&&low==0){lua_pushnil(L);return 1;}
    lua_createtable(L,0,2);lua_pushinteger(L,(int32_t)high);lua_setfield(L,-2,"SL1");
    lua_pushinteger(L,(int32_t)low);lua_setfield(L,-2,"SL2");return 1;
}
static void load_module(lua_State *L, amalur_runtime *r, const char *name) {
    const char *directory=r->runtime_dir;
    size_t a,b,i; int status;
    if (r->runtime_sources) {
        const amalur_runtime_source *match=NULL;
        for (i=0;i<r->runtime_source_count;i++) {
            const amalur_runtime_source *source=&r->runtime_sources[i];
            if (!source->name || !source->data) luaL_error(L,"Invalid runtime source entry");
            if (!strcmp(source->name,name)) {
                if (match) luaL_error(L,"Duplicate runtime source: %s",name);
                match=source;
            }
        }
        if (!match) luaL_error(L,"Missing runtime source: %s",name);
        status=luaL_loadbuffer(L,match->data,match->length,name);
    } else {
    a=strlen(directory); b=strlen(name);
    if (a>4096 || b>256) luaL_error(L,"Runtime module path too long");
    /* Keep the filename in Lua-owned storage so an allocation error anywhere
     * inside luaL_loadfile cannot skip a host-side free. */
    lua_pushfstring(L,"%s/%s",directory,name);
    status=luaL_loadfile(L,lua_tostring(L,-1));lua_remove(L,-2);
    }
    if (status) lua_error(L);
    lua_call(L,0,1);
    if (!lua_istable(L,-1)) luaL_error(L,"Runtime module %s must return a table",name);
}
static int absolute_index(lua_State *L, int index) {
    return index>0 || index<=LUA_REGISTRYINDEX ? index : lua_gettop(L)+index+1;
}
/* Only a stock seeall metatable belonging to an explicitly registered module
 * is admitted. This check never changes the public getmetatable behavior. */
static int module_table_allowed(lua_State *L) {
    amalur_runtime *r=owner(L); int allowed=0, mt;
    if (lua_getmetatable(L,LUA_GLOBALSINDEX)) {lua_pushboolean(L,0);return 1;}
    if (lua_type(L,1)!=LUA_TTABLE || !lua_getmetatable(L,1)) {
        lua_pushboolean(L,0); return 1;
    }
    mt=lua_gettop(L);
    lua_rawgeti(L,LUA_REGISTRYINDEX,r->module_marks_ref);
    lua_pushvalue(L,1); lua_rawget(L,-2);
    if (!lua_rawequal(L,-1,mt)) {lua_pushboolean(L,0);return 1;}
    lua_pop(L,2); lua_pushnil(L);
    while (lua_next(L,mt)) {
        if (lua_type(L,-2)!=LUA_TSTRING || strcmp(lua_tostring(L,-2),"__index") ||
            !lua_rawequal(L,-1,LUA_GLOBALSINDEX)) {
            lua_pushboolean(L,0); return 1;
        }
        allowed=1; lua_pop(L,1);
    }
    lua_pushboolean(L,allowed); return 1;
}
/* One table-valued __index READ fallback only. Inspect actual metatables via
 * C API: public getmetatable may return a forged table-valued __metatable
 * marker hiding an executable __index function. No script callback is called.
 * The target must be plain or an exact host-approved stock seeall table.
 * Protected/root-metatable-metadata and all other chains fail closed. */
static int read_table_allowed(lua_State *L) {
    int mt, target, allowed;
    if (lua_gettop(L)!=1 || lua_type(L,1)!=LUA_TTABLE || !lua_getmetatable(L,1)) {
        lua_pushboolean(L,0); return 1;
    }
    mt=lua_gettop(L);
    if (lua_getmetatable(L,mt)) {lua_pushboolean(L,0);return 1;}
    lua_pushliteral(L,"__metatable");lua_rawget(L,mt);
    if (!lua_isnil(L,-1)) {lua_pushboolean(L,0);return 1;}lua_pop(L,1);
    lua_pushliteral(L,"__index");lua_rawget(L,mt);target=lua_gettop(L);
    if (lua_type(L,target)!=LUA_TTABLE || lua_rawequal(L,1,target)) {lua_pushboolean(L,0);return 1;}
    if (!lua_getmetatable(L,target)) {lua_pushboolean(L,1);return 1;}
    lua_pop(L,1);
    /* Calling this exact private C predicate invokes no arbitrary Lua code. */
    lua_pushcfunction(L,module_table_allowed);lua_pushvalue(L,target);lua_call(L,1,1);
    allowed=lua_type(L,-1)==LUA_TBOOLEAN && lua_toboolean(L,-1);
    lua_pop(L,1);lua_pushboolean(L,allowed);return 1;
}
static int tracked_seeall(lua_State *L) {
    amalur_runtime *r=owner(L); int mt; const char *name;
    luaL_checktype(L,1,LUA_TTABLE);
    lua_getfield(L,1,"_NAME");
    if (lua_type(L,-1)!=LUA_TSTRING) return luaL_error(L,"Module requires an explicit source registration");
    name=lua_tostring(L,-1);
    lua_rawgeti(L,LUA_REGISTRYINDEX,r->preload_ref); lua_getfield(L,-1,name);
    if (lua_type(L,-1)!=LUA_TFUNCTION) return luaL_error(L,"Module requires an explicit source registration");
    lua_getfield(L,LUA_REGISTRYINDEX,"_LOADED"); lua_getfield(L,-1,name);
    if (!lua_rawequal(L,-1,1)) return luaL_error(L,"Module identity does not match loaded registry");
    lua_getfield(L,1,"_M");
    if (!lua_rawequal(L,-1,1)) return luaL_error(L,"Module self identity does not match");
    lua_settop(L,1); lua_pushvalue(L,lua_upvalueindex(1)); lua_pushvalue(L,1); lua_call(L,1,0);
    if (!lua_getmetatable(L,1)) return luaL_error(L,"seeall did not create a metatable");
    mt=lua_gettop(L); lua_rawgeti(L,LUA_REGISTRYINDEX,r->module_marks_ref);
    lua_pushvalue(L,1); lua_pushvalue(L,mt); lua_rawset(L,-3);
    return 0;
}
static void initialize_module_loading(lua_State *L, amalur_runtime *r) {
    int package, public_package;
    lua_getglobal(L,"package"); package=lua_gettop(L);
    /* Keep the original Lua5.1 preload searcher and require function, but no
     * filename or dynamic-library searchers. Its private C environment stays
     * separate from the small public package interface. */
    lua_getfield(L,package,"loaders"); lua_rawgeti(L,-1,1); lua_remove(L,-2);
    lua_newtable(L); lua_pushvalue(L,-2); lua_rawseti(L,-2,1);
    lua_setfield(L,package,"loaders"); lua_pop(L,1);
    lua_newtable(L); lua_pushvalue(L,-1); r->preload_ref=luaL_ref(L,LUA_REGISTRYINDEX);
    lua_setfield(L,package,"preload");
    lua_pushliteral(L,""); lua_setfield(L,package,"path");
    lua_pushliteral(L,""); lua_setfield(L,package,"cpath");
    lua_pushnil(L); lua_setfield(L,package,"loadlib");
    /* Start loaded modules empty. Removing public io/os/debug alone would leave
     * those standard libraries accessible through require's old loaded table. */
    lua_newtable(L); lua_pushvalue(L,-1); lua_setfield(L,LUA_REGISTRYINDEX,"_LOADED");
    lua_setfield(L,package,"loaded");
    lua_newtable(L); lua_newtable(L); lua_pushliteral(L,"k"); lua_setfield(L,-2,"__mode");
    lua_setmetatable(L,-2); r->module_marks_ref=luaL_ref(L,LUA_REGISTRYINDEX);
    lua_newtable(L); public_package=lua_gettop(L);
    lua_getfield(L,package,"loaded"); lua_setfield(L,public_package,"loaded");
    lua_getfield(L,package,"seeall"); lua_pushcclosure(L,tracked_seeall,1);
    lua_setfield(L,public_package,"seeall");
    lua_setglobal(L,"package"); lua_pop(L,1);
    lua_pushcfunction(L,module_table_allowed); lua_setglobal(L,"__amalur_module_table_allowed");
    lua_pushcfunction(L,read_table_allowed);lua_setglobal(L,"__amalur_read_table_allowed");
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
/* Capture the original realm carrier predicate before any recovered modules run.
 * Its private metadata table recognizes only strongly interned type11 tokens;
 * public carrier method/metatable changes cannot broaden membership. */
static int type11_table_key_allowed(lua_State *L) {
    int allowed;
    if (lua_gettop(L)!=1 || lua_type(L,1)!=LUA_TUSERDATA) {
        lua_pushboolean(L,0); return 1;
    }
    lua_pushvalue(L,lua_upvalueindex(1)); lua_pushvalue(L,1); lua_call(L,1,1);
    allowed=lua_type(L,-1)==LUA_TBOOLEAN && lua_toboolean(L,-1);
    lua_pop(L,1); lua_pushboolean(L,allowed); return 1;
}
static int initialize(lua_State *L) {
    amalur_runtime *r=(amalur_runtime*)lua_touserdata(L,1);
    const char *remove_names[]={"io","os","debug","coroutine",
        "dofile","loadfile","load","loadstring",NULL};
    const char **name;
    lua_pushlightuserdata(L,&runtime_key); lua_pushlightuserdata(L,r); lua_rawset(L,LUA_REGISTRYINDEX);
    luaL_openlibs(L);
    lua_pushcfunction(L,bounded_pcall); lua_setglobal(L,"pcall");
    lua_pushcfunction(L,bounded_xpcall); lua_setglobal(L,"xpcall");
    begin_budget(r);
    load_module(L,r,"amalur_uint64.lua");
    lua_pushvalue(L,-1); lua_setglobal(L,"__amalur_uint64"); r->carrier_ref=luaL_ref(L,LUA_REGISTRYINDEX);
    lua_rawgeti(L,LUA_REGISTRYINDEX,r->carrier_ref); lua_getfield(L,-1,"is"); lua_remove(L,-2);
    if (!lua_isfunction(L,-1)) return luaL_error(L,"Original realm carrier membership predicate is missing");
    lua_pushcclosure(L,type11_table_key_allowed,1); lua_setglobal(L,"__amalur_type11_key_allowed");
    load_module(L,r,"amalur_engine_handles.lua"); lua_getfield(L,-1,"new");
    lua_rawgeti(L,LUA_REGISTRYINDEX,r->carrier_ref); lua_call(L,1,1); lua_setglobal(L,"__amalur_handles"); lua_pop(L,1);
    load_module(L,r,"engine_binding_registry.lua"); r->registry_ref=luaL_ref(L,LUA_REGISTRYINDEX);
    load_module(L,r,"amalur_engine_bindings.lua"); r->bridge_ref=luaL_ref(L,LUA_REGISTRYINDEX);
    load_module(L,r,"amalur_native_math.lua"); lua_setglobal(L,"math");
    lua_pushcfunction(L,native_sl_identifier);lua_setglobal(L,"SL");
    lua_newtable(L); install_provider(L,r,-1); lua_pop(L,1);
    initialize_module_loading(L,r);
    for (name=remove_names;*name;name++) { lua_pushnil(L); lua_setglobal(L,*name); }
    lua_settop(L,0); return 0;
}
amalur_runtime *amalur_runtime_create(const amalur_runtime_config *config, char *error, size_t cap) {
    amalur_runtime *r; int status; uint64_t evaluation_budget;
    diagnostic(error,cap,"");
    if (!config || (!config->runtime_sources && (!config->runtime_dir || !*config->runtime_dir))) {
        diagnostic(error,cap,"An explicit runtime directory is required"); return NULL;
    }
    if ((config->runtime_sources && config->runtime_source_count!=5) ||
        (!config->runtime_sources && config->runtime_source_count)) {
        diagnostic(error,cap,"In-memory runtime requires exactly five explicit sources"); return NULL;
    }
    r=(amalur_runtime*)calloc(1,sizeof(*r));
    if (!r) { diagnostic(error,cap,"Host allocation failed"); return NULL; }
    r->runtime_dir=config->runtime_dir;
    r->runtime_sources=config->runtime_sources; r->runtime_source_count=config->runtime_source_count;
    r->budget=config->instruction_budget?config->instruction_budget:1000000;
    r->limit=config->memory_limit_bytes?config->memory_limit_bytes:64u*1024u*1024u;
    r->L=lua_newstate(limited_alloc,r);
    if (!r->L) { diagnostic(error,cap,"Lua state allocation failed"); free(r); return NULL; }
    evaluation_budget=r->budget; r->budget=1000000; /* Separate bounded bootstrap budget. */
    status=lua_cpcall(r->L,initialize,r); lua_sethook(r->L,NULL,0,0); r->runtime_dir=NULL;
    r->runtime_sources=NULL; r->runtime_source_count=0;
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
typedef struct module_registration {
    amalur_runtime *runtime;
    const char *name, *path, *source;
    size_t length;
    int lazy;
} module_registration;
static int lazy_module_loader(lua_State *L) {
    int status,nargs=lua_gettop(L); size_t length;
    const char *name=lua_tostring(L,lua_upvalueindex(1));
    const char *data=lua_tolstring(L,lua_upvalueindex(2),&length);
    status=lua_toboolean(L,lua_upvalueindex(3))?luaL_loadfile(L,data):luaL_loadbuffer(L,data,length,name);
    if (status) return lua_error(L);
    lua_insert(L,1); lua_call(L,nargs,LUA_MULTRET); return lua_gettop(L);
}
static int register_module(lua_State *L) {
    module_registration *registration=(module_registration*)lua_touserdata(L,1);
    amalur_runtime *r=registration->runtime; int status;
    const unsigned char *p=(const unsigned char*)registration->name;
    if (!p || !*p || strlen((const char*)p)>255) return luaL_error(L,"Invalid module name");
    for (;*p;p++) if (*p<32 || *p=='/' || *p=='\\' || *p==':') return luaL_error(L,"Invalid module name");
    lua_rawgeti(L,LUA_REGISTRYINDEX,r->preload_ref); lua_getfield(L,-1,registration->name);
    if (!lua_isnil(L,-1)) return luaL_error(L,"Duplicate module source registration: %s",registration->name);
    lua_pop(L,1);
    lua_getfield(L,LUA_REGISTRYINDEX,"_LOADED"); lua_getfield(L,-1,registration->name);
    if (!lua_isnil(L,-1)) return luaL_error(L,"Module was already loaded: %s",registration->name);
    lua_pop(L,2);
    if (registration->lazy) {
        lua_pushstring(L,registration->name);
        if (registration->path) lua_pushstring(L,registration->path);
        else lua_pushlstring(L,registration->source,registration->length);
        lua_pushboolean(L,registration->path!=NULL); lua_pushcclosure(L,lazy_module_loader,3);
    } else {
        status=registration->path?luaL_loadfile(L,registration->path):
               luaL_loadbuffer(L,registration->source,registration->length,registration->name);
        if (status) return lua_error(L);
    }
    lua_setfield(L,-2,registration->name); return 0;
}
static int registration_call(module_registration *registration,char *error,size_t cap) {
    amalur_runtime *r=registration->runtime; int status;
    diagnostic(error,cap,"");
    if (!r) { diagnostic(error,cap,"Runtime required"); return LUA_ERRRUN; }
    status=lua_cpcall(r->L,register_module,registration);
    if(status) diagnostic(error,cap,lua_type(r->L,-1)==LUA_TSTRING?lua_tostring(r->L,-1):NULL);
    return status;
}
int amalur_runtime_register_module_file(amalur_runtime *r,const char *name,const char *path,char *error,size_t cap) {
    module_registration registration={r,name,path,NULL,0,0};
    if (!path) { diagnostic(error,cap,"Explicit module file required"); return LUA_ERRRUN; }
    return registration_call(&registration,error,cap);
}
int amalur_runtime_register_module_source(amalur_runtime *r,const char *name,const char *source,size_t length,char *error,size_t cap) {
    module_registration registration={r,name,NULL,source,length,0};
    if (!source) { diagnostic(error,cap,"Explicit module source required"); return LUA_ERRRUN; }
    return registration_call(&registration,error,cap);
}
int amalur_runtime_register_module_file_lazy(amalur_runtime *r,const char *name,const char *path,char *error,size_t cap) {
    module_registration registration={r,name,path,NULL,0,1};
    if (!path) { diagnostic(error,cap,"Explicit module file required"); return LUA_ERRRUN; }
    return registration_call(&registration,error,cap);
}
int amalur_runtime_register_module_source_lazy(amalur_runtime *r,const char *name,const char *source,size_t length,char *error,size_t cap) {
    module_registration registration={r,name,NULL,source,length,1};
    if (!source) { diagnostic(error,cap,"Explicit module source required"); return LUA_ERRRUN; }
    return registration_call(&registration,error,cap);
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
