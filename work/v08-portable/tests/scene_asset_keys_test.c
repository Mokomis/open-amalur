#include "scene_asset_keys.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static unsigned checks;
static void check(int condition,const char *message){if(!condition){fprintf(stderr,"FAIL: %s\n",message);exit(1);}++checks;}
static void succeeds(amalur_runtime *runtime,const char *source){char error[1024];int count;int status=amalur_runtime_eval_source(runtime,source,strlen(source),"asset-key-test",&count,error,sizeof(error));check(!status,error);}
static void fails(amalur_runtime *runtime,const char *source,const char *fragment){char error[1024];int count;int status=amalur_runtime_eval_source(runtime,source,strlen(source),"asset-key-test",&count,error,sizeof(error));check(status&&strstr(error,fragment),error);}
static void put32(unsigned char *p,uint32_t value){p[0]=(unsigned char)value;p[1]=(unsigned char)(value>>8);p[2]=(unsigned char)(value>>16);p[3]=(unsigned char)(value>>24);}
static void rejected(const amalur_runtime_config *config,const void *bytes,size_t length,const char *message){
    char error[1024];amalur_runtime *runtime=amalur_runtime_create(config,error,sizeof(error));int status;
    check(runtime!=NULL,error);status=scene_asset_keys_install(runtime,bytes,length,error,sizeof(error));check(status&&strstr(error,message),error);amalur_runtime_destroy(runtime);
}
int main(int argc,char **argv){
    amalur_runtime_config config={0};amalur_runtime *runtime;char error[1024];unsigned char synthetic[24],*bytes;uint32_t hash;FILE *file;long length;int status;
    if(argc!=3){fprintf(stderr,"scene_asset_keys_test RUNTIME_DIR INPUTDEVICEACTION_INIT_BIN\n");return 2;}
    config.runtime_dir=argv[1];file=fopen(argv[2],"rb");check(file!=NULL,"original input action snapshot opens");
    check(!fseek(file,0,SEEK_END),"snapshot seek");length=ftell(file);check(length>0&&length<=524296,"snapshot bounded length");rewind(file);
    bytes=(unsigned char*)malloc((size_t)length);check(bytes!=NULL,"snapshot allocated");check(fread(bytes,1,(size_t)length,file)==(size_t)length,"snapshot complete");fclose(file);
    check(!scene_asset_ascii_hash("LedgerLaunchMap",15,&hash)&&hash==13930338u,"native-probed LedgerLaunchMap hash");
    check(!scene_asset_ascii_hash("A",1,&hash)&&hash==90168u,"ASCII case folding with native table constants");
    check(!scene_asset_ascii_hash("",0,&hash)&&hash==0,"empty native hash");
    check(scene_asset_ascii_hash("\xff",1,&hash)!=0,"nonASCII hash rejected");
    runtime=amalur_runtime_create(&config,error,sizeof(error));check(runtime!=NULL,error);
    status=scene_asset_keys_install(runtime,bytes,(size_t)length,error,sizeof(error));free(bytes);check(!status,error);
    succeeds(runtime,"local a=INPUT_ACTION_KEY('LedgerLaunchMap');local lo,hi=__amalur_handles.to_words(a);assert(lo==0x19b and hi==7813);assert(SH('LedgerLaunchMap')==13930338 and SH('LEDGERLAUNCHMAP')==13930338)");
    succeeds(runtime,"assert(INPUT_ACTION_KEY('__opem_unknown_action_e43a8e23__')==nil);assert(INPUT_ACTION_KEY()==nil and INPUT_ACTION_KEY(12)==nil and INPUT_ACTION_KEY({},1)==nil);assert(SH()==nil and SH(12)==nil and SH('x',1)==nil)");
    succeeds(runtime,"local lo,hi=__amalur_handles.to_words(INPUT_ACTION_KEY('LedgerLaunchMap\\000ignored'));assert(lo==0x19b and hi==7813);assert(SH('None\\000\\255')==SH('None'))");
    succeeds(runtime,"local old=__amalur_handles.from_words;__amalur_handles.from_words=function() error('replacement must not run') end;local lo,hi=__amalur_handles.to_words(INPUT_ACTION_KEY('LedgerLaunchMap'));__amalur_handles.from_words=old;assert(lo==0x19b and hi==7813)");
    fails(runtime,"return SH('\\255')","ASCII");fails(runtime,"return INPUT_ACTION_KEY('\\255')","ASCII");
    put32(synthetic,1);put32(synthetic+4,2);put32(synthetic+8,1);put32(synthetic+12,0xffffffffu);put32(synthetic+16,13930338u);put32(synthetic+20,90168u);
    status=scene_asset_keys_install(runtime,synthetic,sizeof(synthetic),error,sizeof(error));check(status&&strstr(error,"already installed"),"reinstallation does not silently replace globals");amalur_runtime_destroy(runtime);
    runtime=amalur_runtime_create(&config,error,sizeof(error));check(runtime!=NULL,error);status=scene_asset_keys_install(runtime,synthetic,sizeof(synthetic),error,sizeof(error));check(!status,error);
    succeeds(runtime,"local lo,hi=__amalur_handles.to_words(INPUT_ACTION_KEY('A'));assert(lo==0x19b and hi==4294967295);local _,id=__amalur_handles.to_words(INPUT_ACTION_KEY('LedgerLaunchMap'));assert(id==1)");amalur_runtime_destroy(runtime);
    put32(synthetic+20,0);runtime=amalur_runtime_create(&config,error,sizeof(error));check(runtime!=NULL,error);status=scene_asset_keys_install(runtime,synthetic,sizeof(synthetic),error,sizeof(error));check(!status,error);
    succeeds(runtime,"assert(INPUT_ACTION_KEY('')==nil and INPUT_ACTION_KEY('\\000tail')==nil and SH('')==0)");amalur_runtime_destroy(runtime);put32(synthetic+20,90168u);
    put32(synthetic,2);rejected(&config,synthetic,sizeof(synthetic),"version1");put32(synthetic,1);
    rejected(&config,synthetic,sizeof(synthetic)-1,"shape");put32(synthetic+4,65537);rejected(&config,synthetic,sizeof(synthetic),"shape");put32(synthetic+4,2);
    put32(synthetic+8,0);rejected(&config,synthetic,sizeof(synthetic),"Zero");put32(synthetic+8,1);
    put32(synthetic+12,1);rejected(&config,synthetic,sizeof(synthetic),"Duplicate input action ID");put32(synthetic+12,0xffffffffu);
    put32(synthetic+20,13930338u);rejected(&config,synthetic,sizeof(synthetic),"Duplicate input action hash");
    printf("{\"ok\":true,\"checks\":%u,\"scope\":\"input action init snapshot and native ASCII hash/key packing; not full asset manager\"}\n",checks);return 0;
}
