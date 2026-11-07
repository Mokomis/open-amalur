#include "amalur_runtime.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <float.h>

static void json_string(const char *s, size_t n) {
    size_t i; unsigned char c; putchar('"');
    for(i=0;i<n;i++) {
        c=(unsigned char)s[i];
        if(c=='"'||c=='\\'){putchar('\\');putchar(c);}
        else if(c>=32 && c<127)putchar(c);
        else printf("\\u%04x",(unsigned)c);
    }
    putchar('"');
}
static void result(lua_State *L,int index) {
    int type=lua_type(L,index);size_t n;const char *s;lua_Number value;
    switch(type) {
    case LUA_TNIL:printf("{\"type\":\"nil\"}");break;
    case LUA_TBOOLEAN:printf("{\"type\":\"boolean\",\"value\":%s}",lua_toboolean(L,index)?"true":"false");break;
    case LUA_TNUMBER:
        value=lua_tonumber(L,index);printf("{\"type\":\"number\",\"value\":");
        if(value==value && value<=DBL_MAX && value>=-DBL_MAX)printf("%.17g",(double)value);
        else printf("null");
        printf("}");break;
    case LUA_TSTRING:
        s=lua_tolstring(L,index,&n);printf("{\"type\":\"string\",\"bytes\":%lu,\"value\":",(unsigned long)n);json_string(s,n);printf("}");break;
    case LUA_TUSERDATA:
        lua_getglobal(L,"__amalur_uint64");lua_getfield(L,-1,"hex");lua_remove(L,-2);lua_pushvalue(L,index);
        if(lua_pcall(L,1,1,0)==0 && lua_type(L,-1)==LUA_TSTRING) {
            s=lua_tolstring(L,-1,&n);printf("{\"type\":\"amalur-type11\",\"hex\":");json_string(s,n);printf("}");
        } else printf("{\"type\":\"userdata\"}");
        lua_pop(L,1);break;
    default:printf("{\"type\":");s=lua_typename(L,type);json_string(s,strlen(s));printf("}");break;
    }
}
static int unsigned_value(const char *text,uint64_t *value) {
    char *end;unsigned long long parsed;
    if(!*text || *text=='-')return 0;
    errno=0;parsed=strtoull(text,&end,10);
    if(errno || *end || !parsed)return 0;
    *value=(uint64_t)parsed;return 1;
}
static void usage(void) {
    fprintf(stderr,"Usage: amalur-script --runtime-dir DIR [--budget INSTRUCTIONS] [--memory-limit BYTES] SCRIPT.lua\n");
}
int main(int argc,char **argv) {
    amalur_runtime_config config={0};amalur_runtime *runtime;
    const char *script=NULL;char error[2048];int i,count=0,status;uint64_t value;
    for(i=1;i<argc;i++) {
        if(!strcmp(argv[i],"--runtime-dir") && i+1<argc)config.runtime_dir=argv[++i];
        else if(!strcmp(argv[i],"--budget") && i+1<argc) {
            if(!unsigned_value(argv[++i],&config.instruction_budget)){usage();return 2;}
        } else if(!strcmp(argv[i],"--memory-limit") && i+1<argc) {
            if(!unsigned_value(argv[++i],&value) || value>(uint64_t)(size_t)-1){usage();return 2;}
            config.memory_limit_bytes=(size_t)value;
        } else if(argv[i][0]=='-' || script){usage();return 2;} else script=argv[i];
    }
    if(!config.runtime_dir || !script){usage();return 2;}
    runtime=amalur_runtime_create(&config,error,sizeof(error));
    if(!runtime) {printf("{\"ok\":false,\"phase\":\"initialize\",\"error\":");json_string(error,strlen(error));puts("}");return 1;}
    status=amalur_runtime_eval_file(runtime,script,&count,error,sizeof(error));
    if(status){printf("{\"ok\":false,\"phase\":\"evaluate\",\"error\":");json_string(error,strlen(error));puts("}");}
    else {
        printf("{\"ok\":true,\"lua_version\":\"5.1.5\",\"pointer_bits\":%u,\"result_count\":%d,\"results\":[",(unsigned)(sizeof(void*)*8),count);
        for(i=1;i<=count;i++){if(i>1)putchar(',');result(amalur_runtime_state(runtime),i);}
        printf("],\"lua_memory_bytes\":%lu}\n",(unsigned long)amalur_runtime_memory_used(runtime));
    }
    amalur_runtime_destroy(runtime);return status?1:0;
}
