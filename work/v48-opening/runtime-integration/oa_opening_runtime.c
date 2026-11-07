#include "oa_opening_runtime.h"
#include "amalur_runtime.h"
#include "lauxlib.h"
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <math.h>
#include <limits.h>
#include "opening_sha256.h"
typedef struct opening_asset_spec {const char *path,*name;size_t size;unsigned kind;unsigned char sha[32];} opening_asset_spec;
#include "opening_assets.h"
typedef struct loaded_asset {char *bytes;} loaded_asset;
enum operation {OP_INIT,OP_FLAG,OP_EXIT,OP_ACQUIRE,OP_EQUIP,OP_ADVANCE,OP_SNAPSHOT,OP_RESTORE};
struct oa_opening_runtime {
 amalur_runtime *lua;
 oa_opening_host host;
 char player[128];
 loaded_asset assets[OPENING_ASSET_COUNT];
 size_t memory_limit;uint64_t budget,calls,rejections,rebuilds;
 int busy,poisoned,has_last,flag;
 enum operation op;
 unsigned loading;
 int32_t item,arg3;
 uint32_t delta;
 const char *volume,*object;
 oa_opening_snapshot last,read_snapshot,input;
 oa_opening_effect effects[OA_OPENING_MAX_EFFECTS];size_t effect_count;
};
static const char *wos_fields[]={"started_movement_tutorial","is_in_start_room","left_starting_room","gave_player_movement_command","gave_player_look_command","gave_player_loot_command","gave_player_equip_command","movement_on_cooldown","look_on_cooldown","loot_on_cooldown","equip_on_cooldown","player_has_moved","player_has_looked_up","player_has_looted","player_has_equipped","did_shake","shake_once"};
static const char *sword_fields[]={"acquired_once","equipped_once","looked_at_target","attacked_once"};
#define MAX_EXACT_TIME UINT64_C(9007194959773695)
static int fail(char *e,size_t n,const char *s){if(e&&n)snprintf(e,n,"%s",s?s:"opening runtime failure");return 1;}
static int ai(lua_State *L,int i){return i>0||i<=LUA_REGISTRYINDEX?i:lua_gettop(L)+i+1;}
static void rawfield(lua_State *L,int i,const char *k){i=ai(L,i);lua_pushstring(L,k);lua_rawget(L,i);}
static void plain(lua_State *L,int i){if(lua_type(L,i)!=LUA_TTABLE)luaL_error(L,"opening plain table required");if(lua_getmetatable(L,i)){lua_pop(L,1);luaL_error(L,"opening metatable rejected");}}
static double num(lua_State *L,int i,double lo,double hi){double v;if(lua_type(L,i)!=LUA_TNUMBER)luaL_error(L,"opening numeric value required");v=lua_tonumber(L,i);if(!isfinite(v)||v<lo||v>hi||floor(v)!=v)luaL_error(L,"opening integer outside typed domain");return v;}
static uint64_t ufield(lua_State *L,int i,const char *k,uint64_t max){uint64_t n;rawfield(L,i,k);n=(uint64_t)num(L,-1,0,(double)max);lua_pop(L,1);return n;}
static int32_t ifield(lua_State *L,int i,const char *k){int32_t n;rawfield(L,i,k);n=(int32_t)num(L,-1,INT32_MIN,INT32_MAX);lua_pop(L,1);return n;}
static uint32_t flags(lua_State *L,int i,const char **names,unsigned n){uint32_t f=0;unsigned j;plain(L,i);for(j=0;j<n;j++){rawfield(L,i,names[j]);if(lua_type(L,-1)!=LUA_TBOOLEAN)luaL_error(L,"opening source boolean required");if(lua_toboolean(L,-1))f|=1u<<j;lua_pop(L,1);}return f;}
static int valid_snapshot(const oa_opening_snapshot *s){
 unsigned i,j;if(!s||s->version!=1||s->wos_flags>=1u<<17||s->sword_flags>=16||s->cinematic_flags>1||s->clock_ms>MAX_EXACT_TIME||s->serial>MAX_EXACT_TIME||s->timer_count>OA_OPENING_MAX_TIMERS)return 0;
 for(i=0;i<s->timer_count;i++){const oa_opening_timer *t=s->timers+i;if((t->hash!=151774118u&&t->hash!=165407883u)||t->due_ms>MAX_EXACT_TIME||!t->serial||t->serial>s->serial||t->argc!=(t->hash==151774118u?1u:0u)||(t->argc&&t->item_index<0))return 0;for(j=0;j<i;j++)if(s->timers[j].serial==t->serial)return 0;}return 1;
}
static void read_snapshot(lua_State *L,int at,oa_opening_snapshot *s){
 int m,t;unsigned i;const char *profile;at=ai(L,at);plain(L,at);memset(s,0,sizeof(*s));rawfield(L,at,"profile");profile=lua_tostring(L,-1);if(lua_type(L,-1)!=LUA_TSTRING||!profile||strcmp(profile,"opening-first-room-original-lua-v1"))luaL_error(L,"opening profile mismatch");lua_pop(L,1);s->version=1;
 s->clock_ms=ufield(L,at,"clock_ms",MAX_EXACT_TIME);s->serial=ufield(L,at,"serial",MAX_EXACT_TIME);
 rawfield(L,at,"modules");m=lua_gettop(L);plain(L,m);
 rawfield(L,m,"WoS_Start_Room");s->wos_flags=flags(L,-1,wos_fields,17);lua_pop(L,1);
 rawfield(L,m,"Sword_WoS_InitialWeapon");s->sword_flags=flags(L,-1,sword_fields,4);lua_pop(L,1);
 rawfield(L,m,"cinematic_post_char_gen_2");{const char *n[]={"cinematic_finished"};s->cinematic_flags=flags(L,-1,n,1);}lua_pop(L,1);
 rawfield(L,m,"MQ01");plain(L,-1);s->sword_get=ifield(L,-1,"sword_get");lua_pop(L,2);
 rawfield(L,at,"timers");t=lua_gettop(L);plain(L,t);if(lua_objlen(L,t)>OA_OPENING_MAX_TIMERS)luaL_error(L,"opening timer count outside cap");s->timer_count=(uint32_t)lua_objlen(L,t);
 for(i=0;i<s->timer_count;i++){oa_opening_timer *x=s->timers+i;int r;lua_rawgeti(L,t,(int)i+1);r=lua_gettop(L);plain(L,r);x->hash=(uint32_t)ufield(L,r,"hash",UINT32_MAX);x->due_ms=ufield(L,r,"due_ms",MAX_EXACT_TIME);x->serial=ufield(L,r,"serial",MAX_EXACT_TIME);rawfield(L,r,"args");plain(L,-1);x->argc=(uint32_t)ufield(L,-1,"n",1);if(x->argc){lua_rawgeti(L,-1,1);x->item_index=(int32_t)num(L,-1,0,INT32_MAX);lua_pop(L,1);}lua_pop(L,2);}
 lua_pop(L,1);if(!valid_snapshot(s))luaL_error(L,"opening typed snapshot invalid");
}
static void fieldnum(lua_State *L,const char *k,double n){lua_pushnumber(L,n);lua_setfield(L,-2,k);}
static void pushflags(lua_State *L,const char **names,unsigned n,uint32_t f){unsigned i;lua_newtable(L);for(i=0;i<n;i++){lua_pushboolean(L,(f>>i)&1u);lua_setfield(L,-2,names[i]);}}
static void push_snapshot(lua_State *L,const oa_opening_snapshot *s){
 unsigned i;lua_newtable(L);lua_pushliteral(L,"opening-first-room-original-lua-v1");lua_setfield(L,-2,"profile");fieldnum(L,"clock_ms",(double)s->clock_ms);fieldnum(L,"serial",(double)s->serial);
 lua_newtable(L);pushflags(L,wos_fields,17,s->wos_flags);lua_setfield(L,-2,"WoS_Start_Room");pushflags(L,sword_fields,4,s->sword_flags);lua_setfield(L,-2,"Sword_WoS_InitialWeapon");{const char *n[]={"cinematic_finished"};pushflags(L,n,1,s->cinematic_flags);}lua_setfield(L,-2,"cinematic_post_char_gen_2");lua_newtable(L);fieldnum(L,"sword_get",s->sword_get);lua_setfield(L,-2,"MQ01");lua_setfield(L,-2,"modules");
 lua_newtable(L);for(i=0;i<s->timer_count;i++){const oa_opening_timer *t=s->timers+i;lua_newtable(L);fieldnum(L,"hash",t->hash);fieldnum(L,"due_ms",(double)t->due_ms);fieldnum(L,"serial",(double)t->serial);lua_newtable(L);fieldnum(L,"n",t->argc);if(t->argc){lua_pushinteger(L,t->item_index);lua_rawseti(L,-2,1);}lua_setfield(L,-2,"args");lua_rawseti(L,-2,(int)i+1);}lua_setfield(L,-2,"timers");
}
static oa_opening_runtime *owner(lua_State *L){return (oa_opening_runtime*)lua_touserdata(L,lua_upvalueindex(1));}
static int c_player(lua_State *L){lua_pushstring(L,owner(L)->player);return 1;}
static int c_gor(lua_State *L){if(strcmp(luaL_checkstring(L,1),"MQ01_Start_Door_01"))return luaL_error(L,"unresolved source opening GOR");lua_pushinteger(L,1790948);return 1;}
static int c_quest(lua_State *L){if(strcmp(luaL_checkstring(L,1),"MQ01"))return luaL_error(L,"unresolved source opening quest");lua_pushinteger(L,613083);return 1;}
static int c_bool(lua_State *L){oa_opening_runtime *o=owner(L);enum oa_opening_query kind=(enum oa_opening_query)lua_tointeger(L,lua_upvalueindex(2));char e[256]="";int v=-1;int32_t arg=lua_gettop(L)?(int32_t)num(L,1,0,INT32_MAX):0;if(o->host.query_bool(o->host.context,kind,arg,&v,e,sizeof(e)))return luaL_error(L,"%s",e[0]?e:"opening query unavailable");if(v!=0&&v!=1)return luaL_error(L,"opening query did not return a known boolean");lua_pushboolean(L,v);return 1;}
static int c_stage(lua_State *L){oa_opening_runtime *o=owner(L);char e[256]="";int32_t stage=INT32_MIN;if(num(L,1,0,INT32_MAX)!=613083)return luaL_error(L,"unsupported source quest");if(o->host.quest_stage(o->host.context,613083,&stage,e,sizeof(e)))return luaL_error(L,"%s",e[0]?e:"opening quest stage unknown");if(stage==INT32_MIN)return luaL_error(L,"opening quest stage unknown or not supplied");lua_pushinteger(L,stage);return 1;}
static int c_warn(lua_State *L){owner(L)->host.warning(owner(L)->host.context,luaL_checkstring(L,1));return 0;}
static const char *callback_name(const char *s){unsigned i;for(i=0;i<OPENING_ASSET_COUNT;i++)if(asset_specs[i].kind==3&&!strcmp(s,asset_specs[i].name))return asset_specs[i].name;return NULL;}
static int c_prepare(lua_State *L){
 oa_opening_runtime *o=owner(L);size_t count,i;const char *cb=callback_name(luaL_checkstring(L,3));oa_opening_snapshot candidate;if(!cb)return luaL_error(L,"unrecognized original source callback");plain(L,1);count=lua_objlen(L,1);if(count>OA_OPENING_MAX_EFFECTS-o->effect_count)return luaL_error(L,"opening effect batch exceeds cap");read_snapshot(L,2,&candidate);
 for(i=0;i<count;i++){int r,a;const char *name;unsigned n;oa_opening_effect effect;memset(&effect,0,sizeof(effect));effect.source_callback=cb;lua_rawgeti(L,1,(int)i+1);r=lua_gettop(L);plain(L,r);rawfield(L,r,"name");if(lua_type(L,-1)!=LUA_TSTRING)return luaL_error(L,"effect name required");name=lua_tostring(L,-1);
 if(!strcmp(name,"ACTOR.open_gateway")){effect.kind=OA_OPENING_OPEN_GATEWAY;n=1;}
 else if(!strcmp(name,"QUEST.set_stage")){effect.kind=OA_OPENING_SET_STAGE;n=2;}
 else if(!strcmp(name,"tutorial_win.kill_tutorial")){effect.kind=OA_OPENING_KILL_TUTORIAL;n=1;}
 else if(!strcmp(name,"tutorial_win.launch_modal_tutorial")){effect.kind=OA_OPENING_MODAL_TUTORIAL;n=1;}
 else if(!strcmp(name,"tutorial_win.disable_secondary_weapon")){effect.kind=OA_OPENING_SECONDARY_DISABLED;n=1;}
 else if(!strcmp(name,"loot_popup.enable_compare")){effect.kind=OA_OPENING_COMPARE_ENABLED;n=0;}
 else if(!strcmp(name,"interfaceLibrary.autosave_request")){effect.kind=OA_OPENING_AUTOSAVE_REQUEST;n=1;}
 else return luaL_error(L,"unimplemented opening effect: %s",name);
 lua_pop(L,1);rawfield(L,r,"args");a=lua_gettop(L);plain(L,a);if(ufield(L,a,"n",2)!=n)return luaL_error(L,"opening effect arity mismatch");effect.argc=n;
 {unsigned j;for(j=0;j<n;j++){lua_rawgeti(L,a,(int)j+1);if(effect.kind==OA_OPENING_SECONDARY_DISABLED){if(lua_type(L,-1)!=LUA_TBOOLEAN||!lua_toboolean(L,-1))return luaL_error(L,"invalid source secondary lock");effect.args[j]=1;}else effect.args[j]=(int32_t)num(L,-1,INT32_MIN,INT32_MAX);lua_pop(L,1);}}
 if((effect.kind==OA_OPENING_OPEN_GATEWAY&&effect.args[0]!=1790948)||(effect.kind==OA_OPENING_SET_STAGE&&(effect.args[0]!=613083||effect.args[1]!=25))||(effect.kind==OA_OPENING_MODAL_TUTORIAL&&effect.args[0]!=49968583)||(effect.kind==OA_OPENING_AUTOSAVE_REQUEST&&effect.args[0]!=0)||(effect.kind==OA_OPENING_KILL_TUTORIAL&&effect.args[0]!=17524338&&effect.args[0]!=26339831&&effect.args[0]!=40879367))return luaL_error(L,"unsupported source opening effect argument");
 o->effects[o->effect_count++]=effect;lua_pop(L,2);
 }
 /* PREPARE only. No game/UI/save effect is applied here. The outer C API
  * commits once, after budgeted Lua execution and typed post-snapshot succeed. */
 lua_pushboolean(L,1);return 1;
}
static void closure(lua_State *L,oa_opening_runtime *o,const char *n,lua_CFunction f){lua_pushlightuserdata(L,o);lua_pushcclosure(L,f,1);lua_setfield(L,-2,n);}
static void boolclosure(lua_State *L,oa_opening_runtime *o,const char *n,enum oa_opening_query k){lua_pushlightuserdata(L,o);lua_pushinteger(L,k);lua_pushcclosure(L,c_bool,2);lua_setfield(L,-2,n);}
static int c_load(lua_State *L){oa_opening_runtime *o=owner(L);const opening_asset_spec *s=asset_specs+o->loading;if(luaL_loadbuffer(L,o->assets[o->loading].bytes,s->size,s->path))return lua_error(L);lua_call(L,0,1);if(s->kind==3){if(!lua_isfunction(L,-1))return luaL_error(L,"original callback chunk did not return function");lua_getglobal(L,"__oa_functions");lua_pushvalue(L,-2);lua_setfield(L,-2,s->name);lua_pop(L,2);}else{if(!lua_istable(L,-1))return luaL_error(L,"opening module chunk did not return table");lua_setglobal(L,s->name);}lua_pushboolean(L,1);return 1;}
static void method(lua_State *L,const char *name){lua_getglobal(L,"__oa_bridge");lua_getfield(L,-1,name);lua_remove(L,-2);if(!lua_isfunction(L,-1))luaL_error(L,"opening method absent");}
static int c_call(lua_State *L){
 oa_opening_runtime *o=owner(L);lua_settop(L,0);
 switch(o->op){
 case OP_INIT:lua_getglobal(L,"__oa_bridge_impl");lua_getfield(L,-1,"new");lua_remove(L,-2);lua_getglobal(L,"__oa_functions");lua_getglobal(L,"__oa_host");lua_newtable(L);lua_getglobal(L,"__oa_accessors");lua_setfield(L,-2,"accessors");lua_call(L,3,1);lua_setglobal(L,"__oa_bridge");lua_pushboolean(L,1);return 1;
 case OP_FLAG:method(L,"set_cinematic_finished");lua_pushboolean(L,o->flag);lua_call(L,1,LUA_MULTRET);break;
 case OP_EXIT:method(L,"volume_exit");lua_pushstring(L,o->volume);lua_pushstring(L,o->object);lua_call(L,2,LUA_MULTRET);break;
 case OP_ACQUIRE:method(L,"sword_acquired");lua_pushinteger(L,o->item);lua_pushstring(L,o->object);lua_pushinteger(L,o->arg3);lua_call(L,3,LUA_MULTRET);break;
 case OP_EQUIP:method(L,"sword_equipped");lua_pushinteger(L,o->item);lua_call(L,1,LUA_MULTRET);break;
 case OP_ADVANCE:method(L,"advance");lua_pushnumber(L,o->delta);lua_call(L,1,LUA_MULTRET);break;
 case OP_SNAPSHOT:method(L,"snapshot");lua_call(L,0,1);read_snapshot(L,-1,&o->read_snapshot);lua_settop(L,0);lua_pushboolean(L,1);break;
 case OP_RESTORE:method(L,"restore");push_snapshot(L,&o->input);lua_call(L,1,LUA_MULTRET);break;
 default:return luaL_error(L,"opening operation invalid");
 }return lua_gettop(L);
}
static int install(lua_State *L){oa_opening_runtime *o=(oa_opening_runtime*)lua_touserdata(L,1);lua_newtable(L);lua_setglobal(L,"__oa_functions");lua_newtable(L);
 closure(L,o,"player_identity",c_player);closure(L,o,"resolve_gor",c_gor);closure(L,o,"resolve_quest",c_quest);closure(L,o,"get_quest_stage",c_stage);closure(L,o,"apply_effects",c_prepare);closure(L,o,"warn",c_warn);
 boolclosure(L,o,"is_equipped",OA_OPENING_IS_EQUIPPED);boolclosure(L,o,"is_gateway_open",OA_OPENING_GATEWAY_OPEN);boolclosure(L,o,"tutorials_enabled",OA_OPENING_TUTORIALS_ENABLED);boolclosure(L,o,"has_tutorial_fired",OA_OPENING_TUTORIAL_FIRED);boolclosure(L,o,"is_tutorial_active",OA_OPENING_TUTORIAL_ACTIVE);lua_setglobal(L,"__oa_host");
 lua_pushlightuserdata(L,o);lua_pushcclosure(L,c_load,1);lua_setglobal(L,"__oa_load");lua_pushlightuserdata(L,o);lua_pushcclosure(L,c_call,1);lua_setglobal(L,"__oa_call");return 0;
}
static int eval(oa_opening_runtime *o,const char *code,char *e,size_t n){
 int count=0;lua_State *L=amalur_runtime_state(o->lua);if(amalur_runtime_eval_source(o->lua,code,strlen(code),"opening-C-dispatch",&count,e,n))return 1;
 if(count<1||lua_type(L,1)!=LUA_TBOOLEAN||!lua_toboolean(L,1)){const char *why=count>=2&&lua_type(L,2)==LUA_TSTRING?lua_tostring(L,2):"opening callback rejected";return fail(e,n,why);}return 0;
}
static int build(oa_opening_runtime *o,const oa_opening_snapshot *restore,char *e,size_t n){
 amalur_runtime_config c;amalur_runtime_source core[5];unsigned i,k=0;lua_State *L;if(o->lua){amalur_runtime_destroy(o->lua);o->lua=NULL;}memset(&c,0,sizeof(c));memset(core,0,sizeof(core));
 for(i=0;i<OPENING_ASSET_COUNT;i++)if(asset_specs[i].kind==0){if(k>=5)return fail(e,n,"core inventory invalid");core[k].name=asset_specs[i].name;core[k].data=o->assets[i].bytes;core[k].length=asset_specs[i].size;k++;}
 if(k!=5)return fail(e,n,"five production Lua core sources required");c.runtime_sources=core;c.runtime_source_count=5;c.memory_limit_bytes=o->memory_limit;c.instruction_budget=o->budget;
 o->lua=amalur_runtime_create(&c,e,n);if(!o->lua)return 1;L=amalur_runtime_state(o->lua);
 if(lua_cpcall(L,install,o)){fail(e,n,lua_type(L,-1)==LUA_TSTRING?lua_tostring(L,-1):"opening C install failed");return 1;}
 for(i=0;i<OPENING_ASSET_COUNT;i++)if(asset_specs[i].kind>=1&&asset_specs[i].kind<=3){o->loading=i;if(eval(o,"return __oa_load()",e,n))return 1;}
 o->op=OP_INIT;if(eval(o,"return __oa_call()",e,n))return 1;
 if(restore){o->input=*restore;o->op=OP_RESTORE;if(eval(o,"return __oa_call()",e,n))return 1;}
 o->op=OP_SNAPSHOT;if(eval(o,"return __oa_call()",e,n))return 1;o->last=o->read_snapshot;o->has_last=1;o->poisoned=0;return 0;
}
static int event(oa_opening_runtime *o,enum operation op,char *e,size_t n){
 oa_opening_snapshot before;char saved[512],rebuild_error[256]="";int bad;if(!o||!o->lua||o->poisoned)return fail(e,n,"opening runtime unavailable");if(o->busy)return fail(e,n,"opening runtime reentry rejected");o->busy=1;o->calls++;before=o->last;o->effect_count=0;o->op=op;
 bad=eval(o,"return __oa_call()",e,n);if(!bad){o->op=OP_SNAPSHOT;bad=eval(o,"return __oa_call()",e,n);}
 if(!bad&&o->effect_count){bad=o->host.apply_effects(o->host.context,o->effects,o->effect_count,&o->read_snapshot,e,n)!=0;if(bad&&e&&n&&!e[0])fail(e,n,"host did not acknowledge opening effect batch");}
 if(bad){snprintf(saved,sizeof(saved),"%s",e&&n&&e[0]?e:"opening operation failed");o->rejections++;o->rebuilds++;o->effect_count=0;if(build(o,&before,rebuild_error,sizeof(rebuild_error))){o->poisoned=1;if(o->lua){amalur_runtime_destroy(o->lua);o->lua=NULL;}if(e&&n)snprintf(e,n,"%s; recovery failed: %s",saved,rebuild_error);}else fail(e,n,saved);o->busy=0;return 1;}
 o->last=o->read_snapshot;o->effect_count=0;o->busy=0;return 0;
}
oa_opening_runtime *oa_opening_runtime_create_from_assets(const oa_opening_assets *a,const oa_opening_host *h,const oa_opening_runtime_config *c,char *e,size_t n){
 oa_opening_runtime *o;unsigned i;size_t total=0;if(e&&n)e[0]=0;if(!a||!a->size||!a->read||!h||!h->player_identity||!h->query_bool||!h->quest_stage||!h->apply_effects||!h->warning)return (fail(e,n,"explicit opening assets/host services required"),(oa_opening_runtime*)NULL);
 if(!h->player_identity[0]||strlen(h->player_identity)>=128)return (fail(e,n,"invalid player scene/slot/generation string"),(oa_opening_runtime*)NULL);
 o=(oa_opening_runtime*)calloc(1,sizeof(*o));if(!o)return (fail(e,n,"opening C allocation failed"),(oa_opening_runtime*)NULL);o->host=*h;snprintf(o->player,sizeof(o->player),"%s",h->player_identity);o->memory_limit=c&&c->lua_memory_bytes?c->lua_memory_bytes:64u*1024u*1024u;o->budget=c&&c->instruction_budget?c->instruction_budget:200000u;
 for(i=0;i<OPENING_ASSET_COUNT;i++){size_t size=0;unsigned char digest[32];const opening_asset_spec *s=asset_specs+i;if(a->size(a->context,s->path,&size,e,n)||size!=s->size||size>2u*1024u*1024u||total>2u*1024u*1024u-size){fail(e,n,"opening asset length/read contract failed");goto bad;}total+=size;o->assets[i].bytes=(char*)malloc(size?size:1);if(!o->assets[i].bytes){fail(e,n,"opening source allocation failed");goto bad;}if(a->read(a->context,s->path,o->assets[i].bytes,size,e,n))goto bad;sha256(o->assets[i].bytes,size,digest);if(memcmp(digest,s->sha,32)){if(e&&n)snprintf(e,n,"opening SHA256 mismatch: %s",s->path);goto bad;}}
 if(build(o,NULL,e,n))goto bad;return o;
bad:oa_opening_runtime_close(o);return NULL;
}
void oa_opening_runtime_close(oa_opening_runtime *o){unsigned i;if(!o)return;if(o->lua)amalur_runtime_destroy(o->lua);for(i=0;i<OPENING_ASSET_COUNT;i++)free(o->assets[i].bytes);free(o);}
static int start(oa_opening_runtime *o,char *e,size_t n){if(e&&n)e[0]=0;if(!o||o->busy||o->poisoned)return fail(e,n,o&&o->busy?"opening runtime reentry rejected":"opening runtime unavailable");return 0;}
int oa_opening_runtime_cinematic_finished(oa_opening_runtime *o,int v,char *e,size_t n){if(start(o,e,n))return 1;if(v!=0&&v!=1)return fail(e,n,"cinematic completion must be an explicit boolean");o->flag=v;return event(o,OP_FLAG,e,n);}
int oa_opening_runtime_volume_exit(oa_opening_runtime *o,const char *v,const char *who,char *e,size_t n){if(start(o,e,n))return 1;if(!v||!who||strlen(v)>255||strlen(who)>127)return fail(e,n,"invalid source volume/identity");o->volume=v;o->object=who;return event(o,OP_EXIT,e,n);}
int oa_opening_runtime_sword_acquired(oa_opening_runtime *o,int32_t item,const char *who,int32_t arg3,char *e,size_t n){if(start(o,e,n))return 1;if(item<0||!who||strlen(who)>127)return fail(e,n,"invalid source inventory event");o->item=item;o->object=who;o->arg3=arg3;return event(o,OP_ACQUIRE,e,n);}
int oa_opening_runtime_sword_equipped(oa_opening_runtime *o,int32_t item,char *e,size_t n){if(start(o,e,n))return 1;if(item<0)return fail(e,n,"invalid source item index");o->item=item;return event(o,OP_EQUIP,e,n);}
int oa_opening_runtime_advance(oa_opening_runtime *o,uint32_t dt,char *e,size_t n){if(start(o,e,n))return 1;if(dt>INT32_MAX)return fail(e,n,"invalid game-time delta");o->delta=dt;return event(o,OP_ADVANCE,e,n);}
int oa_opening_runtime_snapshot(oa_opening_runtime *o,oa_opening_snapshot *s,char *e,size_t n){if(start(o,e,n))return 1;if(!s)return fail(e,n,"snapshot output required");*s=o->last;return 0;}
int oa_opening_runtime_restore(oa_opening_runtime *o,const oa_opening_snapshot *s,char *e,size_t n){if(start(o,e,n))return 1;if(!valid_snapshot(s))return fail(e,n,"invalid typed opening snapshot");o->input=*s;return event(o,OP_RESTORE,e,n);}
void oa_opening_runtime_get_stats(const oa_opening_runtime *o,oa_opening_runtime_stats *s){if(!s)return;memset(s,0,sizeof(*s));if(!o)return;s->lua_bytes=o->lua?amalur_runtime_memory_used(o->lua):0;s->lua_limit=o->memory_limit;s->instruction_budget=o->budget;s->calls=o->calls;s->rejections=o->rejections;s->rebuilds=o->rebuilds;s->poisoned=o->poisoned;}
