#include "scene_asset_macros_v08.h"
#include "scene_asset_keys.h"
#include "lauxlib.h"
#include <stdio.h>
#include <string.h>
typedef struct macro_request {const char *name;uint32_t category;const unsigned char *bytes;size_t length;} macro_request;
static uint32_t u32le(const unsigned char *p){return (uint32_t)p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24);}
static int valid_name(const char *name){
    const unsigned char *p=(const unsigned char*)name;
    if(!p||!*p||strlen(name)>127||!((*p>='A'&&*p<='Z')||*p=='_'))return 0;
    for(;*p;p++)if(!((*p>='A'&&*p<='Z')||(*p>='0'&&*p<='9')||*p=='_'))return 0;
    return 1;
}
static int macro_lookup(lua_State *L){
    const char *text;size_t length;uint32_t hash,id;
    if(lua_gettop(L)!=1||lua_type(L,1)!=LUA_TSTRING){lua_pushnil(L);return 1;}
    text=lua_tolstring(L,1,&length);if(!length||!*text){lua_pushnil(L);return 1;}
    if(scene_asset_ascii_hash(text,length,&hash))return luaL_error(L,"Unmodeled Amalur ASCII asset macro name domain");
    if(hash==0x233e41u)id=0;
    else{lua_pushnumber(L,(lua_Number)hash);lua_rawget(L,lua_upvalueindex(1));if(lua_isnil(L,-1))return 1;id=(uint32_t)lua_tonumber(L,-1);lua_pop(L,1);}
    lua_pushvalue(L,lua_upvalueindex(2));lua_pushvalue(L,lua_upvalueindex(3));lua_pushnumber(L,(lua_Number)id);lua_call(L,2,1);return 1;
}
static int install(lua_State *L){
    macro_request *request=(macro_request*)lua_touserdata(L,1);const unsigned char *bytes=request->bytes;
    uint32_t count,i,id,hash;int constructor,ids,map;
    if(!valid_name(request->name)||request->category<1||request->category>255)return luaL_error(L,"Explicit uppercase macro name and category1..255 required");
    if(!bytes||request->length<8||u32le(bytes)!=1)return luaL_error(L,"Asset macro snapshot requires version1 header");
    count=u32le(bytes+4);if(!count||count>65536u||request->length!=8u+(size_t)count*8u)return luaL_error(L,"Invalid asset macro snapshot shape/count");
    if(lua_getmetatable(L,LUA_GLOBALSINDEX))return luaL_error(L,"Asset macro installer requires plain realm globals");
    lua_pushstring(L,request->name);lua_rawget(L,LUA_GLOBALSINDEX);if(!lua_isnil(L,-1))return luaL_error(L,"Asset macro global already exists: %s",request->name);lua_pop(L,1);
    lua_getglobal(L,"__amalur_handles");if(lua_type(L,-1)!=LUA_TTABLE||lua_getmetatable(L,-1))return luaL_error(L,"Plain shared Amalur handle adapter required");
    lua_pushliteral(L,"from_words");lua_rawget(L,-2);if(!lua_isfunction(L,-1))return luaL_error(L,"Shared Amalur from_words required");constructor=lua_gettop(L);
    lua_createtable(L,0,(int)count);ids=lua_gettop(L);lua_createtable(L,0,(int)count);map=lua_gettop(L);
    for(i=0;i<count;i++){
        id=u32le(bytes+8+(size_t)i*4);hash=u32le(bytes+8+(size_t)count*4+(size_t)i*4);
        if(!id)return luaL_error(L,"Zero asset ID unsupported in selected snapshot profile");
        lua_pushnumber(L,(lua_Number)id);lua_rawget(L,ids);if(!lua_isnil(L,-1))return luaL_error(L,"Duplicate asset macro ID");lua_pop(L,1);
        lua_pushnumber(L,(lua_Number)id);lua_pushboolean(L,1);lua_rawset(L,ids);
        lua_pushnumber(L,(lua_Number)hash);lua_rawget(L,map);if(!lua_isnil(L,-1))return luaL_error(L,"Duplicate asset macro hash");lua_pop(L,1);
        lua_pushnumber(L,(lua_Number)hash);lua_pushnumber(L,(lua_Number)id);lua_rawset(L,map);
    }
    lua_pushstring(L,request->name);lua_pushvalue(L,map);lua_pushvalue(L,constructor);lua_pushinteger(L,(request->category<<4)|0xbu);
    lua_pushcclosure(L,macro_lookup,3);lua_rawset(L,LUA_GLOBALSINDEX);return 0;
}
int scene_asset_macro_v08_install(amalur_runtime *runtime,const char *name,uint32_t category,const void *snapshot,size_t length,char *error,size_t capacity){
    macro_request request={name,category,(const unsigned char*)snapshot,length};lua_State *L;int status;
    if(error&&capacity)*error=0;
    if(!runtime){if(error&&capacity)snprintf(error,capacity,"Runtime required");return LUA_ERRRUN;}
    L=amalur_runtime_state(runtime);status=lua_cpcall(L,install,&request);
    if(status&&error&&capacity)snprintf(error,capacity,"%s",lua_type(L,-1)==LUA_TSTRING?lua_tostring(L,-1):"Non-string asset macro installer error");
    return status;
}
