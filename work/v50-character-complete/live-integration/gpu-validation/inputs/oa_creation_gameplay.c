
#include "oa_creation_gameplay.h"
#include "oa_mq01_cursor.h"
#include "amalur_runtime.h"
#include "lauxlib.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <float.h>
#include <errno.h>
#include <inttypes.h>
#include <stdint.h>
#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#else
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>
#endif
#include "movement_sha256.h"
#include "creation_patron_tables.inc"
#include "creation_global_tables.inc"
#include "creation_skill_tables.inc"
#include "creation_item_tables.inc"
#include "creation_startup_assets.inc"
typedef char source_inventory_capacity[(sizeof(source_items)/sizeof(source_items[0])+3<=OA_CG_ITEMS_MAX)?1:-1];
#define CHECKPOINT_CAP 32768u
#define SUFFIX ".creation-gameplay-v1.bin"
typedef struct startup_blob {char*bytes;size_t n;} startup_blob;
struct oa_creation_gameplay {
 oa_opening_assets assets;oa_creation_gameplay_config config;
 oa_creator_game_host *game;
 oa_creation_active active;
 startup_blob startup[8];
 char path[1024],error[512];
 unsigned busy,temp_sequence;
 uint64_t writes,attempts,warnings;
};
static const char schema[]="creator-completed-profile+one-opening-realm:v1;skills9;items162+package4three;MQ01source-start0-set5;FatelessOne385357-tag9325294;Healthsignedint;sourcepatrons13;globalstealthandReckoningGates;scene1417252";
static int err(char*e,size_t n,const char*s){if(e&&n)snprintf(e,n,"%s",s);return OA_CG_ERROR;}
static int enter(oa_creation_gameplay*h,char*e,size_t n){if(e&&n)e[0]=0;if(!h)return err(e,n,"creator gameplay unavailable");if(h->busy||oa_creator_game_is_busy(h->game))return err(e,n,"creator gameplay reentry rejected");return 0;}
const oa_patron_record *oa_creation_patron_record(uint32_t id){size_t i;for(i=0;i<sizeof(source_patrons)/sizeof(source_patrons[0]);i++)if(source_patrons[i].id==id)return source_patrons+i;return NULL;}
static float value(uint32_t bits){float f;memcpy(&f,&bits,4);return f;}
static int eval_record(const oa_patron_record*r,uint32_t key,int integer,float base,float*out,char*e,size_t n){
 uint32_t i;float v=base;
 if(!r||!out||(integer!=0&&integer!=1)||!isfinite(base)||(integer&&(base< -2147483648.0f||base>=2147483648.0f)))return err(e,n,"invalid source stat operands");
 if(integer)v=(float)(int32_t)v;
 for(i=0;i<r->count;i++)if(r->effects[i].stat_key==key){
  float x=value(r->effects[i].value_bits);
  if(r->effects[i].operation==1)v=v*x;else if(r->effects[i].operation==3)v=v+x;else return err(e,n,"unsupported source stat operation");
  if(!isfinite(v)||(integer&&(v< -2147483648.0f||v>=2147483648.0f)))return err(e,n,"source stat overflow");
  if(integer)v=(float)(int32_t)v;
 }
 *out=v;return 0;
}
int oa_creation_patron_apply(uint32_t id,uint32_t key,int integer,float base,float*out,char*e,size_t n){return eval_record(oa_creation_patron_record(id),key,integer,base,out,e,n);}
int oa_creation_skill_raw(const oa_creation_owner_state*s,unsigned skill,int32_t*out){if(!s||!out||!s->finalized||skill>=9)return 1;*out=s->skill_raw[skill];return 0;}
int oa_creation_skill_tier_active(const oa_creation_owner_state*s,unsigned skill,unsigned tier){
 size_t i;if(!s||!s->finalized||skill>=9)return 0;
 for(i=0;i<sizeof(source_skill_states)/sizeof(source_skill_states[0]);i++)if(source_skill_states[i].skill==skill&&source_skill_states[i].threshold==tier)return s->skill_raw[skill]>=(int32_t)(tier*10);
 return 0;
}
static int owner_valid(oa_creation_gameplay*h,const oa_creation_active*a){
 const oa_patron_record*r;const int16_t*skills;size_t i,base_count=sizeof(source_items)/sizeof(source_items[0]);uint32_t expected;
 if(oa_creation_validate(&a->profile)||a->profile.phase!=OA_CREATION_COMMITTED||!a->owner.finalized||
 a->owner.quest_stage!=5||a->owner.destiny_buff_id!=385357u||a->owner.destiny_identifier!=9325294u||a->owner.game_started!=1||a->owner.passive_aggressive_disabled!=1||
 a->owner.destiny_locked!=1||a->owner.fateweaver_locked!=1||!a->owner.max_health||
 a->owner.max_health>=INT32_MAX||a->owner.health>a->owner.max_health||a->owner.package4_active>1||
 a->owner.stealth_buff_registered!=1||a->owner.reckoning_buff_registered!=1||
 a->owner.stealth_exiting>1||a->owner.target_can_see_player>1||a->owner.reckoning_active>1)return 0;
 r=oa_creation_patron_record(a->owner.patron_id);
 if(!r||a->owner.patron_id!=oa_creation_source_patron(a->profile.race,a->profile.patron)->buff_id)return 0;
 {float expected_hp;if(eval_record(r,1657941u,1,(float)h->config.base_max_health,&expected_hp,NULL,0)||expected_hp!=(float)a->owner.max_health)return 0;}
 skills=oa_creation_source_skills(a->profile.race);for(i=0;i<9;i++)if(a->owner.skill_raw[i]!=skills[i])return 0;
 expected=(uint32_t)base_count+(a->owner.package4_active?3u:0u);
 if(a->owner.item_count!=expected||expected>OA_CG_ITEMS_MAX)return 0;
 for(i=0;i<base_count;i++)if(memcmp(&a->owner.items[i],&source_items[i],sizeof(source_items[i])))return 0;
 if(a->owner.package4_active)for(i=0;i<3;i++){const oa_creation_item*x=a->owner.items+base_count+i;if(x->type!=source_package4_recipes[i]||x->count!=1||x->equipped_slot!=-1||x->hidden)return 0;}
 return 1;
}
typedef struct codec {unsigned char *b;size_t n,p;int bad;} codec;
static void put8(codec*c,unsigned x){if(c->p>=c->n){c->bad=1;return;}c->b[c->p++]=(unsigned char)x;}
static unsigned get8(codec*c){if(c->p>=c->n){c->bad=1;return 0;}return c->b[c->p++];}
static void put32(codec*c,uint32_t x){unsigned i;for(i=0;i<4;i++)put8(c,x>>(i*8));}
static uint32_t get32(codec*c){uint32_t x=0;unsigned i;for(i=0;i<4;i++)x|=(uint32_t)get8(c)<<(i*8);return x;}
static void put64(codec*c,uint64_t x){unsigned i;for(i=0;i<8;i++)put8(c,(unsigned)(x>>(i*8)));}
static uint64_t get64(codec*c){uint64_t x=0;unsigned i;for(i=0;i<8;i++)x|=(uint64_t)get8(c)<<(i*8);return x;}
static void putbytes(codec*c,const void*p,size_t n){size_t i;for(i=0;i<n;i++)put8(c,((const unsigned char*)p)[i]);}
static int equalbytes(codec*c,const void*p,size_t n){size_t i;int eq=1;for(i=0;i<n;i++)if(get8(c)!=((const unsigned char*)p)[i])eq=0;return eq&&!c->bad;}

static void profile_hash(unsigned char out[32]){
 unsigned char bytes[8192];codec c={bytes,sizeof(bytes),0,0};size_t i,j;
 putbytes(&c,schema,sizeof(schema)-1);put32(&c,oa_creation_catalogue_crc());
 for(i=0;i<sizeof(source_patrons)/sizeof(source_patrons[0]);i++){
  put32(&c,source_patrons[i].id);put32(&c,source_patrons[i].count);
  for(j=0;j<source_patrons[i].count;j++){const oa_patron_effect*x=&source_patrons[i].effects[j];put32(&c,x->stat_key);put32(&c,x->operation);put32(&c,x->value_bits);}
 }
 for(i=0;i<8;i++)putbytes(&c,startup_specs[i].sha,32);
 for(i=0;i<2;i++){put32(&c,source_global_buffs[i].id);for(j=0;j<source_global_buffs[i].count;j++){const oa_patron_effect*x=&source_global_buffs[i].effects[j];put32(&c,x->stat_key);put32(&c,x->operation);put32(&c,x->value_bits);}}
 for(i=0;i<3;i++)put32(&c,source_package4_recipes[i]);
 /* Schema source item bytes are version pinned in this source; include all records. */
 for(i=0;i<sizeof(source_items)/sizeof(source_items[0]);i++){
  put32(&c,source_items[i].type);put32(&c,source_items[i].count);put32(&c,(uint32_t)source_items[i].equipped_slot);put32(&c,source_items[i].hidden);
 }
 for(i=0;i<sizeof(source_skill_states)/sizeof(source_skill_states[0]);i++){put32(&c,source_skill_states[i].skill);put32(&c,source_skill_states[i].threshold);putbytes(&c,source_skill_states[i].name,strlen(source_skill_states[i].name)+1);}
 /* Current source fits8192; never return a partial/source-less digest. */
 if(c.bad){memset(out,0,32);return;}sha256(bytes,c.p,out);
}
static int encode(oa_creation_gameplay*h,oa_creator_game_host*game,const oa_creation_active*a,unsigned char*out,size_t*outn,char*e,size_t n){
 unsigned char profile[OA_CREATION_ENVELOPE_MAX],nested[8192],digest[32];size_t z=0,nz=0;codec c={out,CHECKPOINT_CAP,48,0};unsigned i;
 if(!owner_valid(h,a)||oa_creation_serialize(&a->profile,profile,sizeof(profile),&z))return err(e,n,"invalid active source creation profile");
 if(oa_creator_game_export(game,&a->gameplay,nested,sizeof(nested),&nz,e,n))return 1;
 profile_hash(digest);putbytes(&c,digest,32);put64(&c,h->config.generation);put32(&c,(uint32_t)z);putbytes(&c,profile,z);
 for(i=0;i<9;i++)put32(&c,(uint32_t)a->owner.skill_raw[i]);
 put32(&c,a->owner.patron_id);put32(&c,a->owner.health);put32(&c,a->owner.max_health);put32(&c,a->owner.destiny_buff_id);put32(&c,a->owner.destiny_identifier);
 put32(&c,a->owner.game_started);put32(&c,a->owner.passive_aggressive_disabled);put32(&c,a->owner.destiny_locked);put32(&c,a->owner.fateweaver_locked);
 put32(&c,(uint32_t)a->owner.quest_stage);put32(&c,a->owner.finalized);put32(&c,a->owner.package4_active);
 put32(&c,a->owner.stealth_buff_registered);put32(&c,a->owner.reckoning_buff_registered);
 put32(&c,a->owner.stealth_exiting);put32(&c,a->owner.target_can_see_player);put32(&c,a->owner.reckoning_active);
 put64(&c,a->owner.revision);put32(&c,a->owner.item_count);
 for(i=0;i<a->owner.item_count;i++){const oa_creation_item*x=a->owner.items+i;put32(&c,x->type);put32(&c,x->count);put32(&c,(uint32_t)x->equipped_slot);put32(&c,x->hidden);}
 put32(&c,(uint32_t)nz);putbytes(&c,nested,nz);
 if(c.bad)return err(e,n,"combined profile/gameplay capacity exceeded");
 sha256(out+48,c.p-48,digest);memcpy(out,"OACGCP1",8);{codec head={out,48,8,0};put32(&head,1);put32(&head,(uint32_t)(c.p-48));putbytes(&head,digest,32);}*outn=c.p;return 0;
}
static int decode(oa_creation_gameplay*h,const unsigned char*raw,size_t n,oa_creation_active*a,unsigned char*nested,size_t*nz,char*e,size_t cap){
 unsigned char digest[32],profile[OA_CREATION_ENVELOPE_MAX];codec hd={(unsigned char*)raw,n,8,0},c={(unsigned char*)raw,n,48,0};uint32_t z;unsigned i;
 if(n<48||n>CHECKPOINT_CAP||memcmp(raw,"OACGCP1",8)||get32(&hd)!=1||get32(&hd)!=n-48)return err(e,cap,"combined creation file magic/version/length invalid");
 sha256(raw+48,n-48,digest);if(!equalbytes(&hd,digest,32))return err(e,cap,"combined creation checksum mismatch");
 profile_hash(digest);if(!equalbytes(&c,digest,32)||get64(&c)!=h->config.generation)return err(e,cap,"combined source profile/generation mismatch");
 memset(a,0,sizeof(*a));z=get32(&c);if(z>sizeof(profile)||z>n-c.p)return err(e,cap,"creation profile size invalid");
 for(i=0;i<z;i++)profile[i]=(unsigned char)get8(&c);if(oa_creation_deserialize(&a->profile,profile,z))return err(e,cap,"active appearance/profile envelope invalid");
 for(i=0;i<9;i++){uint32_t x=get32(&c);memcpy(a->owner.skill_raw+i,&x,4);}
 a->owner.patron_id=get32(&c);a->owner.health=get32(&c);a->owner.max_health=get32(&c);a->owner.destiny_buff_id=get32(&c);a->owner.destiny_identifier=get32(&c);
 a->owner.game_started=get32(&c);a->owner.passive_aggressive_disabled=get32(&c);a->owner.destiny_locked=get32(&c);a->owner.fateweaver_locked=get32(&c);
 {uint32_t x=get32(&c);memcpy(&a->owner.quest_stage,&x,4);}a->owner.finalized=get32(&c);a->owner.package4_active=get32(&c);
 a->owner.stealth_buff_registered=get32(&c);a->owner.reckoning_buff_registered=get32(&c);
 a->owner.stealth_exiting=get32(&c);a->owner.target_can_see_player=get32(&c);a->owner.reckoning_active=get32(&c);
 a->owner.revision=get64(&c);a->owner.item_count=get32(&c);
 if(a->owner.item_count>OA_CG_ITEMS_MAX)return err(e,cap,"inventory owner capacity invalid");
 for(i=0;i<a->owner.item_count;i++){oa_creation_item*x=a->owner.items+i;uint32_t y;x->type=get32(&c);x->count=get32(&c);y=get32(&c);memcpy(&x->equipped_slot,&y,4);x->hidden=get32(&c);}
 z=get32(&c);if(z>8192||z>n-c.p)return err(e,cap,"opening nested state size invalid");for(i=0;i<z;i++)nested[i]=(unsigned char)get8(&c);
 if(c.bad||c.p!=n||!owner_valid(h,a)||a->owner.package4_active!=(uint32_t)h->config.package4_active)return err(e,cap,"combined typed owner state invalid");
 *nz=z;return 0;
}
#ifdef _WIN32
static wchar_t *wide(const char*s){int n=MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,s,-1,NULL,0);wchar_t*p;if(n<=0||n>32767)return NULL;p=(wchar_t*)malloc((size_t)n*sizeof(*p));if(p&&!MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,s,-1,p,n)){free(p);return NULL;}return p;}
static FILE *open_read(const char*s){wchar_t*p=wide(s);FILE*f=p?_wfopen(p,L"rb"):NULL;free(p);return f;}
#else
static FILE *open_read(const char*s){return fopen(s,"rb");}
#endif
/* Missing is distinct from corrupt/unreadable; existing bad files are preserved. */
static int read_file(const char*path,unsigned char*out,size_t*n,int*missing,char*e,size_t cap){
 FILE*f;size_t k;*missing=0;errno=0;f=open_read(path);if(!f){if(errno==ENOENT){*missing=1;return 0;}return err(e,cap,"opening checkpoint cannot be opened");}
 k=fread(out,1,CHECKPOINT_CAP,f);if(ferror(f)||fgetc(f)!=EOF){fclose(f);return err(e,cap,"opening checkpoint read/size invalid");}if(fclose(f))return err(e,cap,"opening checkpoint read close failed");*n=k;return 0;
}
static int atomic_replace(oa_creation_gameplay*h,const unsigned char*raw,size_t n,char*e,size_t cap){
 char temp[1200];unsigned trial;h->attempts++;
#ifdef _WIN32
 HANDLE file=INVALID_HANDLE_VALUE;wchar_t*wt=NULL,*wd=NULL;DWORD written;size_t at=0;int committed=0;
 for(trial=0;trial<8;trial++){snprintf(temp,sizeof(temp),"%s.tmp.%lu.%" PRIxPTR ".%u",h->path,(unsigned long)GetCurrentProcessId(),(uintptr_t)h,++h->temp_sequence);wt=wide(temp);if(!wt)return err(e,cap,"opening temporary path invalid");file=CreateFileW(wt,GENERIC_WRITE,0,NULL,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,NULL);if(file!=INVALID_HANDLE_VALUE)break;{DWORD why=GetLastError();free(wt);wt=NULL;if(why!=ERROR_FILE_EXISTS&&why!=ERROR_ALREADY_EXISTS)return err(e,cap,"opening temporary checkpoint create failed");}}
 if(file==INVALID_HANDLE_VALUE)return err(e,cap,"opening temporary checkpoint collision limit");
 while(at<n){DWORD chunk=(DWORD)(n-at);if(!WriteFile(file,raw+at,chunk,&written,NULL)||!written)goto win_done;at+=written;}
 if(!FlushFileBuffers(file))goto win_done;if(!CloseHandle(file)){file=INVALID_HANDLE_VALUE;goto win_done;}file=INVALID_HANDLE_VALUE;wd=wide(h->path);if(!wd)goto win_done;
 if(!MoveFileExW(wt,wd,MOVEFILE_REPLACE_EXISTING|MOVEFILE_WRITE_THROUGH))goto win_done;committed=1;
win_done:if(file!=INVALID_HANDLE_VALUE)CloseHandle(file);if(!committed)DeleteFileW(wt);free(wt);free(wd);if(!committed)return err(e,cap,"opening atomic checkpoint replacement failed");return 0;
#else
 int fd=-1,committed=0;size_t at=0;
 for(trial=0;trial<8;trial++){snprintf(temp,sizeof(temp),"%s.tmp.%lu.%" PRIxPTR ".%u",h->path,(unsigned long)getpid(),(uintptr_t)h,++h->temp_sequence);fd=open(temp,O_WRONLY|O_CREAT|O_EXCL,0600);if(fd>=0)break;if(errno!=EEXIST)return err(e,cap,"opening temporary checkpoint create failed");}
 if(fd<0)return err(e,cap,"opening temporary checkpoint collision limit");while(at<n){ssize_t k=write(fd,raw+at,n-at);if(k<0&&errno==EINTR)continue;if(k<=0)goto posix_done;at+=(size_t)k;}
 if(fsync(fd))goto posix_done;if(close(fd)){fd=-1;goto posix_done;}fd=-1;if(rename(temp,h->path))goto posix_done;committed=1;
posix_done:if(fd>=0)close(fd);if(!committed)unlink(temp);if(!committed)return err(e,cap,"opening atomic checkpoint replacement failed");
 /* Rename is the logical commit point. Directory durability is best effort;
  * a later directory-fsync failure must NOT report rollback after a committed file. */
 {char parent[1024],*slash;int d;snprintf(parent,sizeof(parent),"%s",h->path);slash=strrchr(parent,'/');if(slash){if(slash==parent)slash[1]=0;else *slash=0;}else strcpy(parent,".");d=open(parent,O_RDONLY);if(d>=0){if(fsync(d))h->warnings++;close(d);}else h->warnings++;}return 0;
#endif
}

static int persist(oa_creation_gameplay*h,oa_creator_game_host*game,const oa_creation_active*a,char*e,size_t cap){
 unsigned char bytes[CHECKPOINT_CAP],prior[CHECKPOINT_CAP],nested[8192];size_t n=0,z=0,oldn=0;int missing;oa_creation_active old;
 if(encode(h,game,a,bytes,&n,e,cap)||read_file(h->path,prior,&oldn,&missing,e,cap))return 1;
 if(!missing&&decode(h,prior,oldn,&old,nested,&z,e,cap))return err(e,cap,"incompatible existing creator file preserved");
 if(atomic_replace(h,bytes,n,e,cap))return 1;h->writes++;return 0;
}
/* Core calls only while its actor/UI operation is still privately prepared. */
static int durable(void*v,const oa_creator_game_state*s,char*e,size_t n){
 oa_creation_gameplay*h=v;oa_creation_active a=h->active;
 if(!a.owner.finalized||h->busy)return err(e,n,"outer profile unavailable for source autosave");
 a.gameplay=*s;return persist(h,h->game,&a,e,n);
}
static oa_creator_game_host*new_game(oa_creation_gameplay*h,int32_t stage,char*e,size_t n){
 oa_creator_game_config c;memset(&c,0,sizeof(c));c.generation=h->config.generation;c.item_instance=h->config.item_instance;c.item_index=h->config.item_index;
 c.tutorials_enabled=h->config.tutorials_enabled;c.checkpoint_path=h->path;c.report_context=h->config.report_context;c.report_failure=h->config.report_failure;
 c.pose_validation_context=h->config.pose_context;c.validate_load_pose=h->config.validate_load_pose;c.backend=h->config.gameplay_backend;c.runtime=h->config.runtime;c.owner_quest_stage=stage;
 c.durable_context=h;c.durable_write=durable;return oa_creator_game_create(&h->assets,&c,e,n);
}
typedef struct startup_context {oa_creation_gameplay*h;oa_creation_owner_state*owner;oa_mq01_cursor*cursor;int failed;unsigned start_seen,set_seen,flags_seen;} startup_context;
static startup_context*ctx(lua_State*L){return lua_touserdata(L,lua_upvalueindex(1));}
static int cursor_apply(void*v,const oa_mq01_request*r,char*e,size_t n){
 startup_context*c=v;
 if(r->operation==OA_MQ01_START&&r->previous_stage==-1&&r->target_stage==0){c->owner->quest_stage=0;c->start_seen++;return 0;}
 if(r->operation==OA_MQ01_SET_STAGE&&r->previous_stage==0&&r->target_stage==5&&c->start_seen==1){c->owner->quest_stage=5;c->set_seen++;return 0;}
 return err(e,n,"unsupported source quest callback transition");
}
static int l_resolve(lua_State*L){const char*s=luaL_checkstring(L,1);if(strcmp(s,"MQ01"))return luaL_error(L,"unsupported source quest name");lua_pushinteger(L,613083);return 1;}
static int l_start(lua_State*L){
 startup_context*c=ctx(L);oa_mq01_snapshot s;oa_mq01_request r;oa_mq01_noop why;char e[256]="";
 if(luaL_checkinteger(L,1)!=613083||c->start_seen||oa_mq01_query(c->cursor,613083,c->h->config.generation,&s)!=OA_MQ01_OK||
 oa_mq01_prepare_start(c->cursor,&s,&r,&why)!=OA_MQ01_OK||oa_mq01_commit(c->cursor,c->h->config.generation,&r,cursor_apply,c,e,sizeof(e))!=OA_MQ01_OK)return luaL_error(L,"source start_quest rejected:%s",e);
 return 0;
}
static int l_set(lua_State*L){
 startup_context*c=ctx(L);oa_mq01_snapshot s;oa_mq01_request r;oa_mq01_noop why;char e[256]="";
 if(luaL_checkinteger(L,1)!=613083||luaL_checkinteger(L,2)!=5||c->set_seen||oa_mq01_query(c->cursor,613083,c->h->config.generation,&s)!=OA_MQ01_OK||
 oa_mq01_prepare_set(c->cursor,&s,5,&r,&why)!=OA_MQ01_OK)return luaL_error(L,"source stage5 preparation rejected");
 /* Authored stage5 callback is exactly RETURN; execute that exact body. */
 lua_getglobal(L,"__mq_stage5");lua_call(L,0,0);
 if(oa_mq01_commit(c->cursor,c->h->config.generation,&r,cursor_apply,c,e,sizeof(e))!=OA_MQ01_OK)return luaL_error(L,"source stage5 rejected:%s",e);return 0;
}
static int l_game(lua_State*L){startup_context*c=ctx(L);if(!lua_isboolean(L,1)||!lua_toboolean(L,1)||c->owner->quest_stage!=5)return luaL_error(L,"invalid source game-start");c->owner->game_started=1;c->flags_seen|=1;return 0;}
static int l_passive(lua_State*L){startup_context*c=ctx(L);if(!lua_isboolean(L,1)||!lua_toboolean(L,1))return luaL_error(L,"invalid source passive flag");c->owner->passive_aggressive_disabled=1;c->flags_seen|=2;return 0;}
static int l_destiny(lua_State*L){startup_context*c=ctx(L);c->owner->destiny_locked=1;c->flags_seen|=4;return 0;}
static int l_fate(lua_State*L){startup_context*c=ctx(L);c->owner->fateweaver_locked=1;c->flags_seen|=8;return 0;}
static void closure(lua_State*L,startup_context*c,lua_CFunction f){lua_pushlightuserdata(L,c);lua_pushcclosure(L,f,1);}
static int install(lua_State*L){
 startup_context*c=lua_touserdata(L,1);
 lua_newtable(L);closure(L,c,l_start);lua_setfield(L,-2,"start_quest");closure(L,c,l_set);lua_setfield(L,-2,"set_stage");lua_setglobal(L,"QUEST");
 closure(L,c,l_resolve);lua_setglobal(L,"QUEST_ID");closure(L,c,l_game);lua_setglobal(L,"set_game_start");
 lua_newtable(L);closure(L,c,l_passive);lua_setfield(L,-2,"set_disable_aggressive_mode");lua_setglobal(L,"Passive");
 lua_newtable(L);closure(L,c,l_destiny);lua_setfield(L,-2,"lock_destiny");closure(L,c,l_fate);lua_setfield(L,-2,"lock_fateweaver");lua_setglobal(L,"destiny_manager");return 0;
}
static int source_start(oa_creation_gameplay*h,oa_creation_owner_state*owner,char*e,size_t n){
 amalur_runtime_config cfg;amalur_runtime_source sources[5];amalur_runtime*rt=NULL;lua_State*L;startup_context c;int count=0,bad=1;unsigned i;
 memset(&c,0,sizeof(c));c.h=h;c.owner=owner;
 if(oa_mq01_create(613083,h->config.generation,&c.cursor)!=OA_MQ01_OK)return err(e,n,"source MQ01 constructor unavailable");
 memset(&cfg,0,sizeof(cfg));for(i=0;i<5;i++){sources[i].name=startup_specs[i].name;sources[i].data=h->startup[i].bytes;sources[i].length=h->startup[i].n;}
 cfg.runtime_sources=sources;cfg.runtime_source_count=5;cfg.instruction_budget=h->config.runtime.instruction_budget?h->config.runtime.instruction_budget:200000;
 cfg.memory_limit_bytes=h->config.runtime.lua_memory_bytes?h->config.runtime.lua_memory_bytes:64u*1024u*1024u;
 rt=amalur_runtime_create(&cfg,e,n);if(!rt)goto done;L=amalur_runtime_state(rt);
 if(lua_cpcall(L,install,&c)){err(e,n,"source startup C provider allocation failed");goto done;}
 for(i=5;i<7;i++)if(amalur_runtime_register_module_source(rt,startup_specs[i].name,h->startup[i].bytes,h->startup[i].n,e,n))goto done;
 {const char code[]="__mq_stage5=require('__mq_stage5'); return require('__mq_start')()";
 if(amalur_runtime_eval_source(rt,code,sizeof(code)-1,"source-MQ01-creator-finish",&count,e,n))goto done;}
 if(c.start_seen!=1||c.set_seen!=1||c.flags_seen!=15||owner->quest_stage!=5){err(e,n,"source startup effect sequence incomplete");goto done;}
 bad=0;
done:if(rt)amalur_runtime_destroy(rt);oa_mq01_destroy(&c.cursor);return bad;
}
oa_creation_gameplay*oa_creation_gameplay_create(const oa_opening_assets*a,const oa_creation_gameplay_config*c,char*e,size_t n){
 oa_creation_gameplay*h;size_t z,suf=strlen(SUFFIX);unsigned i;
 if(!a||!a->size||!a->read||!c||!c->generation||!c->item_instance||c->item_index<0||!c->path||
 !c->report_failure||!c->base_max_health||c->base_max_health>=INT32_MAX||c->current_health>c->base_max_health||
 c->package4_active< -1||c->package4_active>1)return(err(e,n,"explicit creator gameplay configuration required"),(oa_creation_gameplay*)NULL);
 z=strlen(c->path);if(z>=1024||z<suf||strcmp(c->path+z-suf,SUFFIX))return(err(e,n,"separate *.creation-gameplay-v1.bin required"),(oa_creation_gameplay*)NULL);
 h=calloc(1,sizeof(*h));if(!h)return NULL;h->assets=*a;h->config=*c;snprintf(h->path,sizeof(h->path),"%s",c->path);
 for(i=0;i<8;i++){
  size_t k=0;unsigned char digest[32];
  if(a->size(a->context,startup_specs[i].path,&k,e,n)||k!=startup_specs[i].size||k>1048576)goto fail;
  h->startup[i].bytes=malloc(k?k:1);h->startup[i].n=k;if(!h->startup[i].bytes||a->read(a->context,startup_specs[i].path,h->startup[i].bytes,k,e,n))goto fail;
  sha256(h->startup[i].bytes,k,digest);if(memcmp(digest,startup_specs[i].sha,32)){err(e,n,"source startup asset hash mismatch");goto fail;}
 }return h;
fail:oa_creation_gameplay_close(h);return NULL;
}
void oa_creation_gameplay_close(oa_creation_gameplay*h){unsigned i;if(!h||h->busy)return;oa_creator_game_close(h->game);for(i=0;i<8;i++)free(h->startup[i].bytes);free(h);}
static int publish(oa_creation_gameplay*h,int loading,oa_creation_active*a,oa_creator_game_host*candidate,int save,char*e,size_t n){
 oa_creation_render_selection selection;void*token=NULL;oa_creation_publish*b=&h->config.appearance;
 if(!b->prepare||!b->commit||!b->abort)return(err(e,n,"actual CPU/GPU appearance and owner-state publisher unavailable"),OA_CG_UNAVAILABLE);
 if(!owner_valid(h,a)||oa_creation_render(&a->profile,&selection))return err(e,n,"source complete profile invalid");
 if(b->prepare(b->context,loading,a,&selection,&token,e,n))return OA_CG_UNAVAILABLE;
 if(save&&persist(h,candidate,a,e,n)){b->abort(b->context,token);return 1;}
 /* File rename is commit point; publication must be pre-reserved/infallible. */
 b->commit(b->context,token);{oa_creator_game_host*old=h->game;h->game=candidate;h->active=*a;oa_creator_game_close(old);}return 0;
}
int oa_creation_gameplay_complete(oa_creation_gameplay*h,const oa_creation_state*draft,uint64_t transaction,const oa_creator_game_pose*pose,char*e,size_t n){
 oa_creation_active a;oa_creation_commit commit;oa_creator_game_host*candidate=NULL;float maxhp;const int16_t*skills;unsigned i;int r=1;size_t base_count=sizeof(source_items)/sizeof(source_items[0]);
 if(enter(h,e,n))return 1;if(h->active.owner.finalized)return OA_CG_ALREADY_ACTIVE;
 if(!draft||draft->phase!=OA_CREATION_DRAFT||!transaction||!pose||oa_creation_validate(draft))return err(e,n,"valid confirmed source draft/transaction/pose required");
 if(h->config.package4_active<0)return(err(e,n,"package4 activity unavailable; not inferred from assets"),OA_CG_UNAVAILABLE);
 {unsigned char raw[CHECKPOINT_CAP],nested[8192];size_t z=0,nz=0;int missing;oa_creation_active prior;
 if(read_file(h->path,raw,&z,&missing,e,n))return 1;
 if(!missing){if(decode(h,raw,z,&prior,nested,&nz,e,n))return err(e,n,"existing incompatible creator file preserved");return OA_CG_ALREADY_ACTIVE;}}
 h->busy=1;memset(&a,0,sizeof(a));a.profile=*draft;
 if(oa_creation_finalize(&a.profile,transaction,&commit)||oa_creation_acknowledge(&a.profile,transaction)){err(e,n,"source profile transaction invalid");goto done;}
 a.owner.patron_id=commit.patron_buff_id;skills=oa_creation_source_skills(draft->race);for(i=0;i<9;i++)a.owner.skill_raw[i]=skills[i];
 if(oa_creation_patron_apply(a.owner.patron_id,1657941u,1,(float)h->config.base_max_health,&maxhp,e,n)||maxhp<1||maxhp>=2147483648.0f)goto done;
 a.owner.max_health=(uint32_t)maxhp;a.owner.health=a.owner.max_health; /* Source adds max then clamps. */
 a.owner.quest_stage=-1;a.owner.destiny_buff_id=385357u;a.owner.destiny_identifier=9325294u;
 if(source_start(h,&a.owner,e,n))goto done;
 a.owner.finalized=1;a.owner.revision=1;a.owner.package4_active=(uint32_t)h->config.package4_active;
 a.owner.stealth_buff_registered=1;a.owner.reckoning_buff_registered=1;
 a.owner.item_count=(uint32_t)base_count;memcpy(a.owner.items,source_items,sizeof(source_items));
 if(a.owner.package4_active)for(i=0;i<3;i++){oa_creation_item*x=a.owner.items+a.owner.item_count++;x->type=source_package4_recipes[i];x->count=1;x->equipped_slot=-1;x->hidden=0;}
 candidate=new_game(h,5,e,n);if(!candidate)goto done;
 if(oa_creator_game_update_pose(candidate,pose,e,n)||oa_creator_game_snapshot(candidate,&a.gameplay,e,n))goto done;
 r=publish(h,0,&a,candidate,1,e,n);if(!r)candidate=NULL;
done:if(candidate)oa_creator_game_close(candidate);h->busy=0;return r;
}
int oa_creation_gameplay_snapshot(oa_creation_gameplay*h,oa_creation_active*out,char*e,size_t n){
 if(enter(h,e,n))return 1;if(!out||!h->active.owner.finalized)return err(e,n,"active creator profile unavailable");
 *out=h->active;return oa_creator_game_snapshot(h->game,&out->gameplay,e,n);
}
oa_creator_game_host*oa_creation_gameplay_game(oa_creation_gameplay*h){return h&&!h->busy&&h->active.owner.finalized?h->game:NULL;}
int oa_creation_gameplay_save(oa_creation_gameplay*h,char*e,size_t n){
 oa_creation_active a;oa_creator_game_stats stats;int r;if(oa_creation_gameplay_snapshot(h,&a,e,n))return 1;
 oa_creator_game_get_stats(h->game,&stats);if(stats.latched||stats.poisoned)return err(e,n,"latched/poisoned opening state cannot be saved");
 h->busy=1;r=persist(h,h->game,&a,e,n);h->busy=0;return r;
}
int oa_creation_gameplay_load(oa_creation_gameplay*h,char*e,size_t n){
 unsigned char raw[CHECKPOINT_CAP],nested[8192];size_t z=0,nz=0;int missing,r=1;oa_creation_active a;oa_creator_game_host*candidate=NULL;
 if(enter(h,e,n))return 1;h->busy=1;
 if(read_file(h->path,raw,&z,&missing,e,n)||missing){if(missing)err(e,n,"combined creator profile absent");goto done;}
 if(decode(h,raw,z,&a,nested,&nz,e,n))goto done;
 candidate=new_game(h,5,e,n);if(!candidate)goto done;
 if(oa_creator_game_import(candidate,nested,nz,e,n)||oa_creator_game_snapshot(candidate,&a.gameplay,e,n))goto done;
 if(h->config.validate_load_pose&&h->config.validate_load_pose(h->config.pose_context,&a.gameplay.pose,e,n))goto done;
 r=publish(h,1,&a,candidate,0,e,n);if(!r)candidate=NULL;
done:if(candidate)oa_creator_game_close(candidate);h->busy=0;return r;
}
int oa_creation_gameplay_action_allowed(oa_creation_gameplay*h,unsigned action){
 if(!h||h->busy||!h->active.owner.finalized)return 0;
 switch(action){case OA_CG_ACTION_DESTINY:return !h->active.owner.destiny_locked;case OA_CG_ACTION_FATEWEAVE:return !h->active.owner.fateweaver_locked;case OA_CG_ACTION_AGGRESSIVE:return !h->active.owner.passive_aggressive_disabled;default:return 0;}
}
int oa_creation_gameplay_combat_gates(oa_creation_gameplay*h,int stealth,int sees,int reckoning,char*e,size_t n){
 if(enter(h,e,n))return 1;if(!h->active.owner.finalized||((stealth!=0&&stealth!=1)||(sees!=0&&sees!=1)||(reckoning!=0&&reckoning!=1)))return err(e,n,"actual typed source combat gates required");
 if(h->active.owner.stealth_exiting!=(uint32_t)stealth||h->active.owner.target_can_see_player!=(uint32_t)sees||h->active.owner.reckoning_active!=(uint32_t)reckoning){
 if(h->active.owner.revision==UINT64_MAX)return err(e,n,"owner revision exhausted");
 h->active.owner.stealth_exiting=(uint32_t)stealth;h->active.owner.target_can_see_player=(uint32_t)sees;h->active.owner.reckoning_active=(uint32_t)reckoning;h->active.owner.revision++;
 }return 0;
}
int oa_creation_gameplay_stat(oa_creation_gameplay*h,uint32_t key,int integer,float base,float*out,char*e,size_t n){
 float x=base;if(!out)return err(e,n,"stat output required");if(enter(h,e,n))return 1;if(!h->active.owner.finalized)return err(e,n,"active source stats unavailable");
 if(oa_creation_patron_apply(h->active.owner.patron_id,key,integer,x,&x,e,n))return 1;
 if(h->active.owner.stealth_exiting&&!h->active.owner.target_can_see_player&&eval_record(source_global_buffs,key,integer,x,&x,e,n))return 1;
 if(h->active.owner.reckoning_active&&eval_record(source_global_buffs+1,key,integer,x,&x,e,n))return 1;
 *out=x;return 0;
}
int oa_creation_gameplay_health(oa_creation_gameplay*h,int32_t delta,char*e,size_t n){
 int64_t hp;if(enter(h,e,n))return 1;if(!h->active.owner.finalized)return err(e,n,"active health unavailable");
 hp=(int64_t)h->active.owner.health+delta;if(hp<0)hp=0;if(hp>h->active.owner.max_health)hp=h->active.owner.max_health;if(h->active.owner.health!=(uint32_t)hp){if(h->active.owner.revision==UINT64_MAX)return err(e,n,"owner revision exhausted");h->active.owner.health=(uint32_t)hp;h->active.owner.revision++;}return 0;
}

int oa_creation_gameplay_actor_state(oa_creation_gameplay*h,const char*name,int*out,char*e,size_t n){
 size_t i;if(enter(h,e,n))return 1;if(!name||!out||!h->active.owner.finalized)return err(e,n,"actual actor-state query required");
 if(!strcmp(name,"Stealth_Exiting")){*out=(int)h->active.owner.stealth_exiting;return 0;}
 if(!strcmp(name,"ReckoningMode")){*out=(int)h->active.owner.reckoning_active;return 0;}
 for(i=0;i<sizeof(source_skill_states)/sizeof(source_skill_states[0]);i++)if(!strcmp(name,source_skill_states[i].name)){
  *out=oa_creation_skill_tier_active(&h->active.owner,source_skill_states[i].skill,source_skill_states[i].threshold);return 0;
 }
 return OA_CG_UNAVAILABLE;
}

int oa_creation_gameplay_buff(oa_creation_gameplay*h,unsigned i,oa_creation_buff_instance*out){
 if(!h||h->busy||!out||!h->active.owner.finalized||i>=4)return OA_CG_UNAVAILABLE;
 out->duration_ms=-1;
 switch(i){
 case 0:out->id=h->active.owner.patron_id;out->identifier=1731073u;break;
 case 1:out->id=385357u;out->identifier=9325294u;break;
 case 2:out->id=1621687u;out->identifier=35299876u;break;
 default:out->id=633989u;out->identifier=11334545u;break;
 }return 0;
}

int oa_creation_source_package_default(unsigned id,int*out){
 if(!out)return OA_CG_ERROR;
 switch(id){
 case 1:case 2:case 3:case 4:case 6:case 7:case 8:case 9:case 10:case 11:*out=1;return 0;
 case 12:*out=0;return 0;
 default:return OA_CG_UNAVAILABLE;
 }
}
