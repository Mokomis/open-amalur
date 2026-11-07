/* Real production C/Lua and real private file I/O.
 * Appearance publisher is a CPU reservation fixture, NOT GPU validation. */
#include "oa_creation_gameplay.h"
#include "amalur_runtime.h"
#include "lauxlib.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
typedef struct fixture {
 const char*opening,*creation;oa_creation_gameplay*host;oa_creation_active reserved,published;
 unsigned prepares,commits,aborts,posechecks,reentries,reports;
 int reject_prepare,reject_pose;uint64_t generation;int package4;
} fixture;
static unsigned checks;
static const unsigned source_tier1_exists[9]={1,1,1,0,0,0,1,0,1};
static const oa_creator_game_pose A={{4311.998f,2805.992f,-314.539f},-3.14159265f,0.125f};
static const oa_creator_game_pose B={{4015.905f,2805.992f,-315.788f},-3.14159265f,0.125f};
#define CHECK(x) do{checks++;if(!(x)){fprintf(stderr,"FAIL line%d %s: %s\n",__LINE__,#x,e);return 1;}}while(0)
static void path(fixture*f,const char*n,char*out,size_t cap){if(!strncmp(n,"creation/",9))snprintf(out,cap,"%s/%s",f->creation,n+9);else snprintf(out,cap,"%s/%s",f->opening,n);}
static int sz(void*v,const char*n,size_t*z,char*e,size_t cap){fixture*f=v;char p[2048];FILE*h;long k;path(f,n,p,sizeof(p));h=fopen(p,"rb");if(!h){snprintf(e,cap,"asset missing:%s",n);return 1;}if(fseek(h,0,SEEK_END)||(k=ftell(h))<0){fclose(h);return 1;}fclose(h);*z=(size_t)k;return 0;}
static int rd(void*v,const char*n,void*out,size_t z,char*e,size_t cap){fixture*f=v;char p[2048];FILE*h;int ok;path(f,n,p,sizeof(p));h=fopen(p,"rb");if(!h)return 1;ok=fread(out,1,z,h)==z&&fgetc(h)==EOF&&!ferror(h);fclose(h);if(!ok)snprintf(e,cap,"asset changed");return !ok;}
static void report(void*v,const char*s){fixture*f=v;f->reports++;printf("source_failure:%s\n",s);}
static int prepare(void*v,int loading,const oa_creation_active*a,const oa_creation_render_selection*r,void**token,char*e,size_t cap){
 fixture*f=v;oa_creation_active probe;char why[256];(void)loading;f->prepares++;
 if(f->host&&oa_creation_gameplay_snapshot(f->host,&probe,why,sizeof(why))&&strstr(why,"reentry"))f->reentries++;
 if(f->reject_prepare){snprintf(e,cap,"CPU appearance reservation rejected");return 1;}
 if(!r||!r->player_simtype||!a->owner.finalized||a->owner.quest_stage!=5||a->profile.phase!=OA_CREATION_COMMITTED)return 1;
 f->reserved=*a;*token=f;return 0;
}
static void commit(void*v,void*token){fixture*f=v;(void)token;f->published=f->reserved;f->commits++;}
static void abort_reservation(void*v,void*token){fixture*f=v;(void)token;f->aborts++;}
static int available(void*v,uint32_t required,char*e,size_t n){(void)v;(void)required;(void)e;(void)n;return 0;}
static int game_prepare(void*v,const oa_creator_game_batch*b,void**token,char*e,size_t n){fixture*f=v;(void)e;(void)n;if(!b||!b->after)return 1;f->reserved.gameplay=*b->after;*token=f;return 0;}
static void game_commit(void*v,void*token){fixture*f=v;(void)token;f->published.gameplay=f->reserved.gameplay;}
static void game_abort(void*v,void*token){(void)v;(void)token;}
static int posecheck(void*v,const oa_creator_game_pose*pose,char*e,size_t n){fixture*f=v;f->posechecks++;if(f->reject_pose||!pose){snprintf(e,n,"current collision candidate rejected");return 1;}return 0;}
static oa_creation_gameplay*create(fixture*f,const char*file,int publish_enabled,char*e,size_t n){
 oa_opening_assets a={f,sz,rd};oa_creation_gameplay_config c;memset(&c,0,sizeof(c));
 c.generation=f->generation;c.item_instance=UINT64_C(0x13300000007);c.item_index=7;c.tutorials_enabled=1;c.current_health=3;c.base_max_health=100;c.package4_active=f->package4;c.path=file;
 c.report_context=f;c.report_failure=report;c.pose_context=f;c.validate_load_pose=posecheck;c.runtime.instruction_budget=200000;c.runtime.lua_memory_bytes=64u*1024u*1024u;
 if(publish_enabled){c.appearance.context=f;c.appearance.prepare=prepare;c.appearance.commit=commit;c.appearance.abort=abort_reservation;}
 c.gameplay_backend.context=f;c.gameplay_backend.capabilities=15;c.gameplay_backend.available=available;c.gameplay_backend.prepare=game_prepare;c.gameplay_backend.commit=game_commit;c.gameplay_backend.abort=game_abort;
 return oa_creation_gameplay_create(&a,&c,e,n);
}
static size_t readbytes(const char*p,unsigned char*b,size_t cap){FILE*f=fopen(p,"rb");size_t n;if(!f)return 0;n=fread(b,1,cap,f);if(ferror(f)||fgetc(f)!=EOF){fclose(f);return 0;}fclose(f);return n;}
static int writebytes(const char*p,const void*b,size_t n){FILE*f=fopen(p,"wb");int ok;if(!f)return 0;ok=fwrite(b,1,n,f)==n;return fclose(f)==0&&ok;}

typedef struct condition_fixture {int stealth,sees;} condition_fixture;
static int cond_has(lua_State*L){condition_fixture*c=lua_touserdata(L,lua_upvalueindex(1));const char*who=luaL_checkstring(L,1),*state=luaL_checkstring(L,2);if(strcmp(who,"owner")||strcmp(state,"Stealth_Exiting"))return luaL_error(L,"unsupported actor-state condition domain");lua_pushboolean(L,c->stealth);return 1;}
static int cond_sees(lua_State*L){condition_fixture*c=lua_touserdata(L,lua_upvalueindex(1));if(strcmp(luaL_checkstring(L,1),"target"))return luaL_error(L,"unsupported target condition domain");lua_pushboolean(L,c->sees);return 1;}
static int cond_id(lua_State*L){if(strcmp(luaL_checkstring(L,1),"Stealth_Exiting"))return luaL_error(L,"unknown actor state");lua_pushliteral(L,"Stealth_Exiting");return 1;}
static int cond_install(lua_State*L){condition_fixture*c=lua_touserdata(L,1);lua_newtable(L);lua_pushlightuserdata(L,c);lua_pushcclosure(L,cond_has,1);lua_setfield(L,-2,"has_actor_state");lua_pushlightuserdata(L,c);lua_pushcclosure(L,cond_sees,1);lua_setfield(L,-2,"can_see_player");lua_setglobal(L,"ACTOR");lua_pushcfunction(L,cond_id);lua_setglobal(L,"ACTOR_STATE_ID");return 0;}
static int test_original_condition(fixture*f,char*e,size_t n){
 amalur_runtime_config cfg;amalur_runtime*rt;condition_fixture c={0,0};lua_State*L;char runtime[2048],condition[2048];int result=0,x,y;
 const char code[]="return require('source_stealth')('owner','target')";
 memset(&cfg,0,sizeof(cfg));snprintf(runtime,sizeof(runtime),"%s/runtime",f->opening);cfg.runtime_dir=runtime;cfg.instruction_budget=200000;cfg.memory_limit_bytes=64u*1024u*1024u;
 rt=amalur_runtime_create(&cfg,e,n);if(!rt)return 1;L=amalur_runtime_state(rt);
 if(lua_cpcall(L,cond_install,&c)){amalur_runtime_destroy(rt);return 1;}
 snprintf(condition,sizeof(condition),"%s/stealth-condition.lua",f->creation);
 if(amalur_runtime_register_module_file(rt,"source_stealth",condition,e,n)){amalur_runtime_destroy(rt);return 1;}
 for(x=0;x<2;x++)for(y=0;y<2;y++){
  c.stealth=x;c.sees=y;
  if(amalur_runtime_eval_source(rt,code,sizeof(code)-1,"original-stealth-condition",&result,e,n)||result!=1||!lua_isboolean(L,1)||lua_toboolean(L,1)!=(x&&!y)){amalur_runtime_destroy(rt);return 1;}
 }
 amalur_runtime_destroy(rt);return 0;
}
int main(int argc,char**argv){
 fixture f;oa_creation_gameplay*h;oa_creation_state draft,untouched;oa_creation_active a,before,after;oa_creator_game_host*game;int32_t stage;float val,expected;unsigned race,sex,patron,i,commits,unique=0;uint32_t ids[13]={0};char e[1024]="",file[1400],badfile[1400],missing[1400];unsigned char bytes[32768],later[32768];size_t z,n;
 if(argc!=4){fprintf(stderr,"usage:creation-gameplay-test OPENING_ASSETS CREATION_ASSETS NEW_OUTPUT_DIRECTORY\n");return 2;}
 memset(&f,0,sizeof(f));f.opening=argv[1];f.creation=argv[2];f.generation=17;f.package4=0;
 CHECK(!test_original_condition(&f,e,sizeof(e)));
 {int active=-9;CHECK(!oa_creation_source_package_default(3,&active)&&active==1);
 CHECK(!oa_creation_source_package_default(4,&active)&&active==1);
 CHECK(!oa_creation_source_package_default(12,&active)&&active==0);
 active=-9;CHECK(oa_creation_source_package_default(99,&active)==OA_CG_UNAVAILABLE&&active==-9);}
 snprintf(file,sizeof(file),"%s/refuse.old-save.bin",argv[3]);CHECK(!create(&f,file,1,e,sizeof(e)));
 snprintf(file,sizeof(file),"%s/no-publisher.creation-gameplay-v1.bin",argv[3]);
 h=create(&f,file,0,e,sizeof(e));CHECK(h);f.host=h;CHECK(!oa_creation_begin(&draft,0,0));untouched=draft;
 CHECK(oa_creation_gameplay_complete(h,&draft,1,&A,e,sizeof(e))==OA_CG_UNAVAILABLE);CHECK(!memcmp(&draft,&untouched,sizeof(draft)));CHECK(!oa_creation_gameplay_game(h));CHECK(!readbytes(file,bytes,sizeof(bytes)));oa_creation_gameplay_close(h);f.host=NULL;
 /* Every allowed race/sex/patron combination; original callback and owner effects. */
 for(race=0;race<4;race++)for(sex=0;sex<2;sex++)for(patron=0;patron<6;patron++){
  const oa_creation_patron*pat=oa_creation_source_patron(race,patron);const int16_t*skills=oa_creation_source_skills(race);const oa_patron_record*rec;
  f.package4=(int)((race+sex+patron)&1u);snprintf(file,sizeof(file),"%s/r%u-s%u-p%u.creation-gameplay-v1.bin",argv[3],race,sex,patron);
  h=create(&f,file,1,e,sizeof(e));CHECK(h);f.host=h;CHECK(!oa_creation_begin(&draft,race,sex));CHECK(!oa_creation_select_patron(&draft,patron));untouched=draft;
  CHECK(!oa_creation_gameplay_complete(h,&draft,100+race*12+sex*6+patron,&A,e,sizeof(e)));CHECK(!memcmp(&draft,&untouched,sizeof(draft)));
  CHECK(!oa_creation_gameplay_snapshot(h,&a,e,sizeof(e)));CHECK(a.profile.phase==OA_CREATION_COMMITTED&&a.profile.race==race&&a.profile.sex==sex&&a.profile.patron==patron);
  CHECK(a.owner.finalized&&a.owner.quest_stage==5&&a.owner.game_started&&a.owner.passive_aggressive_disabled&&a.owner.destiny_locked&&a.owner.fateweaver_locked);
  CHECK(a.owner.stealth_buff_registered&&a.owner.reckoning_buff_registered&&a.owner.destiny_buff_id==385357u&&a.owner.destiny_identifier==9325294u);
  {oa_creation_buff_instance buff;CHECK(!oa_creation_gameplay_buff(h,0,&buff)&&buff.id==pat->buff_id&&buff.identifier==1731073u&&buff.duration_ms==-1);
   CHECK(!oa_creation_gameplay_buff(h,1,&buff)&&buff.id==385357u&&buff.identifier==9325294u);
   CHECK(!oa_creation_gameplay_buff(h,2,&buff)&&buff.id==1621687u&&buff.identifier==35299876u);
   CHECK(!oa_creation_gameplay_buff(h,3,&buff)&&buff.id==633989u&&buff.identifier==11334545u);
   CHECK(oa_creation_gameplay_buff(h,4,&buff)==OA_CG_UNAVAILABLE);}
  CHECK(a.owner.item_count==(f.package4?165u:162u));
  CHECK(a.owner.items[5].type==615585&&a.owner.items[5].count==5);
  CHECK(a.owner.items[6].type==1321542&&a.owner.items[6].equipped_slot==0);
  CHECK(a.owner.items[7].type==1321543&&a.owner.items[7].equipped_slot==0);
  CHECK(a.owner.items[8].type==1330206&&a.owner.items[8].equipped_slot==0);
  CHECK(a.owner.items[9].type==1330207&&a.owner.items[9].equipped_slot==1);
  CHECK(a.owner.items[10].type==1381439&&a.owner.items[10].equipped_slot==0);
  for(i=0;i<9;i++){int32_t raw;CHECK(!oa_creation_skill_raw(&a.owner,i,&raw)&&raw==skills[i]);CHECK(oa_creation_skill_tier_active(&a.owner,i,1)==(source_tier1_exists[i]&&skills[i]>=10));}
  CHECK(!oa_creation_patron_apply(pat->buff_id,1657941,1,100,&expected,e,sizeof(e)));
  CHECK(a.owner.patron_id==pat->buff_id&&a.owner.health==(uint32_t)expected&&a.owner.max_health==(uint32_t)expected);
  CHECK(!oa_creation_gameplay_action_allowed(h,OA_CG_ACTION_DESTINY)&&!oa_creation_gameplay_action_allowed(h,OA_CG_ACTION_FATEWEAVE)&&!oa_creation_gameplay_action_allowed(h,OA_CG_ACTION_AGGRESSIVE));
  rec=oa_creation_patron_record(pat->buff_id);CHECK(rec&&rec->count>0);
  for(i=0;i<rec->count;i++){float source;memcpy(&source,&rec->effects[i].value_bits,4);expected=rec->effects[i].operation==1?10*source:10+source;CHECK(!oa_creation_gameplay_stat(h,rec->effects[i].stat_key,0,10,&val,e,sizeof(e))&&val==expected);}
  for(i=0;i<unique;i++)if(ids[i]==pat->buff_id)break;if(i==unique){CHECK(unique<13);ids[unique++]=pat->buff_id;}
  game=oa_creation_gameplay_game(h);CHECK(game&&!oa_creator_game_quest_stage(game,613083,&stage,e,sizeof(e))&&stage==5);
  commits=f.commits;CHECK(oa_creation_gameplay_complete(h,&draft,999,&A,e,sizeof(e))==OA_CG_ALREADY_ACTIVE&&f.commits==commits);
  CHECK(!oa_creation_gameplay_health(h,-11,e,sizeof(e)));CHECK(!oa_creation_gameplay_save(h,e,sizeof(e)));
  CHECK(!oa_creation_gameplay_snapshot(h,&before,e,sizeof(e)));
  oa_creation_gameplay_close(h);f.host=NULL;
  h=create(&f,file,1,e,sizeof(e));CHECK(h);f.host=h;
  CHECK(oa_creation_gameplay_complete(h,&draft,10000,&A,e,sizeof(e))==OA_CG_ALREADY_ACTIVE);
  CHECK(!oa_creation_gameplay_load(h,e,sizeof(e)));CHECK(!oa_creation_gameplay_snapshot(h,&after,e,sizeof(e)));
  CHECK(!memcmp(&before,&after,sizeof(before)));CHECK(f.published.owner.health==after.owner.health);
  oa_creation_gameplay_close(h);f.host=NULL;
 }
 CHECK(unique==13);
 /* Focused rollback / preservation: failed appearance reservation and real disk error. */
 f.package4=0;snprintf(file,sizeof(file),"%s/atomic.creation-gameplay-v1.bin",argv[3]);snprintf(badfile,sizeof(badfile),"%s/corrupt.creation-gameplay-v1.bin",argv[3]);snprintf(missing,sizeof(missing),"%s/not-a-directory/atomic.creation-gameplay-v1.bin",argv[3]);
 h=create(&f,file,1,e,sizeof(e));CHECK(h);f.host=h;CHECK(!oa_creation_begin(&draft,0,0));f.reject_prepare=1;commits=f.commits;
 CHECK(oa_creation_gameplay_complete(h,&draft,987,&A,e,sizeof(e))!=0&&f.commits==commits&&!oa_creation_gameplay_game(h));CHECK(!readbytes(file,bytes,sizeof(bytes)));
 f.reject_prepare=0;CHECK(!oa_creation_gameplay_complete(h,&draft,987,&A,e,sizeof(e)));
 game=oa_creation_gameplay_game(h);CHECK(game);
 /* Real source global stat gates, all visibility truth-table cases. */
 CHECK(!oa_creation_gameplay_combat_gates(h,0,0,0,e,sizeof(e)));
 CHECK(!oa_creation_gameplay_stat(h,3817837u,0,0.25f,&val,e,sizeof(e))&&val==0.25f);
 CHECK(!oa_creation_gameplay_combat_gates(h,1,1,0,e,sizeof(e)));
 CHECK(!oa_creation_gameplay_stat(h,3817837u,0,0.25f,&val,e,sizeof(e))&&val==0.25f);
 CHECK(!oa_creation_gameplay_combat_gates(h,0,1,0,e,sizeof(e)));
 CHECK(!oa_creation_gameplay_stat(h,3817837u,0,0.25f,&val,e,sizeof(e))&&val==0.25f);
 CHECK(!oa_creation_gameplay_combat_gates(h,1,0,0,e,sizeof(e)));
 CHECK(!oa_creation_gameplay_stat(h,3817837u,0,0.25f,&val,e,sizeof(e))&&val==1.25f);
 CHECK(!oa_creation_gameplay_combat_gates(h,0,0,1,e,sizeof(e)));
 CHECK(!oa_creation_gameplay_stat(h,22889937u,0,10,&val,e,sizeof(e))&&val==25);
 CHECK(!oa_creation_gameplay_stat(h,34457104u,0,10,&val,e,sizeof(e))&&val==35);
 CHECK(!oa_creation_gameplay_combat_gates(h,0,0,0,e,sizeof(e)));
 {int state=-1;CHECK(!oa_creation_gameplay_actor_state(h,"Skill_Alchemy_1",&state,e,sizeof(e))&&state==1);
 CHECK(!oa_creation_gameplay_actor_state(h,"Skill_Blacksmithing_2",&state,e,sizeof(e))&&state==1);
 CHECK(oa_creation_gameplay_actor_state(h,"Invented_Skill_State",&state,e,sizeof(e))==OA_CG_UNAVAILABLE);
 CHECK(!oa_creation_skill_tier_active(&f.published.owner,0,2));}
 /* Actual opening guards/time now query stage5, never create25. */
 CHECK(!oa_creator_game_cinematic_skipped(game,e,sizeof(e)));CHECK(!oa_creator_game_update_pose(game,&B,e,sizeof(e))); /* joins full profile autosave */
 CHECK(!oa_creator_game_take_source_item(game,1790948,1789992,UINT64_C(0x13300000007),17,e,sizeof(e)));
 CHECK(!oa_creator_game_equip_source_item(game,UINT64_C(0x13300000007),17,e,sizeof(e)));
 CHECK(!oa_creator_game_advance(game,15,e,sizeof(e)));CHECK(!oa_creation_gameplay_snapshot(h,&a,e,sizeof(e)));
 CHECK(a.gameplay.owned&&a.gameplay.equipped&&a.gameplay.door_open&&a.gameplay.quest_noops==1&&a.owner.quest_stage==5);
 CHECK(!oa_creator_game_quest_stage(game,613083,&stage,e,sizeof(e))&&stage==5);CHECK(!oa_creation_gameplay_save(h,e,sizeof(e)));
 CHECK(!oa_creation_gameplay_snapshot(h,&before,e,sizeof(e)));n=readbytes(file,bytes,sizeof(bytes));CHECK(n>3000&&n<32768&&!memcmp(bytes,"OACGCP1",8));
 f.reject_pose=1;commits=f.commits;CHECK(oa_creation_gameplay_load(h,e,sizeof(e))!=0&&strstr(e,"collision"));CHECK(!oa_creation_gameplay_snapshot(h,&after,e,sizeof(e))&&!memcmp(&before,&after,sizeof(before))&&commits==f.commits);
 f.reject_pose=0;f.reject_prepare=1;CHECK(oa_creation_gameplay_load(h,e,sizeof(e))!=0);CHECK(!oa_creation_gameplay_snapshot(h,&after,e,sizeof(e))&&!memcmp(&before,&after,sizeof(before)));
 f.reject_prepare=0;CHECK(!oa_creation_gameplay_load(h,e,sizeof(e)));CHECK(!oa_creation_gameplay_snapshot(h,&after,e,sizeof(e))&&!memcmp(&before,&after,sizeof(before)));
 z=readbytes(file,later,sizeof(later));CHECK(z==n&&!memcmp(bytes,later,n));
 oa_creation_gameplay_close(h);f.host=NULL;
 bytes[80]^=1;CHECK(writebytes(badfile,bytes,n));bytes[80]^=1;
 h=create(&f,badfile,1,e,sizeof(e));CHECK(h);f.host=h;CHECK(oa_creation_gameplay_load(h,e,sizeof(e))!=0);CHECK(oa_creation_gameplay_complete(h,&draft,1,&A,e,sizeof(e))!=0&&!oa_creation_gameplay_game(h));oa_creation_gameplay_close(h);f.host=NULL;
 h=create(&f,missing,1,e,sizeof(e));CHECK(h);f.host=h;commits=f.commits;CHECK(oa_creation_gameplay_complete(h,&draft,1,&A,e,sizeof(e))!=0&&!oa_creation_gameplay_game(h)&&f.commits==commits&&f.aborts>0);oa_creation_gameplay_close(h);f.host=NULL;
 f.package4=-1;h=create(&f,file,1,e,sizeof(e));CHECK(h);f.host=h;CHECK(oa_creation_gameplay_complete(h,&draft,1,&A,e,sizeof(e))==OA_CG_UNAVAILABLE&&strstr(e,"package4"));oa_creation_gameplay_close(h);f.host=NULL;
 CHECK(f.reentries>0);
 printf("{\"passed\":true,\"checks\":%u,\"race_sex_patron_cases\":48,\"unique_source_patron_buffs\":%u,\"production_C_Lua\":true,\"CPU_appearance_reservation_fixture\":true,\"GPU_Android_live\":false,\"real_private_atomic_files\":true}\n",checks,unique);return 0;
}
