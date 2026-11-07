#include "amalur_runtime.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static unsigned checks;
static void check(int condition,const char *message){if(!condition){fprintf(stderr,"FAIL: %s\n",message);exit(1);}++checks;}
static void succeeds(amalur_runtime *runtime,const char *code){char error[1024];int count;int status=amalur_runtime_eval_source(runtime,code,strlen(code),"SL-static-contract",&count,error,sizeof(error));check(status==0,error);}
static void fails(amalur_runtime *runtime,const char *code,const char *message){char error[1024];int count;int status=amalur_runtime_eval_source(runtime,code,strlen(code),"SL-static-contract",&count,error,sizeof(error));check(status!=0&&strstr(error,message),error);}
int main(int argc,char **argv){
    amalur_runtime_config config={0};amalur_runtime *runtime;char error[1024];
    if(argc!=2){fprintf(stderr,"sl_identifier_test RUNTIME_DIR\n");return 2;}config.runtime_dir=argv[1];runtime=amalur_runtime_create(&config,error,sizeof(error));check(runtime!=NULL,error);
    succeeds(runtime,"assert(SL()==nil and SL({},1)==nil and SL('string',1)==nil)");
    succeeds(runtime,"assert(SL(nil)==nil and SL(1)==nil and SL(true)==nil and SL(function()end)==nil)");
    succeeds(runtime,"assert(SL({})==nil and SL({SL1=2})==nil and SL({SL1='2',SL2=3})==nil and SL({SL1=2,SL2=false})==nil)");
    succeeds(runtime,"assert(SL({SL1=0,SL2=0})==nil)");
    succeeds(runtime,"local a={SL1=0,SL2=7,extra=9};local b=SL(a);assert(b~=a and b.SL1==0 and b.SL2==7 and b.extra==nil and getmetatable(b)==nil);local n=0;for k,v in pairs(b)do n=n+1 end;assert(n==2);b.SL2=8;assert(a.SL2==7)");
    succeeds(runtime,"local a=SL({SL1=-2147483648,SL2=2147483647});assert(a.SL1==-2147483648 and a.SL2==2147483647);local b=SL({SL1=-1,SL2=0});assert(b.SL1==-1 and b.SL2==0)");
    fails(runtime,"return SL(setmetatable({SL1=2,SL2=3},{}))","metatable");
    fails(runtime,"return SL({SL1=0.5,SL2=1})","signed-int32");
    fails(runtime,"return SL({SL1=2147483648,SL2=1})","signed-int32");
    fails(runtime,"return SL({SL1=0/0,SL2=1})","signed-int32");
    fails(runtime,"return SL('loc_name')","localization service");
    amalur_runtime_destroy(runtime);printf("{\"ok\":true,\"checks\":%u,\"scope\":\"SL table identifier contract from static native trace; no native runtime comparison\"}\n",checks);return 0;
}
