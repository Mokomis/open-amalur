#include "amalur_runtime.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static unsigned checks;
static void check(int condition,const char *message) {
    if(!condition){fprintf(stderr,"FAIL: %s\n",message);exit(1);} ++checks;
}
static char *read_source(const char *directory,const char *name,size_t *size) {
    char path[4096],*data;long length;FILE *f;
    check(strlen(directory)+strlen(name)+2<sizeof(path),"path fits");
    snprintf(path,sizeof(path),"%s/%s",directory,name);f=fopen(path,"rb");check(f!=NULL,"source file opens");
    check(fseek(f,0,SEEK_END)==0,"seek source");length=ftell(f);check(length>=0,"source size");rewind(f);
    data=(char*)malloc((size_t)length+1);check(data!=NULL,"source bytes allocated");
    check(fread(data,1,(size_t)length,f)==(size_t)length,"complete source read");fclose(f);
    *size=(size_t)length;return data;
}
int main(int argc,char **argv) {
    const char *names[]={"amalur_uint64.lua","amalur_engine_handles.lua","engine_binding_registry.lua","amalur_engine_bindings.lua","amalur_native_math.lua"};
    amalur_runtime_config config={0};amalur_runtime_source sources[5];amalur_runtime *r;char error[1024];int i,count,status;
    if(argc!=2){fprintf(stderr,"runtime_sources_test RUNTIME_DIR\n");return 2;}
    for(i=0;i<5;i++){sources[i].name=names[i];sources[i].data=read_source(argv[1],names[i],&sources[i].length);}
    config.runtime_sources=sources;config.runtime_source_count=5;
    r=amalur_runtime_create(&config,error,sizeof(error));check(r!=NULL,error);amalur_runtime_destroy(r);
    config.runtime_source_count=4;r=amalur_runtime_create(&config,error,sizeof(error));check(r==NULL&&strstr(error,"five")!=NULL,"incomplete source count rejected");config.runtime_source_count=5;
    sources[1].name=names[0];r=amalur_runtime_create(&config,error,sizeof(error));check(r==NULL&&strstr(error,"Duplicate")!=NULL,"duplicate source rejected");sources[1].name=names[1];
    sources[1].name="unknown.lua";config.runtime_dir=argv[1];r=amalur_runtime_create(&config,error,sizeof(error));check(r==NULL&&strstr(error,"Missing")!=NULL,"missing source never falls back to filesystem");sources[1].name=names[1];config.runtime_dir=NULL;
    {const char *saved=sources[0].data;size_t length=sources[0].length;sources[0].data="bad syntax !";sources[0].length=12;
     r=amalur_runtime_create(&config,error,sizeof(error));check(r==NULL,"bad core source rejected");sources[0].data=saved;sources[0].length=length;}
    r=amalur_runtime_create(&config,error,sizeof(error));check(r!=NULL,error);
    for(i=0;i<5;i++)free((void*)sources[i].data);memset(sources,0,sizeof(sources));
    {const char *code="assert(type(__amalur_uint64)=='table'); assert(type(math.abs)=='function'); return math.abs(-7)";
     status=amalur_runtime_eval_source(r,code,strlen(code),"borrow-lifetime",&count,error,sizeof(error));
     check(status==0&&count==1&&lua_tonumber(amalur_runtime_state(r),1)==7,"runtime no longer borrows bootstrap bytes");}
    amalur_runtime_destroy(r);printf("{\"ok\":true,\"checks\":%u,\"scope\":\"borrowed in-memory runtime bootstrap\"}\n",checks);return 0;
}
