#include "scene_script_bootstrap.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef struct resource {const char *path,*bytes;size_t length;} resource;
typedef struct memory_resources {resource files[9];} memory_resources;
static unsigned checks;
static void check(int ok,const char *message){if(!ok){fprintf(stderr,"FAIL: %s\n",message);exit(1);}++checks;}
static resource *find(void *context,const char *path){memory_resources *m=(memory_resources*)context;unsigned i;for(i=0;i<9;i++)if(m->files[i].path&&!strcmp(m->files[i].path,path))return &m->files[i];return NULL;}
static int size_resource(void *context,const char *path,size_t *length,char *error,size_t cap){resource *f=find(context,path);if(!f){snprintf(error,cap,"Missing resource %s",path);return 1;}*length=f->length;return 0;}
static int read_resource(void *context,const char *path,char *bytes,size_t length,char *error,size_t cap){resource *f=find(context,path);if(!f||f->length!=length){snprintf(error,cap,"Resource changed");return 1;}memcpy(bytes,f->bytes,length);return 0;}
static void set(resource *f,const char *path,const char *bytes){f->path=path;f->bytes=bytes;f->length=strlen(bytes);}
int main(int argc,char **argv){
    const char *core[]={"amalur_uint64.lua","amalur_engine_handles.lua","engine_binding_registry.lua","amalur_engine_bindings.lua","amalur_native_math.lua"};
    const char *bootstrap="module('Bootstrap',package.seeall);assert(_G.root_started==nil);local d=require('Dependency');_G.bootstrap_value=d.value;_G.bootstrap_count=(_G.bootstrap_count or 0)+1";
    const char *root="assert(_G.bootstrap_value==37,'bootstrap missing');_G.root_started=true;module('Root',package.seeall);require('Bootstrap');assert(bootstrap_count==1);function complete()return bootstrap_value end";
    memory_resources m={0};scene_script_resources resources={&m,size_resource,read_resource};scene_script_options options={0};scene_script_result result;
    amalur_runtime *runtime;char paths[5][128],filename[4096],long_name[257];char *bytes[5];int i;
    if(argc!=2){fprintf(stderr,"bootstrap_order_test RUNTIME_DIR\n");return 2;}
    for(i=0;i<5;i++){
        FILE *f;long length;snprintf(paths[i],sizeof(paths[i]),"runtime/%s",core[i]);snprintf(filename,sizeof(filename),"%s/%s",argv[1],core[i]);
        f=fopen(filename,"rb");check(f!=NULL,"core source opens");check(!fseek(f,0,SEEK_END),"core seek");length=ftell(f);check(length>=0&&length<=16*1024*1024,"core bounded size");rewind(f);
        bytes[i]=(char*)malloc((size_t)length+1);check(bytes[i]!=NULL,"core buffer allocated");check(fread(bytes[i],1,(size_t)length,f)==(size_t)length,"core read complete");fclose(f);bytes[i][length]=0;set(&m.files[i],paths[i],bytes[i]);
    }
    set(&m.files[5],"modules/modules.tsv","Root\troot.lua\nBootstrap\tbootstrap.lua\nDependency\tdependency.lua\n");
    set(&m.files[6],"modules/root.lua",root);set(&m.files[7],"modules/bootstrap.lua",bootstrap);
    set(&m.files[8],"modules/dependency.lua","module('Dependency',package.seeall);value=37");
    options.root_module="Root";options.bootstrap_module="Bootstrap";options.event="complete";
    runtime=scene_script_bootstrap(&resources,&options,&result);
    check(runtime&&result.ok&&result.bootstrap_loaded&&result.root_loaded&&result.event_invoked&&result.registered_modules==3,result.error);
    check(lua_tointeger(amalur_runtime_state(runtime),1)==37,"bootstrap can require registered dependency before root/event");
    lua_getglobal(amalur_runtime_state(runtime),"bootstrap_count");check(lua_tointeger(amalur_runtime_state(runtime),-1)==1,"root re-require uses bootstrap cache");amalur_runtime_destroy(runtime);
    options.bootstrap_module=NULL;runtime=scene_script_bootstrap(&resources,&options,&result);
    check(!runtime&&!result.bootstrap_loaded&&!result.root_loaded&&!strcmp(result.phase,"require")&&strstr(result.error,"bootstrap missing"),"omitted bootstrap does not invent global helpers");
    set(&m.files[6],"modules/root.lua","module('Root',package.seeall);function complete()return 19 end");
    runtime=scene_script_bootstrap(&resources,&options,&result);check(runtime&&result.ok&&!result.bootstrap_loaded&&result.root_loaded&&result.event_invoked,"NULL bootstrap preserves preceding load behavior");amalur_runtime_destroy(runtime);set(&m.files[6],"modules/root.lua",root);
    options.bootstrap_module="Missing";runtime=scene_script_bootstrap(&resources,&options,&result);
    check(!runtime&&!result.bootstrap_loaded&&!result.root_loaded&&!strcmp(result.phase,"preload")&&strstr(result.error,"Missing"),"missing bootstrap stops before root with preload diagnostic");
    options.bootstrap_module="Bootstrap";set(&m.files[7],"modules/bootstrap.lua","error('explicit bootstrap failure')");runtime=scene_script_bootstrap(&resources,&options,&result);
    check(!runtime&&!result.bootstrap_loaded&&!result.root_loaded&&!strcmp(result.phase,"preload")&&strstr(result.error,"explicit bootstrap failure"),"bootstrap Lua error protected and root not attempted");
    set(&m.files[7],"modules/bootstrap.lua","this is not Lua");runtime=scene_script_bootstrap(&resources,&options,&result);
    check(!runtime&&!result.root_loaded&&!strcmp(result.phase,"preload")&&result.registered_modules==3,"lazy bootstrap syntax failure reports preload");
    set(&m.files[7],"modules/bootstrap.lua","while true do end");options.instruction_budget=1000;runtime=scene_script_bootstrap(&resources,&options,&result);
    check(!runtime&&!result.bootstrap_loaded&&!result.root_loaded&&!strcmp(result.phase,"preload")&&strstr(result.error,"budget"),"bootstrap execution remains instruction-bounded");options.instruction_budget=0;set(&m.files[7],"modules/bootstrap.lua",bootstrap);
    options.bootstrap_module="bad/name";runtime=scene_script_bootstrap(&resources,&options,&result);check(!runtime&&!strcmp(result.phase,"arguments")&&result.resource_bytes==0,"bootstrap path rejected before reads");
    options.bootstrap_module="";runtime=scene_script_bootstrap(&resources,&options,&result);check(!runtime&&!strcmp(result.phase,"arguments"),"empty bootstrap name rejected");
    memset(long_name,'x',256);long_name[256]=0;options.bootstrap_module=long_name;runtime=scene_script_bootstrap(&resources,&options,&result);check(!runtime&&!strcmp(result.phase,"arguments"),"bootstrap name byte bound enforced");
    for(i=0;i<5;i++)free(bytes[i]);printf("{\"ok\":true,\"checks\":%u,\"scope\":\"explicit registered bootstrap ordering/error/missing/budget behavior; synthetic modules\"}\n",checks);return 0;
}
