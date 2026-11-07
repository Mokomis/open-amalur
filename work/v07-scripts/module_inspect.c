#include "amalur_runtime.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void json_string(const char *s) {
    const unsigned char *p=(const unsigned char*)s;putchar('"');
    while(*p){if(*p=='"'||*p=='\\'){putchar('\\');putchar(*p);}
        else if(*p>=32&&*p<127)putchar(*p);else printf("\\u%04x",*p);++p;}
    putchar('"');
}
static int loaded_count(lua_State *L) {
    int count=0;lua_getfield(L,LUA_REGISTRYINDEX,"_LOADED");lua_pushnil(L);
    while(lua_next(L,-2)){++count;lua_pop(L,1);}lua_pop(L,1);return count;
}
static int manifest(amalur_runtime *r,const char *filename,int lazy,char *error,size_t cap) {
    char line[8192],path[16384],*tab,*end;FILE *f;size_t prefix=0,n;unsigned number=0;
    const char *p;
    for(p=filename;*p;p++)if(*p=='/'||*p=='\\')prefix=(size_t)(p-filename)+1;
    if(prefix>=sizeof(path)){snprintf(error,cap,"Manifest path too long");return 1;}
    f=fopen(filename,"rb");if(!f){snprintf(error,cap,"Cannot open module manifest");return 1;}
    while(fgets(line,sizeof(line),f)) {
        ++number;n=strlen(line);
        if(n==sizeof(line)-1&&line[n-1]!='\n'){snprintf(error,cap,"Manifest line %u too long",number);fclose(f);return 1;}
        while(n&&(line[n-1]=='\n'||line[n-1]=='\r'))line[--n]=0;
        if(!n||line[0]=='#')continue;
        tab=strchr(line,'\t');
        if(!tab||tab==line||!tab[1]||strchr(tab+1,'\t')){snprintf(error,cap,"Invalid module manifest line %u",number);fclose(f);return 1;}
        *tab++=0;
        if(!strcmp(tab,".")||!strcmp(tab,"..")||strchr(tab,'/')||strchr(tab,'\\')||strchr(tab,':')) {
            snprintf(error,cap,"Module source must be a manifest-local basename on line %u",number);fclose(f);return 1;
        }
        end=tab+strlen(tab);if(prefix+(size_t)(end-tab)>=sizeof(path)){snprintf(error,cap,"Module file path too long");fclose(f);return 1;}
        memcpy(path,filename,prefix);strcpy(path+prefix,tab);
        if((lazy?amalur_runtime_register_module_file_lazy(r,line,path,error,cap):amalur_runtime_register_module_file(r,line,path,error,cap))){fclose(f);return 1;}
    }
    if(ferror(f)){snprintf(error,cap,"Module manifest read failed");fclose(f);return 1;}
    fclose(f);return 0;
}
int main(int argc,char **argv) {
    amalur_runtime_config config={0};amalur_runtime *r;lua_State *L;
    const char *file=NULL,*name=NULL,*event=NULL;char error[2048];int i,status,count=0,lazy=0;
    const char *phase="initialize";
    for(i=1;i<argc;i++) {
        if(!strcmp(argv[i],"--runtime-dir")&&i+1<argc)config.runtime_dir=argv[++i];
        else if(!strcmp(argv[i],"--manifest")&&i+1<argc)file=argv[++i];
        else if(!strcmp(argv[i],"--module")&&i+1<argc)name=argv[++i];
        else if(!strcmp(argv[i],"--event")&&i+1<argc)event=argv[++i];
        else if(!strcmp(argv[i],"--lazy"))lazy=1;
        else {fprintf(stderr,"Unknown or incomplete argument\n");return 2;}
    }
    if(!config.runtime_dir||!file||!name){fprintf(stderr,"amalur-module-inspect --runtime-dir DIR --manifest FILE --module NAME [--event NAME]\n");return 2;}
    r=amalur_runtime_create(&config,error,sizeof(error));
    if(!r){printf("{\"ok\":false,\"phase\":\"initialize\",\"error\":");json_string(error);puts("}");return 1;}
    L=amalur_runtime_state(r);phase="register";status=manifest(r,file,lazy,error,sizeof(error));
    if(!status) {
        lua_pushstring(L,name);lua_setglobal(L,"__opem_requested_module");
        if(event){lua_pushstring(L,event);lua_setglobal(L,"__opem_requested_event");}
        phase=event?"event":"require";
        {const char *source=event?
            "local m=require(__opem_requested_module); local f=m[__opem_requested_event]; if type(f)~='function' then error('Requested event does not exist') end; return f()":
            "return require(__opem_requested_module)";
         status=amalur_runtime_eval_source(r,source,strlen(source),"explicit-module-entry",&count,error,sizeof(error));}
    }
    printf("{\"ok\":%s,\"phase\":",status?"false":"true");json_string(phase);
    printf(",\"module\":");json_string(name);printf(",\"loaded_entries\":%d,\"result_count\":%d",loaded_count(L),count);
    printf(",\"lazy_registration\":%s,\"memory_used_bytes\":%lu",lazy?"true":"false",(unsigned long)amalur_runtime_memory_used(r));
    if(event){printf(",\"event\":");json_string(event);printf(",\"event_argument_count\":0");}
    if(status){printf(",\"error\":");json_string(error);}
    printf(",\"scope\":\"portable recovered-source loading; engine behavior not implemented\"}\n");
    amalur_runtime_destroy(r);return status?1:0;
}
