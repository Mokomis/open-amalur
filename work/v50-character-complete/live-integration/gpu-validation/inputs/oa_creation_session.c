#include "oa_creation_session.h"
#include "oa_stream.h"
#include <android/asset_manager.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <math.h>

struct oa_creation_session {
 AAssetManager *assets;oa_ca_renderer *renderer;
 oa_creation_session_config config;oa_creation_gameplay *host;
 char path[1024];int busy,has_active;
 oa_creation_active active;oa_ca_actor *actor;
 struct oa_stream *load_stream;opem_controller_config load_config;
 opem_collision_world *staged_world;opem_controller staged_body;
 oa_creator_game_pose staged_pose;
};
typedef struct session_reservation {
 oa_ca_actor *actor;oa_creation_active active;int loading;
} session_reservation;
static int fail(char *e,size_t n,const char *s){if(e&&n)snprintf(e,n,"%s",s);return OA_CG_ERROR;}
static int enter(oa_creation_session *s,char *e,size_t n){
 if(!s)return fail(e,n,"Character session is unavailable");
 if(s->busy)return fail(e,n,"Character session is busy");s->busy=1;return 0;
}
static AAsset *asset_open(oa_creation_session *s,const char *name){
 char path[512];int n;
 if(!name||strstr(name,"..")||strchr(name,':')||name[0]=='/'||name[0]=='\\')return NULL;
 n=snprintf(path,sizeof(path),"opening-runtime/%s",name);
 if(n<0||(size_t)n>=sizeof(path))return NULL;
 return AAssetManager_open(s->assets,path,AASSET_MODE_BUFFER);
}
static int asset_size(void *ctx,const char *name,size_t *n,char *e,size_t cap){
 AAsset *a;int64_t bytes;if(!n)return fail(e,cap,"Opening asset size output is missing");
 a=asset_open((oa_creation_session*)ctx,name);if(!a)return fail(e,cap,"Pinned opening asset is missing");
 bytes=AAsset_getLength64(a);AAsset_close(a);
 if(bytes<0||bytes>1048576)return fail(e,cap,"Pinned opening asset size is rejected");
 *n=(size_t)bytes;return 0;
}
static int asset_read(void *ctx,const char *name,void *p,size_t n,char *e,size_t cap){
 AAsset *a=asset_open((oa_creation_session*)ctx,name);size_t at=0;
 if(!a)return fail(e,cap,"Pinned opening asset is missing");
 if((!p&&n)||n>1048576||AAsset_getLength64(a)!=(int64_t)n){AAsset_close(a);return fail(e,cap,"Pinned opening asset size changed");}
 while(at<n){int k=AAsset_read(a,(unsigned char*)p+at,n-at);if(k<=0){AAsset_close(a);return fail(e,cap,"Pinned opening asset read failed");}at+=(size_t)k;}
 AAsset_close(a);return 0;
}
static void discard_collision(oa_creation_session *s){
 opem_collision_destroy(s->staged_world);s->staged_world=NULL;
}
static int validate_pose(void *ctx,const oa_creator_game_pose *p,char *e,size_t n){
 oa_creation_session *s=(oa_creation_session*)ctx;unsigned i;
 if(!s->load_stream)return fail(e,n,"Character restore requires current collision");
 discard_collision(s);
 s->staged_world=oa_stream_collision_now(s->load_stream,p->feet,e,n);
 if(!s->staged_world)return OA_CG_ERROR;
 if(!opem_controller_spawn(s->staged_world,&s->load_config,p->feet,&s->staged_body,e,n))return OA_CG_ERROR;
 for(i=0;i<3;i++)if(fabsf(s->staged_body.feet[i]-p->feet[i])>2.f)
  return fail(e,n,"Saved character pose requires relocation; progress preserved");
 if(!opem_controller_clear(s->staged_world,&s->load_config,p->feet,e,n))return OA_CG_ERROR;
 memcpy(s->staged_body.feet,p->feet,sizeof(p->feet));
 memcpy(s->staged_body.last_safe_feet,p->feet,sizeof(p->feet));
 s->staged_pose=*p;return 0;
}
/* These are the FIVE actual equipped owner items, not guessed actor attachments.
 * Validate exact source identity/slot/count before passing the owner's type IDs.
 */
static int equipment(const oa_creation_active *a,uint32_t out[5],char *e,size_t n){
 static const uint32_t type[5]={1321542u,1321543u,1330206u,1330207u,1381439u};
 static const int32_t slot[5]={0,0,0,1,0};unsigned i,j,found=0,seen=0;
 if(a->owner.item_count>OA_CG_ITEMS_MAX)return fail(e,n,"Active equipment count is invalid");
 for(i=0;i<a->owner.item_count;i++){
  const oa_creation_item *item=&a->owner.items[i];
  if(item->equipped_slot<0)continue;
  for(j=0;j<5;j++)if(item->type==type[j])break;
  if(j==5||item->equipped_slot!=slot[j]||item->count!=1||item->hidden||(seen&(1u<<j)))
   return fail(e,n,"Active source equipment cannot be rendered exactly");
  seen|=1u<<j;out[found++]=item->type;
 }
 if(found!=5||seen!=31u)return fail(e,n,"Five source equipped items are required");return 0;
}
static oa_ca_actor *prepare_actor(oa_creation_session *s,const oa_creation_active *a,char *e,size_t n){
 uint32_t types[5];if(equipment(a,types,e,n))return NULL;
 return oa_ca_actor_prepare(s->renderer,&a->profile,OA_AP_GAMEPLAY,types,5,e,n);
}
static int publish_prepare(void *ctx,int loading,const oa_creation_active *a,
 const oa_creation_render_selection *render,void **token,char *e,size_t n){
 oa_creation_session *s=(oa_creation_session*)ctx;session_reservation *r;
 (void)render;if(!token)return fail(e,n,"Character reservation output is missing");*token=NULL;
 if(loading&&(!s->staged_world||!s->load_stream))return fail(e,n,"Restored collision was not reserved");
 r=(session_reservation*)calloc(1,sizeof(*r));if(!r)return fail(e,n,"Character reservation allocation failed");
 r->active=*a;r->loading=loading;r->actor=prepare_actor(s,a,e,n);
 if(!r->actor){free(r);return OA_CG_ERROR;}*token=r;return 0;
}
static void publish_abort(void *ctx,void *token){
 session_reservation *r=(session_reservation*)token;(void)ctx;
 if(r){oa_ca_actor_close(r->actor);free(r);}
}
static void publish_commit(void *ctx,void *token){
 oa_creation_session *s=(oa_creation_session*)ctx;session_reservation *r=(session_reservation*)token;
 oa_ca_actor *old=s->actor;opem_collision_world *world=s->staged_world;
 s->actor=r->actor;r->actor=NULL;s->active=r->active;s->has_active=1;
 s->staged_world=NULL;
 s->config.publish(s->config.publish_context,r->loading,&s->active,s->actor,world,
  world?&s->staged_body:NULL,&s->active.gameplay.pose);
 oa_ca_actor_close(old);free(r);
}
static void report(void *ctx,const char *why){
 oa_creation_session *s=(oa_creation_session*)ctx;
 if(s->config.report_failure)s->config.report_failure(s->config.report_context,why);
}
oa_creation_session *oa_creation_session_open(AAssetManager *assets,oa_ca_renderer *renderer,
 const oa_creation_session_config *config,char *e,size_t n){
 oa_creation_session *s;oa_creation_gameplay_config cfg;oa_opening_assets io;int k,active;
 if(e&&n)e[0]=0;
 if(!assets||!renderer||!config||!config->save_directory||!config->save_directory[0]||!config->publish||
 config->space!=OA_CREATOR_GAME_SCENE||config->region!=OA_CREATOR_GAME_REGION||
 !config->generation||!config->item_instance||config->item_index<0||
 (config->tutorials_enabled!=0&&config->tutorials_enabled!=1)){
  fail(e,n,"Character session requires actual actor, storage and source identity");return NULL;}
 if(oa_creation_source_package_default(4,&active)||active!=1){fail(e,n,"Source package4 default is unavailable");return NULL;}
 s=(oa_creation_session*)calloc(1,sizeof(*s));if(!s){fail(e,n,"Character session allocation failed");return NULL;}
 s->assets=assets;s->renderer=renderer;s->config=*config;
 k=snprintf(s->path,sizeof(s->path),"%s/wellofsouls.creation-gameplay-v1.bin",config->save_directory);
 if(k<0||(size_t)k>=sizeof(s->path)){free(s);fail(e,n,"Character progress path is too long");return NULL;}
 memset(&cfg,0,sizeof(cfg));cfg.generation=config->generation;cfg.item_instance=config->item_instance;
 cfg.item_index=config->item_index;cfg.tutorials_enabled=config->tutorials_enabled;
 cfg.package4_active=active;cfg.current_health=50;cfg.base_max_health=50;cfg.path=s->path;
 cfg.appearance.context=s;cfg.appearance.prepare=publish_prepare;cfg.appearance.commit=publish_commit;cfg.appearance.abort=publish_abort;
 cfg.gameplay_backend=config->gameplay_backend;cfg.report_context=s;cfg.report_failure=report;
 cfg.pose_context=s;cfg.validate_load_pose=validate_pose;cfg.runtime=config->runtime;
 io.context=s;io.size=asset_size;io.read=asset_read;
 s->host=oa_creation_gameplay_create(&io,&cfg,e,n);
 if(!s->host){oa_creation_session_close(s);return NULL;}return s;
}
void oa_creation_session_close(oa_creation_session *s){
 if(!s||s->busy)return;discard_collision(s);oa_ca_actor_close(s->actor);
 oa_creation_gameplay_close(s->host);free(s);
}
int oa_creation_session_complete(oa_creation_session *s,const oa_creation_state *draft,
 uint64_t transaction,const oa_creator_game_pose *pose,char *e,size_t n){
 int r;if(enter(s,e,n))return OA_CG_ERROR;
 r=oa_creation_gameplay_complete(s->host,draft,transaction,pose,e,n);s->busy=0;return r;
}
int oa_creation_session_load(oa_creation_session *s,struct oa_stream *stream,
 const opem_controller_config *config,char *e,size_t n){
 int r;if(!stream||!config)return fail(e,n,"Character restore needs the current stream/controller");
 if(enter(s,e,n))return OA_CG_ERROR;discard_collision(s);s->load_stream=stream;s->load_config=*config;
 r=oa_creation_gameplay_load(s->host,e,n);discard_collision(s);s->load_stream=NULL;s->busy=0;return r;
}
int oa_creation_session_save(oa_creation_session *s,char *e,size_t n){
 int r;if(enter(s,e,n))return OA_CG_ERROR;r=oa_creation_gameplay_save(s->host,e,n);s->busy=0;return r;
}
static int refresh(oa_creation_session *s,char *e,size_t n){
 oa_creation_active candidate;int r=oa_creation_gameplay_snapshot(s->host,&candidate,e,n);
 if(!r){s->active=candidate;s->has_active=1;}return r;
}
int oa_creation_session_refresh(oa_creation_session *s,char *e,size_t n){
 int r;if(enter(s,e,n))return OA_CG_ERROR;r=refresh(s,e,n);s->busy=0;return r;
}
static int finish_event(oa_creation_session *s,int r,char *e,size_t n){
 char ignored[128];int snap=refresh(s,ignored,sizeof(ignored));s->busy=0;
 if(!r&&snap)return fail(e,n,"Active character cache could not be refreshed");return r;
}
int oa_creation_session_update_pose(oa_creation_session *s,const oa_creator_game_pose *pose,char *e,size_t n){
 oa_creator_game_host *game;int r;if(enter(s,e,n))return OA_CG_ERROR;
 game=oa_creation_gameplay_game(s->host);if(!game){s->busy=0;return fail(e,n,"Active character is unavailable");}
 r=oa_creator_game_update_pose(game,pose,e,n);return finish_event(s,r,e,n);
}
int oa_creation_session_advance(oa_creation_session *s,uint32_t ms,char *e,size_t n){
 oa_creator_game_host *game;int r;if(enter(s,e,n))return OA_CG_ERROR;
 game=oa_creation_gameplay_game(s->host);if(!game){s->busy=0;return fail(e,n,"Active character is unavailable");}
 r=oa_creator_game_advance(game,ms,e,n);return finish_event(s,r,e,n);
}
int oa_creation_session_cinematic(oa_creation_session *s,int skipped,char *e,size_t n){
 oa_creator_game_host *game;int r;if(skipped!=0&&skipped!=1)return fail(e,n,"Explicit cinematic completion or skip is required");
 if(enter(s,e,n))return OA_CG_ERROR;game=oa_creation_gameplay_game(s->host);
 if(!game){s->busy=0;return fail(e,n,"Active character is unavailable");}
 r=skipped?oa_creator_game_cinematic_skipped(game,e,n):oa_creator_game_cinematic_completed(game,e,n);
 return finish_event(s,r,e,n);
}
const oa_creation_active *oa_creation_session_active(const oa_creation_session *s){return s&&s->has_active?&s->active:NULL;}
oa_ca_actor *oa_creation_session_actor(const oa_creation_session *s){return s?s->actor:NULL;}
oa_creation_gameplay *oa_creation_session_gameplay(oa_creation_session *s){return s?s->host:NULL;}
oa_creator_game_host *oa_creation_session_game(oa_creation_session *s){return s?oa_creation_gameplay_game(s->host):NULL;}
const char *oa_creation_session_checkpoint_path(const oa_creation_session *s){return s?s->path:NULL;}
void oa_creation_session_release_actor(oa_creation_session *s){if(!s||s->busy)return;oa_ca_actor_close(s->actor);s->actor=NULL;}
int oa_creation_session_rebuild_actor(oa_creation_session *s,char *e,size_t n){
 oa_ca_actor *actor,*old;if(enter(s,e,n))return OA_CG_ERROR;
 if(!s->has_active){s->busy=0;return fail(e,n,"Active character is unavailable");}
 actor=prepare_actor(s,&s->active,e,n);if(!actor){s->busy=0;return OA_CG_ERROR;}
 old=s->actor;s->actor=actor;oa_ca_actor_close(old);s->busy=0;return 0;
}
