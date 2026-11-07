#include "scene_script_bootstrap.h"
#include "lauxlib.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef struct memory_resource {const char *path,*data;size_t length;} memory_resource;
typedef struct memory_resources {memory_resource files[8];int fail_read;} memory_resources;
static unsigned checks;
static void check(int condition,const char *message){if(!condition){fprintf(stderr,"FAIL: %s\n",message);exit(1);}++checks;}
static memory_resource *find(void *context,const char *path){memory_resources *resources=(memory_resources*)context;unsigned i;for(i=0;i<8;i++)if(!strcmp(resources->files[i].path,path))return &resources->files[i];return NULL;}
static int size_resource(void *context,const char *path,size_t *length,char *error,size_t cap){memory_resource *file=find(context,path);if(!file){snprintf(error,cap,"Missing resource %s",path);return 1;}*length=file->length;return 0;}
static int read_resource(void *context,const char *path,char *data,size_t length,char *error,size_t cap){memory_resources *resources=(memory_resources*)context;memory_resource *file=find(context,path);if(!file||file->length!=length||resources->fail_read){snprintf(error,cap,"Injected read failure");return 1;}memcpy(data,file->data,length);return 0;}
static void set(memory_resource *entry,const char *path,const char *data){entry->path=path;entry->data=data;entry->length=strlen(data);}
static int setup_success(amalur_runtime *runtime,void *context,char *error,size_t cap){lua_State *L=amalur_runtime_state(runtime);(void)error;(void)cap;(*(int*)context)++;lua_pushinteger(L,41);lua_setglobal(L,"host_fixture_value");return 0;}
static int setup_failure(amalur_runtime *runtime,void *context,char *error,size_t cap){(void)runtime;(void)context;snprintf(error,cap,"Explicit host setup failure");return 1;}
static int setup_lua_error(amalur_runtime *runtime,void *context,char *error,size_t cap){(void)context;(void)error;(void)cap;return luaL_error(amalur_runtime_state(runtime),"Raised host setup Lua error");}
int main(int argc,char **argv){
    const char *names[]={"amalur_uint64.lua","amalur_engine_handles.lua","engine_binding_registry.lua","amalur_engine_bindings.lua","amalur_native_math.lua"};
    const char *manifest="Root\troot.lua\nDependency\tdependency.lua\n";
    memory_resources memory={0};scene_script_resources resources={&memory,size_resource,read_resource};scene_script_options options={0};scene_script_result result;amalur_runtime *runtime;char paths[5][128],filename[4096],error[1024];int i,status,count,setup_calls=0;char *bytes[5];
    if(argc!=2){fprintf(stderr,"scene_script_bootstrap_test RUNTIME_DIR\n");return 2;}
    for(i=0;i<5;i++){
        FILE *file;long length;snprintf(paths[i],sizeof(paths[i]),"runtime/%s",names[i]);snprintf(filename,sizeof(filename),"%s/%s",argv[1],names[i]);file=fopen(filename,"rb");check(file!=NULL,"core source opens");
        check(fseek(file,0,SEEK_END)==0,"core seek");length=ftell(file);check(length>=0,"core size");rewind(file);bytes[i]=(char*)malloc((size_t)length+1);check(bytes[i]!=NULL,"core allocated");
        check(fread(bytes[i],1,(size_t)length,file)==(size_t)length,"core read");fclose(file);bytes[i][length]=0;set(&memory.files[i],paths[i],bytes[i]);
    }
    set(&memory.files[5],"modules/modules.tsv",manifest);
    set(&memory.files[6],"modules/root.lua","module('Root',package.seeall); local dependency=require('Dependency'); function complete() return dependency.value end; function missing() return UNIMPLEMENTED_SERVICE.query() end");
    set(&memory.files[7],"modules/dependency.lua","module('Dependency',package.seeall); value=37");
    options.root_module="Root";options.event="complete";
    runtime=scene_script_bootstrap(&resources,&options,&result);
    check(runtime&&result.ok&&result.root_loaded&&result.event_invoked&&result.registered_modules==2,result.error);
    check(lua_tointeger(amalur_runtime_state(runtime),1)==37,"event result comes from recovered module dependency");
    {const char *code="return require('Root').complete()";status=amalur_runtime_eval_source(runtime,code,strlen(code),"live-realm",&count,error,sizeof(error));check(!status&&count==1&&lua_tointeger(amalur_runtime_state(runtime),1)==37,"returned realm remains usable");}
    amalur_runtime_destroy(runtime);
    options.setup=setup_success;options.setup_context=&setup_calls;runtime=scene_script_bootstrap(&resources,&options,&result);
    check(runtime&&setup_calls==1,"host setup called once before module execution");lua_getglobal(amalur_runtime_state(runtime),"host_fixture_value");check(lua_tointeger(amalur_runtime_state(runtime),-1)==41,"explicit host setup reaches realm");amalur_runtime_destroy(runtime);
    options.setup=setup_failure;runtime=scene_script_bootstrap(&resources,&options,&result);check(!runtime&&!strcmp(result.phase,"host_setup")&&strstr(result.error,"Explicit"),"host setup return error preserved");
    options.setup=setup_lua_error;runtime=scene_script_bootstrap(&resources,&options,&result);check(!runtime&&!strcmp(result.phase,"host_setup")&&strstr(result.error,"Raised"),"host setup Lua error protected");options.setup=NULL;
    options.event="missing";runtime=scene_script_bootstrap(&resources,&options,&result);check(!runtime&&result.root_loaded&&!result.event_invoked&&!strcmp(result.phase,"event"),"missing native service fails explicitly at event");options.event=NULL;
    set(&memory.files[5],"modules/modules.tsv","Root\t../root.lua\n");runtime=scene_script_bootstrap(&resources,&options,&result);check(!runtime&&!strcmp(result.phase,"manifest"),"manifest paths cannot escape logical root");
    set(&memory.files[5],"modules/modules.tsv","Root\troot.lua\nRoot\tdependency.lua\n");runtime=scene_script_bootstrap(&resources,&options,&result);check(!runtime&&strstr(result.error,"Duplicate"),"duplicate name rejected");
    set(&memory.files[5],"modules/modules.tsv","Root\tmissing.lua\n");runtime=scene_script_bootstrap(&resources,&options,&result);check(!runtime&&!strcmp(result.phase,"preflight"),"missing module discovered before realm creation");
    set(&memory.files[5],"modules/modules.tsv",manifest);options.maximum_total_bytes=1;runtime=scene_script_bootstrap(&resources,&options,&result);check(!runtime&&strstr(result.error,"limit"),"total byte cap enforced");options.maximum_total_bytes=0;
    memory.files[7].length=17u*1024u*1024u;runtime=scene_script_bootstrap(&resources,&options,&result);check(!runtime&&!strcmp(result.phase,"preflight"),"oversized module rejected before read");memory.files[7].length=strlen(memory.files[7].data);
    memory.fail_read=1;runtime=scene_script_bootstrap(&resources,&options,&result);check(!runtime&&strstr(result.error,"Injected"),"resource read failure preserved");memory.fail_read=0;
    set(&memory.files[7],"modules/dependency.lua","this is not lua");runtime=scene_script_bootstrap(&resources,&options,&result);check(!runtime&&!result.root_loaded&&!strcmp(result.phase,"require")&&result.registered_modules==2,"lazy syntax error reported in require phase");
    for(i=0;i<5;i++)free(bytes[i]);printf("{\"ok\":true,\"checks\":%u,\"scope\":\"shared scene script bootstrap; synthetic module fixtures\"}\n",checks);return 0;
}
