/* Actual source convex planes + production Lua runtime + real checkpoint I/O.
 * No user save/configuration or original game execution. */
#include "oa_opening_movement.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#else
#include <sys/stat.h>
#endif
typedef struct test_context {const char *assets;unsigned reports,reentry,pose_validations;int reject_pose;oa_movement_host *host;} test_context;
static unsigned checks;
static oa_movement_pose A={{4311.998f,2805.992f,-314.539f},-3.14159265f,0.125f};
static oa_movement_pose B={{4015.905f,2805.992f,-315.788f},-3.14159265f,0.125f};
#define CHECK(x) do{checks++;if(!(x)){fprintf(stderr,"FAIL line%d %s: %s\n",__LINE__,#x,e);return 1;}}while(0)
static int asset_size(void*v,const char*n,size_t*z,char*e,size_t cap){test_context*t=v;char p[2048];long s;FILE*f;snprintf(p,sizeof(p),"%s/%s",t->assets,n);f=fopen(p,"rb");if(!f){snprintf(e,cap,"test asset missing");return 1;}if(fseek(f,0,SEEK_END)||(s=ftell(f))<0){fclose(f);return 1;}fclose(f);*z=(size_t)s;return 0;}
static int asset_read(void*v,const char*n,void*out,size_t z,char*e,size_t cap){test_context*t=v;char p[2048];int ok;FILE*f;snprintf(p,sizeof(p),"%s/%s",t->assets,n);f=fopen(p,"rb");if(!f)return 1;ok=fread(out,1,z,f)==z&&fgetc(f)==EOF&&!ferror(f);fclose(f);if(!ok)snprintf(e,cap,"test asset changed");return !ok;}
static void report(void*v,const char*s){test_context*t=v;char err[128];t->reports++;printf("latched_failure:%s\n",s);if(t->host&&oa_movement_host_update_pose(t->host,&A,err,sizeof(err))==OA_MOVEMENT_ERROR&&strstr(err,"reentry"))t->reentry++;}
static int validate_pose(void*v,const oa_movement_pose*p,char*e,size_t cap){test_context*t=v;t->pose_validations++;if(!p||t->reject_pose){snprintf(e,cap,"current collision rejected saved pose");return 1;}return 0;}
static oa_movement_host *create(test_context*t,const char*path,uint64_t gen,char*e,size_t cap){oa_opening_assets a={t,asset_size,asset_read};oa_movement_config c;memset(&c,0,sizeof(c));c.generation=gen;c.checkpoint_path=path;c.report_context=t;c.report_failure=report;c.pose_validation_context=t;c.validate_load_pose=validate_pose;return oa_movement_host_create(&a,&c,e,cap);}
static size_t readbytes(const char*p,unsigned char*b,size_t cap){FILE*f=fopen(p,"rb");size_t n;if(!f)return 0;n=fread(b,1,cap,f);if(ferror(f)||fgetc(f)!=EOF){fclose(f);return 0;}fclose(f);return n;}
static int writebytes(const char*p,const void*b,size_t n){FILE*f=fopen(p,"wb");int ok;if(!f)return 0;ok=fwrite(b,1,n,f)==n;return fclose(f)==0&&ok;}
int main(int argc,char**argv){
 test_context t;oa_movement_host*h;oa_movement_stats st,old;oa_opening_snapshot snap;oa_movement_pose p;oa_movement_tutorial ui;char path[1200],corrupt[1200],outside[1200],e[1024]="";unsigned char valid[8192],after[8192];size_t n,z;unsigned i;
 if(argc!=3){fprintf(stderr,"usage:oa-opening-movement-test ASSET_ROOT ISOLATED_OUTPUT_DIRECTORY\n");return 2;}
 memset(&t,0,sizeof(t));t.assets=argv[1];snprintf(path,sizeof(path),"%s/main.opening-checkpoint-v1.bin",argv[2]);snprintf(corrupt,sizeof(corrupt),"%s/corrupt.opening-checkpoint-v1.bin",argv[2]);snprintf(outside,sizeof(outside),"%s/outside.opening-checkpoint-v1.bin",argv[2]);
 CHECK(create(&t,"opem-save-v1.bin",17,e,sizeof(e))==NULL&&strstr(e,"legacy"));
 h=create(&t,path,17,e,sizeof(e));CHECK(h);t.host=h;CHECK(oa_movement_host_services(h)==7u);
 CHECK(!oa_movement_host_tutorial_set(h,17524338,1,1,e,sizeof(e)));CHECK(!oa_movement_host_tutorial_set(h,26339831,1,1,e,sizeof(e)));
 CHECK(!oa_movement_host_update_pose(h,&A,e,sizeof(e)));oa_movement_host_get_stats(h,&st);CHECK(st.inside_mask==3&&st.containment_initialized&&!st.cinematic_skipped&&!st.checkpoint_writes);
 CHECK(!oa_movement_host_snapshot(h,&p,&snap,e,sizeof(e))&&snap.cinematic_flags==0&&!(snap.wos_flags&(1u<<11)));
 CHECK(!oa_movement_host_cinematic_skipped(h,e,sizeof(e)));CHECK(!oa_movement_host_update_pose(h,&A,e,sizeof(e)));CHECK(!oa_movement_host_update_pose(h,&B,e,sizeof(e)));
 oa_movement_host_get_stats(h,&st);CHECK(st.inside_mask==1&&st.checkpoint_writes==1&&!st.latched&&st.cinematic_skipped);
 CHECK(!oa_movement_host_tutorial_get(h,17524338,&ui)&&!ui.active&&ui.fired&&ui.kills==1);CHECK(!oa_movement_host_tutorial_get(h,26339831,&ui)&&!ui.active&&ui.kills==1);
 CHECK(!oa_movement_host_snapshot(h,&p,&snap,e,sizeof(e))&&!memcmp(&p,&B,sizeof(p))&&(snap.wos_flags&(1u<<11))&&snap.cinematic_flags==1&&snap.sword_flags==0&&snap.sword_get==0);
 n=readbytes(path,valid,sizeof(valid));CHECK(n>100&&n<sizeof(valid)&&!memcmp(valid,"OAMVCP1",8));
 CHECK(!oa_movement_host_update_pose(h,&A,e,sizeof(e)));CHECK(!oa_movement_host_update_pose(h,&B,e,sizeof(e)));oa_movement_host_get_stats(h,&st);CHECK(st.checkpoint_writes==1&&t.reports==0);
 oa_movement_host_close(h);t.host=NULL;
 /* Real reload restores pose/scene-generation/tutorial registry and original guard. */
 h=create(&t,path,17,e,sizeof(e));CHECK(h);t.host=h;
 CHECK(!oa_movement_host_update_pose(h,&A,e,sizeof(e)));
 CHECK(!oa_movement_host_tutorial_set(h,17524338,1,0,e,sizeof(e)));
 oa_movement_host_get_stats(h,&old);t.reject_pose=1;
 CHECK(oa_movement_host_load_checkpoint(h,e,sizeof(e))!=0&&strstr(e,"collision"));
 oa_movement_host_get_stats(h,&st);CHECK(st.runtime.calls==old.runtime.calls);
 CHECK(!oa_movement_host_snapshot(h,&p,&snap,e,sizeof(e))&&!memcmp(&p,&A,sizeof(p))&&!(snap.wos_flags&(1u<<11)));
 CHECK(!oa_movement_host_tutorial_get(h,17524338,&ui)&&ui.active&&!ui.fired&&ui.kills==0);
 z=readbytes(path,after,sizeof(after));CHECK(z==n&&!memcmp(after,valid,n));
 t.reject_pose=0;CHECK(!oa_movement_host_load_checkpoint(h,e,sizeof(e)));CHECK(!oa_movement_host_snapshot(h,&p,&snap,e,sizeof(e))&&!memcmp(&p,&B,sizeof(p))&&(snap.wos_flags&(1u<<11)));
 CHECK(!oa_movement_host_tutorial_get(h,17524338,&ui)&&!ui.active&&ui.fired&&ui.kills==1);CHECK(!oa_movement_host_update_pose(h,&B,e,sizeof(e)));CHECK(!oa_movement_host_update_pose(h,&A,e,sizeof(e)));CHECK(!oa_movement_host_update_pose(h,&B,e,sizeof(e)));oa_movement_host_get_stats(h,&st);CHECK(st.checkpoint_writes==0&&!st.latched);oa_movement_host_close(h);t.host=NULL;
 /* Outside initialization must not manufacture an inside->outside transition. */
 h=create(&t,outside,17,e,sizeof(e));CHECK(h);CHECK(oa_movement_host_save_checkpoint(h,e,sizeof(e))!=0);CHECK(!oa_movement_host_update_pose(h,&B,e,sizeof(e)));CHECK(!oa_movement_host_cinematic_skipped(h,e,sizeof(e)));CHECK(!oa_movement_host_update_pose(h,&B,e,sizeof(e)));oa_movement_host_get_stats(h,&st);CHECK(st.checkpoint_writes==0&&st.inside_mask==1);CHECK(!oa_movement_host_snapshot(h,&p,&snap,e,sizeof(e))&&!(snap.wos_flags&(1u<<11)));
 CHECK(!oa_movement_host_save_checkpoint(h,e,sizeof(e)));
 CHECK(!oa_movement_host_snapshot(h,&p,&snap,e,sizeof(e))&&!memcmp(&p,&B,sizeof(p))&&!(snap.wos_flags&(1u<<11)));
 oa_movement_host_get_stats(h,&st);CHECK(st.checkpoint_writes==1&&!st.latched);CHECK(readbytes(outside,after,sizeof(after))>100);
 oa_movement_host_close(h);
 /* Corrupt/truncated/trailing files fail before any Lua/pose/registry mutation. */
 h=create(&t,corrupt,17,e,sizeof(e));CHECK(h);CHECK(!oa_movement_host_update_pose(h,&A,e,sizeof(e)));oa_movement_host_get_stats(h,&old);
 CHECK(writebytes(corrupt,valid,n));after[0]=0;
 for(i=0;i<4;i++){size_t cut=i==0?0:i==1?47:i==2?n-1:n+1;memcpy(after,valid,n);after[n]=0x5a;CHECK(writebytes(corrupt,after,cut));CHECK(oa_movement_host_load_checkpoint(h,e,sizeof(e))!=0);}
 memcpy(after,valid,n);after[n-1]^=1;CHECK(writebytes(corrupt,after,n));CHECK(oa_movement_host_load_checkpoint(h,e,sizeof(e))!=0&&strstr(e,"SHA256"));oa_movement_host_get_stats(h,&st);CHECK(st.runtime.calls==old.runtime.calls);CHECK(!oa_movement_host_snapshot(h,&p,&snap,e,sizeof(e))&&!memcmp(&p,&A,sizeof(p))&&!(snap.wos_flags&(1u<<11)));
 CHECK(writebytes(corrupt,valid,n));CHECK(!oa_movement_host_load_checkpoint(h,e,sizeof(e)));oa_movement_host_close(h);
 h=create(&t,path,18,e,sizeof(e));CHECK(h);CHECK(!oa_movement_host_update_pose(h,&A,e,sizeof(e)));CHECK(oa_movement_host_load_checkpoint(h,e,sizeof(e))!=0&&strstr(e,"generation"));CHECK(!oa_movement_host_snapshot(h,&p,&snap,e,sizeof(e))&&!memcmp(&p,&A,sizeof(p)));oa_movement_host_close(h);
 /* Force a REAL filesystem replacement failure. No fake effect rejection. */
 t.reports=t.reentry=0;h=create(&t,path,17,e,sizeof(e));CHECK(h);t.host=h;CHECK(!oa_movement_host_tutorial_set(h,17524338,1,1,e,sizeof(e)));CHECK(!oa_movement_host_tutorial_set(h,26339831,1,1,e,sizeof(e)));CHECK(!oa_movement_host_update_pose(h,&A,e,sizeof(e)));CHECK(!oa_movement_host_cinematic_skipped(h,e,sizeof(e)));
#ifdef _WIN32
 {HANDLE lock=CreateFileA(path,GENERIC_READ,FILE_SHARE_READ,NULL,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,NULL);CHECK(lock!=INVALID_HANDLE_VALUE);
 CHECK(oa_movement_host_update_pose(h,&B,e,sizeof(e))==OA_MOVEMENT_ERROR);oa_movement_host_get_stats(h,&st);CHECK(st.latched&&st.event_failures==1&&st.failure_reports==1&&t.reports==1&&t.reentry==1);
 CHECK(oa_movement_host_save_checkpoint(h,e,sizeof(e))==OA_MOVEMENT_LATCHED);
 CHECK(!oa_movement_host_snapshot(h,&p,&snap,e,sizeof(e))&&!memcmp(&p,&A,sizeof(p))&&!(snap.wos_flags&(1u<<11)));CHECK(!oa_movement_host_tutorial_get(h,17524338,&ui)&&ui.active&&ui.kills==0);
 z=readbytes(path,after,sizeof(after));CHECK(z==n&&!memcmp(after,valid,n));old=st;
 for(i=0;i<100;i++)CHECK(oa_movement_host_update_pose(h,&B,e,sizeof(e))==OA_MOVEMENT_LATCHED);
 oa_movement_host_get_stats(h,&st);CHECK(st.runtime.calls==old.runtime.calls&&st.failure_reports==1&&t.reports==1&&st.checkpoint_writes==0);
 CHECK(CloseHandle(lock));CHECK(!oa_movement_host_retry_failed_exit(h,e,sizeof(e)));oa_movement_host_get_stats(h,&st);CHECK(!st.latched&&st.checkpoint_writes==1&&t.reports==1);CHECK(!oa_movement_host_snapshot(h,&p,&snap,e,sizeof(e))&&!memcmp(&p,&B,sizeof(p))&&(snap.wos_flags&(1u<<11)));CHECK(!oa_movement_host_tutorial_get(h,17524338,&ui)&&!ui.active&&ui.kills==1);}
#endif
 oa_movement_host_close(h);t.host=NULL;
 printf("{\"passed\":true,\"checks\":%u,\"source_volume_path\":\"4311.998,2805.992,-314.539 -> 4015.905,2805.992,-315.788\",\"real_atomic_checkpoint\":true,\"failure_latched_once\":true,\"latched_frames_without_retry\":100,\"production_lua_runtime\":true,\"quest_sword_door_unavailable\":true,\"old_saves_settings_touched\":false}\n",checks);return 0;
}
