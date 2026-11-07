#include "scene_enums_v08.h"
#include "scene_asset_keys.h"
#include "lauxlib.h"
#include <stdio.h>
#include <string.h>
typedef struct enum_request {const unsigned char *bytes;size_t length;} enum_request;
static uint32_t read32(const unsigned char *p){return (uint32_t)p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24);}
static int enum_lookup(lua_State *L){
    const char *group_text,*member_text;size_t group_length,member_length;uint32_t group,member;
    if(lua_gettop(L)!=2||lua_type(L,1)!=LUA_TSTRING||lua_type(L,2)!=LUA_TSTRING){lua_pushnil(L);return 1;}
    group_text=lua_tolstring(L,1,&group_length);member_text=lua_tolstring(L,2,&member_length);
    if(scene_asset_ascii_hash(group_text,group_length,&group)||scene_asset_ascii_hash(member_text,member_length,&member))
        return luaL_error(L,"Unmodeled Amalur ASCII enum name domain");
    lua_pushnumber(L,(lua_Number)group);lua_rawget(L,lua_upvalueindex(1));
    if(lua_isnil(L,-1))return 1;
    lua_pushnumber(L,(lua_Number)member);lua_rawget(L,-2);return 1;
}
static int install(lua_State *L){
    enum_request *request=(enum_request*)lua_touserdata(L,1);const unsigned char *bytes=request->bytes;
    uint32_t count,i,group,member,bits;int groups,members;lua_Number value;
    if(!bytes||request->length<12||memcmp(bytes,"AENU",4)||read32(bytes+4)!=1)
        return luaL_error(L,"Enum snapshot requires AENU version1 header");
    count=read32(bytes+8);
    if(count>SCENE_ENUMS_V08_MAX_ENTRIES||request->length!=12u+(size_t)count*12u)
        return luaL_error(L,"Invalid enum snapshot shape/count");
    if(lua_getmetatable(L,LUA_GLOBALSINDEX))return luaL_error(L,"Enum installer requires plain realm globals");
    lua_pushliteral(L,"STE");lua_rawget(L,LUA_GLOBALSINDEX);
    if(!lua_isnil(L,-1))return luaL_error(L,"Enum global STE already exists");lua_pop(L,1);
    lua_createtable(L,0,(int)count);groups=lua_gettop(L);
    for(i=0;i<count;i++){
        const unsigned char *record=bytes+12+(size_t)i*12;
        group=read32(record);member=read32(record+4);bits=read32(record+8);
        lua_pushnumber(L,(lua_Number)group);lua_rawget(L,groups);
        if(lua_isnil(L,-1)){
            lua_pop(L,1);lua_newtable(L);
            lua_pushnumber(L,(lua_Number)group);lua_pushvalue(L,-2);lua_rawset(L,groups);
        }
        members=lua_gettop(L);
        lua_pushnumber(L,(lua_Number)member);lua_rawget(L,members);
        if(!lua_isnil(L,-1))return luaL_error(L,"Duplicate enum group/member hash pair");lua_pop(L,1);
        value=bits<=2147483647u?(lua_Number)bits:(lua_Number)bits-4294967296.0;
        lua_pushnumber(L,(lua_Number)member);lua_pushnumber(L,value);lua_rawset(L,members);lua_pop(L,1);
    }
    lua_pushliteral(L,"STE");lua_pushvalue(L,groups);lua_pushcclosure(L,enum_lookup,1);lua_rawset(L,LUA_GLOBALSINDEX);return 0;
}
int scene_enums_v08_install(amalur_runtime *runtime,const void *snapshot,size_t length,char *error,size_t capacity){
    enum_request request={(const unsigned char*)snapshot,length};lua_State *L;int status;
    if(error&&capacity)*error=0;
    if(!runtime){if(error&&capacity)snprintf(error,capacity,"Runtime required");return LUA_ERRRUN;}
    L=amalur_runtime_state(runtime);status=lua_cpcall(L,install,&request);
    if(status&&error&&capacity)snprintf(error,capacity,"%s",lua_type(L,-1)==LUA_TSTRING?lua_tostring(L,-1):"Non-string enum installer error");
    return status;
}
