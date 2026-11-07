#include "scene_profile_v08.h"
#include "lauxlib.h"
#include <stdio.h>
#include <string.h>
static char controller_state_key;
static char content_state_key;
typedef struct profile_call {
    amalur_runtime *runtime;
    scene_controller_state_v08 controller;
    scene_content_state_v08 content;
    scene_platform_state_v08 platform;
    int fresh_profile;
    scene_quick_save_state_v08 quick_save;
    int no_language_packs;
    int max_anisotropy;
    char *error;
    size_t capacity;
} profile_call;
static int valid_content(const scene_content_state_v08 *state){
    return state&&(state->is_set==0||state->is_set==1);
}
static int valid_platform(const scene_platform_state_v08 *state){
    return state&&(state->is_set==0||state->is_set==1);
}
static int valid_quick_save(const scene_quick_save_state_v08 *state){
    return state&&(state->is_set==0||state->is_set==1)&&(state->supported==0||state->supported==1);
}
static int valid_state(const scene_controller_state_v08 *state){
    return state&&(state->is_set==0||state->is_set==1)&&
        (state->domain==SCENE_CONTROLLER_DOMAIN_NATIVE_KIND||
         state->domain==SCENE_CONTROLLER_DOMAIN_ANDROID_LOGICAL_STANDARD||
         state->domain==SCENE_CONTROLLER_DOMAIN_ANDROID_LOGICAL_REVERSED);
}
static int game_engine_version(lua_State *L){
    if(lua_gettop(L)!=0)return luaL_error(L,"Unmodeled GAME.get_game_engine_version argument domain");
    lua_pushinteger(L,1000);return 1;
}
/* Native00e43060 pushes exactly low0xfb/high0 and returns one value.
 * Construct once from the trusted fresh realm adapter during protected install;
 * capture the canonical token, never resolve mutable public constructors later.
 * This does not implement object existence, lookup, or handle validity queries. */
static int game_empty_object_handle(lua_State *L){
    if(lua_gettop(L)!=0)return luaL_error(L,"Unmodeled GAME.get_empty_object_handle argument domain");
    lua_pushvalue(L,lua_upvalueindex(1));return 1;
}
static int push_empty_object_handle(lua_State *L){
    lua_pushliteral(L,"__amalur_handles");lua_rawget(L,LUA_GLOBALSINDEX);
    if(lua_type(L,-1)!=LUA_TTABLE||lua_getmetatable(L,-1))return luaL_error(L,"Plain shared Amalur handle adapter required");
    lua_pushliteral(L,"from_words");lua_rawget(L,-2);
    if(!lua_isfunction(L,-1))return luaL_error(L,"Shared Amalur from_words required");
    lua_pushinteger(L,0xfb);lua_pushinteger(L,0);lua_call(L,2,1);
    if(lua_type(L,-1)!=LUA_TUSERDATA)return luaL_error(L,"Canonical empty object handle required");
    lua_remove(L,-2);return 1;
}
/* Native00c8ca50 reads a device's virtual+0x24 integer kind and returns1 iff
 * kind is0x0d or0x0f. No platform label or Android classification is inferred.
 * The original Lua callback00e44b10 passes this result to00aa1910.
 * Android domains are explicitly selected host menu policies. They ignore the
 * native integer; logical reverse alone requests a swap. */
static int input_button_swap(lua_State *L){
    scene_controller_state_v08 *state=(scene_controller_state_v08*)lua_touserdata(L,lua_upvalueindex(1));
    if(lua_gettop(L)!=0)return luaL_error(L,"Unmodeled INPUT.is_east_asian_controller_button_swap_required argument domain");
    if(!state||!state->is_set)return luaL_error(L,"Portable controller state is unset: explicit controller state required");
    if(state->domain==SCENE_CONTROLLER_DOMAIN_NATIVE_KIND)
        lua_pushboolean(L,state->native_device_kind==13||state->native_device_kind==15);
    else if(state->domain==SCENE_CONTROLLER_DOMAIN_ANDROID_LOGICAL_STANDARD)
        lua_pushboolean(L,0);
    else if(state->domain==SCENE_CONTROLLER_DOMAIN_ANDROID_LOGICAL_REVERSED)
        lua_pushboolean(L,1);
    else return luaL_error(L,"Unmodeled portable controller-state domain");
    return 1;
}
/* Native00e5f500 intersects registered-ID mask00a8cba0 with active-ID mask
 * 00a8cbe0 and tests bit(index&31). This port admits only integer indices0..31;
 * it does not guess coercions, package ownership, or out-of-range behavior. */
static int content_package_active(lua_State *L){
    scene_content_state_v08 *state=(scene_content_state_v08*)lua_touserdata(L,lua_upvalueindex(1));
    lua_Number index;uint32_t bit;
    if(lua_gettop(L)!=1||lua_type(L,1)!=LUA_TNUMBER)
        return luaL_error(L,"Unmodeled GAME.is_content_package_active argument domain: integer0..31 required");
    index=lua_tonumber(L,1);
    if(!(index>=0&&index<=31)||index!=(lua_Number)(uint32_t)index)
        return luaL_error(L,"Unmodeled GAME.is_content_package_active argument domain: integer0..31 required");
    if(!state||!state->is_set)return luaL_error(L,"Portable content state is unset: explicit mounted-package state required");
    bit=UINT32_C(1)<<(uint32_t)index;
    lua_pushboolean(L,(state->registered_mask&state->active_mask&bit)!=0);return 1;
}
/* Parent native trace: 00b513e0 obtains enum10 from0103a510, resolves "win32"
 * via0103a5f0, constructs/hash-populates through00af4d40/00af14b0, and passes
 * the stored hash through00aa1790 (numeric helper confirmation parent-owned).
 * Verified hash table gives SH("win32")585298 and SH("android")2096549.
 * Android is an explicit NEW host platform, absent from the native enum. */
static int window_platform(lua_State *L){
    scene_platform_state_v08 *state=(scene_platform_state_v08*)lua_touserdata(L,lua_upvalueindex(1));
    if(lua_gettop(L)!=0)return luaL_error(L,"Unmodeled WINDOW.get_platform argument domain");
    if(!state||!state->is_set)return luaL_error(L,"Portable platform state is unset: explicit platform name hash required");
    lua_pushinteger(L,state->name_hash);return 1;
}
/* Native00b60850 calls00c45250, which returns16, then uses signed integer
 * marshaling. This port instead advertises a copied explicit renderer cap.
 * Android preview selects1 because anisotropic filtering is not implemented;
 * that is a new host capability, not parity with the native Windows value. */
static int window_max_anisotrophy(lua_State *L){
    lua_Integer maximum=lua_tointeger(L,lua_upvalueindex(1));
    if(lua_gettop(L)!=0)return luaL_error(L,"Unmodeled WINDOW.get_max_anisotrophy argument domain");
    if(maximum==0)return luaL_error(L,"Portable renderer anisotropy capability is unset: explicit maximum required");
    lua_pushinteger(L,maximum);return 1;
}
/* Native00e28000 starts from00aa1e40's zero payload/type12. Missing hash in
 * 00f1ebf0 leaves that unchanged;00b50cf0 copies payload/type and00aadd20 type12
 * emits Lua tag0 (nil). The host dictionary starts empty and is Lua-owned;
 * getter/setter closures share it without native profile imports or disk I/O. */
static int preference_int32(lua_State *L,int index){
    lua_Number value;
    if(lua_type(L,index)!=LUA_TNUMBER)return 0;
    value=lua_tonumber(L,index);
    return value>=(lua_Number)INT32_MIN&&value<=(lua_Number)INT32_MAX&&value==(lua_Number)(int32_t)value;
}
static int fresh_profile_get_variable(lua_State *L){
    if(lua_gettop(L)!=1||!preference_int32(L,1))
        return luaL_error(L,"Unmodeled PROFILE.get_variable argument domain: signed-int32 hash required");
    if(!lua_toboolean(L,lua_upvalueindex(1)))
        return luaL_error(L,"Portable preference state is unset: explicit fresh-session configuration required");
    lua_pushvalue(L,1);lua_rawget(L,lua_upvalueindex(2));return 1;
}
/* Native00e299a0 marshals value,00e27f60's non-table path calls00f2c300:
 * replace matching hash via00aa1ac0, otherwise append via00f202f0. Only exact
 * signed-int32 NUMBER values are admitted here; other kinds remain unmodeled. */
static int fresh_profile_set_variable(lua_State *L){
    if(lua_gettop(L)!=2||!preference_int32(L,1)||!preference_int32(L,2))
        return luaL_error(L,"Unmodeled PROFILE.set_variable argument domain: signed-int32 hash and number required");
    if(!lua_toboolean(L,lua_upvalueindex(1)))
        return luaL_error(L,"Portable preference state is unset: explicit fresh-session configuration required");
    lua_pushvalue(L,1);lua_pushvalue(L,2);lua_rawset(L,lua_upvalueindex(2));return 0;
}
/* Original Windows00e2ab60 pushes1 into boolean constructor00aa1910, then
 * marshals via00aaeba0. That Windows capability is not evidence that this
 * Android host implements saves; the copied host capability is explicit. */
static int platform_supports_quick_save(lua_State *L){
    if(lua_gettop(L)!=0)return luaL_error(L,"Unmodeled SAVE_RESTORE.does_platform_support_quick_save argument domain");
    if(!lua_toboolean(L,lua_upvalueindex(1)))return luaL_error(L,"Portable quick-save state is unset: explicit host capability required");
    lua_pushboolean(L,lua_toboolean(L,lua_upvalueindex(2)));return 1;
}
/* Native00eb75c0/00eb76b0 always prepend signedint32 -1, then append only
 * available pack IDs0..48;00aaebe0 marshals one-based tables. With an explicit
 * empty mounted catalog, only -1 remains. Native name arrays use localized
 * "Automatic (resolved language)" text. This host has no localization packs:
 * "Automatic" is a NEW explicit display fallback, not native label parity. */
static int language_catalog(lua_State *L){
    const char *name=lua_tostring(L,lua_upvalueindex(3));
    if(lua_gettop(L)!=0)return luaL_error(L,"Unmodeled GAME.%s argument domain",name);
    if(!lua_toboolean(L,lua_upvalueindex(1)))
        return luaL_error(L,"Portable language catalog is unset: explicit no-language-packs state required");
    lua_createtable(L,1,0);
    if(lua_toboolean(L,lua_upvalueindex(2)))lua_pushliteral(L,"Automatic");else lua_pushinteger(L,-1);
    lua_rawseti(L,-2,1);return 1;
}
static void add_language_catalog(lua_State *L,const char *name,int no_language_packs,int names){
    lua_pushboolean(L,no_language_packs);lua_pushboolean(L,names);lua_pushstring(L,name);
    lua_pushcclosure(L,language_catalog,3);lua_setfield(L,-2,name);
}
static int install(lua_State *L){
    profile_call *call=(profile_call*)lua_touserdata(L,1);scene_controller_state_v08 *state;
    scene_content_state_v08 *content;scene_platform_state_v08 *platform;
    int state_index,content_index,platform_index,preferences_index,empty_handle_index,status;
    lua_pushlightuserdata(L,&controller_state_key);lua_rawget(L,LUA_REGISTRYINDEX);
    if(!lua_isnil(L,-1))return luaL_error(L,"Scene v08 controller profile is already installed");lua_pop(L,1);
    push_empty_object_handle(L);empty_handle_index=lua_gettop(L);
    state=(scene_controller_state_v08*)lua_newuserdata(L,sizeof(*state));*state=call->controller;
    if(!state->is_set)state->native_device_kind=0;state_index=lua_gettop(L);
    content=(scene_content_state_v08*)lua_newuserdata(L,sizeof(*content));*content=call->content;
    if(!content->is_set)content->registered_mask=content->active_mask=0;content_index=lua_gettop(L);
    platform=(scene_platform_state_v08*)lua_newuserdata(L,sizeof(*platform));*platform=call->platform;
    if(!platform->is_set)platform->name_hash=0;platform_index=lua_gettop(L);
    lua_newtable(L);preferences_index=lua_gettop(L);
    lua_newtable(L);
    lua_newtable(L);lua_pushcfunction(L,game_engine_version);lua_setfield(L,-2,"get_game_engine_version");
    lua_pushvalue(L,empty_handle_index);lua_pushcclosure(L,game_empty_object_handle,1);lua_setfield(L,-2,"get_empty_object_handle");
    lua_pushvalue(L,content_index);lua_pushcclosure(L,content_package_active,1);lua_setfield(L,-2,"is_content_package_active");
    add_language_catalog(L,"get_available_ost_languages",call->no_language_packs,0);
    add_language_catalog(L,"get_available_audio_languages",call->no_language_packs,0);
    add_language_catalog(L,"get_available_ost_language_names",call->no_language_packs,1);
    add_language_catalog(L,"get_available_audio_language_names",call->no_language_packs,1);lua_setfield(L,-2,"GAME");
    lua_newtable(L);lua_pushvalue(L,state_index);lua_pushcclosure(L,input_button_swap,1);lua_setfield(L,-2,"is_east_asian_controller_button_swap_required");lua_setfield(L,-2,"INPUT");
    lua_newtable(L);lua_pushvalue(L,platform_index);lua_pushcclosure(L,window_platform,1);lua_setfield(L,-2,"get_platform");
    lua_pushinteger(L,call->max_anisotropy);lua_pushcclosure(L,window_max_anisotrophy,1);lua_setfield(L,-2,"get_max_anisotrophy");lua_setfield(L,-2,"WINDOW");
    lua_newtable(L);
    lua_pushboolean(L,call->fresh_profile);lua_pushvalue(L,preferences_index);lua_pushcclosure(L,fresh_profile_get_variable,2);lua_setfield(L,-2,"get_variable");
    lua_pushboolean(L,call->fresh_profile);lua_pushvalue(L,preferences_index);lua_pushcclosure(L,fresh_profile_set_variable,2);lua_setfield(L,-2,"set_variable");lua_setfield(L,-2,"PROFILE");
    lua_newtable(L);lua_pushboolean(L,call->quick_save.is_set);lua_pushboolean(L,call->quick_save.supported);lua_pushcclosure(L,platform_supports_quick_save,2);lua_setfield(L,-2,"does_platform_support_quick_save");lua_setfield(L,-2,"SAVE_RESTORE");
    status=amalur_runtime_set_provider(call->runtime,-1,call->error,call->capacity);if(status)return lua_error(L);
    lua_pushlightuserdata(L,&controller_state_key);lua_pushvalue(L,state_index);lua_rawset(L,LUA_REGISTRYINDEX);
    lua_pushlightuserdata(L,&content_state_key);lua_pushvalue(L,content_index);lua_rawset(L,LUA_REGISTRYINDEX);
    return 0;
}
static int set_controller(lua_State *L){
    profile_call *call=(profile_call*)lua_touserdata(L,1);scene_controller_state_v08 *state;
    lua_pushlightuserdata(L,&controller_state_key);lua_rawget(L,LUA_REGISTRYINDEX);
    if(lua_type(L,-1)!=LUA_TUSERDATA||lua_objlen(L,-1)!=sizeof(*state))return luaL_error(L,"Scene v08 controller profile is not installed");
    state=(scene_controller_state_v08*)lua_touserdata(L,-1);*state=call->controller;
    if(!state->is_set)state->native_device_kind=0;return 0;
}
static int set_content(lua_State *L){
    profile_call *call=(profile_call*)lua_touserdata(L,1);scene_content_state_v08 *state;
    lua_pushlightuserdata(L,&content_state_key);lua_rawget(L,LUA_REGISTRYINDEX);
    if(lua_type(L,-1)!=LUA_TUSERDATA||lua_objlen(L,-1)!=sizeof(*state))return luaL_error(L,"Scene v08 content profile is not installed");
    state=(scene_content_state_v08*)lua_touserdata(L,-1);*state=call->content;
    if(!state->is_set)state->registered_mask=state->active_mask=0;return 0;
}
static int protected_call(profile_call *call,lua_CFunction function){
    lua_State *L=amalur_runtime_state(call->runtime);int status=lua_cpcall(L,function,call);
    if(status&&call->error&&call->capacity)snprintf(call->error,call->capacity,"%s",lua_type(L,-1)==LUA_TSTRING?lua_tostring(L,-1):"Non-string v08 profile error");
    return status;
}
int scene_profile_v08_install(amalur_runtime *runtime,const scene_profile_v08_options *options,char *error,size_t capacity){
    profile_call call={0};
    if(error&&capacity)*error=0;
    if(!runtime||!options||!options->target_sha256||strcmp(options->target_sha256,AMALUR_SCENE_PROFILE_V08_SHA256)||!valid_state(&options->controller)||!valid_content(&options->content)||!valid_platform(&options->platform)||(options->fresh_profile!=0&&options->fresh_profile!=1)||!valid_quick_save(&options->quick_save)||(options->no_language_packs!=0&&options->no_language_packs!=1)||options->max_anisotropy<0||options->max_anisotropy>16){
        if(error&&capacity)snprintf(error,capacity,"Explicit supported native SHA256 and valid controller/content/platform/fresh-profile/quick-save/no-language-packs/max-anisotropy state required");return LUA_ERRRUN;
    }
    call.runtime=runtime;call.controller=options->controller;call.content=options->content;call.platform=options->platform;call.fresh_profile=options->fresh_profile;call.quick_save=options->quick_save;call.no_language_packs=options->no_language_packs;call.max_anisotropy=options->max_anisotropy;call.error=error;call.capacity=capacity;
    return protected_call(&call,install);
}
int scene_profile_v08_set_controller(amalur_runtime *runtime,const scene_controller_state_v08 *state,char *error,size_t capacity){
    profile_call call={0};
    if(error&&capacity)*error=0;
    if(!runtime||!valid_state(state)){
        if(error&&capacity)snprintf(error,capacity,"Runtime and controller state with is_set0or1 and a supported domain required");return LUA_ERRRUN;
    }
    call.runtime=runtime;call.controller=*state;call.error=error;call.capacity=capacity;
    return protected_call(&call,set_controller);
}
int scene_profile_v08_set_content(amalur_runtime *runtime,const scene_content_state_v08 *state,char *error,size_t capacity){
    profile_call call={0};
    if(error&&capacity)*error=0;
    if(!runtime||!valid_content(state)){
        if(error&&capacity)snprintf(error,capacity,"Runtime and content state with is_set0or1 required");return LUA_ERRRUN;
    }
    call.runtime=runtime;call.content=*state;call.error=error;call.capacity=capacity;
    return protected_call(&call,set_content);
}
