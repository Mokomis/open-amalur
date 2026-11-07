#include "scene_script_bootstrap.h"
#include "lauxlib.h"
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

typedef struct entry {char *name,*file;size_t length;} entry;
typedef struct requested_names {const char *root,*event,*bootstrap;} requested_names;
typedef struct setup_call {amalur_runtime *runtime;const scene_script_options *options;scene_script_result *result;} setup_call;
static void phase(scene_script_result *result,const char *name) {
    snprintf(result->phase,sizeof(result->phase),"%s",name);
}
static int error(scene_script_result *result,const char *message) {
    snprintf(result->error,sizeof(result->error),"%s",message);return 1;
}
static int plain_name(const char *name,size_t maximum) {
    const unsigned char *p=(const unsigned char*)name;
    if(!p||!*p||strlen(name)>maximum)return 0;
    for(;*p;p++)if(*p<32||*p==127||*p=='/'||*p=='\\'||*p==':')return 0;
    return 1;
}
static int measure(const scene_script_resources *io,const char *path,size_t limit,
                   size_t total_limit,size_t *total,size_t *length,scene_script_result *result) {
    *length=0;
    if(io->size(io->context,path,length,result->error,sizeof(result->error))) {
        if(!*result->error)snprintf(result->error,sizeof(result->error),"Cannot size resource: %s",path);
        return 1;
    }
    if(*length>limit||*total>total_limit||*length>total_limit-*total)
        return error(result,"Resource source or total byte limit exceeded");
    *total+=*length;result->resource_bytes=*total;return 0;
}
static char *read_bytes(const scene_script_resources *io,const char *path,size_t length,scene_script_result *result) {
    char *data;
    if(length==(size_t)-1){error(result,"Resource length overflow");return NULL;}
    data=(char*)malloc(length+1);
    if(!data){error(result,"Resource buffer allocation failed");return NULL;}
    if(io->read(io->context,path,data,length,result->error,sizeof(result->error))) {
        if(!*result->error)snprintf(result->error,sizeof(result->error),"Cannot read resource: %s",path);
        free(data);return NULL;
    }
    data[length]=0;return data;
}
static int parse_manifest(char *data,size_t length,entry *entries,unsigned *count,scene_script_result *result) {
    char *line=data,*end=data+length,*next,*tab;size_t n;unsigned i;
    if(memchr(data,0,length))return error(result,"Manifest contains NUL byte");
    while(line<end) {
        next=(char*)memchr(line,'\n',(size_t)(end-line));
        if(next)*next++=0;else next=end;
        n=strlen(line);if(n&&line[n-1]=='\r')line[--n]=0;
        if(!n||line[0]=='#'){line=next;continue;}
        if(n>8191)return error(result,"Manifest line exceeds bound");
        tab=strchr(line,'\t');if(!tab||strchr(tab+1,'\t'))return error(result,"Manifest needs exactly name and basename columns");
        *tab++=0;
        if(!plain_name(line,255)||!plain_name(tab,1000)||!strcmp(tab,".")||!strcmp(tab,".."))
            return error(result,"Invalid manifest module name or source basename");
        if(*count>=4096)return error(result,"Module manifest exceeds4096 entries");
        for(i=0;i<*count;i++)if(!strcmp(entries[i].name,line))return error(result,"Duplicate module manifest name");
        entries[*count].name=line;entries[*count].file=tab;++*count;line=next;
    }
    if(!*count)return error(result,"Empty module manifest");return 0;
}
static int set_requested_names(lua_State *L) {
    requested_names *names=(requested_names*)lua_touserdata(L,1);
    lua_pushstring(L,names->root);lua_setglobal(L,"__opem_scene_root");
    if(names->event){lua_pushstring(L,names->event);lua_setglobal(L,"__opem_scene_event");}
    if(names->bootstrap){lua_pushstring(L,names->bootstrap);lua_setglobal(L,"__opem_scene_bootstrap");}
    return 0;
}
static int invoke_setup(lua_State *L) {
    setup_call *call=(setup_call*)lua_touserdata(L,1);
    if(call->options->setup(call->runtime,call->options->setup_context,call->result->error,sizeof(call->result->error)))
        return luaL_error(L,"%s",*call->result->error?call->result->error:"Host setup callback failed");
    return 0;
}
amalur_runtime *scene_script_bootstrap(const scene_script_resources *io,
                                     const scene_script_options *options,scene_script_result *result) {
    static const char *core_names[]={"amalur_uint64.lua","amalur_engine_handles.lua","engine_binding_registry.lua","amalur_engine_bindings.lua","amalur_native_math.lua"};
    scene_script_options defaults={0};scene_script_result ignored;amalur_runtime_config config={0};
    amalur_runtime_source core[5]={{0}};amalur_runtime *runtime=NULL;
    entry *entries=NULL;char *manifest=NULL,*data=NULL;char path[1100];size_t total=0,manifest_length,total_limit,source_limit;
    unsigned i,count=0;int status,results;requested_names names;lua_State *L;
    if(!result)result=&ignored;memset(result,0,sizeof(*result));phase(result,"arguments");
    if(!options)options=&defaults;
    if(!io||!io->size||!io->read){error(result,"Resource size/read callbacks required");goto failure;}
    names.root=options->root_module?options->root_module:"SpaceCommon";names.event=options->event;names.bootstrap=options->bootstrap_module;
    if(!plain_name(names.root,255)||(names.event&&!plain_name(names.event,255))||(names.bootstrap&&!plain_name(names.bootstrap,255))){error(result,"Invalid root, event or bootstrap module name");goto failure;}
    total_limit=options->maximum_total_bytes?options->maximum_total_bytes:64u*1024u*1024u;
    source_limit=options->maximum_source_bytes?options->maximum_source_bytes:16u*1024u*1024u;
    phase(result,"manifest");
    if(measure(io,"modules/modules.tsv",1024u*1024u,total_limit,&total,&manifest_length,result))goto failure;
    manifest=read_bytes(io,"modules/modules.tsv",manifest_length,result);if(!manifest)goto failure;
    entries=(entry*)calloc(4096,sizeof(*entries));if(!entries){error(result,"Manifest entry allocation failed");goto failure;}
    if(parse_manifest(manifest,manifest_length,entries,&count,result))goto failure;
    phase(result,"preflight");
    for(i=0;i<5;i++) {
        core[i].name=core_names[i];snprintf(path,sizeof(path),"runtime/%s",core_names[i]);
        if(measure(io,path,source_limit,total_limit,&total,&core[i].length,result))goto failure;
    }
    for(i=0;i<count;i++) {
        snprintf(path,sizeof(path),"modules/%s",entries[i].file);
        if(measure(io,path,source_limit,total_limit,&total,&entries[i].length,result))goto failure;
    }
    phase(result,"initialize");
    for(i=0;i<5;i++) {
        snprintf(path,sizeof(path),"runtime/%s",core_names[i]);core[i].data=read_bytes(io,path,core[i].length,result);
        if(!core[i].data)goto failure;
    }
    config.runtime_sources=core;config.runtime_source_count=5;
    config.instruction_budget=options->instruction_budget;config.memory_limit_bytes=options->lua_memory_limit;
    runtime=amalur_runtime_create(&config,result->error,sizeof(result->error));
    for(i=0;i<5;i++){free((void*)core[i].data);core[i].data=NULL;}
    if(!runtime)goto failure;
    if(options->setup) {
        setup_call call={runtime,options,result};phase(result,"host_setup");
        status=lua_cpcall(amalur_runtime_state(runtime),invoke_setup,&call);
        if(status){L=amalur_runtime_state(runtime);error(result,lua_type(L,-1)==LUA_TSTRING?lua_tostring(L,-1):"Non-string Lua host setup error");goto failure;}
    }
    phase(result,"register");
    for(i=0;i<count;i++) {
        snprintf(path,sizeof(path),"modules/%s",entries[i].file);data=read_bytes(io,path,entries[i].length,result);if(!data)goto failure;
        status=amalur_runtime_register_module_source_lazy(runtime,entries[i].name,data,entries[i].length,result->error,sizeof(result->error));
        free(data);data=NULL;if(status)goto failure;++result->registered_modules;
    }
    free(entries);entries=NULL;free(manifest);manifest=NULL;
    phase(result,"entry_setup");L=amalur_runtime_state(runtime);status=lua_cpcall(L,set_requested_names,&names);
    if(status){error(result,lua_type(L,-1)==LUA_TSTRING?lua_tostring(L,-1):"Non-string Lua entry setup error");goto failure;}
    if(names.bootstrap) {
        const char *code="return require(__opem_scene_bootstrap)";
        phase(result,"preload");status=amalur_runtime_eval_source(runtime,code,strlen(code),"scene-bootstrap-load",&results,result->error,sizeof(result->error));
        if(status)goto failure;result->bootstrap_loaded=1;
    }
    phase(result,"require");
    {const char *code="return require(__opem_scene_root)";
     status=amalur_runtime_eval_source(runtime,code,strlen(code),"scene-root-load",&results,result->error,sizeof(result->error));}
    if(status)goto failure;result->root_loaded=1;
    if(names.event) {
        const char *code="local m=require(__opem_scene_root); local f=m[__opem_scene_event]; if type(f)~='function' then error('Requested scene event does not exist') end; return f()";
        phase(result,"event");status=amalur_runtime_eval_source(runtime,code,strlen(code),"scene-zero-argument-event",&results,result->error,sizeof(result->error));
        if(status)goto failure;result->event_invoked=1;
    }
    result->lua_memory_bytes=amalur_runtime_memory_used(runtime);result->ok=1;phase(result,"complete");return runtime;
failure:
    free(data);free(entries);free(manifest);
    for(i=0;i<5;i++)free((void*)core[i].data);
    if(runtime){result->lua_memory_bytes=amalur_runtime_memory_used(runtime);amalur_runtime_destroy(runtime);}
    return NULL;
}
