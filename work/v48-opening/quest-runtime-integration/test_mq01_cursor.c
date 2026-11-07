#include "oa_mq01_cursor.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static unsigned checks=0;
#define CHECK(x) do{checks++;if(!(x)){fprintf(stderr,"FAIL line %d: %s\n",__LINE__,#x);exit(1);}}while(0)
typedef struct {
 oa_mq01_cursor *cursor;
 unsigned calls,accepted;
 int reject,reenter,mutate_argument;
 int32_t host_stage;
 uint64_t generation;
 oa_mq01_snapshot expected;
} recorded_host;
/* RECORDED ACKNOWLEDGED TEST BACKEND ONLY.
 * It models an atomic acknowledgement, not native startup/QuestMgr effects. */
static int acknowledge(void *ctx,const oa_mq01_request *r,char *error,size_t cap) {
 recorded_host *h=(recorded_host*)ctx;oa_mq01_snapshot s;oa_mq01_request nested;
 oa_mq01_noop reason;oa_mq01_cursor *same=h->cursor;
 h->calls++;
 CHECK(r->quest_id==OA_MQ01_QUEST_ID);
 CHECK(r->previous_stage==h->host_stage);
 if(h->reenter){
  CHECK(oa_mq01_query(h->cursor,OA_MQ01_QUEST_ID,h->generation,&s)==OA_MQ01_BUSY);
  CHECK(oa_mq01_prepare_set(h->cursor,&h->expected,10,&nested,&reason)==OA_MQ01_BUSY);
  CHECK(oa_mq01_commit(h->cursor,h->generation,r,acknowledge,h,error,cap)==OA_MQ01_BUSY);
  CHECK(oa_mq01_cancel(h->cursor,h->generation,r)==OA_MQ01_BUSY);
  CHECK(oa_mq01_destroy(&same)==OA_MQ01_BUSY && same==h->cursor);
 }
 if(h->reject){if(error&&cap)(void)snprintf(error,cap,"recorded effects unavailable");return 1;}
 h->host_stage=r->target_stage;h->accepted++;return 0;
}
static oa_mq01_snapshot snapshot(oa_mq01_cursor *c,uint64_t gen) {
 oa_mq01_snapshot s;CHECK(oa_mq01_query(c,OA_MQ01_QUEST_ID,gen,&s)==OA_MQ01_OK);return s;
}
static int same_snapshot(oa_mq01_snapshot a,oa_mq01_snapshot b) {
 return a.quest_id==b.quest_id&&a.generation==b.generation&&a.revision==b.revision&&
        a.stage_index==b.stage_index&&a.stage_id==b.stage_id;
}
static oa_mq01_request perform_set(oa_mq01_cursor *c,recorded_host *h,int32_t target) {
 oa_mq01_snapshot s=snapshot(c,h->generation);oa_mq01_request r;oa_mq01_noop reason;char e[96];
 CHECK(oa_mq01_prepare_set(c,&s,target,&r,&reason)==OA_MQ01_OK);
 h->expected=s;
 CHECK(oa_mq01_commit(c,h->generation,&r,acknowledge,h,e,sizeof(e))==OA_MQ01_OK);
 s=snapshot(c,h->generation);CHECK(s.stage_id==target&&s.stage_id==h->host_stage&&e[0]==0);return r;
}
int main(void){
 oa_mq01_cursor *c=NULL,*a=NULL,*b=NULL;oa_mq01_snapshot s,old,unchanged;oa_mq01_request r,denied,forged,ra,rb,sentinel;
 oa_mq01_noop reason;oa_mq01_status status;char error[128];recorded_host host;unsigned calls;size_t n,i;const int32_t *ids;
 static const int32_t expected[]={0,5,10,20,30,40,45,50,60,65,80,90,100};
 memset(&host,0,sizeof(host));host.host_stage=-1;host.generation=101;
 ids=oa_mq01_stage_ids(&n);CHECK(n==13);
 for(i=0;i<n;i++)CHECK(ids[i]==expected[i]&&ids[i]!=25);
 CHECK(oa_mq01_create(1,101,&c)==OA_MQ01_UNSUPPORTED&&c==NULL);
 CHECK(oa_mq01_create(OA_MQ01_QUEST_ID,0,&c)==OA_MQ01_BAD_ARGUMENT&&c==NULL);
 CHECK(oa_mq01_create(OA_MQ01_QUEST_ID,101,&c)==OA_MQ01_OK&&c!=NULL);
 host.cursor=c;
 s=snapshot(c,101);CHECK(s.stage_id==-1&&s.stage_index==-1&&s.revision==0);
 unchanged=s;CHECK(oa_mq01_query(c,1,101,&unchanged)==OA_MQ01_UNSUPPORTED);CHECK(same_snapshot(s,unchanged));
 CHECK(oa_mq01_query(c,OA_MQ01_QUEST_ID,102,&unchanged)==OA_MQ01_STALE);CHECK(same_snapshot(s,unchanged));
 memset(&r,0xa5,sizeof(r));memcpy(&sentinel,&r,sizeof(r));
 CHECK(oa_mq01_prepare_set(c,&s,5,&r,&reason)==OA_MQ01_NO_CHANGE&&reason==OA_MQ01_NOOP_UNSTARTED);
 CHECK(memcmp(&r,&sentinel,sizeof(r))==0&&same_snapshot(s,snapshot(c,101)));
 CHECK(oa_mq01_prepare_set(c,&s,25,&r,&reason)==OA_MQ01_NO_CHANGE&&reason==OA_MQ01_NOOP_UNSTARTED);
 old=s;CHECK(oa_mq01_prepare_start(c,&s,&r,&reason)==OA_MQ01_OK);
 CHECK(r.previous_stage==-1&&r.target_stage==0&&r.operation==OA_MQ01_START);
 CHECK(same_snapshot(s,snapshot(c,101))); /* PREPARE cannot start. */
 CHECK(oa_mq01_prepare_set(c,&s,5,&forged,&reason)==OA_MQ01_BUSY);
 CHECK(oa_mq01_commit(c,101,&r,NULL,&host,error,sizeof(error))==OA_MQ01_CALLBACK_REQUIRED);
 CHECK(same_snapshot(s,snapshot(c,101))&&host.calls==0);
 CHECK(oa_mq01_commit(c,102,&r,acknowledge,&host,error,sizeof(error))==OA_MQ01_STALE&&host.calls==0);
 forged=r;forged.target_stage=5;
 CHECK(oa_mq01_commit(c,101,&forged,acknowledge,&host,error,sizeof(error))==OA_MQ01_STALE&&host.calls==0);
 forged=r;forged.previous_stage=0;
 CHECK(oa_mq01_commit(c,101,&forged,acknowledge,&host,error,sizeof(error))==OA_MQ01_STALE&&host.calls==0);
 host.reject=1;host.expected=s;denied=r;
 CHECK(oa_mq01_commit(c,101,&r,acknowledge,&host,error,sizeof(error))==OA_MQ01_HOST_REJECTED);
 CHECK(same_snapshot(old,snapshot(c,101))&&host.host_stage==-1&&host.accepted==0);
 calls=host.calls;
 CHECK(oa_mq01_commit(c,101,&denied,acknowledge,&host,error,sizeof(error))==OA_MQ01_STALE&&host.calls==calls);
 CHECK(oa_mq01_prepare_start(c,&s,&r,&reason)==OA_MQ01_OK&&r.request_id!=denied.request_id);
 CHECK(oa_mq01_commit(c,101,&denied,acknowledge,&host,error,sizeof(error))==OA_MQ01_STALE);
 host.reject=0;host.reenter=1;
 CHECK(oa_mq01_commit(c,101,&r,acknowledge,&host,error,sizeof(error))==OA_MQ01_OK);
 host.reenter=0;s=snapshot(c,101);CHECK(s.stage_id==0&&s.stage_index==0&&s.revision==1&&host.host_stage==0);
 calls=host.calls;
 CHECK(oa_mq01_commit(c,101,&r,acknowledge,&host,error,sizeof(error))==OA_MQ01_STALE&&host.calls==calls);
 CHECK(oa_mq01_prepare_start(c,&s,&r,&reason)==OA_MQ01_NO_CHANGE&&reason==OA_MQ01_NOOP_ALREADY_STARTED);
 CHECK(oa_mq01_prepare_set(c,&s,0,&r,&reason)==OA_MQ01_NO_CHANGE&&reason==OA_MQ01_NOOP_SAME_STAGE);
 perform_set(c,&host,5);s=snapshot(c,101);CHECK(s.stage_index==1&&s.revision==2);
 CHECK(oa_mq01_prepare_set(c,&old,20,&r,&reason)==OA_MQ01_STALE);
 old=s;calls=host.calls;
 CHECK(oa_mq01_prepare_set(c,&s,25,&r,&reason)==OA_MQ01_NO_CHANGE&&reason==OA_MQ01_NOOP_UNDEFINED_STAGE);
 CHECK(same_snapshot(old,snapshot(c,101))&&host.calls==calls);
 CHECK(oa_mq01_prepare_set(c,&s,5,&r,&reason)==OA_MQ01_NO_CHANGE&&reason==OA_MQ01_NOOP_SAME_STAGE);
 CHECK(oa_mq01_prepare_set(c,&s,-1,&r,&reason)==OA_MQ01_NO_CHANGE&&reason==OA_MQ01_NOOP_UNDEFINED_STAGE);
 CHECK(oa_mq01_prepare_set(c,&s,INT32_MAX,&r,&reason)==OA_MQ01_NO_CHANGE&&reason==OA_MQ01_NOOP_UNDEFINED_STAGE);
 CHECK(oa_mq01_prepare_set(c,&s,20,&r,&reason)==OA_MQ01_OK);
 host.reject=1;host.expected=s;denied=r;
 CHECK(oa_mq01_commit(c,101,&r,acknowledge,&host,error,sizeof(error))==OA_MQ01_HOST_REJECTED);
 CHECK(same_snapshot(s,snapshot(c,101))&&host.host_stage==5);
 CHECK(oa_mq01_commit(c,101,&denied,acknowledge,&host,error,sizeof(error))==OA_MQ01_STALE);
 host.reject=0;
 perform_set(c,&host,20);rb=perform_set(c,&host,5); /* Explicit new regression is allowed. */
 s=snapshot(c,101);CHECK(s.stage_id==5&&s.revision==4);
 CHECK(oa_mq01_prepare_set(c,&s,10,&r,&reason)==OA_MQ01_OK);
 CHECK(oa_mq01_cancel(c,101,&r)==OA_MQ01_OK);
 CHECK(oa_mq01_commit(c,101,&r,acknowledge,&host,error,sizeof(error))==OA_MQ01_STALE);
 CHECK(same_snapshot(s,snapshot(c,101)));
 /* Every actual source ID is supported with an acknowledged transition, including explicit0. */
 for(i=0;i<n;i++){s=snapshot(c,101);if(s.stage_id!=ids[i])perform_set(c,&host,ids[i]);}
 s=snapshot(c,101);CHECK(s.stage_id==100);calls=host.calls;
 CHECK(oa_mq01_commit(c,101,&rb,acknowledge,&host,error,sizeof(error))==OA_MQ01_STALE);
 CHECK(host.calls==calls&&same_snapshot(s,snapshot(c,101)));
 /* A fresh, explicit source request can regress100->5; an old token cannot. */
 perform_set(c,&host,5);CHECK(snapshot(c,101).stage_id==5);
 CHECK(oa_mq01_destroy(&c)==OA_MQ01_OK&&c==NULL);
 CHECK(oa_mq01_destroy(&c)==OA_MQ01_OK);
 CHECK(oa_mq01_create(OA_MQ01_QUEST_ID,202,&a)==OA_MQ01_OK);
 CHECK(oa_mq01_create(OA_MQ01_QUEST_ID,202,&b)==OA_MQ01_OK);
 s=snapshot(a,202);old=snapshot(b,202);
 CHECK(oa_mq01_prepare_start(a,&s,&ra,&reason)==OA_MQ01_OK);
 CHECK(oa_mq01_prepare_start(b,&old,&rb,&reason)==OA_MQ01_OK);
 CHECK(oa_mq01_commit(b,202,&ra,acknowledge,&host,error,sizeof(error))==OA_MQ01_STALE); /* Issuer differs. */
 CHECK(oa_mq01_cancel(a,202,&ra)==OA_MQ01_OK);
 CHECK(oa_mq01_cancel(b,202,&rb)==OA_MQ01_OK);
 CHECK(oa_mq01_destroy(&a)==OA_MQ01_OK&&oa_mq01_destroy(&b)==OA_MQ01_OK);
 CHECK(oa_mq01_create(OA_MQ01_QUEST_ID,203,&a)==OA_MQ01_OK);
 s=snapshot(a,203);CHECK(oa_mq01_prepare_start(a,&s,&r,&reason)==OA_MQ01_OK);
 CHECK(oa_mq01_commit(a,203,&ra,acknowledge,&host,error,sizeof(error))==OA_MQ01_STALE);
 CHECK(snapshot(a,203).stage_id==-1);
 CHECK(oa_mq01_destroy(&a)==OA_MQ01_OK);
 status=OA_MQ01_CALLBACK_REQUIRED;CHECK(oa_mq01_status_name(status)!=NULL);
 printf("{\"result\":\"PASS\",\"checks\":%u,\"host_backend\":\"recorded atomic acknowledgements only; no native QuestMgr/startup effects\",\"quest_table\":13}\n",checks);
 return 0;
}
