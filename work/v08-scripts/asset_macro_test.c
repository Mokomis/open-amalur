#include "scene_asset_macros_v08.h"
#include "scene_asset_keys.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static unsigned checks;
static void check(int condition,const char *message){if(!condition){fprintf(stderr,"FAIL: %s\n",message);exit(1);}++checks;}
static void succeeds(amalur_runtime *runtime,const char *source){int count;char error[1024];int status=amalur_runtime_eval_source(runtime,source,strlen(source),"asset-macro-test",&count,error,sizeof(error));check(!status,error);}
static void fails(amalur_runtime *runtime,const char *source,const char *fragment){int count;char error[1024];int status=amalur_runtime_eval_source(runtime,source,strlen(source),"asset-macro-test",&count,error,sizeof(error));check(status&&strstr(error,fragment),error);}
static void put32(unsigned char *p,uint32_t value){p[0]=(unsigned char)value;p[1]=(unsigned char)(value>>8);p[2]=(unsigned char)(value>>16);p[3]=(unsigned char)(value>>24);}
static void rejected(const amalur_runtime_config *config,const char *name,uint32_t category,const void *bytes,size_t length,const char *fragment){
    char error[1024];amalur_runtime *runtime=amalur_runtime_create(config,error,sizeof(error));int status;check(runtime!=NULL,error);
    status=scene_asset_macro_v08_install(runtime,name,category,bytes,length,error,sizeof(error));check(status&&strstr(error,fragment),error);amalur_runtime_destroy(runtime);
}
int main(int argc,char **argv){
    amalur_runtime_config config={0};amalur_runtime *runtime;FILE *file;long length;unsigned char *bytes,synthetic[24];uint32_t hash;char error[1024];int status,top;
    if(argc!=3){fprintf(stderr,"asset_macro_test RUNTIME_DIR VERIFIED_MERGED_LOOT_SNAPSHOT\n");return 2;}
    config.runtime_dir=argv[1];file=fopen(argv[2],"rb");check(file!=NULL,"merged original loot snapshot opens");
    check(!fseek(file,0,SEEK_END),"snapshot seek");length=ftell(file);check(length>0&&length<=524296,"snapshot bounded length");rewind(file);bytes=(unsigned char*)malloc((size_t)length);check(bytes!=NULL,"snapshot allocated");check(fread(bytes,1,(size_t)length,file)==(size_t)length,"snapshot complete");fclose(file);
    check(!scene_asset_ascii_hash("loot_all_common_wpn_1h_swords",strlen("loot_all_common_wpn_1h_swords"),&hash)&&hash==56373026u,"native-probed sword loot name hash");
    runtime=amalur_runtime_create(&config,error,sizeof(error));check(runtime!=NULL,error);top=lua_gettop(amalur_runtime_state(runtime));
    status=scene_asset_macro_v08_install(runtime,"LOOT_TABLE_ID",0x37,bytes,(size_t)length,error,sizeof(error));free(bytes);check(!status,error);check(lua_gettop(amalur_runtime_state(runtime))==top,"installation preserves caller stack");
    succeeds(runtime,"assert(SH==nil and INPUT_ACTION_KEY==nil);local lo,hi=__amalur_handles.to_words(LOOT_TABLE_ID('loot_all_common_wpn_1h_swords'));assert(lo==0x37b and hi==353414)");
    succeeds(runtime,"local lo,hi=__amalur_handles.to_words(LOOT_TABLE_ID('LOOT_ALL_COMMON_WPN_1H_SWORDS\\000ignored'));assert(lo==0x37b and hi==353414)");
    succeeds(runtime,"assert(LOOT_TABLE_ID()==nil and LOOT_TABLE_ID(1)==nil and LOOT_TABLE_ID('x',1)==nil and LOOT_TABLE_ID('')==nil and LOOT_TABLE_ID('\\000ignored')==nil and LOOT_TABLE_ID('__unknown_loot_e3785d__')==nil)");
    succeeds(runtime,"local old=__amalur_handles.from_words;__amalur_handles.from_words=function()error('replacement must not run')end;local lo,hi=__amalur_handles.to_words(LOOT_TABLE_ID('loot_all_common_wpn_1h_swords'));__amalur_handles.from_words=old;assert(lo==0x37b and hi==353414)");
    fails(runtime,"return LOOT_TABLE_ID('\\255')","ASCII");
    put32(synthetic,1);put32(synthetic+4,2);put32(synthetic+8,0xffffffffu);put32(synthetic+12,1);put32(synthetic+16,90168u);put32(synthetic+20,0);
    status=scene_asset_keys_install(runtime,synthetic,sizeof(synthetic),error,sizeof(error));check(!status,error);
    succeeds(runtime,"assert(SH('A')==90168);local lo,hi=__amalur_handles.to_words(INPUT_ACTION_KEY('A'));assert(lo==0x19b and hi==4294967295);local a,b=__amalur_handles.to_words(LOOT_TABLE_ID('loot_all_common_wpn_1h_swords'));assert(a==0x37b and b==353414)");
    status=scene_asset_macro_v08_install(runtime,"LOOT_TABLE_ID",0x37,synthetic,sizeof(synthetic),error,sizeof(error));check(status&&strstr(error,"already exists"),"existing macro is not replaced");amalur_runtime_destroy(runtime);
    runtime=amalur_runtime_create(&config,error,sizeof(error));check(runtime!=NULL,error);
    status=scene_asset_macro_v08_install(runtime,"TEST_LOW",1,synthetic,sizeof(synthetic),error,sizeof(error));check(!status,error);
    status=scene_asset_macro_v08_install(runtime,"TEST_HIGH",255,synthetic,sizeof(synthetic),error,sizeof(error));check(!status,error);
    succeeds(runtime,"local a,b=__amalur_handles.to_words(TEST_LOW('A'));assert(a==0x1b and b==4294967295);a,b=__amalur_handles.to_words(TEST_HIGH('A'));assert(a==0xffb and b==4294967295);assert(TEST_LOW('')==nil and TEST_HIGH('\\000x')==nil)");amalur_runtime_destroy(runtime);
    rejected(&config,"bad_name",1,synthetic,sizeof(synthetic),"uppercase");rejected(&config,"1BAD",1,synthetic,sizeof(synthetic),"uppercase");
    rejected(&config,"TEST",0,synthetic,sizeof(synthetic),"category");rejected(&config,"TEST",256,synthetic,sizeof(synthetic),"category");
    put32(synthetic,2);rejected(&config,"TEST",1,synthetic,sizeof(synthetic),"version1");put32(synthetic,1);
    rejected(&config,"TEST",1,synthetic,sizeof(synthetic)-1,"shape");put32(synthetic+4,65537);rejected(&config,"TEST",1,synthetic,sizeof(synthetic),"shape");put32(synthetic+4,2);
    put32(synthetic+8,0);rejected(&config,"TEST",1,synthetic,sizeof(synthetic),"Zero");put32(synthetic+8,0xffffffffu);
    put32(synthetic+12,0xffffffffu);rejected(&config,"TEST",1,synthetic,sizeof(synthetic),"Duplicate asset macro ID");put32(synthetic+12,1);
    put32(synthetic+20,90168);rejected(&config,"TEST",1,synthetic,sizeof(synthetic),"Duplicate asset macro hash");put32(synthetic+20,0);
    runtime=amalur_runtime_create(&config,error,sizeof(error));check(runtime!=NULL,error);succeeds(runtime,"setmetatable(_G,{})");status=scene_asset_macro_v08_install(runtime,"TEST",1,synthetic,sizeof(synthetic),error,sizeof(error));check(status&&strstr(error,"plain realm"),"global metatable rejected");amalur_runtime_destroy(runtime);
    printf("{\"ok\":true,\"checks\":%u,\"scope\":\"generic snapshot macro mechanics plus native-proven loot category/name mapping; not full asset manager\"}\n",checks);return 0;
}
