/* Actual production C/Lua runtime; acknowledged HOST BACKEND IS SIMULATED. */
#include "oa_opening_runtime.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef struct fixture {const char *root;int corrupt,equipped,gateway,known,stage,enabled,reject,bad;unsigned effects,autosaves,modals,compare,reentry;oa_opening_runtime *self;} fixture;
static unsigned checks;
#define CHECK(x) do{checks++;if(!(x)){fprintf(stderr,"FAIL line%d %s: %s\n",__LINE__,#x,e);return 1;}}while(0)
static int sz(void*v,const char*n,size_t*out,char*e,size_t c){fixture*f=v;char p[2048];FILE*h;long k;snprintf(p,sizeof(p),"%s/%s",f->root,n);h=fopen(p,"rb");if(!h){snprintf(e,c,"missing fixture asset");return 1;}if(fseek(h,0,SEEK_END)||(k=ftell(h))<0){fclose(h);return 1;}fclose(h);*out=(size_t)k;return 0;}
static int rd(void*v,const char*n,void*out,size_t z,char*e,size_t c){fixture*f=v;char p[2048];FILE*h;int ok;snprintf(p,sizeof(p),"%s/%s",f->root,n);h=fopen(p,"rb");if(!h)return 1;ok=fread(out,1,z,h)==z&&fgetc(h)==EOF&&!ferror(h);fclose(h);if(!ok){snprintf(e,c,"fixture size changed");return 1;}if(f->corrupt&&strstr(n,"Sword_WoS_InitialWeapon/functions/function_0_0.lua"))((unsigned char*)out)[z-1]^=1;return 0;}
static int query(void*v,enum oa_opening_query q,int32_t a,int*out,char*e,size_t c){fixture*f=v;(void)e;(void)c;if(f->bad){*out=2;return 0;}switch(q){case OA_OPENING_IS_EQUIPPED:if(a!=7)return 1;*out=f->equipped;break;case OA_OPENING_GATEWAY_OPEN:if(a!=1790948)return 1;*out=f->gateway;break;case OA_OPENING_TUTORIALS_ENABLED:*out=f->enabled;break;case OA_OPENING_TUTORIAL_FIRED:case OA_OPENING_TUTORIAL_ACTIVE:*out=0;break;default:return 1;}return 0;}
static int stage(void*v,uint32_t id,int32_t*out,char*e,size_t c){fixture*f=v;if(f->known==2)return 0;if(id!=613083||!f->known){snprintf(e,c,"fixture quest stage unknown");return 1;}*out=f->stage;return 0;}
static int apply(void*v,const oa_opening_effect*a,size_t n,const oa_opening_snapshot*s,char*e,size_t c){fixture*f=v;size_t i;if(f->reject){snprintf(e,c,"fixture service unavailable");return 1;}
 for(i=0;i<n;i++)if(a[i].kind<1||a[i].kind>7||!a[i].source_callback||(a[i].kind==OA_OPENING_AUTOSAVE_REQUEST&&!(s->wos_flags&(1u<<11)))){snprintf(e,c,"fixture effect invalid");return 1;}
 for(i=0;i<n;i++){f->effects++;switch(a[i].kind){case OA_OPENING_OPEN_GATEWAY:f->gateway=1;break;case OA_OPENING_SET_STAGE:f->stage=a[i].args[1];break;case OA_OPENING_AUTOSAVE_REQUEST:f->autosaves++;break;case OA_OPENING_MODAL_TUTORIAL:f->modals++;break;case OA_OPENING_COMPARE_ENABLED:f->compare++;break;default:break;}}
 if(f->self){oa_opening_snapshot x;char err[128];if(oa_opening_runtime_snapshot(f->self,&x,err,sizeof(err))&&strstr(err,"reentry"))f->reentry++;}return 0;}
static void warn(void*v,const char*s){(void)v;fprintf(stderr,"fixture warning:%s\n",s);}
static void reset(fixture*f,const char*root){memset(f,0,sizeof(*f));f->root=root;f->known=1;f->stage=5;f->enabled=1;}
static oa_opening_runtime *create(fixture*f,uint64_t budget,size_t memory,char*e,size_t c){oa_opening_assets a={f,sz,rd};oa_opening_host h={f,"scene1417252:player1:g1",query,stage,apply,warn};oa_opening_runtime_config k={memory,budget};return oa_opening_runtime_create_from_assets(&a,&h,&k,e,c);}
int main(int argc,char**argv){fixture f;oa_opening_runtime*o;oa_opening_snapshot s,before,after;oa_opening_runtime_stats stats;char e[1024]="";unsigned i;const char*who="scene1417252:player1:g1";if(argc!=2)return 2;
 reset(&f,argv[1]);o=create(&f,200000,64u*1024u*1024u,e,sizeof(e));CHECK(o);f.self=o;
 CHECK(!oa_opening_runtime_volume_exit(o,"Tutorial_Volume_Move",who,e,sizeof(e))&&f.effects==0);
 CHECK(oa_opening_runtime_cinematic_finished(o,2,e,sizeof(e))!=0);CHECK(!oa_opening_runtime_cinematic_finished(o,1,e,sizeof(e)));
 CHECK(!oa_opening_runtime_volume_exit(o,"Tutorial_Volume_Move","scene1417252:player1:g0",e,sizeof(e))&&f.effects==0);
 CHECK(!oa_opening_runtime_volume_exit(o,"unknown",who,e,sizeof(e))&&f.effects==0);
 CHECK(!oa_opening_runtime_volume_exit(o,"Tutorial_Volume_Move",who,e,sizeof(e)));CHECK(f.autosaves==1&&f.effects==3&&f.reentry==1);
 CHECK(!oa_opening_runtime_volume_exit(o,"Tutorial_Volume_Move2",who,e,sizeof(e))&&f.autosaves==1);
 CHECK(!oa_opening_runtime_sword_acquired(o,7,"other:g1",1,e,sizeof(e)));CHECK(!oa_opening_runtime_snapshot(o,&s,e,sizeof(e))&&s.timer_count==0);
 CHECK(!oa_opening_runtime_sword_acquired(o,7,who,1,e,sizeof(e)));CHECK(!oa_opening_runtime_snapshot(o,&s,e,sizeof(e)));
 CHECK(s.sword_flags==1&&(s.wos_flags&(1u<<13))&&s.sword_get==1&&s.timer_count==2);
 CHECK(!oa_opening_runtime_advance(o,14,e,sizeof(e))&&!f.gateway&&f.modals==0);
 CHECK(!oa_opening_runtime_advance(o,1,e,sizeof(e))&&f.modals==1&&!f.gateway&&f.stage==5);
 f.equipped=1;CHECK(!oa_opening_runtime_sword_equipped(o,7,e,sizeof(e)));CHECK(!oa_opening_runtime_advance(o,15,e,sizeof(e)));
 CHECK(f.gateway&&f.stage==25&&f.compare==1);CHECK(!oa_opening_runtime_snapshot(o,&s,e,sizeof(e))&&s.timer_count==0&&(s.sword_flags&2));
 before=s;s.timer_count=1;s.serial=1;s.timers[0].hash=123;s.timers[0].serial=1;CHECK(oa_opening_runtime_restore(o,&s,e,sizeof(e))!=0);CHECK(!oa_opening_runtime_snapshot(o,&after,e,sizeof(e))&&!memcmp(&after,&before,sizeof(after)));
 oa_opening_runtime_get_stats(o,&stats);CHECK(stats.lua_bytes>0&&stats.lua_bytes<=stats.lua_limit&&stats.instruction_budget==200000&&!stats.poisoned);printf("production_runtime_lua_bytes=%zu\n",stats.lua_bytes);oa_opening_runtime_close(o);
 reset(&f,argv[1]);o=create(&f,200000,64u*1024u*1024u,e,sizeof(e));CHECK(o);f.self=o;CHECK(!oa_opening_runtime_cinematic_finished(o,1,e,sizeof(e)));f.reject=1;CHECK(oa_opening_runtime_volume_exit(o,"Tutorial_Volume_Move",who,e,sizeof(e))!=0);CHECK(!oa_opening_runtime_snapshot(o,&s,e,sizeof(e))&&!(s.wos_flags&(1u<<11))&&f.effects==0);
 f.reject=0;CHECK(!oa_opening_runtime_volume_exit(o,"Tutorial_Volume_Move",who,e,sizeof(e))&&f.autosaves==1);f.reject=1;CHECK(oa_opening_runtime_sword_acquired(o,7,who,1,e,sizeof(e))!=0);CHECK(!oa_opening_runtime_snapshot(o,&s,e,sizeof(e))&&!(s.sword_flags&1)&&s.timer_count==0);
 f.reject=0;CHECK(!oa_opening_runtime_sword_acquired(o,7,who,1,e,sizeof(e)));f.equipped=1;CHECK(!oa_opening_runtime_sword_equipped(o,7,e,sizeof(e)));CHECK(!oa_opening_runtime_snapshot(o,&before,e,sizeof(e)));f.known=0;CHECK(oa_opening_runtime_advance(o,15,e,sizeof(e))!=0&&strstr(e,"unknown"));CHECK(!f.gateway);CHECK(!oa_opening_runtime_snapshot(o,&after,e,sizeof(e))&&!memcmp(&after,&before,sizeof(after)));f.known=2;CHECK(oa_opening_runtime_advance(o,15,e,sizeof(e))!=0&&strstr(e,"not supplied"));CHECK(!f.gateway);f.known=1;CHECK(!oa_opening_runtime_advance(o,15,e,sizeof(e))&&f.gateway&&f.stage==25);
 f.bad=1;CHECK(oa_opening_runtime_sword_acquired(o,7,who,1,e,sizeof(e))!=0&&strstr(e,"boolean"));f.bad=0;oa_opening_runtime_get_stats(o,&stats);CHECK(stats.rebuilds>=4&&!stats.poisoned);oa_opening_runtime_close(o);
 reset(&f,argv[1]);{oa_opening_assets a={&f,sz,rd};oa_opening_host h={&f,"scene1417252:player1:g1",query,stage,NULL,warn};CHECK(oa_opening_runtime_create_from_assets(&a,&h,NULL,e,sizeof(e))==NULL&&strstr(e,"explicit"));}
 reset(&f,argv[1]);f.corrupt=1;CHECK(create(&f,200000,64u*1024u*1024u,e,sizeof(e))==NULL&&strstr(e,"SHA256"));reset(&f,argv[1]);CHECK(create(&f,200000,32768,e,sizeof(e))==NULL);
 reset(&f,argv[1]);o=create(&f,40000,64u*1024u*1024u,e,sizeof(e));CHECK(o);CHECK(!oa_opening_runtime_snapshot(o,&s,e,sizeof(e)));s.timer_count=OA_OPENING_MAX_TIMERS;s.serial=OA_OPENING_MAX_TIMERS;for(i=0;i<s.timer_count;i++){s.timers[i].hash=165407883;s.timers[i].due_ms=0;s.timers[i].serial=i+1;s.timers[i].argc=0;s.timers[i].item_index=0;}
 CHECK(!oa_opening_runtime_restore(o,&s,e,sizeof(e)));CHECK(!oa_opening_runtime_snapshot(o,&before,e,sizeof(e)));CHECK(oa_opening_runtime_advance(o,0,e,sizeof(e))!=0&&strstr(e,"budget"));CHECK(!oa_opening_runtime_snapshot(o,&after,e,sizeof(e))&&!memcmp(&after,&before,sizeof(after))&&f.effects==0);oa_opening_runtime_get_stats(o,&stats);CHECK(stats.rebuilds==1&&!stats.poisoned);oa_opening_runtime_close(o);
 printf("{\"passed\":true,\"checks\":%u,\"backend\":\"simulated acknowledged host\",\"lua\":\"production amalur_runtime + Lua5.1.5\",\"budget_rollback\":true,\"asset_hash_rejection\":true,\"user_files_touched\":false}\n",checks);return 0;
}
