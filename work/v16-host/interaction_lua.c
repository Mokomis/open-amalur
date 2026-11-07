#include "interaction_lua.h"
#include "lauxlib.h"
#include <stdio.h>
#include <string.h>
#define OA_OBJECT_META "OpemAmalur.SceneObject.v1"
typedef struct object_ref {oa_interaction *owner;oa_handle handle;} object_ref;
static const oa_object *checked(lua_State *L,int index,oa_interaction *owner){object_ref *r=(object_ref*)luaL_checkudata(L,index,OA_OBJECT_META);const oa_object *o;if(r->owner!=owner)return (luaL_error(L,"Scene object belongs to another engine"),(const oa_object*)NULL);o=oa_object_resolve(&owner->registry,r->handle);if(!o)luaL_error(L,"Scene object handle has expired");return o;}
static void push_object(lua_State *L,oa_interaction *s,oa_handle h){object_ref *r=(object_ref*)lua_newuserdata(L,sizeof(*r));r->owner=s;r->handle=h;luaL_getmetatable(L,OA_OBJECT_META);lua_setmetatable(L,-2);}
static int object_id(lua_State *L){object_ref *r=(object_ref*)luaL_checkudata(L,1,OA_OBJECT_META);const oa_object *o=checked(L,1,r->owner);lua_pushnumber(L,o->source_id);return 1;}
static int open_alchemy(lua_State *L){oa_interaction *s=(oa_interaction*)lua_touserdata(L,lua_upvalueindex(1));if(!s->ready||!oa_object_resolve(&s->registry,s->selected)||s->selected.slot!=s->workbench.slot||s->selected.generation!=s->workbench.generation)return luaL_error(L,"Alchemy requires an active Workbench interaction");s->window_open=1;s->page=0;s->tab=0;snprintf(s->status,sizeof(s->status),s->inventory.count?"YOUR ANDROID INVENTORY":"YOUR ANDROID INVENTORY IS EMPTY");return 0;}
static int dispatch(lua_State *L){oa_interaction *s=(oa_interaction*)lua_touserdata(L,lua_upvalueindex(1));checked(L,1,s);checked(L,2,s);lua_getglobal(L,"Workbench");lua_getfield(L,-1,"on_interact");if(!lua_isfunction(L,-1))return luaL_error(L,"Recovered Workbench callback absent");lua_pushvalue(L,1);lua_pushvalue(L,2);lua_call(L,2,0);return 0;}
static int install(lua_State *L){oa_interaction *s=(oa_interaction*)lua_touserdata(L,1);
 if(luaL_newmetatable(L,OA_OBJECT_META)){lua_newtable(L);lua_pushcfunction(L,object_id);lua_setfield(L,-2,"source_id");lua_setfield(L,-2,"__index");lua_pushliteral(L,"engine-owned scene object");lua_setfield(L,-2,"__metatable");}lua_pop(L,1);
 /* A real authored alchemy window service at the recovered interface. The
  * native UI graph is deliberately not represented by successful no-op calls. */
 lua_newtable(L);lua_pushlightuserdata(L,s);lua_pushcclosure(L,open_alchemy,1);lua_setfield(L,-2,"open_alchemy_win");lua_pushvalue(L,-1);lua_setglobal(L,"alchemy_win");
 lua_getglobal(L,"package");lua_getfield(L,-1,"loaded");lua_pushvalue(L,-3);lua_setfield(L,-2,"alchemy_win");lua_pop(L,3);
 lua_pushlightuserdata(L,s);lua_pushcclosure(L,dispatch,1);lua_setglobal(L,"__opem_workbench_dispatch");
 push_object(L,s,s->workbench);lua_setglobal(L,"__opem_workbench_object");push_object(L,s,s->player);lua_setglobal(L,"__opem_player_object");return 0;
}
int oa_lua_install(amalur_runtime *r,oa_interaction *s,const char *source,size_t length,char *error,size_t cap){lua_State *L;int count,status;const char *require="return require('Workbench')";
 if(!r||!s||!source)return 1;L=amalur_runtime_state(r);lua_pushcfunction(L,install);lua_pushlightuserdata(L,s);status=lua_pcall(L,1,0,0);if(status){snprintf(error,cap,"%s",lua_tostring(L,-1));lua_settop(L,0);return 1;}
 if(amalur_runtime_register_module_source(r,"Workbench",source,length,error,cap))return 1;
 if(amalur_runtime_eval_source(r,require,strlen(require),"Workbench-module",&count,error,cap))return 1;s->ready=1;lua_settop(L,0);return 0;
}
int oa_lua_interact(amalur_runtime *r,oa_interaction *s,char *error,size_t cap){int count,old;const char *code="__opem_workbench_dispatch(__opem_workbench_object,__opem_player_object)";
 if(!r||!s||!s->ready||!oa_object_resolve(&s->registry,s->selected)){snprintf(error,cap,"Workbench unavailable");return 1;}old=s->window_open;
 if(amalur_runtime_eval_source(r,code,strlen(code),"scene-Workbench-on_interact",&count,error,cap)){s->window_open=old;return 1;}return 0;
}
