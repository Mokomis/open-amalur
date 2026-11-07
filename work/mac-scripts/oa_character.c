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
int oa_character_parse(oa_character *c,uint8_t *bytes,size_t size,char *error,size_t error_size){
 size_t at=8;uint32_t i,head[4];memset(c,0,sizeof(*c));
 if(size<24||memcmp(bytes,"OACHAR01",8))return fail(error,error_size,"character asset header invalid");
 memcpy(head,bytes+at,16);at+=16;c->joints=head[0];c->clip_count=head[1];c->part_count=head[2];c->texture_count=head[3];
 if(!c->joints||c->joints>OA_CHAR_MAX_JOINTS||c->joints%2||!c->clip_count||c->clip_count>OA_CHAR_MAX_CLIPS||!c->part_count||c->part_count>OA_CHAR_MAX_PARTS||c->texture_count>OA_CHAR_MAX_TEXTURES)return fail(error,error_size,"character asset counts invalid");
 NEED(c->joints*2u);memcpy(c->parents,bytes+at,c->joints*2u);at+=c->joints*2u;
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
 c->bytes=bytes;c->size=size;c->weight[OA_CLIP_IDLE]=1;c->ready=1;oa_character_pose(c);return 1;
}
void oa_character_free(oa_character *c){free(c->bytes);memset(c,0,sizeof(*c));}
void oa_character_animate(oa_character *c,float speed,float velocity_units,float dt){
 /* Authored thresholds and playback rates chosen to limit visible foot sliding. */
 uint32_t i;float rate[3]={1.0f,velocity_units/150.0f,velocity_units/420.0f},target[3]={0,0,0},fade=dt*8.0f,sum=0;
 int wanted=speed<.05f?OA_CLIP_IDLE:speed<.45f?OA_CLIP_WALK:OA_CLIP_RUN;
 if(!c->ready||c->clip_count<3)return;
 if(rate[1]<.5f)rate[1]=.5f;if(rate[2]<.5f)rate[2]=.5f;
 target[wanted]=1;if(fade>1)fade=1;
 for(i=0;i<3;i++){const oa_char_clip *k=c->clips+i;float period=(float)(k->frames-1)/k->fps;
  c->weight[i]+=(target[i]-c->weight[i])*fade;sum+=c->weight[i];
  c->time[i]=fmodf(c->time[i]+dt*rate[i],period);}
 if(sum>0)for(i=0;i<3;i++)c->weight[i]/=sum;
}
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
