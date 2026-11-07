#include "scene_asset_keys.h"
#include "lauxlib.h"
#include <stdint.h>
#include <string.h>
#include <stdio.h>

static const uint32_t weights[50]={
 0x7f,0x32b,0x63d,0x853,0xabd,0x1297,0x1597,0x1741,0x1fb5,0x2543,
 0x2821,0x2a01,0x2b97,0x300d,0x33a1,0x377f,0x3c35,0x4511,0x48e5,0x4a45,
 0x5261,0x5623,0x6217,0x64c9,0x6b41,0x6d99,0x738d,0x7859,0x7f63,0x86a5,
 0x8ce3,0x9287,0x9743,0x9c9d,0xa3ff,0xa939,0xb01b,0xb947,0xc203,0xc64f,
 0xd0cd,0xd8ad,0xdf69,0xe7e9,0xf223,0xfe2f,0x11ecd,0x13019,0x148ff,0x15bb1
};
int scene_asset_ascii_hash(const char *bytes,size_t length,uint32_t *hash){
    size_t i;uint32_t value=0;
    if(!bytes||!hash||length>2147483647u)return 1;
    for(i=0;i<length&&bytes[i];i++){
        uint32_t c=(unsigned char)bytes[i];if(c>127)return 1;
        if(c>='A'&&c<='Z')c+='a'-'A';
        value+=weights[i%50]*c+weights[c%50]*(uint32_t)(i+1);
    }
    *hash=value;return 0;
}
static uint32_t u32le(const unsigned char *p){return (uint32_t)p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24);}
static int lua_hash(lua_State *L,uint32_t *hash){
    const char *text;size_t length;
    if(lua_gettop(L)!=1||lua_type(L,1)!=LUA_TSTRING){lua_pushnil(L);return 0;}
    text=lua_tolstring(L,1,&length);
    if(scene_asset_ascii_hash(text,length,hash))luaL_error(L,"Unmodeled Amalur ASCII string hash domain");
    return 1;
}
static int string_hash(lua_State *L){
    uint32_t hash;lua_Number signed_value;
    if(!lua_hash(L,&hash))return 1;
    signed_value=hash<=2147483647u?(lua_Number)hash:(lua_Number)hash-4294967296.0;
    lua_pushnumber(L,signed_value);return 1;
}
static int input_action_key(lua_State *L){
    uint32_t hash,id;
    if(!lua_hash(L,&hash))return 1;
    /* Native00aa7bd0 rejects empty C strings before consulting the manager. */
    if(!*lua_tostring(L,1)){lua_pushnil(L);return 1;}
    if(hash==0x233e41u)id=0;
    else{
        lua_pushnumber(L,(lua_Number)hash);lua_rawget(L,lua_upvalueindex(1));
        if(lua_isnil(L,-1))return 1;
        id=(uint32_t)lua_tonumber(L,-1);lua_pop(L,1);
    }
    lua_pushvalue(L,lua_upvalueindex(2));lua_pushinteger(L,0x19b);lua_pushnumber(L,(lua_Number)id);lua_call(L,2,1);return 1;
}
typedef struct installation {const unsigned char *bytes;size_t length;} installation;
static int install(lua_State *L){
    installation *request=(installation*)lua_touserdata(L,1);
    const unsigned char *bytes=request->bytes;uint32_t count,i,id,hash;int ids,map,constructor,key_function,hash_function;
    if(!bytes||request->length<8||u32le(bytes)!=1)return luaL_error(L,"Input action snapshot requires version1 header");
    count=u32le(bytes+4);
    if(!count||count>65536u||request->length!=8u+(size_t)count*8u)return luaL_error(L,"Invalid input action snapshot shape/count");
    lua_getglobal(L,"INPUT_ACTION_KEY");if(!lua_isnil(L,-1))return luaL_error(L,"INPUT_ACTION_KEY already installed");lua_pop(L,1);
    lua_getglobal(L,"SH");if(!lua_isnil(L,-1))return luaL_error(L,"SH already installed");lua_pop(L,1);
    if(lua_getmetatable(L,LUA_GLOBALSINDEX))return luaL_error(L,"Asset installer requires plain realm globals");
    lua_getglobal(L,"__amalur_handles");if(!lua_istable(L,-1))return luaL_error(L,"Shared Amalur handle adapter required");
    lua_getfield(L,-1,"from_words");if(!lua_isfunction(L,-1))return luaL_error(L,"Shared Amalur from_words required");
    constructor=lua_gettop(L);
    lua_createtable(L,0,(int)count);ids=lua_gettop(L);lua_createtable(L,0,(int)count);map=lua_gettop(L);
    for(i=0;i<count;i++){
        id=u32le(bytes+8+(size_t)i*4);hash=u32le(bytes+8+(size_t)count*4+(size_t)i*4);
        if(id==0)return luaL_error(L,"Zero input action ID is unsupported in the selected snapshot profile");
        lua_pushnumber(L,(lua_Number)id);lua_rawget(L,ids);if(!lua_isnil(L,-1))return luaL_error(L,"Duplicate input action ID");lua_pop(L,1);
        lua_pushnumber(L,(lua_Number)id);lua_pushboolean(L,1);lua_rawset(L,ids);
        lua_pushnumber(L,(lua_Number)hash);lua_rawget(L,map);if(!lua_isnil(L,-1))return luaL_error(L,"Duplicate input action hash");lua_pop(L,1);
        lua_pushnumber(L,(lua_Number)hash);lua_pushnumber(L,(lua_Number)id);lua_rawset(L,map);
    }
    lua_pushvalue(L,map);lua_pushvalue(L,constructor);lua_pushcclosure(L,input_action_key,2);key_function=lua_gettop(L);
    lua_pushcfunction(L,string_hash);hash_function=lua_gettop(L);
    /* Validation and closure construction finish before publishing. A Lua OOM
     * during publication can still leave one global installed: caller must
     * discard the realm after any installer failure (bootstrap does so). */
    lua_pushliteral(L,"INPUT_ACTION_KEY");lua_pushvalue(L,key_function);lua_rawset(L,LUA_GLOBALSINDEX);
    lua_pushliteral(L,"SH");lua_pushvalue(L,hash_function);lua_rawset(L,LUA_GLOBALSINDEX);
    return 0;
}
int scene_asset_keys_install(amalur_runtime *runtime,const void *bytes,size_t length,char *error,size_t cap){
    installation request={(const unsigned char*)bytes,length};lua_State *L;int status;
    if(error&&cap)*error=0;
    if(!runtime){if(error&&cap)snprintf(error,cap,"Runtime required");return LUA_ERRRUN;}
    L=amalur_runtime_state(runtime);status=lua_cpcall(L,install,&request);
    if(status&&error&&cap)snprintf(error,cap,"%s",lua_type(L,-1)==LUA_TSTRING?lua_tostring(L,-1):"Non-string asset installer error");
    return status;
}
