#include "scene_enums_v08.h"
#include "scene_asset_keys.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static unsigned checks;
static void check(int ok,const char *message){if(!ok){fprintf(stderr,"FAIL: %s\n",message);exit(1);}++checks;}
static void succeeds(amalur_runtime *r,const char *s){char error[1024];int n,status=amalur_runtime_eval_source(r,s,strlen(s),"enum-snapshot-test",&n,error,sizeof(error));check(!status,error);}
static void fails(amalur_runtime *r,const char *s,const char *fragment){char error[1024];int n,status=amalur_runtime_eval_source(r,s,strlen(s),"enum-snapshot-test",&n,error,sizeof(error));check(status&&strstr(error,fragment),error);}
static void put32(unsigned char *p,uint32_t value){p[0]=(unsigned char)value;p[1]=(unsigned char)(value>>8);p[2]=(unsigned char)(value>>16);p[3]=(unsigned char)(value>>24);}
static uint32_t hash(const char *text){uint32_t value=0;check(!scene_asset_ascii_hash(text,strlen(text),&value),"fixture ASCII hash accepted");return value;}
static void header(unsigned char *bytes,uint32_t count){memcpy(bytes,"AENU",4);put32(bytes+4,1);put32(bytes+8,count);}
static void record(unsigned char *bytes,unsigned index,uint32_t group,uint32_t member,uint32_t value){unsigned char *p=bytes+12+index*12;put32(p,group);put32(p+4,member);put32(p+8,value);}
static amalur_runtime *create(const amalur_runtime_config *config){char error[1024];amalur_runtime *r=amalur_runtime_create(config,error,sizeof(error));check(r!=NULL,error);return r;}
static void rejected(const amalur_runtime_config *config,const void *snapshot,size_t length,const char *fragment){
    char error[1024];amalur_runtime *r=create(config);lua_State *L=amalur_runtime_state(r);int top=lua_gettop(L),status;
    status=scene_enums_v08_install(r,snapshot,length,error,sizeof(error));check(status&&strstr(error,fragment),error);
    check(lua_gettop(L)==top+1,"failure leaves one protected Lua error");lua_pop(L,1);
    lua_getglobal(L,"STE");check(lua_isnil(L,-1),"malformed snapshot does not publish STE");lua_pop(L,1);amalur_runtime_destroy(r);
}
int main(int argc,char **argv){
    amalur_runtime_config config={0},limited={0};amalur_runtime *runtime;lua_State *L;
    unsigned char snapshot[12+7*12],copy[sizeof(snapshot)+1],empty[12],*large;char error[1024],long_name[1025];
    uint32_t group,member,long_hash=0;size_t long_length;unsigned i;int status,top;
    if(argc!=2){fprintf(stderr,"enum_snapshot_test RUNTIME_DIR\n");return 2;}config.runtime_dir=argv[1];
    group=hash("Test");member=hash("positive");header(snapshot,7);
    record(snapshot,0,group,member,7);record(snapshot,1,group,hash("minus_one"),0xffffffffu);
    record(snapshot,2,group,hash("minimum"),0x80000000u);record(snapshot,3,group,hash("maximum"),0x7fffffffu);
    record(snapshot,4,hash("Other"),member,0);record(snapshot,5,0,0,(uint32_t)-123);
    memset(long_name,'a',sizeof(long_name));
    for(long_length=1;long_length<sizeof(long_name);long_length++){
        if(scene_asset_ascii_hash(long_name,long_length,&long_hash))check(0,"long fixture hash accepted");
        if(long_hash&0x80000000u)break;
    }
    check(long_length<sizeof(long_name),"fixture exercises unsigned high-bit hash keys");long_name[long_length]=0;
    record(snapshot,6,long_hash,long_hash,42);memcpy(copy,snapshot,sizeof(snapshot));
    runtime=create(&config);L=amalur_runtime_state(runtime);lua_pushinteger(L,123);top=lua_gettop(L);
    status=scene_enums_v08_install(runtime,snapshot,sizeof(snapshot),error,sizeof(error));check(!status,error);
    check(lua_gettop(L)==top&&lua_tointeger(L,-1)==123,"success preserves caller stack");lua_pop(L,1);
    memset(snapshot,0,sizeof(snapshot)); /* Installer must own every copied value. */
    lua_pushlstring(L,long_name,long_length);lua_setglobal(L,"enum_long_name");
    succeeds(runtime,"assert(STE('Test','positive')==7 and STE('tEsT','POSITIVE')==7);assert(STE('Test','minus_one')==-1 and STE('Test','minimum')==-2147483648 and STE('Test','maximum')==2147483647);assert(STE('Other','positive')==0 and STE('','')==-123 and STE(enum_long_name,enum_long_name)==42)");
    succeeds(runtime,"assert(STE('Test\\000ignored','positive\\000\\255')==7);assert(STE('missing','positive')==nil and STE('Test','missing')==nil);assert(select('#',STE('missing','positive'))==1 and select('#',STE())==1)");
    succeeds(runtime,"assert(STE()==nil and STE('Test')==nil and STE('Test','positive',nil)==nil);assert(STE(1,'positive')==nil and STE('Test',1)==nil and STE(nil,'positive')==nil and STE('Test',false)==nil and STE(function()end,'positive')==nil);local t=setmetatable({},{__tostring=function()error('coercion must not occur')end});assert(STE(t,'positive')==nil and STE('Test',t)==nil);assert(STE(newproxy(true),'positive')==nil)");
    fails(runtime,"return STE('Test','\\255')","ASCII");fails(runtime,"return STE('\\255','positive')","ASCII");
    succeeds(runtime,"SH=function()error('public SH must not be called')end;assert(STE('Test','positive')==7)");
    header(empty,0);status=scene_enums_v08_install(runtime,empty,sizeof(empty),error,sizeof(error));check(status&&strstr(error,"already exists"),"existing STE refused");lua_pop(L,1);
    succeeds(runtime,"assert(STE('Test','positive')==7)");amalur_runtime_destroy(runtime);
    runtime=create(&config);status=scene_enums_v08_install(runtime,empty,sizeof(empty),error,sizeof(error));check(!status,error);
    succeeds(runtime,"assert(STE('any','thing')==nil and STE('','')==nil)");amalur_runtime_destroy(runtime);
    rejected(&config,NULL,12,"header");rejected(&config,copy,11,"header");
    copy[0]='X';rejected(&config,copy,sizeof(snapshot),"header");copy[0]='A';
    put32(copy+4,2);rejected(&config,copy,sizeof(snapshot),"header");put32(copy+4,1);
    rejected(&config,copy,sizeof(snapshot)-1,"shape");rejected(&config,copy,sizeof(snapshot)+1,"shape");
    put32(copy+8,65537);rejected(&config,copy,sizeof(snapshot),"shape");put32(copy+8,7);
    memcpy(copy+24,copy+12,12);rejected(&config,copy,sizeof(snapshot),"Duplicate");
    runtime=create(&config);succeeds(runtime,"setmetatable(_G,{})");status=scene_enums_v08_install(runtime,empty,sizeof(empty),error,sizeof(error));check(status&&strstr(error,"plain realm"),"global metatable refused");amalur_runtime_destroy(runtime);
    runtime=create(&config);succeeds(runtime,"STE=false");status=scene_enums_v08_install(runtime,empty,sizeof(empty),error,sizeof(error));check(status&&strstr(error,"already exists"),"even false existing global refused");amalur_runtime_destroy(runtime);
    status=scene_enums_v08_install(NULL,empty,sizeof(empty),error,sizeof(error));check(status&&strstr(error,"Runtime"),"null runtime refused");
    large=(unsigned char*)malloc(SCENE_ENUMS_V08_MAX_BYTES);check(large!=NULL,"bounded maximum snapshot allocated");header(large,SCENE_ENUMS_V08_MAX_ENTRIES);
    for(i=0;i<SCENE_ENUMS_V08_MAX_ENTRIES;i++)record(large,i,i,0,i);
    limited.runtime_dir=argv[1];limited.memory_limit_bytes=4u*1024u*1024u;runtime=create(&limited);
    status=scene_enums_v08_install(runtime,large,SCENE_ENUMS_V08_MAX_BYTES,error,sizeof(error));free(large);
    check(status==LUA_ERRMEM,"large valid snapshot exceeds deliberately small Lua cap with protected OOM");
    check(amalur_runtime_memory_used(runtime)<=limited.memory_limit_bytes,"Lua cap remains enforced after installer OOM");amalur_runtime_destroy(runtime);
    printf("{\"ok\":true,\"checks\":%u,\"scope\":\"STE snapshot mechanics, strict argument domains and protected ownership; synthetic data, no native enum-loader parity claim\"}\n",checks);return 0;
}
