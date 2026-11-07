#include "oa_canopy.h"
#include <stdlib.h>
#include <string.h>
#include <math.h>

typedef struct canopy_portal{uint32_t a,b,id;float center[3],normal[3],right[3],up[3];}canopy_portal;
struct oa_canopy{uint32_t nodes,portals,hops,initial,current;uint32_t *ids;unsigned char *distance;canopy_portal *edges;float feet[3];int have_feet;};
static uint32_t get_u32(const unsigned char *p){uint32_t n;memcpy(&n,p,4);return n;}
static int node(const oa_canopy *c,uint32_t id){unsigned i;for(i=0;i<c->nodes;i++)if(c->ids[i]==id)return (int)i;return -1;}
static float dot3(const float a[3],const float b[3]){return a[0]*b[0]+a[1]*b[1]+a[2]*b[2];}
static void rebuild(oa_canopy *c){unsigned hop,i;int start=node(c,c->current);memset(c->distance,255,c->nodes);if(start<0)return;c->distance[start]=0;
 /* Native fdcf20/fef1c0 traverse undirected portal endpoints with a remaining-hop budget. */
 for(hop=0;hop<c->hops;hop++)for(i=0;i<c->portals;i++){int a=node(c,c->edges[i].a),b=node(c,c->edges[i].b);if(c->distance[a]==hop&&c->distance[b]>hop+1)c->distance[b]=(unsigned char)(hop+1);if(c->distance[b]==hop&&c->distance[a]>hop+1)c->distance[a]=(unsigned char)(hop+1);}}
oa_canopy *oa_canopy_open(const void *data,size_t size){const unsigned char *p=(const unsigned char*)data;oa_canopy *c;uint32_t n,e,h,initial,i,j;size_t at;
 if(!p||size<32||memcmp(p,"OACAN01",8))return NULL;n=get_u32(p+8);e=get_u32(p+12);initial=get_u32(p+16);h=get_u32(p+20);
 if(!n||n>256||e>1024||h>16||get_u32(p+28)||size!=32+(size_t)n*4+(size_t)e*60)return NULL;
 c=(oa_canopy*)calloc(1,sizeof(*c));if(!c)return NULL;c->nodes=n;c->portals=e;c->hops=h;c->initial=initial;c->ids=(uint32_t*)malloc(n*4);c->distance=(unsigned char*)malloc(n);c->edges=(canopy_portal*)calloc(e?e:1,sizeof(canopy_portal));
 if(!c->ids||!c->distance||!c->edges){oa_canopy_close(c);return NULL;}
 for(i=0;i<n;i++){c->ids[i]=get_u32(p+32+i*4);if(!c->ids[i]||(i&&c->ids[i]<=c->ids[i-1])){oa_canopy_close(c);return NULL;}}
 at=32+(size_t)n*4;
 for(i=0;i<e;i++){canopy_portal *q=c->edges+i;const unsigned char *r=p+at+i*60;q->a=get_u32(r);q->b=get_u32(r+4);q->id=get_u32(r+8);memcpy(q->center,r+12,12);memcpy(q->normal,r+24,12);memcpy(q->right,r+36,12);memcpy(q->up,r+48,12);
  if(q->a==q->b||node(c,q->a)<0||node(c,q->b)<0){oa_canopy_close(c);return NULL;}
  for(j=0;j<12;j++){float v;memcpy(&v,r+12+j*4,4);if(!isfinite(v)){oa_canopy_close(c);return NULL;}}
  if(dot3(q->normal,q->normal)<.99f||dot3(q->normal,q->normal)>1.01f||dot3(q->right,q->right)<1||dot3(q->up,q->up)<1){oa_canopy_close(c);return NULL;}}
 if(!oa_canopy_set_space(c,initial)){oa_canopy_close(c);return NULL;}return c;}
void oa_canopy_close(oa_canopy *c){if(c){free(c->ids);free(c->distance);free(c->edges);free(c);}}
int oa_canopy_set_space(oa_canopy *c,uint32_t id){if(!c)return 0;if(!id)id=c->initial;if(node(c,id)<0)return 0;c->current=id;c->have_feet=0;rebuild(c);return 1;}
void oa_canopy_restore(oa_canopy *c,uint32_t id){if(!c)return;if(id&&oa_canopy_set_space(c,id))return;c->current=0;c->have_feet=0;rebuild(c);}
uint32_t oa_canopy_space(const oa_canopy *c){return c?c->current:0;}
uint32_t oa_canopy_initial(const oa_canopy *c){return c?c->initial:0;}
unsigned oa_canopy_admitted(const oa_canopy *c){unsigned i,n=0;if(c)for(i=0;i<c->nodes;i++)if(c->distance[i]<=c->hops)n++;return n;}
int oa_canopy_admits(const oa_canopy *c,uint32_t id){int i;if(!c||!c->current||!id)return 1;i=node(c,id);return i>=0&&c->distance[i]<=c->hops;}
void oa_canopy_move(oa_canopy *c,const float feet[3]){unsigned step;float from[3],to[3];if(!c||!feet)return;for(step=0;step<3;step++)if(!isfinite(feet[step]))return;
 if(!c->have_feet){memcpy(c->feet,feet,12);c->have_feet=1;return;}memcpy(from,c->feet,12);memcpy(to,feet,12);memcpy(c->feet,feet,12);
 /* Custom controller policy: cross the authored finite portal rectangle. Native
  * camera identity propagation and graph admission are proven separately;
  * this crossing policy is not claimed as a recovered actor implementation. */
 for(step=0;step<16;step++){unsigned i;float best=2;const canopy_portal *hit=NULL;float hitpoint[3]={0};
  for(i=0;i<c->portals;i++){const canopy_portal *p=c->edges+i;float a[3],b[3],d0,d1,t,v[3],r2,u2;unsigned j;if(c->current&&c->current!=p->a&&c->current!=p->b)continue;
   for(j=0;j<3;j++){a[j]=from[j]-p->center[j];b[j]=to[j]-p->center[j];}d0=dot3(a,p->normal);d1=dot3(b,p->normal);
   if(!c->current){if(!((d0>=0&&d1<0)||(d0<=0&&d1>0)))continue;}else if(c->current==p->a){if(!(d0>=0&&d1<0))continue;}else if(!(d0<=0&&d1>0))continue;t=d0/(d0-d1);if(t>=best)continue;
   for(j=0;j<3;j++)v[j]=a[j]+t*(b[j]-a[j]);r2=dot3(p->right,p->right);u2=dot3(p->up,p->up);
   if(fabsf(dot3(v,p->right))>r2||fabsf(dot3(v,p->up))>u2)continue;best=t;hit=p;for(j=0;j<3;j++)hitpoint[j]=p->center[j]+v[j];}
  if(!hit)break;if(!c->current){float relative[3];unsigned j;for(j=0;j<3;j++)relative[j]=to[j]-hit->center[j];c->current=dot3(relative,hit->normal)>0?hit->a:hit->b;}else c->current=c->current==hit->a?hit->b:hit->a;rebuild(c);memcpy(from,hitpoint,12);}
}
