/* Production C/Lua + actual private checkpoint I/O.
 * Actor/UI backend is a recorded two-phase CPU fixture, NOT a live engine/UI. */
#include "oa_opening_gameplay.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#endif
typedef struct fixture {
 const char *assets;
 oa_gameplay_host *host;
 unsigned reports,prepares,commits,aborts,validations,reentries,effect_count;
 unsigned set25,modals;
 int unavailable,reject_prepare,reject_pose;
 oa_gameplay_state staged,visible;
} fixture;
static unsigned checks;
static oa_gameplay_pose A={{4311.998f,2805.992f,-314.539f},-3.14159265f,0.125f};
static oa_gameplay_pose B={{4015.905f,2805.992f,-315.788f},-3.14159265f,0.125f};
#define CHECK(x) do{checks++;if(!(x)){fprintf(stderr,"FAIL line%d %s: %s\n",__LINE__,#x,e);return 1;}}while(0)
static int sz(void*v,const char*n,size_t*z,char*e,size_t c){
 fixture*f=v;char p[2048];long s;FILE*h;snprintf(p,sizeof(p),"%s/%s",f->assets,n);h=fopen(p,"rb");
 if(!h){snprintf(e,c,"test asset missing");return 1;}if(fseek(h,0,SEEK_END)||(s=ftell(h))<0){fclose(h);return 1;}fclose(h);*z=(size_t)s;return 0;
}
static int rd(void*v,const char*n,void*out,size_t z,char*e,size_t c){
 fixture*f=v;char p[2048];FILE*h;int ok;snprintf(p,sizeof(p),"%s/%s",f->assets,n);h=fopen(p,"rb");if(!h)return 1;
 ok=fread(out,1,z,h)==z&&fgetc(h)==EOF&&!ferror(h);fclose(h);if(!ok)snprintf(e,c,"test asset changed");return !ok;
}
static void report(void*v,const char*s){fixture*f=v;f->reports++;printf("latched_failure:%s\n",s);}
static int available(void*v,uint32_t required,char*e,size_t c){
 fixture*f=v;(void)required;if(f->unavailable){snprintf(e,c,"recorded actor/UI fixture unavailable");return 1;}return 0;
}
static int prepare(void*v,const oa_gameplay_batch*b,void**token,char*e,size_t c){
 fixture*f=v;oa_gameplay_state state;char err[128];size_t i;f->prepares++;
 if(f->host&&oa_gameplay_snapshot(f->host,&state,err,sizeof(err))&&strstr(err,"reentry"))f->reentries++;
 if(f->reject_prepare){snprintf(e,c,"recorded actor/UI prepare rejected");return 1;}
 if(!b||b->scene!=1417252||b->container_gor!=1790948||b->container_instance!=1789992||b->item_type!=1360571||
    b->generation!=17||b->item_instance!=UINT64_C(0x123456789a)||b->item_index!=7||b->previous_revision!=b->before->revision)
  return 1;
 for(i=0;i<b->effect_count;i++){
  if(!b->effects[i].source_callback)return 1;
  /* Counts are staged below, only commit publishes them. */
 }
 f->staged=*b->after;*token=f;return 0;
}
static void commit(void*v,void*token){fixture*f=v;(void)token;f->visible=f->staged;f->commits++;}
static void abort_tx(void*v,void*token){fixture*f=v;(void)token;f->aborts++;}
static int validate_pose(void*v,const oa_gameplay_pose*p,char*e,size_t c){
 fixture*f=v;f->validations++;if(f->reject_pose||!p){snprintf(e,c,"current collision fixture rejected");return 1;}return 0;
}
static oa_gameplay_host*create(fixture*f,const char*path,uint32_t caps,int enabled,char*e,size_t c){
 oa_opening_assets a={f,sz,rd};oa_gameplay_config k;memset(&k,0,sizeof(k));k.generation=17;k.item_instance=UINT64_C(0x123456789a);k.item_index=7;k.tutorials_enabled=enabled;
 k.checkpoint_path=path;k.report_context=f;k.report_failure=report;k.pose_validation_context=f;k.validate_load_pose=validate_pose;
 k.backend.context=f;k.backend.capabilities=caps;k.backend.available=available;k.backend.prepare=prepare;k.backend.commit=commit;k.backend.abort=abort_tx;
 return oa_gameplay_create(&a,&k,e,c);
}
static size_t readbytes(const char*p,unsigned char*b,size_t cap){
 FILE*f=fopen(p,"rb");size_t n;if(!f)return 0;n=fread(b,1,cap,f);if(ferror(f)||fgetc(f)!=EOF){fclose(f);return 0;}fclose(f);return n;
}
static int writebytes(const char*p,const void*b,size_t n){FILE*f=fopen(p,"wb");int ok;if(!f)return 0;ok=fwrite(b,1,n,f)==n;return fclose(f)==0&&ok;}
static int state_eq(const oa_gameplay_state*a,const oa_gameplay_state*b){return !memcmp(a,b,sizeof(*a));}
static int take(oa_gameplay_host*h,char*e,size_t n){return oa_gameplay_take_source_item(h,1790948,1789992,UINT64_C(0x123456789a),17,e,n);}
static int equip(oa_gameplay_host*h,char*e,size_t n){return oa_gameplay_equip_source_item(h,UINT64_C(0x123456789a),17,e,n);}
int main(int argc,char**argv){
 fixture f;oa_gameplay_host*h;oa_gameplay_state s,before,after,moved;oa_gameplay_stats stats,stats0;int32_t stage=123;
 char path[1200],badpath[1200],noio[1200],timerpath[1200],disabledpath[1200],e[1024]="";
 unsigned char bytes[8192],later[8192];size_t n,z;unsigned i,reports,commits;oa_gameplay_tutorial registry[3];

 if(argc==5&&!strcmp(argv[1],"--load-check")){
  int result,expect_reject=atoi(argv[4]);
  memset(&f,0,sizeof(f));f.assets=argv[2];h=create(&f,argv[3],15,1,e,sizeof(e));CHECK(h);f.host=h;
  CHECK(!oa_gameplay_update_pose(h,&A,e,sizeof(e)));CHECK(!oa_gameplay_snapshot(h,&before,e,sizeof(e)));
  result=oa_gameplay_load_checkpoint(h,e,sizeof(e));
  CHECK(expect_reject?result!=0:result==0);
  if(expect_reject){CHECK(!oa_gameplay_snapshot(h,&after,e,sizeof(e))&&state_eq(&before,&after)&&!f.commits);fprintf(stderr,"expected rejection: %s\n",e);}
  else {CHECK(!oa_gameplay_snapshot(h,&after,e,sizeof(e)));printf("loaded_clock=%llu timers=%u owned=%u equipped=%u door=%u quest_noops=%llu\n",(unsigned long long)after.lua.clock_ms,after.lua.timer_count,after.owned,after.equipped,after.door_open,(unsigned long long)after.quest_noops);}
  oa_gameplay_close(h);
  printf("{\"passed\":true,\"checks\":%u,\"expected_rejection\":%d}\n",checks,expect_reject);return 0;
 }
 if(argc!=3){fprintf(stderr,"usage:gameplay-test ASSET_ROOT NEW_PRIVATE_OUTPUT_DIR\n");return 2;}
 memset(&f,0,sizeof(f));f.assets=argv[1];
 snprintf(path,sizeof(path),"%s/main.opening-gameplay-v1.bin",argv[2]);
 snprintf(badpath,sizeof(badpath),"%s/corrupt.opening-gameplay-v1.bin",argv[2]);
 snprintf(noio,sizeof(noio),"%s/no-directory/failed.opening-gameplay-v1.bin",argv[2]);
 snprintf(timerpath,sizeof(timerpath),"%s/timers.opening-gameplay-v1.bin",argv[2]);
 snprintf(disabledpath,sizeof(disabledpath),"%s/disabled.opening-gameplay-v1.bin",argv[2]);
 CHECK(!create(&f,"opem-save-v1.bin",15,1,e,sizeof(e))&&strstr(e,"old saves"));
 h=create(&f,path,0,1,e,sizeof(e));CHECK(h);f.host=h;
 CHECK(!oa_gameplay_quest_stage(h,613083,&stage,e,sizeof(e))&&stage==-1);
 stage=123;CHECK(oa_gameplay_quest_stage(h,999,&stage,e,sizeof(e))==OA_GAMEPLAY_UNAVAILABLE&&stage==123);
 CHECK(!oa_gameplay_update_pose(h,&A,e,sizeof(e)));CHECK(!oa_gameplay_snapshot(h,&before,e,sizeof(e))&&before.inside==3&&before.container_count==1&&!before.owned&&!before.skipped);
 CHECK(take(h,e,sizeof(e))!=0);CHECK(!oa_gameplay_snapshot(h,&after,e,sizeof(e))&&state_eq(&before,&after)&&!f.commits);
 reports=f.reports;CHECK(oa_gameplay_advance(h,15,e,sizeof(e))==OA_GAMEPLAY_LATCHED&&f.reports==reports);
 oa_gameplay_close(h);f.host=NULL;
 h=create(&f,path,15,1,e,sizeof(e));CHECK(h);f.host=h;
 CHECK(!oa_gameplay_tutorial_set(h,17524338,1,1,e,sizeof(e)));CHECK(!oa_gameplay_tutorial_set(h,26339831,1,1,e,sizeof(e)));
 CHECK(!oa_gameplay_update_pose(h,&A,e,sizeof(e)));CHECK(!oa_gameplay_cinematic_skipped(h,e,sizeof(e)));
 CHECK(oa_gameplay_cinematic_skipped(h,e,sizeof(e))==OA_GAMEPLAY_NO_CHANGE);
 CHECK(!oa_gameplay_update_pose(h,&B,e,sizeof(e)));
 CHECK(!oa_gameplay_snapshot(h,&moved,e,sizeof(e))&&(moved.lua.wos_flags&(1u<<11))&&moved.tutorials[0].kills==1&&moved.tutorials[1].kills==1);
 oa_gameplay_get_stats(h,&stats);CHECK(stats.writes==1&&stats.runtime.lua_bytes>0&&!stats.poisoned&&!stats.runtime.poisoned);
 n=readbytes(path,bytes,sizeof(bytes));CHECK(n>300&&n<8192&&!memcmp(bytes,"OAGPCP1",8));
 CHECK(!oa_gameplay_snapshot(h,&before,e,sizeof(e)));
 CHECK(oa_gameplay_take_source_item(h,1790948,1789992,UINT64_C(0x123456789a),16,e,sizeof(e))==OA_GAMEPLAY_UNAVAILABLE);
 CHECK(oa_gameplay_take_source_item(h,999,1789992,UINT64_C(0x123456789a),17,e,sizeof(e))==OA_GAMEPLAY_UNAVAILABLE);
 CHECK(oa_gameplay_equip_source_item(h,UINT64_C(0x123456789a),17,e,sizeof(e))==OA_GAMEPLAY_UNAVAILABLE);
 CHECK(!oa_gameplay_snapshot(h,&after,e,sizeof(e))&&state_eq(&before,&after));
 f.unavailable=1;commits=f.commits;
 CHECK(take(h,e,sizeof(e))==OA_GAMEPLAY_UNAVAILABLE);
 CHECK(!oa_gameplay_snapshot(h,&after,e,sizeof(e))&&state_eq(&before,&after)&&f.commits==commits);
 f.unavailable=0;CHECK(!oa_gameplay_clear_failure(h,e,sizeof(e)));
 f.reject_prepare=1;commits=f.commits;
 CHECK(take(h,e,sizeof(e))!=0);CHECK(!oa_gameplay_snapshot(h,&after,e,sizeof(e))&&state_eq(&before,&after)&&f.commits==commits);
 z=readbytes(path,later,sizeof(later));CHECK(z==n&&!memcmp(bytes,later,n));
 CHECK(oa_gameplay_advance(h,15,e,sizeof(e))==OA_GAMEPLAY_LATCHED);f.reject_prepare=0;
 CHECK(!oa_gameplay_clear_failure(h,e,sizeof(e)));CHECK(!take(h,e,sizeof(e)));
 CHECK(!oa_gameplay_snapshot(h,&s,e,sizeof(e))&&s.owned&&s.container_count==0&&!s.equipped&&s.secondary_disabled&&!s.door_open&&s.lua.timer_count==2&&s.lua.sword_get==1);
 before=s;commits=f.commits;CHECK(take(h,e,sizeof(e))==OA_GAMEPLAY_NO_CHANGE&&f.commits==commits);
 CHECK(!oa_gameplay_snapshot(h,&after,e,sizeof(e))&&state_eq(&before,&after));
 CHECK(!oa_gameplay_advance(h,14,e,sizeof(e)));CHECK(!oa_gameplay_snapshot(h,&s,e,sizeof(e))&&s.lua.clock_ms==14&&!s.door_open&&s.lua.timer_count==2);
 CHECK(!oa_gameplay_advance(h,1,e,sizeof(e)));CHECK(!oa_gameplay_snapshot(h,&s,e,sizeof(e))&&s.lua.clock_ms==15&&!s.door_open&&s.lua.timer_count==1&&s.tutorials[4].active&&s.tutorials[4].fired&&(s.lua.wos_flags&(1u<<6)));
 CHECK(!oa_gameplay_save_checkpoint(h,e,sizeof(e))); /* Pending poll timer persisted exactly. */
 CHECK(!equip(h,e,sizeof(e)));CHECK(!oa_gameplay_snapshot(h,&s,e,sizeof(e))&&s.equipped&&(s.lua.sword_flags&2));
 before=s;CHECK(equip(h,e,sizeof(e))==OA_GAMEPLAY_NO_CHANGE);CHECK(!oa_gameplay_snapshot(h,&after,e,sizeof(e))&&state_eq(&before,&after));
 f.reject_prepare=1;commits=f.commits;CHECK(oa_gameplay_advance(h,15,e,sizeof(e))!=0);
 CHECK(!oa_gameplay_snapshot(h,&after,e,sizeof(e))&&state_eq(&before,&after)&&f.commits==commits);
 f.reject_prepare=0;CHECK(!oa_gameplay_clear_failure(h,e,sizeof(e)));CHECK(!oa_gameplay_advance(h,15,e,sizeof(e)));
 CHECK(!oa_gameplay_snapshot(h,&s,e,sizeof(e))&&s.door_open&&s.compare_enabled&&s.lua.timer_count==0&&s.quest_noops==1&&s.lua.clock_ms==30);
 CHECK(!oa_gameplay_quest_stage(h,613083,&stage,e,sizeof(e))&&stage==-1);CHECK(f.visible.door_open&&f.visible.equipped&&f.reentries>0);
 CHECK(!oa_gameplay_save_checkpoint(h,e,sizeof(e)));before=s;
 n=readbytes(path,bytes,sizeof(bytes));CHECK(n>300&&!memcmp(bytes,"OAGPCP1",8));
 CHECK(oa_gameplay_advance(h,1001,e,sizeof(e))!=0);CHECK(!oa_gameplay_snapshot(h,&after,e,sizeof(e))&&state_eq(&before,&after));
 f.reject_pose=1;commits=f.commits;oa_gameplay_get_stats(h,&stats0);
 CHECK(oa_gameplay_load_checkpoint(h,e,sizeof(e))!=0&&strstr(e,"collision"));
 oa_gameplay_get_stats(h,&stats);CHECK(stats.runtime.calls==stats0.runtime.calls);
 CHECK(!oa_gameplay_snapshot(h,&after,e,sizeof(e))&&state_eq(&before,&after)&&f.commits==commits);
 f.reject_pose=0;f.reject_prepare=1;commits=f.commits;
 CHECK(oa_gameplay_load_checkpoint(h,e,sizeof(e))!=0);
 CHECK(!oa_gameplay_snapshot(h,&after,e,sizeof(e))&&state_eq(&before,&after)&&f.commits==commits);
 z=readbytes(path,later,sizeof(later));CHECK(z==n&&!memcmp(bytes,later,n));
 f.reject_prepare=0;CHECK(!oa_gameplay_clear_failure(h,e,sizeof(e)));
 CHECK(!oa_gameplay_load_checkpoint(h,e,sizeof(e)));CHECK(!oa_gameplay_snapshot(h,&s,e,sizeof(e))&&s.door_open&&s.owned&&s.equipped&&s.quest_noops==1&&s.lua.clock_ms==30&&s.revision>before.revision);
 CHECK(!oa_gameplay_quest_stage(h,613083,&stage,e,sizeof(e))&&stage==-1);
 oa_gameplay_close(h);f.host=NULL;
 h=create(&f,path,15,1,e,sizeof(e));CHECK(h);f.host=h;CHECK(!oa_gameplay_load_checkpoint(h,e,sizeof(e)));
 CHECK(!oa_gameplay_snapshot(h,&s,e,sizeof(e))&&s.door_open&&s.equipped&&!memcmp(&s.lua,&before.lua,sizeof(s.lua)));
 oa_gameplay_close(h);f.host=NULL;
 /* Corrupt payload: checksum, typed timer and source profile rejection preserve state/file. */
 bytes[64]^=1;CHECK(writebytes(badpath,bytes,n));bytes[64]^=1;
 h=create(&f,badpath,15,1,e,sizeof(e));CHECK(h);f.host=h;CHECK(!oa_gameplay_update_pose(h,&A,e,sizeof(e)));CHECK(!oa_gameplay_snapshot(h,&before,e,sizeof(e)));
 CHECK(oa_gameplay_load_checkpoint(h,e,sizeof(e))!=0&&strstr(e,"SHA256"));
 CHECK(!oa_gameplay_snapshot(h,&after,e,sizeof(e))&&state_eq(&before,&after));
 CHECK(oa_gameplay_save_checkpoint(h,e,sizeof(e))!=0&&strstr(e,"preserved"));
 oa_gameplay_close(h);f.host=NULL;
 /* Every truncation rejects before state/UI mutation. */
 h=create(&f,badpath,15,1,e,sizeof(e));CHECK(h);f.host=h;CHECK(!oa_gameplay_snapshot(h,&before,e,sizeof(e)));
 for(i=0;i<n;i++){CHECK(writebytes(badpath,bytes,i));commits=f.commits;CHECK(oa_gameplay_load_checkpoint(h,e,sizeof(e))!=0);CHECK(!oa_gameplay_snapshot(h,&after,e,sizeof(e))&&state_eq(&before,&after)&&f.commits==commits);}
 oa_gameplay_close(h);f.host=NULL;
 /* Disk failure after external prepare aborts and restores original Lua+registry+pose. */
 h=create(&f,noio,15,1,e,sizeof(e));CHECK(h);f.host=h;CHECK(!oa_gameplay_update_pose(h,&A,e,sizeof(e)));CHECK(!oa_gameplay_cinematic_skipped(h,e,sizeof(e)));CHECK(!oa_gameplay_snapshot(h,&before,e,sizeof(e)));
 commits=f.commits;CHECK(oa_gameplay_update_pose(h,&B,e,sizeof(e))!=0);
 CHECK(!oa_gameplay_snapshot(h,&after,e,sizeof(e))&&state_eq(&before,&after)&&f.commits==commits&&f.aborts>0);
 reports=f.reports;oa_gameplay_get_stats(h,&stats0);
 for(i=0;i<20;i++)CHECK(oa_gameplay_update_pose(h,&B,e,sizeof(e))==OA_GAMEPLAY_LATCHED);
 oa_gameplay_get_stats(h,&stats);CHECK(f.reports==reports&&stats.runtime.calls==stats0.runtime.calls&&!stats.poisoned);
 oa_gameplay_close(h);f.host=NULL;
 /* One supplied movement realm migrates into a fresh host; caller retires old one. */
 h=create(&f,timerpath,15,1,e,sizeof(e));CHECK(h);f.host=h;
 memcpy(registry,moved.tutorials,sizeof(registry));
 CHECK(!oa_gameplay_migrate_movement(h,1417252,17,&moved.pose,&moved.lua,registry,3,e,sizeof(e)));
 CHECK(!oa_gameplay_snapshot(h,&s,e,sizeof(e))&&s.initialized&&!s.owned&&!memcmp(&s.lua,&moved.lua,sizeof(s.lua)));
 CHECK(oa_gameplay_migrate_movement(h,1417252,17,&moved.pose,&moved.lua,registry,3,e,sizeof(e))!=0);
 CHECK(!take(h,e,sizeof(e)));CHECK(!oa_gameplay_save_checkpoint(h,e,sizeof(e)));
 CHECK(!oa_gameplay_snapshot(h,&before,e,sizeof(e))&&before.lua.timer_count==2);
 oa_gameplay_close(h);f.host=NULL;
 h=create(&f,timerpath,15,1,e,sizeof(e));CHECK(h);f.host=h;CHECK(!oa_gameplay_load_checkpoint(h,e,sizeof(e)));
 CHECK(!oa_gameplay_snapshot(h,&after,e,sizeof(e))&&after.lua.timer_count==2&&!memcmp(&after.lua,&before.lua,sizeof(after.lua)));
 CHECK(!equip(h,e,sizeof(e)));CHECK(!oa_gameplay_advance(h,15,e,sizeof(e)));CHECK(!oa_gameplay_snapshot(h,&s,e,sizeof(e))&&s.door_open&&s.lua.timer_count==0&&s.quest_noops==1);
 oa_gameplay_close(h);f.host=NULL;
 /* Tutorials disabled is explicit config: original Lua may open immediately on take. */
 h=create(&f,disabledpath,15,0,e,sizeof(e));CHECK(h);f.host=h;CHECK(!oa_gameplay_update_pose(h,&A,e,sizeof(e)));CHECK(!take(h,e,sizeof(e)));
 CHECK(!oa_gameplay_snapshot(h,&s,e,sizeof(e))&&s.door_open&&!s.equipped&&s.quest_noops==1&&s.lua.timer_count==1);CHECK(!oa_gameplay_save_checkpoint(h,e,sizeof(e)));oa_gameplay_close(h);f.host=NULL;
 /* Unknown option causes failure, not silent disable/enable. */
 h=create(&f,disabledpath,15,-1,e,sizeof(e));CHECK(h);f.host=h;CHECK(!oa_gameplay_update_pose(h,&A,e,sizeof(e)));CHECK(!oa_gameplay_snapshot(h,&before,e,sizeof(e)));
 CHECK(take(h,e,sizeof(e))!=0&&strstr(e,"option unavailable"));CHECK(!oa_gameplay_snapshot(h,&after,e,sizeof(e))&&state_eq(&before,&after));oa_gameplay_close(h);f.host=NULL;
 printf("{\"passed\":true,\"checks\":%u,\"runtime\":\"production amalur_runtime Lua5.1.5\",\"actor_ui\":\"recorded CPU two-phase fixture\",\"live_gpu_ui_android\":false,\"real_private_checkpoint_io\":true,\"reports\":%u,\"backend_commits\":%u}\n",checks,f.reports,f.commits);
 return 0;
}
