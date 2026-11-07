
#include "oa_opening_gameplay.h"
#include "oa_mq01_cursor.h"
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
#define CHECKPOINT_SUFFIX ".opening-gameplay-v1.bin"
#define SCENE OA_GAMEPLAY_SCENE
#define REGION OA_GAMEPLAY_REGION
#define MAX_INTEGER UINT64_C(9007194959773695)
typedef char ieee32[(sizeof(float)==4&&FLT_RADIX==2&&FLT_MANT_DIG==24&&FLT_MAX_EXP==128)?1:-1];
static const uint32_t tutorial_ids[5]={17524338u,26339831u,40879367u,61835887u,49968583u};
static const char gameplay_schema[]=
 "opening-gameplay-v1;scene1417252;region1262814;GOR1790948;container1789992;"
 "item1360571:quantity1;MQ01-613083:explicit-unstarted-only;"
 "tutorials17524338,26339831,40879367,61835887,49968583;step1000;single-item;"
 "fieldwise-state-v1;source-eight-functions;source-volume-profile;timer15";
struct oa_gameplay_host {
 oa_opening_runtime *runtime;
 oa_mq01_cursor *quest;
 oa_gameplay_config config;
 oa_gameplay_state state,next;
 char path[1024],identity[128],error[512];
 oa_opening_effect effects[OA_OPENING_MAX_EFFECTS];
 size_t effect_count;
 enum oa_gameplay_action action;
 uint32_t required;
 unsigned busy,latched,poisoned,temp_sequence,save_requested,unavailable;
 uint64_t writes,attempts,failures,reports,warnings;
};
static int error(char*e,size_t n,const char*s){if(e&&n)snprintf(e,n,"%s",s?s:"opening gameplay failure");return OA_GAMEPLAY_ERROR;}
static int start(oa_gameplay_host*h,char*e,size_t n){
 if(e&&n)e[0]=0;
 if(!h)return error(e,n,"opening gameplay host unavailable");
 if(h->busy)return error(e,n,"opening gameplay reentry rejected");
 if(h->poisoned)return error(e,n,"opening gameplay recovery failed; recreate host");
 return 0;
}
static int ready(oa_gameplay_host*h,char*e,size_t n){
 if(start(h,e,n))return 1;
 if(h->latched){error(e,n,h->error);return OA_GAMEPLAY_LATCHED;}
 return 0;
}
static int pose_valid(const oa_gameplay_pose*p){unsigned i;if(!p)return 0;for(i=0;i<3;i++)if(!isfinite(p->feet[i]))return 0;return isfinite(p->yaw)&&isfinite(p->pitch);}
static uint32_t containment(const oa_gameplay_pose*p){
 unsigned i,j;uint32_t mask=0;
 for(i=0;i<3;i++){int in=1;for(j=0;j<6;j++){const double*q=source_volumes[i].planes[j];if(q[0]*p->feet[0]+q[1]*p->feet[1]+q[2]*p->feet[2]+q[3]>0){in=0;break;}}if(in)mask|=1u<<i;}return mask;
}
static int ti(uint32_t id){unsigned i;for(i=0;i<5;i++)if(tutorial_ids[i]==id)return (int)i;return -1;}
static void latch(oa_gameplay_host*h,const char*why){
 h->failures++;if(!h->latched){h->latched=1;snprintf(h->error,sizeof(h->error),"%s",why&&why[0]?why:"opening source event failed");h->reports++;h->config.report_failure(h->config.report_context,h->error);}
}
static int state_valid(oa_gameplay_host*h,const oa_gameplay_state*s){
 unsigned i,j,launch=0,poll=0;const oa_opening_snapshot*l=&s->lua;
 const uint32_t mutable_wos=(1u<<6)|(1u<<11)|(1u<<13)|(1u<<14);
 if(!pose_valid(&s->pose)||s->initialized>1||s->inside>7||s->skipped>1||
    (s->initialized&&s->inside!=containment(&s->pose))||
    (!s->initialized&&s->inside)||s->container_count>1||s->owned>1||
    s->container_count+s->owned!=1||s->equipped>s->owned||s->door_open>s->owned||
    s->secondary_disabled!=s->owned||s->compare_enabled!=s->door_open)return 0;
 if(l->version!=1||(l->wos_flags&~mutable_wos)!=0x780u||l->sword_flags>3||
    (l->sword_flags&1)!=s->owned||((l->sword_flags>>1)&1)!=s->equipped||
    ((l->wos_flags>>13)&1)!=s->owned||((l->wos_flags>>14)&1)!=s->equipped||
    ((l->wos_flags>>6)&1)>s->owned||l->sword_get!=(int32_t)s->owned||
    l->cinematic_flags!=s->skipped||l->clock_ms>MAX_INTEGER||l->serial>MAX_INTEGER||
    l->timer_count>2||(!s->owned&&l->timer_count))return 0;
 for(i=0;i<5;i++)if(s->tutorials[i].id!=tutorial_ids[i]||s->tutorials[i].active>1||s->tutorials[i].fired>1)return 0;
 for(i=0;i<l->timer_count;i++){
  const oa_opening_timer*t=l->timers+i;
  if(!t->serial||t->serial>l->serial||t->due_ms<=l->clock_ms||
     t->due_ms>MAX_INTEGER||t->due_ms-l->clock_ms>15)return 0;
  for(j=0;j<i;j++)if(t->serial==l->timers[j].serial)return 0;
  if(t->hash==151774118u){if(++launch>1||t->argc!=1||t->item_index!=h->config.item_index)return 0;}
  else if(t->hash==165407883u){if(++poll>1||t->argc||t->item_index||s->door_open)return 0;}
  else return 0;
 }
 return 1;
}
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

static int encode(oa_gameplay_host*h,const oa_gameplay_state*s,unsigned char*out,size_t*out_n,char*e,size_t cap){
 codec c={out,CHECKPOINT_CAP,48,0};unsigned i;unsigned char digest[32],schema[32];size_t idn=strlen(h->identity);
 if(!state_valid(h,s)||!s->initialized)return error(e,cap,"incoherent gameplay checkpoint candidate");
 sha256(gameplay_schema,sizeof(gameplay_schema)-1,schema);
 putbytes(&c,volume_profile,32);putbytes(&c,runtime_profile,32);putbytes(&c,schema,32);
 put32(&c,SCENE);put32(&c,REGION);put64(&c,h->config.generation);
 put32(&c,OA_GAMEPLAY_CONTAINER_GOR);put32(&c,OA_GAMEPLAY_CONTAINER_INSTANCE);put32(&c,OA_GAMEPLAY_SWORD_TYPE);
 put64(&c,h->config.item_instance);put32(&c,(uint32_t)h->config.item_index);
 put32(&c,OA_MQ01_QUEST_ID);put32(&c,UINT32_MAX); /* Explicit ctor, not quest-start effects. */
 put32(&c,(uint32_t)h->config.tutorials_enabled);
 put32(&c,(uint32_t)idn);putbytes(&c,h->identity,idn);
 for(i=0;i<3;i++)putfloat(&c,s->pose.feet[i]);putfloat(&c,s->pose.yaw);putfloat(&c,s->pose.pitch);
 put32(&c,s->inside);put32(&c,s->initialized);put32(&c,s->skipped);
 put32(&c,s->container_count);put32(&c,s->owned);put32(&c,s->equipped);put32(&c,s->door_open);
 put32(&c,s->secondary_disabled);put32(&c,s->compare_enabled);put64(&c,s->revision);put64(&c,s->quest_noops);
 put32(&c,5);for(i=0;i<5;i++){const oa_gameplay_tutorial*t=s->tutorials+i;put32(&c,t->id);put32(&c,t->active);put32(&c,t->fired);put32(&c,t->kills);}
 put32(&c,s->lua.version);put32(&c,s->lua.wos_flags);put32(&c,s->lua.sword_flags);put32(&c,s->lua.cinematic_flags);put32(&c,(uint32_t)s->lua.sword_get);
 put64(&c,s->lua.clock_ms);put64(&c,s->lua.serial);put32(&c,s->lua.timer_count);
 for(i=0;i<s->lua.timer_count;i++){const oa_opening_timer*t=s->lua.timers+i;put32(&c,t->hash);put64(&c,t->due_ms);put64(&c,t->serial);put32(&c,t->argc);put32(&c,(uint32_t)t->item_index);}
 if(c.bad)return error(e,cap,"gameplay checkpoint envelope exceeded");
 sha256(out+48,c.p-48,digest);memcpy(out,"OAGPCP1",8);{codec head={out,48,8,0};put32(&head,1);put32(&head,(uint32_t)(c.p-48));putbytes(&head,digest,32);}*out_n=c.p;return 0;
}
static int decode(oa_gameplay_host*h,const unsigned char*raw,size_t n,oa_gameplay_state*s,char*e,size_t cap){
 unsigned char digest[32],schema[32];codec hd={(unsigned char*)raw,n,8,0},c={(unsigned char*)raw,n,48,0};unsigned i;uint32_t bytes,idn;
 if(n<48||n>CHECKPOINT_CAP||memcmp(raw,"OAGPCP1",8))return error(e,cap,"gameplay checkpoint magic/size invalid");
 if(get32(&hd)!=1)return error(e,cap,"gameplay checkpoint version unsupported");bytes=get32(&hd);
 if(bytes!=n-48)return error(e,cap,"gameplay checkpoint length mismatch");
 sha256(raw+48,n-48,digest);if(!equalbytes(&hd,digest,32))return error(e,cap,"gameplay checkpoint SHA256 mismatch");
 sha256(gameplay_schema,sizeof(gameplay_schema)-1,schema);memset(s,0,sizeof(*s));
 if(!equalbytes(&c,volume_profile,32)||!equalbytes(&c,runtime_profile,32)||!equalbytes(&c,schema,32))return error(e,cap,"gameplay source/schema profile mismatch");
 if(get32(&c)!=SCENE||get32(&c)!=REGION||get64(&c)!=h->config.generation)return error(e,cap,"gameplay scene/generation mismatch");
 if(get32(&c)!=OA_GAMEPLAY_CONTAINER_GOR||get32(&c)!=OA_GAMEPLAY_CONTAINER_INSTANCE||get32(&c)!=OA_GAMEPLAY_SWORD_TYPE||
    get64(&c)!=h->config.item_instance||get32(&c)!=(uint32_t)h->config.item_index||
    get32(&c)!=OA_MQ01_QUEST_ID||get32(&c)!=UINT32_MAX||get32(&c)!=(uint32_t)h->config.tutorials_enabled)
  return error(e,cap,"gameplay item/quest/options mapping mismatch");
 idn=get32(&c);if(idn!=strlen(h->identity)||idn>127||!equalbytes(&c,h->identity,idn))return error(e,cap,"gameplay identity mismatch");
 for(i=0;i<3;i++)s->pose.feet[i]=getfloat(&c);s->pose.yaw=getfloat(&c);s->pose.pitch=getfloat(&c);
 s->inside=get32(&c);s->initialized=get32(&c);s->skipped=get32(&c);
 s->container_count=get32(&c);s->owned=get32(&c);s->equipped=get32(&c);s->door_open=get32(&c);
 s->secondary_disabled=get32(&c);s->compare_enabled=get32(&c);s->revision=get64(&c);s->quest_noops=get64(&c);
 if(get32(&c)!=5)return error(e,cap,"gameplay tutorial schema mismatch");
 for(i=0;i<5;i++){oa_gameplay_tutorial*t=s->tutorials+i;t->id=get32(&c);t->active=get32(&c);t->fired=get32(&c);t->kills=get32(&c);}
 s->lua.version=get32(&c);s->lua.wos_flags=get32(&c);s->lua.sword_flags=get32(&c);s->lua.cinematic_flags=get32(&c);{uint32_t x=get32(&c);memcpy(&s->lua.sword_get,&x,4);}
 s->lua.clock_ms=get64(&c);s->lua.serial=get64(&c);s->lua.timer_count=get32(&c);
 if(s->lua.timer_count>2)return error(e,cap,"gameplay timer count invalid");
 for(i=0;i<s->lua.timer_count;i++){oa_opening_timer*t=s->lua.timers+i;uint32_t x;t->hash=get32(&c);t->due_ms=get64(&c);t->serial=get64(&c);t->argc=get32(&c);x=get32(&c);memcpy(&t->item_index,&x,4);}
 if(c.bad||c.p!=n||!state_valid(h,s)||!s->initialized)return error(e,cap,"gameplay checkpoint typed payload invalid");return 0;
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
static int atomic_replace(oa_gameplay_host*h,const unsigned char*raw,size_t n,char*e,size_t cap){
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

static int checkpoint_write(oa_gameplay_host*h,const oa_gameplay_state*s,char*e,size_t cap){
 unsigned char raw[CHECKPOINT_CAP],oldraw[CHECKPOINT_CAP];size_t n=0,oldn=0;int missing;oa_gameplay_state old;
 if(encode(h,s,raw,&n,e,cap)||read_file(h->path,oldraw,&oldn,&missing,e,cap))return 1;
 if(!missing&&decode(h,oldraw,oldn,&old,e,cap))return error(e,cap,"invalid/incompatible existing gameplay checkpoint preserved");
 if(atomic_replace(h,raw,n,e,cap))return 1;h->writes++;return 0;
}
static int admit(oa_gameplay_host*h,uint32_t required,char*e,size_t n){
 const oa_gameplay_backend*b=&h->config.backend;
 if(!required)return 0;
 if((required&b->capabilities)!=required||!b->available||!b->prepare||!b->commit||!b->abort)
  {h->unavailable=1;return error(e,n,"required actual actor/UI capability unavailable");}
 if(b->available(b->context,required,e,n)){h->unavailable=1;return error(e,n,"actual actor/UI service not ready");}
 return 0;
}
static int query(void*v,enum oa_opening_query q,int32_t arg,int*out,char*e,size_t n){
 oa_gameplay_host*h=v;const oa_gameplay_state*s=&h->next;int i;
 switch(q){
 case OA_OPENING_IS_EQUIPPED:if(arg!=h->config.item_index)return error(e,n,"source item index unmapped");if(admit(h,OA_GAMEPLAY_CAP_ITEM|OA_GAMEPLAY_CAP_EQUIP,e,n))return 1;*out=(int)s->equipped;return 0;
 case OA_OPENING_GATEWAY_OPEN:if(arg!=OA_GAMEPLAY_CONTAINER_GOR)return error(e,n,"source GOR unavailable");if(admit(h,OA_GAMEPLAY_CAP_DOOR,e,n))return 1;*out=(int)s->door_open;return 0;
 case OA_OPENING_TUTORIALS_ENABLED:if(h->config.tutorials_enabled<0){h->unavailable=1;return error(e,n,"tutorial option unavailable");}*out=h->config.tutorials_enabled;return 0;
 case OA_OPENING_TUTORIAL_ACTIVE:case OA_OPENING_TUTORIAL_FIRED:
  i=ti((uint32_t)arg);if(i<0)return error(e,n,"source tutorial not registered");
  *out=(int)(q==OA_OPENING_TUTORIAL_ACTIVE?s->tutorials[i].active:s->tutorials[i].fired);return 0;
 default:return error(e,n,"unsupported opening query");
 }
}
static int quest_query(void*v,uint32_t id,int32_t*out,char*e,size_t n){
 oa_gameplay_host*h=v;oa_mq01_snapshot s;
 if(oa_mq01_query(h->quest,id,h->config.generation,&s)!=OA_MQ01_OK)return error(e,n,"unsupported quest service");
 if(s.stage_id!=-1||s.stage_index!=-1||s.revision)return error(e,n,"active quest effects unavailable in this profile");*out=s.stage_id;return 0;
}
static void warning(void*v,const char*s){oa_gameplay_host*h=v;(void)s;h->warnings++;}
/* PREPARE-ONLY Lua effect receiver. Runtime may call it once per public callback.
 * All effects from all volume callbacks in one update share this candidate.
 * Nothing visible, no disk, no backend commit here. */
static int apply(void*v,const oa_opening_effect*a,size_t count,const oa_opening_snapshot*lua,char*e,size_t n){
 oa_gameplay_host*h=v;size_t j;
 if(!h->busy||count>OA_OPENING_MAX_EFFECTS||h->effect_count>OA_OPENING_MAX_EFFECTS-count)return error(e,n,"gameplay effect transaction overflow");
 for(j=0;j<count;j++){
  const oa_opening_effect*x=a+j;int i;
  if(!x->source_callback)return error(e,n,"effect source identity missing");
  switch(x->kind){
  case OA_OPENING_OPEN_GATEWAY:
   if(x->argc!=1||x->args[0]!=OA_GAMEPLAY_CONTAINER_GOR)return error(e,n,"unmapped source gateway effect");
   h->required|=OA_GAMEPLAY_CAP_DOOR;h->next.door_open=1;break;
  case OA_OPENING_SET_STAGE:{
   oa_mq01_snapshot before;oa_mq01_request plan;oa_mq01_noop reason;oa_mq01_status r;
   if(x->argc!=2||x->args[0]!=OA_MQ01_QUEST_ID||x->args[1]!=25)return error(e,n,"real quest transition effects unavailable");
   if(oa_mq01_query(h->quest,OA_MQ01_QUEST_ID,h->config.generation,&before)!=OA_MQ01_OK)return error(e,n,"MQ01 cursor unavailable");
   r=oa_mq01_prepare_set(h->quest,&before,25,&plan,&reason);
   if(r!=OA_MQ01_NO_CHANGE||reason!=OA_MQ01_NOOP_UNSTARTED){if(r==OA_MQ01_OK)oa_mq01_cancel(h->quest,h->config.generation,&plan);return error(e,n,"quest transition requires unsupported native effects");}
   if(h->next.quest_noops==UINT64_MAX)return error(e,n,"quest no-op log exhausted");h->next.quest_noops++;break;
  }
  case OA_OPENING_KILL_TUTORIAL:
   if(x->argc!=1||(i=ti((uint32_t)x->args[0]))<0||i>2)return error(e,n,"unregistered tutorial kill");
   if(h->next.tutorials[i].kills==UINT32_MAX)return error(e,n,"tutorial kill log exhausted");
   h->next.tutorials[i].active=0;h->next.tutorials[i].kills++;h->required|=OA_GAMEPLAY_CAP_UI;break;
  case OA_OPENING_MODAL_TUTORIAL:
   if(x->argc!=1||x->args[0]!=49968583)return error(e,n,"unsupported modal tutorial");
   i=ti(49968583);h->next.tutorials[i].active=1;h->next.tutorials[i].fired=1;h->required|=OA_GAMEPLAY_CAP_UI;break;
  case OA_OPENING_SECONDARY_DISABLED:
   if(x->argc!=1||(x->args[0]!=0&&x->args[0]!=1))return error(e,n,"invalid secondary UI effect");
   h->next.secondary_disabled=(uint32_t)x->args[0];h->required|=OA_GAMEPLAY_CAP_UI;break;
  case OA_OPENING_COMPARE_ENABLED:
   if(x->argc)return error(e,n,"invalid compare UI effect");
   h->next.compare_enabled=1;h->required|=OA_GAMEPLAY_CAP_UI;break;
  case OA_OPENING_AUTOSAVE_REQUEST:
   if(x->argc!=1||x->args[0]!=0||h->save_requested)return error(e,n,"unsupported autosave batch");
   h->save_requested=1;break;
  default:return error(e,n,"unimplemented source effect unavailable");
  }
  h->effects[h->effect_count++]=*x;
 }
 h->next.lua=*lua;return 0;
}
static void begin(oa_gameplay_host*h,enum oa_gameplay_action action){
 h->busy=1;h->next=h->state;h->effect_count=0;h->save_requested=0;h->required=0;h->unavailable=0;h->action=action;
}
static int rollback(oa_gameplay_host*h,char*e,size_t n){
 char why[512],restore_error[256]="";
 snprintf(why,sizeof(why),"%s",e&&n&&e[0]?e:"gameplay transaction rejected");
 if(oa_opening_runtime_restore(h->runtime,&h->state.lua,restore_error,sizeof(restore_error))){h->poisoned=1;if(e&&n)snprintf(e,n,"%s; Lua rollback failed: %s",why,restore_error);}
 else error(e,n,why);
 latch(h,e&&n?e:why);h->busy=0;return h->unavailable?OA_GAMEPLAY_UNAVAILABLE:OA_GAMEPLAY_ERROR;
}
static int finish(oa_gameplay_host*h,int lua_failed,char*e,size_t n){
 oa_gameplay_backend*b=&h->config.backend;void*token=NULL;oa_gameplay_batch batch;
 if(lua_failed)return rollback(h,e,n);
 if(oa_opening_runtime_snapshot(h->runtime,&h->next.lua,e,n)||!state_valid(h,&h->next)){
  if(!(e&&n&&e[0]))error(e,n,"unrelated/incoherent gameplay candidate rejected");return rollback(h,e,n);
 }
 if(h->state.revision==UINT64_MAX||h->next.revision==UINT64_MAX){error(e,n,"gameplay revision exhausted");return rollback(h,e,n);}
 h->next.revision=(h->next.revision>h->state.revision?h->next.revision:h->state.revision)+1;
 if(admit(h,h->required,e,n))return rollback(h,e,n);
 memset(&batch,0,sizeof(batch));batch.action=h->action;batch.required_capabilities=h->required;
 batch.scene=SCENE;batch.container_gor=OA_GAMEPLAY_CONTAINER_GOR;batch.container_instance=OA_GAMEPLAY_CONTAINER_INSTANCE;batch.item_type=OA_GAMEPLAY_SWORD_TYPE;
 batch.generation=h->config.generation;batch.item_instance=h->config.item_instance;batch.item_index=h->config.item_index;
 batch.previous_revision=h->state.revision;batch.before=&h->state;batch.after=&h->next;batch.effects=h->effects;batch.effect_count=h->effect_count;
 if(h->required&&b->prepare(b->context,&batch,&token,e,n))return rollback(h,e,n);
 if(h->save_requested&&checkpoint_write(h,&h->next,e,n)){
  if(h->required)b->abort(b->context,token);return rollback(h,e,n);
 }
 /* No fallible operations after logical file rename. */
 if(h->required)b->commit(b->context,token);
 h->state=h->next;h->busy=0;return 0;
}
oa_gameplay_host *oa_gameplay_create(const oa_opening_assets*a,const oa_gameplay_config*c,char*e,size_t n){
 oa_gameplay_host*h;oa_opening_host host;size_t z,suf=strlen(CHECKPOINT_SUFFIX);unsigned i;
 if(!c||!c->generation||!c->item_instance||c->item_index<0||!c->checkpoint_path||!c->report_failure||
    c->tutorials_enabled< -1||c->tutorials_enabled>1||(c->backend.capabilities&~15u))
  return (error(e,n,"explicit gameplay source mapping/configuration required"),(oa_gameplay_host*)NULL);
 z=strlen(c->checkpoint_path);if(z>=1024||z<suf||strcmp(c->checkpoint_path+z-suf,CHECKPOINT_SUFFIX))
  return (error(e,n,"dedicated *.opening-gameplay-v1.bin required; old saves refused"),(oa_gameplay_host*)NULL);
 h=calloc(1,sizeof(*h));if(!h)return (error(e,n,"gameplay host allocation failed"),(oa_gameplay_host*)NULL);
 h->config=*c;snprintf(h->path,sizeof(h->path),"%s",c->checkpoint_path);
 snprintf(h->identity,sizeof(h->identity),"scene1417252:player1:g%" PRIu64,c->generation);
 h->state.container_count=1;for(i=0;i<5;i++)h->state.tutorials[i].id=tutorial_ids[i];
 if(oa_mq01_create(OA_MQ01_QUEST_ID,c->generation,&h->quest)!=OA_MQ01_OK){free(h);return (error(e,n,"MQ01 constructor failed"),(oa_gameplay_host*)NULL);}
 memset(&host,0,sizeof(host));host.context=h;host.player_identity=h->identity;host.query_bool=query;host.quest_stage=quest_query;host.apply_effects=apply;host.warning=warning;
 h->runtime=oa_opening_runtime_create_from_assets(a,&host,&c->runtime,e,n);
 if(!h->runtime||oa_opening_runtime_snapshot(h->runtime,&h->state.lua,e,n)||!state_valid(h,&h->state)){oa_gameplay_close(h);return NULL;}
 return h;
}
void oa_gameplay_close(oa_gameplay_host*h){if(!h||h->busy)return;oa_opening_runtime_close(h->runtime);oa_mq01_destroy(&h->quest);free(h);}
int oa_gameplay_cinematic_skipped(oa_gameplay_host*h,char*e,size_t n){
 int r=ready(h,e,n);if(r)return r;if(h->state.skipped)return OA_GAMEPLAY_NO_CHANGE;
 begin(h,OA_GAMEPLAY_SKIP);h->next.skipped=1;return finish(h,oa_opening_runtime_cinematic_finished(h->runtime,1,e,n),e,n);
}
int oa_gameplay_update_pose(oa_gameplay_host*h,const oa_gameplay_pose*p,char*e,size_t n){
 uint32_t inside,exits;unsigned i;int r=ready(h,e,n);if(r)return r;if(!pose_valid(p))return error(e,n,"finite feet pose required");
 inside=containment(p);exits=h->state.initialized?(h->state.inside&~inside):0;
 begin(h,OA_GAMEPLAY_MOVE);h->next.pose=*p;h->next.inside=inside;h->next.initialized=1;
 for(i=0;i<3;i++)if(exits&(1u<<i))if(oa_opening_runtime_volume_exit(h->runtime,source_volumes[i].name,h->identity,e,n))return finish(h,1,e,n);
 return finish(h,0,e,n);
}
int oa_gameplay_take_source_item(oa_gameplay_host*h,uint32_t gor,uint32_t instance,uint64_t item,uint64_t generation,char*e,size_t n){
 int r=ready(h,e,n);if(r)return r;
 if(gor!=OA_GAMEPLAY_CONTAINER_GOR||instance!=OA_GAMEPLAY_CONTAINER_INSTANCE||item!=h->config.item_instance||generation!=h->config.generation)
  return (error(e,n,"unmapped source container/item generation"),OA_GAMEPLAY_UNAVAILABLE);
 if(h->state.owned)return OA_GAMEPLAY_NO_CHANGE;if(!h->state.initialized)return error(e,n,"accepted pose required");
 begin(h,OA_GAMEPLAY_TAKE);h->next.container_count=0;h->next.owned=1;h->required=OA_GAMEPLAY_CAP_ITEM;
 return finish(h,oa_opening_runtime_sword_acquired(h->runtime,h->config.item_index,h->identity,1,e,n),e,n);
}
int oa_gameplay_equip_source_item(oa_gameplay_host*h,uint64_t item,uint64_t generation,char*e,size_t n){
 int r=ready(h,e,n);if(r)return r;if(item!=h->config.item_instance||generation!=h->config.generation)return OA_GAMEPLAY_UNAVAILABLE;
 if(!h->state.owned)return (error(e,n,"source item not owned"),OA_GAMEPLAY_UNAVAILABLE);
 if(h->state.equipped)return OA_GAMEPLAY_NO_CHANGE;
 begin(h,OA_GAMEPLAY_EQUIP);h->next.equipped=1;h->required=OA_GAMEPLAY_CAP_EQUIP;
 return finish(h,oa_opening_runtime_sword_equipped(h->runtime,h->config.item_index,e,n),e,n);
}
int oa_gameplay_advance(oa_gameplay_host*h,uint32_t dt,char*e,size_t n){
 int r=ready(h,e,n);if(r)return r;if(dt>OA_GAMEPLAY_STEP_MAX_MS)return error(e,n,"game-time step exceeds bounded host policy");
 begin(h,OA_GAMEPLAY_ADVANCE);return finish(h,oa_opening_runtime_advance(h->runtime,dt,e,n),e,n);
}
int oa_gameplay_snapshot(oa_gameplay_host*h,oa_gameplay_state*out,char*e,size_t n){
 if(start(h,e,n))return 1;if(!out)return error(e,n,"typed gameplay output required");*out=h->state;return 0;
}
int oa_gameplay_quest_stage(oa_gameplay_host*h,uint32_t id,int32_t*out,char*e,size_t n){
 int r;if(start(h,e,n))return 1;if(!out)return error(e,n,"quest output required");h->busy=1;r=quest_query(h,id,out,e,n);h->busy=0;return r?OA_GAMEPLAY_UNAVAILABLE:0;
}
int oa_gameplay_save_checkpoint(oa_gameplay_host*h,char*e,size_t n){
 int r=ready(h,e,n);if(r)return r;if(!h->state.initialized)return error(e,n,"accepted pose required");h->busy=1;r=checkpoint_write(h,&h->state,e,n);h->busy=0;return r;
}
static int validate_load_pose(oa_gameplay_host*h,const oa_gameplay_state*s,char*e,size_t n){
 if(h->config.validate_load_pose&&h->config.validate_load_pose(h->config.pose_validation_context,&s->pose,e,n)){
  if(!(e&&n&&e[0]))error(e,n,"saved pose rejected by current collision");return 1;
 }return 0;
}
int oa_gameplay_load_checkpoint(oa_gameplay_host*h,char*e,size_t n){
 unsigned char raw[CHECKPOINT_CAP];size_t z=0;int missing,r;oa_gameplay_state s;
 if(start(h,e,n))return 1;h->busy=1;
 r=read_file(h->path,raw,&z,&missing,e,n);if(!r&&missing)r=error(e,n,"gameplay checkpoint absent");
 if(!r)r=decode(h,raw,z,&s,e,n);
 if(!r)r=validate_load_pose(h,&s,e,n);
 if(r){h->busy=0;return 1;}
 begin(h,OA_GAMEPLAY_LOAD);h->next=s;
 /* Restoring visual/inventory/UI state must be genuinely admitted too. */
 h->required=(s.owned||h->state.owned?OA_GAMEPLAY_CAP_ITEM:0)|(s.equipped||h->state.equipped?OA_GAMEPLAY_CAP_EQUIP:0)|
  (s.door_open||h->state.door_open?OA_GAMEPLAY_CAP_DOOR:0)|OA_GAMEPLAY_CAP_UI;
 r=finish(h,oa_opening_runtime_restore(h->runtime,&s.lua,e,n),e,n);
 if(!r){h->latched=0;h->error[0]=0;}return r;
}
int oa_gameplay_migrate_movement(oa_gameplay_host*h,uint32_t scene,uint64_t generation,const oa_gameplay_pose*p,const oa_opening_snapshot*l,const oa_gameplay_tutorial*t,size_t count,char*e,size_t n){
 unsigned i;int r=ready(h,e,n);oa_gameplay_state s;
 if(r)return r;
 if(scene!=SCENE||generation!=h->config.generation||!p||!l||!t||count!=3||
    h->state.initialized||h->state.revision||h->state.owned||l->sword_flags||l->sword_get||l->timer_count)
  return error(e,n,"only fresh same-scene movement realm may migrate");
 s=h->state;s.pose=*p;s.inside=containment(p);s.initialized=1;s.skipped=l->cinematic_flags;s.lua=*l;
 for(i=0;i<3;i++)s.tutorials[i]=t[i];
 if(!state_valid(h,&s))return error(e,n,"movement migration schema invalid");
 h->busy=1;r=validate_load_pose(h,&s,e,n);if(r){h->busy=0;return 1;}
 begin(h,OA_GAMEPLAY_MIGRATE);h->next=s;h->required=OA_GAMEPLAY_CAP_UI;
 return finish(h,oa_opening_runtime_restore(h->runtime,l,e,n),e,n);
}
int oa_gameplay_clear_failure(oa_gameplay_host*h,char*e,size_t n){
 if(start(h,e,n))return 1;if(!h->latched)return OA_GAMEPLAY_NO_CHANGE;
 h->latched=0;h->error[0]=0;
 /* Explicitly abandon failed crossing, preserving accepted pose/containment.
  * Caller may retry the original motion deliberately; ordinary advance alone
  * never retries it. No loss of checkpoint containment initialization. */
 return 0;
}
int oa_gameplay_tutorial_set(oa_gameplay_host*h,uint32_t id,int active,int fired,char*e,size_t n){
 int i,r=ready(h,e,n);if(r)return r;i=ti(id);if(i<0)return OA_GAMEPLAY_UNAVAILABLE;
 if((active!=0&&active!=1)||(fired!=0&&fired!=1))return error(e,n,"typed tutorial booleans required");
 if(h->state.revision==UINT64_MAX)return error(e,n,"gameplay revision exhausted");
 h->state.tutorials[i].active=(uint32_t)active;h->state.tutorials[i].fired=(uint32_t)fired;h->state.revision++;return 0;
}
void oa_gameplay_get_stats(const oa_gameplay_host*h,oa_gameplay_stats*s){
 if(!s)return;memset(s,0,sizeof(*s));if(!h)return;s->writes=h->writes;s->attempts=h->attempts;s->failures=h->failures;s->reports=h->reports;s->warnings=h->warnings;s->latched=h->latched;s->poisoned=h->poisoned;oa_opening_runtime_get_stats(h->runtime,&s->runtime);
}
