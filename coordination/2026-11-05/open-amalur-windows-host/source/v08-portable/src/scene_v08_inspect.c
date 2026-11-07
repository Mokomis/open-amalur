#include "scene_script_bootstrap.h"
#include "scene_asset_keys.h"
#include "scene_asset_macros_v08.h"
#include "scene_profile_v08.h"
#include "scene_enums_v08.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef struct directories {const char *runtime,*modules;} directories;
typedef struct macro_snapshot {const char *name,*path;uint32_t category;char *bytes;size_t length;} macro_snapshot;
typedef struct input_actions_snapshot {char *bytes;size_t length;char *enum_bytes;size_t enum_length;const char *profile_sha256;scene_controller_state_v08 controller;int no_optional_content,android_platform,fresh_profile,no_quick_save,no_language_packs,preview_renderer;macro_snapshot macros[32];unsigned macro_count;} input_actions_snapshot;
static int parse_category(const char *text,uint32_t *category){
    const unsigned char *p=(const unsigned char*)text;uint32_t value=0,base=10;
    if(p[0]=='0'&&(p[1]=='x'||p[1]=='X')){base=16;p+=2;}if(!*p)return 0;
    for(;*p;p++){
        uint32_t digit;if(*p>='0'&&*p<='9')digit=*p-'0';else if(*p>='a'&&*p<='f')digit=*p-'a'+10;else if(*p>='A'&&*p<='F')digit=*p-'A'+10;else return 0;
        if(digit>=base||value>(255u-digit)/base)return 0;value=value*base+digit;
    }
    if(!value)return 0;*category=value;return 1;
}
static int parse_controller_kind(const char *text,int32_t *kind){
    const unsigned char *p=(const unsigned char*)text;uint64_t value=0,limit;int negative=0;
    if(*p=='-'){negative=1;++p;}if(!*p)return 0;limit=negative?2147483648u:2147483647u;
    for(;*p;p++){
        unsigned digit;if(*p<'0'||*p>'9')return 0;digit=(unsigned)(*p-'0');
        if(value>(limit-digit)/10u)return 0;value=value*10u+digit;
    }
    *kind=negative?(value==2147483648u?INT32_MIN:-(int32_t)value):(int32_t)value;return 1;
}
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
    int status;unsigned i;
    if(snapshot->profile_sha256){scene_profile_v08_options profile={0};profile.target_sha256=snapshot->profile_sha256;profile.controller=snapshot->controller;profile.content.is_set=snapshot->no_optional_content;profile.platform.is_set=snapshot->android_platform;profile.platform.name_hash=2096549;profile.fresh_profile=snapshot->fresh_profile;profile.no_language_packs=snapshot->no_language_packs;profile.max_anisotropy=snapshot->preview_renderer?1:0;profile.quick_save.is_set=snapshot->no_quick_save;status=scene_profile_v08_install(runtime,&profile,error,cap);if(status)return status;}
    if(snapshot->bytes){status=scene_asset_keys_install(runtime,snapshot->bytes,snapshot->length,error,cap);if(status)return status;}
    if(snapshot->enum_bytes){status=scene_enums_v08_install(runtime,snapshot->enum_bytes,snapshot->enum_length,error,cap);if(status)return status;}
    for(i=0;i<snapshot->macro_count;i++){
        macro_snapshot *macro=&snapshot->macros[i];
        status=scene_asset_macro_v08_install(runtime,macro->name,macro->category,macro->bytes,macro->length,error,cap);if(status)return status;
    }
    return 0;
}
static int read_asset_snapshot(const char *path,char **bytes,size_t *size,size_t remaining,size_t maximum,char *error,size_t cap){
    FILE *file=fopen(path,"rb");long length;
    if(!file){snprintf(error,cap,"Cannot open asset snapshot");return 1;}
    if(fseek(file,0,SEEK_END)||(length=ftell(file))<0||fseek(file,0,SEEK_SET)){
        fclose(file);snprintf(error,cap,"Cannot size asset snapshot");return 1;
    }
    if((size_t)length>maximum){fclose(file);snprintf(error,cap,"Asset snapshot exceeds%lu-byte limit",(unsigned long)maximum);return 1;}
    if((size_t)length>remaining){fclose(file);snprintf(error,cap,"Asset snapshots exceed16MiB total byte limit");return 1;}
    *bytes=(char*)malloc((size_t)length+1);
    if(!*bytes){fclose(file);snprintf(error,cap,"Asset snapshot allocation failed");return 1;}
    if(fread(*bytes,1,(size_t)length,file)!=(size_t)length||fgetc(file)!=EOF||ferror(file)){
        fclose(file);free(*bytes);*bytes=NULL;snprintf(error,cap,"Asset snapshot read incomplete or size changed");return 1;
    }
    fclose(file);*size=(size_t)length;return 0;
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
    input_actions_snapshot snapshot={0};const char *input_actions=NULL,*enums=NULL;unsigned macro_index;size_t snapshot_bytes=0;
    for(i=1;i<argc;i++) {
        if(!strcmp(argv[i],"--runtime-dir")&&i+1<argc)dirs.runtime=argv[++i];
        else if(!strcmp(argv[i],"--modules-dir")&&i+1<argc)dirs.modules=argv[++i];
        else if(!strcmp(argv[i],"--module")&&i+1<argc)options.root_module=argv[++i];
        else if(!strcmp(argv[i],"--bootstrap-module")&&i+1<argc)options.bootstrap_module=argv[++i];
        else if(!strcmp(argv[i],"--event")&&i+1<argc)options.event=argv[++i];
        else if(!strcmp(argv[i],"--enums")&&i+1<argc)enums=argv[++i];
        else if(!strcmp(argv[i],"--input-actions")&&i+1<argc)input_actions=argv[++i];
        else if(!strcmp(argv[i],"--loot-tables")&&i+1<argc){
            macro_snapshot *macro;if(snapshot.macro_count>=32){fprintf(stderr,"At most32 asset macros are allowed, including --loot-tables\n");return 2;}
            macro=&snapshot.macros[snapshot.macro_count++];macro->name="LOOT_TABLE_ID";macro->category=0x37;macro->path=argv[++i];
        }
        else if(!strcmp(argv[i],"--asset-macro")&&i+3<argc){
            macro_snapshot *macro;if(snapshot.macro_count>=32){fprintf(stderr,"At most32 asset macros are allowed, including --loot-tables\n");return 2;}
            macro=&snapshot.macros[snapshot.macro_count++];macro->name=argv[++i];
            if(!parse_category(argv[++i],&macro->category)){fprintf(stderr,"Asset category must be decimal or0x-prefixed hexadecimal1..255\n");return 2;}
            macro->path=argv[++i];
        }
        else if(!strcmp(argv[i],"--native-profile")&&i+1<argc)snapshot.profile_sha256=argv[++i];
        else if(!strcmp(argv[i],"--preview-renderer"))snapshot.preview_renderer=1;
        else if(!strcmp(argv[i],"--no-language-packs"))snapshot.no_language_packs=1;
        else if(!strcmp(argv[i],"--no-quick-save"))snapshot.no_quick_save=1;
        else if(!strcmp(argv[i],"--fresh-profile"))snapshot.fresh_profile=1;
        else if(!strcmp(argv[i],"--android-platform"))snapshot.android_platform=1;
        else if(!strcmp(argv[i],"--no-optional-content"))snapshot.no_optional_content=1;
        else if(!strcmp(argv[i],"--android-standard-layout")){if(snapshot.controller.is_set){fprintf(stderr,"Choose one controller-state option\n");return 2;}snapshot.controller.is_set=1;snapshot.controller.domain=SCENE_CONTROLLER_DOMAIN_ANDROID_LOGICAL_STANDARD;}
        else if(!strcmp(argv[i],"--controller-kind")&&i+1<argc){
            if(snapshot.controller.is_set){fprintf(stderr,"Choose one controller-state option\n");return 2;}
            if(!parse_controller_kind(argv[++i],&snapshot.controller.native_device_kind)){fprintf(stderr,"Controller fixture kind must be a signed-int32 decimal integer\n");return 2;}
            snapshot.controller.is_set=1;
        }
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
    if(!dirs.runtime||!dirs.modules){fprintf(stderr,"scene_v08_inspect --runtime-dir DIR --modules-dir DIR [--module NAME] [--bootstrap-module NAME] [--event NAME] [--memory-mib N] [--enums FILE] [--input-actions FILE] [--loot-tables FILE] [--asset-macro NAME CATEGORY FILE]... [--native-profile SHA256] [--controller-kind SIGNED_INT32] [--instruction-budget N]\n");return 2;}
    if((snapshot.controller.is_set||snapshot.no_optional_content||snapshot.android_platform||snapshot.fresh_profile||snapshot.no_quick_save||snapshot.no_language_packs||snapshot.preview_renderer)&&!snapshot.profile_sha256){fprintf(stderr,"Controller fixture requires explicit --native-profile SHA256\n");return 2;}
    if(input_actions){
        strcpy(result.phase,"input_actions");
        if(read_asset_snapshot(input_actions,&snapshot.bytes,&snapshot.length,16u*1024u*1024u,524296u,result.error,sizeof(result.error)))goto report;
        snapshot_bytes+=snapshot.length;
    }
    if(enums){
        strcpy(result.phase,"enums");
        if(read_asset_snapshot(enums,&snapshot.enum_bytes,&snapshot.enum_length,16u*1024u*1024u-snapshot_bytes,SCENE_ENUMS_V08_MAX_BYTES,result.error,sizeof(result.error)))goto report;
        snapshot_bytes+=snapshot.enum_length;
    }
    for(macro_index=0;macro_index<snapshot.macro_count;macro_index++){
        macro_snapshot *macro=&snapshot.macros[macro_index];strcpy(result.phase,"asset_macros");
        if(read_asset_snapshot(macro->path,&macro->bytes,&macro->length,16u*1024u*1024u-snapshot_bytes,524296u,result.error,sizeof(result.error)))goto report;
        snapshot_bytes+=macro->length;
    }
    if(enums||input_actions||snapshot.macro_count||snapshot.profile_sha256){options.setup=input_actions_setup;options.setup_context=&snapshot;}
    resources.context=&dirs;resources.size=resource_size;resources.read=resource_read;
    options.maximum_total_bytes=128u*1024u*1024u;
    runtime=scene_script_bootstrap(&resources,&options,&result);
report:
    free(snapshot.bytes);free(snapshot.enum_bytes);
    for(macro_index=0;macro_index<snapshot.macro_count;macro_index++)free(snapshot.macros[macro_index].bytes);
    printf("{\"ok\":%s,\"phase\":",result.ok?"true":"false");json_string(result.phase);
    printf(",\"instruction_budget\":%lu",(unsigned long)(options.instruction_budget?options.instruction_budget:1000000u));
    printf(",\"lua_memory_limit_bytes\":%lu,\"resource_limit_bytes\":%lu",(unsigned long)options.lua_memory_limit,(unsigned long)options.maximum_total_bytes);
    printf(",\"asset_macro_count\":%u,\"asset_snapshot_bytes\":%lu",snapshot.macro_count,(unsigned long)snapshot_bytes);
    printf(",\"controller_state_mode\":\"%s\"",snapshot.controller.is_set?(snapshot.controller.domain==SCENE_CONTROLLER_DOMAIN_ANDROID_LOGICAL_STANDARD?"android-logical-standard":"native-kind-fixture"):"unset");
    printf(",\"optional_content_mode\":\"%s\"",snapshot.no_optional_content?"known-empty":"unset");
    printf(",\"platform_mode\":\"%s\"",snapshot.android_platform?"android":"unset");
    printf(",\"profile_mode\":\"%s\"",snapshot.fresh_profile?"fresh-session-memory":"unset");
    printf(",\"quick_save_mode\":\"%s\"",snapshot.no_quick_save?"unsupported":"unset");
    printf(",\"language_catalog_mode\":\"%s\",\"renderer_max_anisotropy\":%d",snapshot.no_language_packs?"known-empty-host-Automatic":"unset",snapshot.preview_renderer?1:0);
    printf(",\"bootstrap_loaded\":%s",result.bootstrap_loaded?"true":"false");
    if(snapshot.controller.is_set&&snapshot.controller.domain==SCENE_CONTROLLER_DOMAIN_NATIVE_KIND)printf(",\"controller_kind\":%ld",(long)snapshot.controller.native_device_kind);
    printf(",\"root_loaded\":%s,\"event_invoked\":%s,\"event_argument_count\":%d,\"registered_modules\":%u,\"resource_bytes\":%lu,\"lua_memory_bytes\":%lu,\"error\":",result.root_loaded?"true":"false",result.event_invoked?"true":"false",result.event_argument_count,result.registered_modules,(unsigned long)result.resource_bytes,(unsigned long)result.lua_memory_bytes);
    json_string(result.error);puts(",\"scope\":\"portable recovered module loading; no native behavior equivalence\"}");
    amalur_runtime_destroy(runtime);return result.ok?0:1;
}
