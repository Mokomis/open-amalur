#include "oa_opening_movement.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <math.h>
#include <float.h>
#include <errno.h>
#include <inttypes.h>
#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#else
#include <unistd.h>
#include <fcntl.h>
#include <sys/stat.h>
#endif
#include "movement_sha256.h"
typedef struct movement_volume {const char *name;uint32_t instance;double planes[6][4];} movement_volume;
#include "opening_movement_planes.h"
#define CHECKPOINT_CAP 8192u
#define CHECKPOINT_SUFFIX ".opening-checkpoint-v1.bin"
#define SCENE 1417252u
#define REGION 1262814u
typedef char movement_float_must_be_ieee32[(sizeof(float)==4&&FLT_RADIX==2&&FLT_MANT_DIG==24&&FLT_MAX_EXP==128)?1:-1];
typedef struct checkpoint_state {oa_movement_pose pose;oa_opening_snapshot lua;oa_movement_tutorial tutorial[3];uint32_t inside,skipped;} checkpoint_state;
struct oa_movement_host {
 oa_opening_runtime *runtime;oa_movement_config config;
 char path[1024],identity[128],error[512];
 oa_movement_pose pose,pending_pose,failed_pose;
 oa_movement_tutorial tutorial[3];
 uint32_t inside,initialized,skipped,pending_inside,failed_inside;
 unsigned busy,latched,failed_exits,temp_sequence;
 uint64_t writes,attempts,failures,reports,warnings;
};
static const uint32_t tutorial_ids[3]={17524338u,26339831u,40879367u};
static int error(char *e,size_t c,const char *s){if(e&&c)snprintf(e,c,"%s",s?s:"opening movement failure");return OA_MOVEMENT_ERROR;}
static int start(oa_movement_host*h,char*e,size_t c){if(e&&c)e[0]=0;if(!h)return error(e,c,"opening movement host unavailable");if(h->busy)return error(e,c,"opening movement reentry rejected");return 0;}
static int pose_valid(const oa_movement_pose*p){unsigned i;if(!p)return 0;for(i=0;i<3;i++)if(!isfinite(p->feet[i]))return 0;return isfinite(p->yaw)&&isfinite(p->pitch);}
static uint32_t containment(const oa_movement_pose*p){unsigned i,j;uint32_t mask=0;for(i=0;i<3;i++){int inside=1;for(j=0;j<6;j++){const double*q=source_volumes[i].planes[j];double d=q[0]*(double)p->feet[0]+q[1]*(double)p->feet[1]+q[2]*(double)p->feet[2]+q[3];if(d>0){inside=0;break;}}if(inside)mask|=1u<<i;}return mask;}
static int tutorial_index(uint32_t id){unsigned i;for(i=0;i<3;i++)if(tutorial_ids[i]==id)return (int)i;return -1;}
typedef struct codec {unsigned char *b;size_t n,p;int bad;} codec;
static void put8(codec*c,unsigned x){if(c->p>=c->n){c->bad=1;return;}c->b[c->p++]=(unsigned char)x;}
static unsigned get8(codec*c){if(c->p>=c->n){c->bad=1;return 0;}return c->b[c->p++];}
static void put32(codec*c,uint32_t x){unsigned i;for(i=0;i<4;i++)put8(c,x>>(i*8));}
static uint32_t get32(codec*c){uint32_t x=0;unsigned i;for(i=0;i<4;i++)x|=(uint32_t)get8(c)<<(i*8);return x;}
static void put64(codec*c,uint64_t x){unsigned i;for(i=0;i<8;i++)put8(c,(unsigned)(x>>(i*8)));}
static uint64_t get64(codec*c){uint64_t x=0;unsigned i;for(i=0;i<8;i++)x|=(uint64_t)get8(c)<<(i*8);return x;}
static void putfloat(codec*c,float f){uint32_t x;memcpy(&x,&f,4);put32(c,x);}
static float getfloat(codec*c){uint32_t x=get32(c);float f;memcpy(&f,&x,4);return f;}
static void putbytes(codec*c,const void*p,size_t n){size_t i;for(i=0;i<n;i++)put8(c,((const unsigned char*)p)[i]);}
static int equalbytes(codec*c,const void*p,size_t n){size_t i;int eq=1;for(i=0;i<n;i++)if(get8(c)!=((const unsigned char*)p)[i])eq=0;return eq&&!c->bad;}
static int movement_snapshot_valid(const oa_opening_snapshot*s){
 /* This host has NO sword/quest/door producer. It never admits their restored
  * state/timers from another profile and therefore cannot manufacture progress. */
 return s->version==1&&s->wos_flags<(1u<<17)&&s->sword_flags==0&&s->sword_get==0&&s->cinematic_flags<=1&&s->timer_count==0&&s->clock_ms<=UINT64_C(9007194959773695)&&s->serial<=UINT64_C(9007194959773695);
}
static int encode(oa_movement_host*h,const checkpoint_state*s,unsigned char*out,size_t*out_n,char*e,size_t cap){
 codec c={out,CHECKPOINT_CAP,48,0};unsigned i;unsigned char digest[32];size_t idn=strlen(h->identity);if(!pose_valid(&s->pose)||!movement_snapshot_valid(&s->lua)||s->skipped!=s->lua.cinematic_flags||s->inside!=containment(&s->pose))return error(e,cap,"incoherent opening checkpoint candidate");
 putbytes(&c,volume_profile,32);putbytes(&c,runtime_profile,32);put32(&c,SCENE);put32(&c,REGION);put64(&c,h->config.generation);put32(&c,(uint32_t)idn);putbytes(&c,h->identity,idn);
 for(i=0;i<3;i++)putfloat(&c,s->pose.feet[i]);putfloat(&c,s->pose.yaw);putfloat(&c,s->pose.pitch);put32(&c,s->inside);put32(&c,s->skipped);
 put32(&c,3);for(i=0;i<3;i++){const oa_movement_tutorial*t=s->tutorial+i;if(t->id!=tutorial_ids[i]||t->active>1||t->fired>1)return error(e,cap,"invalid tutorial registry candidate");put32(&c,t->id);put32(&c,t->active);put32(&c,t->fired);put32(&c,t->kills);}
 put32(&c,s->lua.version);put32(&c,s->lua.wos_flags);put32(&c,s->lua.sword_flags);put32(&c,s->lua.cinematic_flags);put32(&c,(uint32_t)s->lua.sword_get);put64(&c,s->lua.clock_ms);put64(&c,s->lua.serial);put32(&c,s->lua.timer_count);
 /* Field-wise timer encoding is versioned even though movement profile requires0. */
 for(i=0;i<s->lua.timer_count;i++){const oa_opening_timer*t=s->lua.timers+i;put32(&c,t->hash);put64(&c,t->due_ms);put64(&c,t->serial);put32(&c,t->argc);put32(&c,(uint32_t)t->item_index);}
 if(c.bad)return error(e,cap,"opening checkpoint exceeds bounded envelope");sha256(out+48,c.p-48,digest);memcpy(out,"OAMVCP1",8);{codec head={out,48,8,0};put32(&head,1);put32(&head,(uint32_t)(c.p-48));putbytes(&head,digest,32);}*out_n=c.p;return 0;
}
static int decode(oa_movement_host*h,const unsigned char*raw,size_t n,checkpoint_state*s,char*e,size_t cap){
 unsigned char digest[32];codec head={(unsigned char*)raw,n,8,0},c={(unsigned char*)raw,n,48,0};unsigned i;uint32_t bytes,idn;uint64_t gen;
 if(n<48||n>CHECKPOINT_CAP||memcmp(raw,"OAMVCP1",8))return error(e,cap,"opening checkpoint magic/size invalid");
 if(get32(&head)!=1)return error(e,cap,"opening checkpoint version unsupported");bytes=get32(&head);if(bytes!=n-48)return error(e,cap,"opening checkpoint length mismatch");sha256(raw+48,n-48,digest);if(!equalbytes(&head,digest,32))return error(e,cap,"opening checkpoint SHA256 mismatch");
 memset(s,0,sizeof(*s));if(!equalbytes(&c,volume_profile,32)||!equalbytes(&c,runtime_profile,32))return error(e,cap,"opening checkpoint source profile mismatch");
 if(get32(&c)!=SCENE||get32(&c)!=REGION)return error(e,cap,"opening checkpoint scene mismatch");gen=get64(&c);if(gen!=h->config.generation)return error(e,cap,"opening checkpoint generation mismatch");idn=get32(&c);if(idn!=strlen(h->identity)||idn>127||!equalbytes(&c,h->identity,idn))return error(e,cap,"opening checkpoint registry identity mismatch");
 for(i=0;i<3;i++)s->pose.feet[i]=getfloat(&c);s->pose.yaw=getfloat(&c);s->pose.pitch=getfloat(&c);s->inside=get32(&c);s->skipped=get32(&c);if(get32(&c)!=3)return error(e,cap,"opening checkpoint tutorial count invalid");
 for(i=0;i<3;i++){oa_movement_tutorial*t=s->tutorial+i;t->id=get32(&c);t->active=get32(&c);t->fired=get32(&c);t->kills=get32(&c);if(t->id!=tutorial_ids[i]||t->active>1||t->fired>1)return error(e,cap,"opening checkpoint tutorial state invalid");}
 s->lua.version=get32(&c);s->lua.wos_flags=get32(&c);s->lua.sword_flags=get32(&c);s->lua.cinematic_flags=get32(&c);{uint32_t x=get32(&c);memcpy(&s->lua.sword_get,&x,4);}s->lua.clock_ms=get64(&c);s->lua.serial=get64(&c);s->lua.timer_count=get32(&c);
 if(s->lua.timer_count>OA_OPENING_MAX_TIMERS)return error(e,cap,"opening checkpoint timer count invalid");
 for(i=0;i<s->lua.timer_count;i++){oa_opening_timer*t=s->lua.timers+i;uint32_t x;t->hash=get32(&c);t->due_ms=get64(&c);t->serial=get64(&c);t->argc=get32(&c);x=get32(&c);memcpy(&t->item_index,&x,4);}
 if(c.bad||c.p!=n||!pose_valid(&s->pose)||s->inside>7||s->inside!=containment(&s->pose)||s->skipped>1||s->skipped!=s->lua.cinematic_flags||!movement_snapshot_valid(&s->lua))return error(e,cap,"opening checkpoint payload/schema invalid");return 0;
}
#ifdef _WIN32
static wchar_t *wide(const char*s){int n=MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,s,-1,NULL,0);wchar_t*p;if(n<=0||n>32767)return NULL;p=(wchar_t*)malloc((size_t)n*sizeof(*p));if(p&&!MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,s,-1,p,n)){free(p);return NULL;}return p;}
static FILE *open_read(const char*s){wchar_t*p=wide(s);FILE*f=p?_wfopen(p,L"rb"):NULL;free(p);return f;}
#else
static FILE *open_read(const char*s){return fopen(s,"rb");}
#endif
/* Missing is distinct from corrupt/unreadable; existing bad files are preserved. */
static int read_file(const char*path,unsigned char*out,size_t*n,int*missing,char*e,size_t cap){
 FILE*f;size_t k;*missing=0;errno=0;f=open_read(path);if(!f){if(errno==ENOENT){*missing=1;return 0;}return error(e,cap,"opening checkpoint cannot be opened");}
 k=fread(out,1,CHECKPOINT_CAP,f);if(ferror(f)||fgetc(f)!=EOF){fclose(f);return error(e,cap,"opening checkpoint read/size invalid");}if(fclose(f))return error(e,cap,"opening checkpoint read close failed");*n=k;return 0;
}
static int atomic_replace(oa_movement_host*h,const unsigned char*raw,size_t n,char*e,size_t cap){
 char temp[1200];unsigned trial;h->attempts++;
#ifdef _WIN32
 HANDLE file=INVALID_HANDLE_VALUE;wchar_t*wt=NULL,*wd=NULL;DWORD written;size_t at=0;int committed=0;
 for(trial=0;trial<8;trial++){snprintf(temp,sizeof(temp),"%s.tmp.%lu.%" PRIxPTR ".%u",h->path,(unsigned long)GetCurrentProcessId(),(uintptr_t)h,++h->temp_sequence);wt=wide(temp);if(!wt)return error(e,cap,"opening temporary path invalid");file=CreateFileW(wt,GENERIC_WRITE,0,NULL,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,NULL);if(file!=INVALID_HANDLE_VALUE)break;{DWORD why=GetLastError();free(wt);wt=NULL;if(why!=ERROR_FILE_EXISTS&&why!=ERROR_ALREADY_EXISTS)return error(e,cap,"opening temporary checkpoint create failed");}}
 if(file==INVALID_HANDLE_VALUE)return error(e,cap,"opening temporary checkpoint collision limit");
 while(at<n){DWORD chunk=(DWORD)(n-at);if(!WriteFile(file,raw+at,chunk,&written,NULL)||!written)goto win_done;at+=written;}
 if(!FlushFileBuffers(file))goto win_done;if(!CloseHandle(file)){file=INVALID_HANDLE_VALUE;goto win_done;}file=INVALID_HANDLE_VALUE;wd=wide(h->path);if(!wd)goto win_done;
 if(!MoveFileExW(wt,wd,MOVEFILE_REPLACE_EXISTING|MOVEFILE_WRITE_THROUGH))goto win_done;committed=1;
win_done:if(file!=INVALID_HANDLE_VALUE)CloseHandle(file);if(!committed)DeleteFileW(wt);free(wt);free(wd);if(!committed)return error(e,cap,"opening atomic checkpoint replacement failed");return 0;
#else
 int fd=-1,committed=0;size_t at=0;
 for(trial=0;trial<8;trial++){snprintf(temp,sizeof(temp),"%s.tmp.%lu.%" PRIxPTR ".%u",h->path,(unsigned long)getpid(),(uintptr_t)h,++h->temp_sequence);fd=open(temp,O_WRONLY|O_CREAT|O_EXCL,0600);if(fd>=0)break;if(errno!=EEXIST)return error(e,cap,"opening temporary checkpoint create failed");}
 if(fd<0)return error(e,cap,"opening temporary checkpoint collision limit");while(at<n){ssize_t k=write(fd,raw+at,n-at);if(k<0&&errno==EINTR)continue;if(k<=0)goto posix_done;at+=(size_t)k;}
 if(fsync(fd))goto posix_done;if(close(fd)){fd=-1;goto posix_done;}fd=-1;if(rename(temp,h->path))goto posix_done;committed=1;
posix_done:if(fd>=0)close(fd);if(!committed)unlink(temp);if(!committed)return error(e,cap,"opening atomic checkpoint replacement failed");
 /* Rename is the logical commit point. Directory durability is best effort;
  * a later directory-fsync failure must NOT report rollback after a committed file. */
 {char parent[1024],*slash;int d;snprintf(parent,sizeof(parent),"%s",h->path);slash=strrchr(parent,'/');if(slash){if(slash==parent)slash[1]=0;else *slash=0;}else strcpy(parent,".");d=open(parent,O_RDONLY);if(d>=0){if(fsync(d))h->warnings++;close(d);}else h->warnings++;}return 0;
#endif
}
static int checkpoint_write(oa_movement_host*h,const checkpoint_state*s,char*e,size_t cap){
 unsigned char raw[CHECKPOINT_CAP],prior[CHECKPOINT_CAP];size_t n=0,oldn=0;int missing;checkpoint_state old;
 if(encode(h,s,raw,&n,e,cap))return 1;
 if(read_file(h->path,prior,&oldn,&missing,e,cap))return 1;
 if(!missing&&decode(h,prior,oldn,&old,e,cap))return error(e,cap,"existing invalid/incompatible opening checkpoint preserved");
 if(atomic_replace(h,raw,n,e,cap))return 1;h->writes++;return 0;
}
static int query(void*v,enum oa_opening_query kind,int32_t arg,int*out,char*e,size_t cap){
 oa_movement_host*h=v;int i;
 if(kind==OA_OPENING_TUTORIAL_ACTIVE||kind==OA_OPENING_TUTORIAL_FIRED){i=tutorial_index((uint32_t)arg);if(i<0)return error(e,cap,"source tutorial not registered in movement host");*out=(int)(kind==OA_OPENING_TUTORIAL_ACTIVE?h->tutorial[i].active:h->tutorial[i].fired);return 0;}
 if(kind==OA_OPENING_IS_EQUIPPED)return error(e,cap,"source sword1360571 is unmapped; unavailable");
 if(kind==OA_OPENING_GATEWAY_OPEN)return error(e,cap,"native door1790948 is unspawned; unavailable");
 return error(e,cap,"tutorial option/gameplay query unavailable in movement host");
}
static int quest(void*v,uint32_t id,int32_t*out,char*e,size_t cap){(void)v;(void)id;(void)out;return error(e,cap,"native initial quest stage unknown; unavailable");}
static void warning(void*v,const char*s){oa_movement_host*h=v;(void)s;h->warnings++;}
static int apply(void*v,const oa_opening_effect*a,size_t n,const oa_opening_snapshot*candidate,char*e,size_t cap){
 oa_movement_host*h=v;checkpoint_state next;size_t j;int save=0;
 memset(&next,0,sizeof(next));next.pose=h->pending_pose;next.inside=h->pending_inside;next.skipped=h->skipped;next.lua=*candidate;memcpy(next.tutorial,h->tutorial,sizeof(next.tutorial));
 /* Complete effect validation and in-memory preparation BEFORE disk/UI/state. */
 for(j=0;j<n;j++){
  if(a[j].kind==OA_OPENING_KILL_TUTORIAL){int i;if(a[j].argc!=1||(i=tutorial_index((uint32_t)a[j].args[0]))<0)return error(e,cap,"unregistered tutorial kill unavailable");if(next.tutorial[i].kills==UINT32_MAX)return error(e,cap,"tutorial kill counter exhausted");next.tutorial[i].active=0;next.tutorial[i].kills++;}
  else if(a[j].kind==OA_OPENING_AUTOSAVE_REQUEST){if(a[j].argc!=1||a[j].args[0]!=0||save)return error(e,cap,"unsupported checkpoint request");save=1;}
  else return error(e,cap,"unimplemented gameplay/UI effect unavailable in movement host");
 }
 if(!movement_snapshot_valid(candidate))return error(e,cap,"movement host refuses unrelated sword/quest/timer progress");
 if(save&&checkpoint_write(h,&next,e,cap))return 1;
 /* No fallible operation follows the atomic file commit. Rendering consumes this
  * actual registry; there is no pretended native WINDOW service. */
 memcpy(h->tutorial,next.tutorial,sizeof(h->tutorial));return 0;
}
static void latch(oa_movement_host*h,const char*why){
 h->failures++;if(!h->latched){h->latched=1;snprintf(h->error,sizeof(h->error),"%s",why&&why[0]?why:"opening source event failed");h->reports++;h->config.report_failure(h->config.report_context,h->error);}
}
static int dispatch_exits(oa_movement_host*h,unsigned exits,const oa_movement_pose*p,uint32_t inside,char*e,size_t cap){
 unsigned i;h->pending_pose=*p;h->pending_inside=inside;
 for(i=0;i<3;i++)if(exits&(1u<<i)){
  if(oa_opening_runtime_volume_exit(h->runtime,source_volumes[i].name,h->identity,e,cap)){h->failed_pose=*p;h->failed_inside=inside;h->failed_exits=exits&~((1u<<i)-1u);latch(h,e);return OA_MOVEMENT_ERROR;}
  /* Original callbacks commit independently. Preserve any accepted predecessor
   * if a later exit in the same update fails; remaining exits stay latched. */
  h->pose=*p;h->inside=inside;h->initialized=1;
 }
 h->pose=*p;h->inside=inside;h->initialized=1;h->failed_exits=0;return 0;
}
oa_movement_host *oa_movement_host_create(const oa_opening_assets*a,const oa_movement_config*c,char*e,size_t cap){
 oa_movement_host*h;oa_opening_host host;size_t n,suf=strlen(CHECKPOINT_SUFFIX);unsigned i;
 if(!c||!c->generation||!c->checkpoint_path||!c->report_failure)return (error(e,cap,"explicit scene generation, dedicated checkpoint path and failure reporter required"),(oa_movement_host*)NULL);
 n=strlen(c->checkpoint_path);if(n>=1024||n<suf||strcmp(c->checkpoint_path+n-suf,CHECKPOINT_SUFFIX))return (error(e,cap,"dedicated *.opening-checkpoint-v1.bin path required; legacy saves/settings refused"),(oa_movement_host*)NULL);
 h=(oa_movement_host*)calloc(1,sizeof(*h));if(!h)return (error(e,cap,"movement host allocation failed"),(oa_movement_host*)NULL);h->config=*c;snprintf(h->path,sizeof(h->path),"%s",c->checkpoint_path);snprintf(h->identity,sizeof(h->identity),"scene1417252:player1:g%" PRIu64,c->generation);
 for(i=0;i<3;i++)h->tutorial[i].id=tutorial_ids[i];memset(&host,0,sizeof(host));host.context=h;host.player_identity=h->identity;host.query_bool=query;host.quest_stage=quest;host.apply_effects=apply;host.warning=warning;
 h->runtime=oa_opening_runtime_create_from_assets(a,&host,&c->runtime,e,cap);if(!h->runtime){free(h);return NULL;}return h;
}
void oa_movement_host_close(oa_movement_host*h){if(!h)return;oa_opening_runtime_close(h->runtime);free(h);}
int oa_movement_host_cinematic_skipped(oa_movement_host*h,char*e,size_t cap){
 if(start(h,e,cap))return 1;if(h->latched){error(e,cap,h->error);return OA_MOVEMENT_LATCHED;}h->busy=1;
 if(oa_opening_runtime_cinematic_finished(h->runtime,1,e,cap)){latch(h,e);h->busy=0;return 1;}h->skipped=1;h->busy=0;return 0;
}
int oa_movement_host_update_pose(oa_movement_host*h,const oa_movement_pose*p,char*e,size_t cap){
 uint32_t inside;unsigned exits;int r;if(start(h,e,cap))return 1;if(h->latched){error(e,cap,h->error);return OA_MOVEMENT_LATCHED;}if(!pose_valid(p))return error(e,cap,"finite source player pose required");inside=containment(p);
 if(!h->initialized){h->pose=*p;h->inside=inside;h->initialized=1;return 0;}exits=h->inside&~inside;h->busy=1;r=dispatch_exits(h,exits,p,inside,e,cap);h->busy=0;return r;
}
int oa_movement_host_retry_failed_exit(oa_movement_host*h,char*e,size_t cap){
 int r;if(start(h,e,cap))return 1;if(!h->latched||!h->failed_exits)return error(e,cap,"no retryable source exit is latched");h->busy=1;r=dispatch_exits(h,h->failed_exits,&h->failed_pose,h->failed_inside,e,cap);if(!r){h->latched=0;h->error[0]=0;}h->busy=0;return r;
}
int oa_movement_host_load_checkpoint(oa_movement_host*h,char*e,size_t cap){
 unsigned char raw[CHECKPOINT_CAP];size_t n=0;int missing;checkpoint_state s;if(start(h,e,cap))return 1;h->busy=1;
 if(read_file(h->path,raw,&n,&missing,e,cap)||missing||decode(h,raw,n,&s,e,cap)){if(missing)error(e,cap,"opening checkpoint absent");h->busy=0;return 1;}
 if(h->config.validate_load_pose&&h->config.validate_load_pose(h->config.pose_validation_context,&s.pose,e,cap)){
  if(!(e&&cap&&e[0]))error(e,cap,"saved pose rejected by current collision validation");
  h->busy=0;return OA_MOVEMENT_ERROR;
 }
 if(oa_opening_runtime_restore(h->runtime,&s.lua,e,cap)){h->busy=0;return 1;}h->pose=s.pose;h->inside=s.inside;h->initialized=1;h->skipped=s.skipped;memcpy(h->tutorial,s.tutorial,sizeof(h->tutorial));h->latched=0;h->failed_exits=0;h->error[0]=0;h->busy=0;return 0;
}
int oa_movement_host_save_checkpoint(oa_movement_host*h,char*e,size_t cap){
 checkpoint_state s;int r;if(start(h,e,cap))return 1;
 if(h->latched){error(e,cap,h->error);return OA_MOVEMENT_LATCHED;}
 if(!h->initialized)return error(e,cap,"accepted movement pose required before saving checkpoint");
 memset(&s,0,sizeof(s));s.pose=h->pose;s.inside=h->inside;s.skipped=h->skipped;memcpy(s.tutorial,h->tutorial,sizeof(s.tutorial));h->busy=1;
 r=oa_opening_runtime_snapshot(h->runtime,&s.lua,e,cap);
 if(!r)r=checkpoint_write(h,&s,e,cap);
 h->busy=0;return r?OA_MOVEMENT_ERROR:OA_MOVEMENT_OK;
}
int oa_movement_host_tutorial_set(oa_movement_host*h,uint32_t id,int active,int fired,char*e,size_t cap){
 int i;if(start(h,e,cap))return 1;if(h->latched){error(e,cap,h->error);return OA_MOVEMENT_LATCHED;}i=tutorial_index(id);if(i<0)return OA_MOVEMENT_UNAVAILABLE;if((active!=0&&active!=1)||(fired!=0&&fired!=1))return error(e,cap,"explicit tutorial registry booleans required");h->tutorial[i].active=(uint32_t)active;h->tutorial[i].fired=(uint32_t)fired;return 0;
}
int oa_movement_host_tutorial_get(const oa_movement_host*h,uint32_t id,oa_movement_tutorial*out){int i;if(!h||!out||h->busy)return OA_MOVEMENT_ERROR;i=tutorial_index(id);if(i<0)return OA_MOVEMENT_UNAVAILABLE;*out=h->tutorial[i];return 0;}
int oa_movement_host_snapshot(oa_movement_host*h,oa_movement_pose*p,oa_opening_snapshot*s,char*e,size_t cap){if(start(h,e,cap))return 1;if(!h->initialized||!p||!s)return error(e,cap,"accepted source pose/snapshot unavailable");if(oa_opening_runtime_snapshot(h->runtime,s,e,cap))return 1;*p=h->pose;return 0;}
void oa_movement_host_get_stats(const oa_movement_host*h,oa_movement_stats*s){if(!s)return;memset(s,0,sizeof(*s));if(!h)return;s->scene=SCENE;s->region=REGION;s->inside_mask=h->inside;s->containment_initialized=h->initialized;s->cinematic_skipped=h->skipped;s->latched=h->latched;s->generation=h->config.generation;s->checkpoint_writes=h->writes;s->event_failures=h->failures;s->failure_reports=h->reports;oa_opening_runtime_get_stats(h->runtime,&s->runtime);}
unsigned oa_movement_host_services(const oa_movement_host*h){return h?OA_MOVEMENT_SERVICE_VOLUMES|OA_MOVEMENT_SERVICE_TUTORIAL_REGISTRY|OA_MOVEMENT_SERVICE_CHECKPOINT:0;}
