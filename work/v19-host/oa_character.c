#include "oa_character.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static void qmul(float o[4],const float a[4],const float b[4]){
 float r[4]={a[3]*b[0]+a[0]*b[3]+a[1]*b[2]-a[2]*b[1],a[3]*b[1]-a[0]*b[2]+a[1]*b[3]+a[2]*b[0],a[3]*b[2]+a[0]*b[1]-a[1]*b[0]+a[2]*b[3],a[3]*b[3]-a[0]*b[0]-a[1]*b[1]-a[2]*b[2]};memcpy(o,r,sizeof(r));
}
static void qrot(float o[3],const float q[4],const float v[3]){
 float t[3]={2*(q[1]*v[2]-q[2]*v[1]),2*(q[2]*v[0]-q[0]*v[2]),2*(q[0]*v[1]-q[1]*v[0])};
 float r[3]={v[0]+q[3]*t[0]+q[1]*t[2]-q[2]*t[1],v[1]+q[3]*t[1]+q[2]*t[0]-q[0]*t[2],v[2]+q[3]*t[2]+q[0]*t[1]-q[1]*t[0]};memcpy(o,r,sizeof(r));
}
static int fail(char *error,size_t n,const char *why){if(error&&n)snprintf(error,n,"%s",why);return 0;}
#define NEED(bytes_needed) do{if((uint64_t)(bytes_needed)>(uint64_t)(size-at))return fail(error,error_size,"character asset truncated");}while(0)
/* Forward speed the clip was animated for: how fast the lowest moving joint travels while it is on the ground. */
static float planted_speed(const oa_character *c,const oa_char_clip *k){
 uint32_t f,j,best=0,frames=k->frames,joints=c->joints;float *w=(float*)malloc(sizeof(float)*3u*frames*joints),(*q)[4]=(float(*)[4])malloc(sizeof(float)*4u*joints),lowest=1e30f,floor_z=1e30f,sum=0;unsigned count=0;
 if(!w||!q){free(w);free(q);return 0;}
 for(f=0;f<frames;f++)for(j=0;j<joints;j++){const float *a=k->pose+(size_t)(f*joints+j)*7;float *p=w+(size_t)(f*joints+j)*3;if(c->parents[j]<0){memcpy(q[j],a,16);memcpy(p,a+4,12);}else{int up=c->parents[j];float r[3];qmul(q[j],q[up],a);qrot(r,q[up],a+4);p[0]=w[(size_t)(f*joints+(uint32_t)up)*3]+r[0];p[1]=w[(size_t)(f*joints+(uint32_t)up)*3+1]+r[1];p[2]=w[(size_t)(f*joints+(uint32_t)up)*3+2]+r[2];}}
 for(j=0;j<joints;j++){float mean=0,x0=1e30f,x1=-1e30f;for(f=0;f<frames;f++){const float *p=w+(size_t)(f*joints+j)*3;mean+=p[2];if(p[0]<x0)x0=p[0];if(p[0]>x1)x1=p[0];}mean/=(float)frames;if(x1-x0>5.f&&mean<lowest){lowest=mean;best=j;}}
 if(lowest<1e29f){for(f=0;f<frames;f++){float z=w[(size_t)(f*joints+best)*3+2];if(z<floor_z)floor_z=z;}
  for(f=0;f+1<frames;f++){const float *p=w+(size_t)(f*joints+best)*3,*n=w+(size_t)((f+1)*joints+best)*3;if(p[2]<=floor_z+6.f){float dx=n[0]-p[0],dy=n[1]-p[1];sum+=sqrtf(dx*dx+dy*dy)*k->fps;count++;}}}
 free(w);free(q);return count?sum/(float)count:0;}
int oa_character_parse(oa_character *c,uint8_t *bytes,size_t size,char *error,size_t error_size){
 size_t at=8;uint32_t i,head[4];memset(c,0,sizeof(*c));
 if(size<24||memcmp(bytes,"OACHAR01",8))return fail(error,error_size,"character asset header invalid");
 memcpy(head,bytes+at,16);at+=16;c->joints=head[0];c->clip_count=head[1];c->part_count=head[2];c->texture_count=head[3];
 if(!c->joints||c->joints>OA_CHAR_MAX_JOINTS||!c->clip_count||c->clip_count>OA_CHAR_MAX_CLIPS||!c->part_count||c->part_count>OA_CHAR_MAX_PARTS||c->texture_count>OA_CHAR_MAX_TEXTURES)return fail(error,error_size,"character asset counts invalid");
 /* Padded so the clips that follow stay aligned. */NEED((c->joints+1u)/2u*4u);memcpy(c->parents,bytes+at,c->joints*2u);at+=(c->joints+1u)/2u*4u;
 for(i=0;i<c->joints;i++)if(c->parents[i]>=(int16_t)i)return fail(error,error_size,"character joint order invalid");
 for(i=0;i<c->clip_count;i++){oa_char_clip *k=c->clips+i;NEED(8);memcpy(&k->frames,bytes+at,4);memcpy(&k->fps,bytes+at+4,4);at+=8;
  if(k->frames<2||k->frames>100000||!(k->fps>0&&k->fps<1000))return fail(error,error_size,"character clip invalid");
  NEED((uint64_t)k->frames*c->joints*28u);k->pose=(const float*)(bytes+at);at+=(size_t)k->frames*c->joints*28u;}
 for(i=0;i<c->texture_count;i++){oa_char_texture *t=c->textures+i;NEED(8);memcpy(&t->width,bytes+at,4);memcpy(&t->height,bytes+at+4,4);at+=8;
  if(!t->width||!t->height||t->width>4096||t->height>4096)return fail(error,error_size,"character texture invalid");
  NEED((uint64_t)t->width*t->height*4u);t->rgba=bytes+at;at+=(size_t)t->width*t->height*4u;}
 for(i=0;i<c->part_count;i++){oa_char_part *p=c->parts+i;uint32_t v,k;uint8_t *record;NEED(16);memcpy(&p->vertices,bytes+at,4);memcpy(&p->indices,bytes+at+4,4);memcpy(&p->palette_count,bytes+at+8,4);memcpy(&p->texture,bytes+at+12,4);at+=16;
  if(!p->vertices||p->vertices>1000000||!p->indices||p->indices%3||p->indices>6000000||!p->palette_count||p->palette_count>OA_CHAR_MAX_PALETTE||p->texture>=(int32_t)c->texture_count)return fail(error,error_size,"character part invalid");
  NEED((uint64_t)p->palette_count*OA_CHAR_PALETTE_BYTES);p->palette=bytes+at;
  for(k=0;k<p->palette_count;k++){uint32_t joint;memcpy(&joint,p->palette+k*OA_CHAR_PALETTE_BYTES,4);if(joint>=c->joints)return fail(error,error_size,"character palette joint invalid");}
  at+=(size_t)p->palette_count*OA_CHAR_PALETTE_BYTES;
  NEED((uint64_t)p->vertices*OA_CHAR_VERTEX_BYTES);p->vertex=bytes+at;
  for(v=0;v<p->vertices;v++){record=(uint8_t*)p->vertex+v*OA_CHAR_VERTEX_BYTES;for(k=0;k<4;k++)if(record[32+k]>=p->palette_count){float w;memcpy(&w,record+36+k*4,4);if(w>0)return fail(error,error_size,"character vertex joint invalid");record[32+k]=0;}}
  at+=(size_t)p->vertices*OA_CHAR_VERTEX_BYTES;
  NEED((uint64_t)p->indices*4u);p->index=(const uint32_t*)(bytes+at);
  for(k=0;k<p->indices;k++)if(p->index[k]>=p->vertices)return fail(error,error_size,"character index invalid");
  at+=(size_t)p->indices*4u;}
 if(at!=size)return fail(error,error_size,"character asset has trailing bytes");
 {static const uint32_t moves[4]={OA_CLIP_WALK,OA_CLIP_RUN,OA_CLIP_COMBAT+OA_CLIP_WALK,OA_CLIP_COMBAT+OA_CLIP_RUN};for(i=0;i<4;i++)if(moves[i]<c->clip_count&&(moves[i]<3||c->clip_count>OA_CLIP_COMBAT+2u))c->clip_speed[moves[i]]=planted_speed(c,c->clips+moves[i]);}
 c->move_clip=-1;c->idle_next=14.f;c->idle_seed=431608u;
 /* The slope and lean clips hold one pose each, relative to a reference this code has not recovered. The difference within each pair is what is used: half of it either way about their middle. */
 if(c->clip_count==OA_CHAR_MAX_CLIPS&&(c->lean_delta=(float*)malloc(sizeof(float)*8u*c->joints))!=NULL){uint32_t j,pair;for(pair=0;pair<2;pair++)for(j=0;j<c->joints;j++){const oa_char_clip *ka=c->clips+OA_CLIP_SLOPE_UP+pair*2,*kb=ka+1;const float *qa=ka->pose+(size_t)(ka->frames/2u*c->joints+j)*7,*qb=kb->pose+(size_t)(kb->frames/2u*c->joints+j)*7;float s=qa[0]*qb[0]+qa[1]*qb[1]+qa[2]*qb[2]+qa[3]*qb[3]<0?-1.f:1.f,m[4],n,*d=c->lean_delta+(size_t)(pair*c->joints+j)*4;uint32_t e;for(e=0;e<4;e++)m[e]=qa[e]+qb[e]*s;n=sqrtf(m[0]*m[0]+m[1]*m[1]+m[2]*m[2]+m[3]*m[3]);if(n<1e-4f){d[0]=d[1]=d[2]=0;d[3]=1;continue;}for(e=0;e<3;e++)m[e]=-m[e]/n;m[3]/=n;qmul(d,qa,m);}}
 c->bytes=bytes;c->size=size;c->weight[OA_CLIP_IDLE]=1;c->oneshot=-1;c->ready=1;oa_character_pose(c);return 1;
}
void oa_character_free(oa_character *c){free(c->lean_delta);free(c->bytes);memset(c,0,sizeof(*c));}
/* The loop frame closest to where a clip ends, so it leads into the loop without a step. */
static float loop_entry(const oa_character *c,const oa_char_clip *from,const oa_char_clip *loop){
 uint32_t f,j,best=0;float low=1e30f;const float *end=from->pose+(size_t)(from->frames-1u)*c->joints*7;
 for(f=0;f+1<loop->frames;f++){float e=0;const float *p=loop->pose+(size_t)f*c->joints*7;for(j=0;j<c->joints;j++){const float *a=end+j*7,*b=p+j*7;float d=a[0]*b[0]+a[1]*b[1]+a[2]*b[2]+a[3]*b[3];e+=1.f-d*d;}if(e<low){low=e;best=f;}}
 return (float)best/loop->fps;}
/* Which clip carries a change of movement. The 45 and 135 degree limits and the 0.5 second short stop are authored. */
static void movement_change(oa_character *c,int moving,int running,float dt){
 if(c->oneshot>=0){c->move_clip=-1;c->was_moving=moving;c->idle_for=0;return;}
 if(moving&&!c->was_moving){float turn=remainderf(c->move_target-c->facing,6.283185307f),size=fabsf(turn);int clip;
  c->turn_total=0;
  if(size<.7854f)clip=running?OA_CLIP_RUN_START:OA_CLIP_WALK_START;
  else{c->turn_total=turn;if(size>2.3562f&&running)clip=OA_CLIP_RUN_TURN_BACK;else if(running)clip=turn>0?OA_CLIP_RUN_TURN_LEFT:OA_CLIP_RUN_TURN_RIGHT;else clip=turn>0?OA_CLIP_WALK_TURN_LEFT:OA_CLIP_WALK_TURN_RIGHT;}
  c->move_clip=clip;c->time[clip]=0;c->moved_for=0;}
 else if(!moving&&c->was_moving){int clip=c->weight[OA_CLIP_RUN]+c->weight[OA_CLIP_COMBAT+OA_CLIP_RUN]+(c->move_clip==OA_CLIP_RUN_START||c->move_clip==OA_CLIP_RUN_TURN_LEFT||c->move_clip==OA_CLIP_RUN_TURN_RIGHT||c->move_clip==OA_CLIP_RUN_TURN_BACK?1.f:0.f)>.5f?(c->moved_for<.5f?OA_CLIP_RUN_STOP_SHORT:OA_CLIP_RUN_STOP):OA_CLIP_WALK_STOP;c->move_clip=clip;c->time[clip]=0;c->turn_total=0;c->idle_for=0;}
 if(moving){c->moved_for+=dt;c->idle_for=0;}
 else if(c->move_clip<0&&!c->combat_stance){c->idle_for+=dt;if(c->idle_for>c->idle_next){int clip=OA_CLIP_IDLE_VARIATION+(int)((c->idle_seed>>16)%4u);c->idle_seed=c->idle_seed*1103515245u+12345u;c->move_clip=clip;c->time[clip]=0;c->idle_for=0;c->idle_next=14.f+(float)((c->idle_seed>>16)%12u);}}
 c->was_moving=moving;}
float oa_character_turn_step(const oa_character *c,float turn,float dt){
 /* Turn clips contain transient skeletal rotation and finish near the run-entry pose.
  * The extra facing rotation/timing below is authored host policy; native root-motion
  * trajectories and motion-tree timing have not been recovered. */
 float step=dt*12.0f;
 if(c->turn_total!=0&&c->move_clip>=0&&c->lean_delta){const oa_char_clip *k=c->clips+c->move_clip;float period=(float)(k->frames-1)/k->fps;if(c->time[c->move_clip]<period*.2f)return 0;step=fabsf(c->turn_total)/(period*.4f)*dt;}
 return turn>step?step:turn<-step?-step:turn;}
void oa_character_animate(oa_character *c,float speed,float velocity_units,float dt){
 /* Playback follows travel speed, so a planted foot stays put. The walk to run threshold is authored. */
 uint32_t i;float target[OA_CHAR_MAX_CLIPS]={0},fade=dt*(c->oneshot>=0||c->move_clip>=0?14.0f:8.0f),sum=0;
 uint32_t base=c->combat_stance&&c->clip_count>OA_CLIP_COMBAT+2u?OA_CLIP_COMBAT:0u;
 uint32_t wanted=base+(speed<.05f?OA_CLIP_IDLE:speed<.7f?OA_CLIP_WALK:OA_CLIP_RUN);
 if(!c->ready)return;
 if(c->clip_count<3){const oa_char_clip *k=c->clips;c->time[0]=fmodf(c->time[0]+dt,(float)(k->frames-1)/k->fps);return;}
 if(c->lean_delta)movement_change(c,speed>=.05f,speed>=.7f,dt);
 target[c->oneshot>=0?(uint32_t)c->oneshot:c->move_clip>=0?(uint32_t)c->move_clip:wanted]=1;if(fade>1)fade=1;
 for(i=0;i<c->clip_count;i++){const oa_char_clip *k=c->clips+i;float period=(float)(k->frames-1)/k->fps;
  c->weight[i]+=(target[i]-c->weight[i])*fade;sum+=c->weight[i];
  if((int)i==c->oneshot){c->time[i]+=dt*c->oneshot_rate;if(c->time[i]>=period){c->time[i]=period;if(!c->oneshot_hold)c->oneshot=-1;}}
  else if((int)i==c->move_clip){c->time[i]+=dt;if(c->time[i]>=period){c->time[i]=period;c->move_clip=-1;c->turn_total=0;if(speed>=.05f){uint32_t role=speed<.7f?OA_CLIP_WALK:OA_CLIP_RUN;c->time[role]=loop_entry(c,k,c->clips+role);if(c->clip_count>OA_CLIP_COMBAT+role)c->time[OA_CLIP_COMBAT+role]=c->time[role];}}}
  else if(i<3||(i>=OA_CLIP_COMBAT&&i<OA_CLIP_COMBAT+3u)){uint32_t role=i>=OA_CLIP_COMBAT?i-OA_CLIP_COMBAT:i;float rate=1.f;if(role){float travel=c->clip_speed[i]>1.f?c->clip_speed[i]:(role==OA_CLIP_WALK?150.f:420.f);rate=velocity_units/travel;if(rate<.5f)rate=.5f;if(rate>2.f)rate=2.f;}c->time[i]=fmodf(c->time[i]+dt*rate,period);}}
 if(sum>0)for(i=0;i<c->clip_count;i++)c->weight[i]/=sum;
}
void oa_character_play(oa_character *c,int clip,int hold,float rate){if(!c->ready||clip<0||(uint32_t)clip>=c->clip_count)return;c->oneshot=clip;c->oneshot_hold=hold;c->oneshot_rate=rate;c->time[clip]=0;}
void oa_character_stop(oa_character *c){c->oneshot=-1;}
void oa_character_pose(oa_character *c){
 uint32_t j,i;if(!c->ready)return;
 for(j=0;j<c->joints;j++){float q[4]={0,0,0,0},t[3]={0,0,0},n;
  for(i=0;i<c->clip_count;i++){const oa_char_clip *k=c->clips+i;float w=c->weight[i],at,alpha,sign,rq[4];uint32_t a,b,e;const float *ka,*kb;
   if(w<=0)continue;at=c->time[i]*k->fps;a=(uint32_t)at;if(a>=k->frames-1)a=k->frames-2;b=a+1;alpha=at-(float)a;if(alpha>1)alpha=1;
   ka=k->pose+(size_t)(a*c->joints+j)*7;kb=k->pose+(size_t)(b*c->joints+j)*7;
   sign=ka[0]*kb[0]+ka[1]*kb[1]+ka[2]*kb[2]+ka[3]*kb[3]<0?-1.f:1.f;
   for(e=0;e<4;e++)rq[e]=ka[e]+(kb[e]*sign-ka[e])*alpha;
   sign=q[0]*rq[0]+q[1]*rq[1]+q[2]*rq[2]+q[3]*rq[3]<0?-1.f:1.f;
   for(e=0;e<4;e++)q[e]+=rq[e]*sign*w;
   for(e=0;e<3;e++)t[e]+=(ka[4+e]+(kb[4+e]-ka[4+e])*alpha)*w;}
  n=sqrtf(q[0]*q[0]+q[1]*q[1]+q[2]*q[2]+q[3]*q[3]);if(n>0){q[0]/=n;q[1]/=n;q[2]/=n;q[3]/=n;}else q[3]=1;
  if(c->lean_delta&&(c->slope!=0||c->lean!=0)){uint32_t pair;for(pair=0;pair<2;pair++){float amount=pair?c->lean:c->slope,dq[4];const float *d=c->lean_delta+(size_t)(pair*c->joints+j)*4;uint32_t e;if(amount==0||(d[0]==0&&d[1]==0&&d[2]==0))continue;dq[0]=d[0]*amount;dq[1]=d[1]*amount;dq[2]=d[2]*amount;dq[3]=1.f+(d[3]-1.f)*fabsf(amount);n=sqrtf(dq[0]*dq[0]+dq[1]*dq[1]+dq[2]*dq[2]+dq[3]*dq[3]);for(e=0;e<4;e++)dq[e]/=n;qmul(q,dq,q);}}
  if(c->parents[j]<0){memcpy(c->world_q[j],q,sizeof(q));memcpy(c->world_t[j],t,sizeof(t));}
  else{const int p=c->parents[j];float r[3];qmul(c->world_q[j],c->world_q[p],q);qrot(r,c->world_q[p],t);for(i=0;i<3;i++)c->world_t[j][i]=c->world_t[p][i]+r[i];}}
}
uint32_t oa_character_bones(const oa_character *c,const oa_char_part *part,float *rows){
 uint32_t i;float root[4]={0,0,sinf(c->facing*.5f),cosf(c->facing*.5f)};
 for(i=0;i<part->palette_count;i++){const uint8_t *record=part->palette+i*OA_CHAR_PALETTE_BYTES;uint32_t joint;float iq[4],it[3],q[4],t[3],w[3],*row=rows+i*12,x,y,z,s;
  memcpy(&joint,record,4);memcpy(iq,record+4,16);memcpy(it,record+20,12);
  qmul(q,c->world_q[joint],iq);qrot(t,c->world_q[joint],it);t[0]+=c->world_t[joint][0];t[1]+=c->world_t[joint][1];t[2]+=c->world_t[joint][2];
  qmul(q,root,q);qrot(w,root,t);
  x=q[0];y=q[1];z=q[2];s=q[3];
  row[0]=1-2*(y*y+z*z);row[1]=2*(x*y-z*s);row[2]=2*(x*z+y*s);row[3]=w[0]+c->feet[0];
  row[4]=2*(x*y+z*s);row[5]=1-2*(x*x+z*z);row[6]=2*(y*z-x*s);row[7]=w[1]+c->feet[1];
  row[8]=2*(x*z-y*s);row[9]=2*(y*z+x*s);row[10]=1-2*(x*x+y*y);row[11]=w[2]+c->feet[2];}
 return part->palette_count;
}
