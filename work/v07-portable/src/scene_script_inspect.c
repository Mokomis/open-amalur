#include "scene_script_bootstrap.h"
#include "scene_asset_keys.h"
#include "scene_profile.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef struct directories {const char *runtime,*modules;} directories;
typedef struct input_actions_snapshot {char *bytes;size_t length;const char *profile_sha256;} input_actions_snapshot;
static int parse_instruction_budget(const char *text,uint64_t *budget){
    const unsigned char *p=(const unsigned char*)text;uint64_t value=0;
    if(!*p)return 0;
    for(;*p;p++){
        unsigned digit;if(*p<'0'||*p>'9')return 0;digit=(unsigned)(*p-'0');
        if(value>(100000000u-digit)/10u)return 0;
        value=value*10u+digit;
    }
    if(!value)return 0;*budget=value;return 1;
}
static int input_actions_setup(amalur_runtime *runtime,void *context,char *error,size_t cap){
    input_actions_snapshot *snapshot=(input_actions_snapshot*)context;
    int status;
    if(snapshot->profile_sha256){status=scene_profile_install(runtime,snapshot->profile_sha256,error,cap);if(status)return status;}
    return snapshot->bytes?scene_asset_keys_install(runtime,snapshot->bytes,snapshot->length,error,cap):0;
}
static int read_input_actions(const char *path,input_actions_snapshot *snapshot,char *error,size_t cap){
    FILE *file=fopen(path,"rb");long length;
    if(!file){snprintf(error,cap,"Cannot open input action snapshot");return 1;}
    if(fseek(file,0,SEEK_END)||(length=ftell(file))<0||fseek(file,0,SEEK_SET)){
        fclose(file);snprintf(error,cap,"Cannot size input action snapshot");return 1;
    }
    if(length>524296){fclose(file);snprintf(error,cap,"Input action snapshot exceeds524296-byte limit");return 1;}
    snapshot->bytes=(char*)malloc((size_t)length+1);
    if(!snapshot->bytes){fclose(file);snprintf(error,cap,"Input action snapshot allocation failed");return 1;}
    if(fread(snapshot->bytes,1,(size_t)length,file)!=(size_t)length||fgetc(file)!=EOF||ferror(file)){
        fclose(file);free(snapshot->bytes);snapshot->bytes=NULL;snprintf(error,cap,"Input action snapshot read incomplete or size changed");return 1;
    }
    fclose(file);snapshot->length=(size_t)length;return 0;
}
static int open_resource(void *context,const char *logical,FILE **file,size_t *length,char *error,size_t cap) {
    directories *dirs=(directories*)context;const char *dir,*basename;char path[4096];long size;
    if(!strncmp(logical,"runtime/",8)){dir=dirs->runtime;basename=logical+8;}
    else if(!strncmp(logical,"modules/",8)){dir=dirs->modules;basename=logical+8;}
    else{snprintf(error,cap,"Unknown resource category");return 1;}
    if(strlen(dir)+strlen(basename)+2>sizeof(path)){snprintf(error,cap,"Resource path too long");return 1;}
    snprintf(path,sizeof(path),"%s/%s",dir,basename);*file=fopen(path,"rb");
    if(!*file){snprintf(error,cap,"Cannot open resource: %s",logical);return 1;}
    if(fseek(*file,0,SEEK_END)||(size=ftell(*file))<0||fseek(*file,0,SEEK_SET)){
        fclose(*file);*file=NULL;snprintf(error,cap,"Cannot size resource: %s",logical);return 1;
    }
    *length=(size_t)size;return 0;
}
static int resource_size(void *context,const char *path,size_t *length,char *error,size_t cap) {
    FILE *file=NULL;if(open_resource(context,path,&file,length,error,cap))return 1;fclose(file);return 0;
}
static int resource_read(void *context,const char *path,char *data,size_t length,char *error,size_t cap) {
    FILE *file=NULL;size_t actual;
    if(open_resource(context,path,&file,&actual,error,cap))return 1;
    if(actual!=length){fclose(file);snprintf(error,cap,"Resource size changed: %s",path);return 1;}
    if(fread(data,1,length,file)!=length){fclose(file);snprintf(error,cap,"Incomplete resource read: %s",path);return 1;}
    fclose(file);return 0;
}
static void json_string(const char *text) {
    const unsigned char *p=(const unsigned char*)text;putchar('"');
    for(;*p;p++){if(*p=='"'||*p=='\\'){putchar('\\');putchar(*p);}else if(*p>=32&&*p<127)putchar(*p);else printf("\\u%04x",*p);}putchar('"');
}
int main(int argc,char **argv) {
    directories dirs={0};scene_script_resources resources={0};scene_script_options options={0};scene_script_result result={0};amalur_runtime *runtime=NULL;int i;
    input_actions_snapshot snapshot={0};const char *input_actions=NULL;
    for(i=1;i<argc;i++) {
        if(!strcmp(argv[i],"--runtime-dir")&&i+1<argc)dirs.runtime=argv[++i];
        else if(!strcmp(argv[i],"--modules-dir")&&i+1<argc)dirs.modules=argv[++i];
        else if(!strcmp(argv[i],"--module")&&i+1<argc)options.root_module=argv[++i];
        else if(!strcmp(argv[i],"--event")&&i+1<argc)options.event=argv[++i];
        else if(!strcmp(argv[i],"--input-actions")&&i+1<argc)input_actions=argv[++i];
        else if(!strcmp(argv[i],"--native-profile")&&i+1<argc)snapshot.profile_sha256=argv[++i];
        else if(!strcmp(argv[i],"--instruction-budget")&&i+1<argc){
            if(!parse_instruction_budget(argv[++i],&options.instruction_budget)){fprintf(stderr,"Instruction budget must be an integer1..100000000\n");return 2;}
        }
        else if(!strcmp(argv[i],"--memory-mib")&&i+1<argc){
            char *end;unsigned long value=strtoul(argv[++i],&end,10);
            if(!*argv[i]||*end||value<1||value>1024){fprintf(stderr,"Memory cap must be1..1024MiB\n");return 2;}
            options.lua_memory_limit=(size_t)value*1024u*1024u;
        }
        else {fprintf(stderr,"Invalid argument\n");return 2;}
    }
    if(!dirs.runtime||!dirs.modules){fprintf(stderr,"scene_script_inspect --runtime-dir DIR --modules-dir DIR [--module NAME] [--event NAME] [--memory-mib N] [--input-actions FILE] [--native-profile SHA256] [--instruction-budget N]\n");return 2;}
    if(input_actions){
        strcpy(result.phase,"input_actions");
        if(read_input_actions(input_actions,&snapshot,result.error,sizeof(result.error)))goto report;
    }
    if(input_actions||snapshot.profile_sha256){options.setup=input_actions_setup;options.setup_context=&snapshot;}
    resources.context=&dirs;resources.size=resource_size;resources.read=resource_read;
    runtime=scene_script_bootstrap(&resources,&options,&result);
report:
    free(snapshot.bytes);
    printf("{\"ok\":%s,\"phase\":",result.ok?"true":"false");json_string(result.phase);
    printf(",\"instruction_budget\":%lu",(unsigned long)(options.instruction_budget?options.instruction_budget:1000000u));
    printf(",\"root_loaded\":%s,\"event_invoked\":%s,\"event_argument_count\":%d,\"registered_modules\":%u,\"resource_bytes\":%lu,\"lua_memory_bytes\":%lu,\"error\":",result.root_loaded?"true":"false",result.event_invoked?"true":"false",result.event_argument_count,result.registered_modules,(unsigned long)result.resource_bytes,(unsigned long)result.lua_memory_bytes);
    json_string(result.error);puts(",\"scope\":\"portable recovered module loading; no native behavior equivalence\"}");
    amalur_runtime_destroy(runtime);return result.ok?0:1;
}
