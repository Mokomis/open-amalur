#include "oa_mq01_cursor.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#define MAGIC UINT32_C(0x4d513031)
struct oa_mq01_cursor {
 uint32_t magic,quest_id;
 uint64_t generation,revision,next_request_id;
 int32_t stage_index;
 int pending,in_callback;
 oa_mq01_request request;
};
static const int32_t ids[]={0,5,10,20,30,40,45,50,60,65,80,90,100};
#define COUNT (sizeof(ids)/sizeof(ids[0]))
static int valid(const oa_mq01_cursor *c) {
 return c && c->magic==MAGIC && c->quest_id==OA_MQ01_QUEST_ID &&
        c->generation!=0 && c->stage_index>=-1 &&
        (c->stage_index<0 || (size_t)c->stage_index<COUNT);
}
static int32_t stage(const oa_mq01_cursor *c) {
 return c->stage_index<0?-1:ids[c->stage_index];
}
static void error_text(char *out,size_t cap,const char *text) {
 if(out && cap) (void)snprintf(out,cap,"%s",text);
}
static int same_snapshot(const oa_mq01_cursor *c,const oa_mq01_snapshot *s) {
 return s && s->quest_id==c->quest_id && s->generation==c->generation &&
        s->revision==c->revision && s->stage_index==c->stage_index &&
        s->stage_id==stage(c);
}
static int same_request(const oa_mq01_request *a,const oa_mq01_request *b) {
 return a->version==b->version && a->quest_id==b->quest_id &&
        a->operation==b->operation && a->generation==b->generation &&
        a->previous_revision==b->previous_revision && a->request_id==b->request_id &&
        a->previous_index==b->previous_index && a->previous_stage==b->previous_stage &&
        a->target_index==b->target_index && a->target_stage==b->target_stage &&
        a->issuer_cookie==b->issuer_cookie;
}
static oa_mq01_status check_expected(oa_mq01_cursor *c,const oa_mq01_snapshot *s) {
 if(!valid(c)||!s)return OA_MQ01_BAD_ARGUMENT;
 if(c->in_callback)return OA_MQ01_BUSY;
 if(s->quest_id!=OA_MQ01_QUEST_ID)return OA_MQ01_UNSUPPORTED;
 if(!same_snapshot(c,s))return OA_MQ01_STALE;
 if(c->pending)return OA_MQ01_BUSY;
 return OA_MQ01_OK;
}
static oa_mq01_status issue(oa_mq01_cursor *c,uint32_t op,int32_t target,oa_mq01_request *out) {
 oa_mq01_request r;
 if(c->revision==UINT64_MAX || c->next_request_id==UINT64_MAX)return OA_MQ01_EXHAUSTED;
 memset(&r,0,sizeof(r));
 r.version=OA_MQ01_CURSOR_VERSION;r.quest_id=c->quest_id;r.operation=op;
 r.generation=c->generation;r.previous_revision=c->revision;
 r.request_id=c->next_request_id+1;r.previous_index=c->stage_index;
 r.previous_stage=stage(c);r.target_index=target;r.target_stage=ids[target];
 r.issuer_cookie=(uintptr_t)c;
 c->next_request_id=r.request_id;c->request=r;c->pending=1;*out=r;
 return OA_MQ01_OK;
}
static oa_mq01_status check_request(oa_mq01_cursor *c,uint64_t gen,const oa_mq01_request *r) {
 if(!valid(c)||!r)return OA_MQ01_BAD_ARGUMENT;
 if(c->in_callback)return OA_MQ01_BUSY;
 if(r->quest_id!=OA_MQ01_QUEST_ID)return OA_MQ01_UNSUPPORTED;
 if(gen!=c->generation || !c->pending || !same_request(r,&c->request) ||
    r->generation!=c->generation || r->previous_revision!=c->revision ||
    r->previous_index!=c->stage_index || r->previous_stage!=stage(c))return OA_MQ01_STALE;
 return OA_MQ01_OK;
}
oa_mq01_status oa_mq01_create(uint32_t quest_id,uint64_t gen,oa_mq01_cursor **out) {
 oa_mq01_cursor *c;
 if(!out||*out||!gen)return OA_MQ01_BAD_ARGUMENT;
 if(quest_id!=OA_MQ01_QUEST_ID)return OA_MQ01_UNSUPPORTED;
 c=(oa_mq01_cursor*)calloc(1,sizeof(*c));if(!c)return OA_MQ01_NO_MEMORY;
 c->magic=MAGIC;c->quest_id=quest_id;c->generation=gen;c->stage_index=-1;*out=c;
 return OA_MQ01_OK;
}
oa_mq01_status oa_mq01_destroy(oa_mq01_cursor **out) {
 oa_mq01_cursor *c;
 if(!out)return OA_MQ01_BAD_ARGUMENT;
 c=*out;if(!c)return OA_MQ01_OK;
 if(!valid(c))return OA_MQ01_BAD_ARGUMENT;
 if(c->in_callback)return OA_MQ01_BUSY;
 memset(c,0,sizeof(*c));free(c);*out=NULL;return OA_MQ01_OK;
}
oa_mq01_status oa_mq01_query(const oa_mq01_cursor *c,uint32_t q,uint64_t gen,oa_mq01_snapshot *out) {
 oa_mq01_snapshot s;
 if(!out)return OA_MQ01_BAD_ARGUMENT;
 if(q!=OA_MQ01_QUEST_ID)return OA_MQ01_UNSUPPORTED;
 if(!valid(c))return OA_MQ01_BAD_ARGUMENT;
 if(c->in_callback)return OA_MQ01_BUSY;
 if(gen!=c->generation)return OA_MQ01_STALE;
 memset(&s,0,sizeof(s));s.quest_id=c->quest_id;s.generation=c->generation;
 s.revision=c->revision;s.stage_index=c->stage_index;s.stage_id=stage(c);*out=s;
 return OA_MQ01_OK;
}
oa_mq01_status oa_mq01_prepare_start(oa_mq01_cursor *c,const oa_mq01_snapshot *s,
                                    oa_mq01_request *out,oa_mq01_noop *reason) {
 oa_mq01_status result;
 if(reason)*reason=OA_MQ01_NOOP_NONE;
 if(!out)return OA_MQ01_BAD_ARGUMENT;
 result=check_expected(c,s);if(result!=OA_MQ01_OK)return result;
 if(c->stage_index>=0){if(reason)*reason=OA_MQ01_NOOP_ALREADY_STARTED;return OA_MQ01_NO_CHANGE;}
 return issue(c,OA_MQ01_START,0,out);
}
oa_mq01_status oa_mq01_prepare_set(oa_mq01_cursor *c,const oa_mq01_snapshot *s,
                                  int32_t target,oa_mq01_request *out,oa_mq01_noop *reason) {
 size_t i;oa_mq01_status result;
 if(reason)*reason=OA_MQ01_NOOP_NONE;
 if(!out)return OA_MQ01_BAD_ARGUMENT;
 result=check_expected(c,s);if(result!=OA_MQ01_OK)return result;
 if(c->stage_index<0){if(reason)*reason=OA_MQ01_NOOP_UNSTARTED;return OA_MQ01_NO_CHANGE;}
 for(i=0;i<COUNT && ids[i]!=target;i++){}
 if(i==COUNT){if(reason)*reason=OA_MQ01_NOOP_UNDEFINED_STAGE;return OA_MQ01_NO_CHANGE;}
 if((int32_t)i==c->stage_index){if(reason)*reason=OA_MQ01_NOOP_SAME_STAGE;return OA_MQ01_NO_CHANGE;}
 return issue(c,OA_MQ01_SET_STAGE,(int32_t)i,out);
}
oa_mq01_status oa_mq01_commit(oa_mq01_cursor *c,uint64_t gen,const oa_mq01_request *r,
                             oa_mq01_apply_fn apply,void *ctx,char *err,size_t cap) {
 oa_mq01_status status;oa_mq01_request call;int acknowledged;int32_t committed_target;
 if(err&&cap)err[0]=0;
 status=check_request(c,gen,r);
 if(status!=OA_MQ01_OK){error_text(err,cap,oa_mq01_status_name(status));return status;}
 if(!apply){error_text(err,cap,"MQ01 transition requires a real host acknowledgement");return OA_MQ01_CALLBACK_REQUIRED;}
 /* Copy before the callback: caller-owned request storage may be changed by its owner. */
 call=c->request;committed_target=c->request.target_index;c->in_callback=1;
 acknowledged=apply(ctx,&call,err,cap);
 if(err&&cap)err[cap-1]=0;
 c->in_callback=0;c->pending=0;memset(&c->request,0,sizeof(c->request));
 if(acknowledged!=0){
  if(!err||!cap||!err[0])error_text(err,cap,"MQ01 host rejected transition; cursor unchanged");
  return OA_MQ01_HOST_REJECTED;
 }
 c->stage_index=committed_target;c->revision++;
 if(err&&cap)err[0]=0;
 return OA_MQ01_OK;
}
oa_mq01_status oa_mq01_cancel(oa_mq01_cursor *c,uint64_t gen,const oa_mq01_request *r) {
 oa_mq01_status status=check_request(c,gen,r);
 if(status!=OA_MQ01_OK)return status;
 c->pending=0;memset(&c->request,0,sizeof(c->request));return OA_MQ01_OK;
}
const int32_t *oa_mq01_stage_ids(size_t *count){if(count)*count=COUNT;return ids;}
const char *oa_mq01_status_name(oa_mq01_status s) {
 switch(s){
 case OA_MQ01_OK:return "ok";case OA_MQ01_NO_CHANGE:return "native guarded no-op";
 case OA_MQ01_UNSUPPORTED:return "unsupported quest";case OA_MQ01_STALE:return "stale request/state";
 case OA_MQ01_BUSY:return "pending transition or callback reentry";case OA_MQ01_HOST_REJECTED:return "host rejected";
 case OA_MQ01_BAD_ARGUMENT:return "bad argument";case OA_MQ01_NO_MEMORY:return "allocation failed";
 case OA_MQ01_EXHAUSTED:return "revision/request counter exhausted";case OA_MQ01_CALLBACK_REQUIRED:return "host callback required";
 default:return "unknown status";
 }
}
