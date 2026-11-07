#include "oa_appearance.h"
#include <string.h>
#include <math.h>
#include <limits.h>
static uint32_t u32(const void*p){uint32_t v;memcpy(&v,p,4);return v;}
static int32_t i32(const void*p){int32_t v;memcpy(&v,p,4);return v;}
static float f32(const void*p){float v;memcpy(&v,p,4);return v;}
static int span(size_t n,uint32_t off,uint32_t count,uint32_t stride){return stride&&off<=n&&count<=(n-off)/stride;}
int oa_am_find(const oa_am_model*m,const char tag[4],oa_am_chunk*c){
 uint32_t i;if(!m||!c)return 0;
 for(i=0;i<m->chunks;i++){const unsigned char*d=m->bytes+m->dir+16*i;
  if(!memcmp(d,tag,4)){c->data=m->bytes+u32(d+4);c->count=u32(d+8);c->stride=u32(d+12);return 1;}}
 return 0;
}
static int get(const oa_am_model*m,const char*t,uint32_t stride,oa_am_chunk*c){return oa_am_find(m,t,c)&&c->stride==stride;}
int oa_am_open(oa_am_model*m,const void*p,size_t n){
 uint32_t i,j;oa_am_chunk b,a,v,ib,rv,cv,ix,r;oa_am_model q;
 if(!m||!p||n<32||memcmp(p,"OAAM001\0",8))return 0;
 memset(m,0,sizeof(*m));q.bytes=(const unsigned char*)p;q.size=n;
 if(u32(q.bytes+8)!=1||u32(q.bytes+16)!=n||n>UINT32_MAX)return 0;
 q.fab=u32(q.bytes+12);q.chunks=u32(q.bytes+20);q.dir=u32(q.bytes+24);
 if(q.chunks>64||!span(n,q.dir,q.chunks,16))return 0;
 for(i=0;i<q.chunks;i++){const unsigned char*d=q.bytes+q.dir+i*16;
  if(!span(n,u32(d+4),u32(d+8),u32(d+12)))return 0;
  for(j=0;j<i;j++)if(!memcmp(d,q.bytes+q.dir+j*16,4))return 0;
 }
 if(!get(&q,"BONE",64,&b)||!get(&q,"ASMB",128,&a)||!get(&q,"VBUF",32,&v)||
 !get(&q,"IBUF",16,&ib)||!get(&q,"RAWV",1,&rv)||!get(&q,"VERT",96,&cv)||
 !get(&q,"INDX",4,&ix)||!get(&q,"RMAP",52,&r))return 0;
 for(i=0;i<b.count;i++){int32_t pidx=i32(b.data+i*64);if(pidx< -1||(pidx>=0&&(uint32_t)pidx>=b.count))return 0;}
 for(i=0;i<v.count;i++){const unsigned char*d=v.data+i*32;uint32_t cnt=u32(d+12),sz=u32(d+20);
  if(!span(rv.count,u32(d),cnt,u32(d+8))||u32(d+4)!=(uint64_t)cnt*u32(d+8))return 0;
  if(sz&&(sz!=(uint64_t)cnt*96||!span((size_t)cv.count*96,u32(d+16),cnt,96)))return 0;
 }
 for(i=0;i<ib.count;i++){const unsigned char*d=ib.data+i*16;if(!span((size_t)ix.count*4,u32(d),u32(d+4),4))return 0;}
 for(i=0;i<a.count;i++){const unsigned char*d=a.data+i*128,*vd,*id;uint32_t k,vc;
  if(u32(d)>=v.count||u32(d+4)>=ib.count||u32(d+16)>r.count||u32(d+20)>r.count-u32(d+16))return 0;
  if(i32(d+12)<-1||(i32(d+12)>=0&&(uint32_t)i32(d+12)>=b.count))return 0;
  vd=v.data+u32(d)*32;id=ib.data+u32(d+4)*16;vc=u32(vd+12);
  for(k=0;k<u32(id+4);k++)if(u32(ix.data+u32(id)+k*4)>=vc)return 0;
  for(k=0;k<u32(d+20);k++){int32_t bi=i32(r.data+(u32(d+16)+k)*52+48);if(bi<0||(uint32_t)bi>=b.count)return 0;}
 }
 *m=q;return 1;
}
uint32_t oa_am_surface_count(const oa_am_model*m){oa_am_chunk c;return get(m,"ASMB",128,&c)?c.count:0;}
int oa_am_surface_get(const oa_am_model*m,uint32_t ai,oa_am_surface*out){
 oa_am_chunk a,v,ib,cv,ix,r;const unsigned char*d,*vd,*id;
 if(!m||!out||!get(m,"ASMB",128,&a)||ai>=a.count)return 0;
 get(m,"VBUF",32,&v);get(m,"IBUF",16,&ib);get(m,"VERT",96,&cv);get(m,"INDX",4,&ix);get(m,"RMAP",52,&r);
 d=a.data+ai*128;vd=v.data+u32(d)*32;id=ib.data+u32(d+4)*16;
 if(!u32(vd+20))return 0;memset(out,0,sizeof(*out));
 out->vertices96=cv.data+u32(vd+16);out->indices=(const uint32_t*)(ix.data+u32(id));
 out->vertex_count=u32(vd+12);out->index_count=u32(id+4);out->material_id=u32(d+8);
 out->assembly=ai;out->group_mask=u32(d+24);out->weighted=u32(d+28);out->rigid_bone=i32(d+12);
 out->palette_count=u32(d+20)?u32(d+20):1;out->remaps52=r.data+u32(d+16)*52;
 out->source_vb=u32(d);out->source_ib=u32(d+4);return 1;
}
static void ident(float*m){uint32_t i;for(i=0;i<12;i++)m[i]=(i==0||i==5||i==10)?1.f:0.f;}
static void mul(const float*a,const float*b,float*out){float t[12];int r,c,k;
 for(r=0;r<3;r++){for(c=0;c<3;c++){t[r*4+c]=0;for(k=0;k<3;k++)t[r*4+c]+=a[r*4+k]*b[k*4+c];}
 t[r*4+3]=a[r*4+3];for(k=0;k<3;k++)t[r*4+3]+=a[r*4+k]*b[k*4+3];}
 memcpy(out,t,sizeof(t));
}
void oa_am_source_tqs_matrix(const float q[4],const float t[3],const float s[3],float*m){
 float x=-q[0],y=-q[1],z=-q[2],w=q[3];
 m[0]=(1-2*(y*y+z*z))*s[0];m[1]=2*(x*y-z*w)*s[1];m[2]=2*(x*z+y*w)*s[2];m[3]=t[0];
 m[4]=2*(x*y+z*w)*s[0];m[5]=(1-2*(x*x+z*z))*s[1];m[6]=2*(y*z-x*w)*s[2];m[7]=t[1];
 m[8]=2*(x*z-y*w)*s[0];m[9]=2*(y*z+x*w)*s[1];m[10]=(1-2*(x*x+y*y))*s[2];m[11]=t[2];
}
static void rawmat(const unsigned char*b,int runtime,float*m){float q[4],t[3],s[3];int i;
 for(i=0;i<4;i++)q[i]=f32(b+(runtime?16:0)+i*4);
 for(i=0;i<3;i++){t[i]=f32(b+(runtime?0:16)+i*4);s[i]=f32(b+32+i*4);}
 oa_am_source_tqs_matrix(q,t,s,m);
}
int oa_am_rest_world(const oa_am_model*m,float*out,size_t cap){
 oa_am_chunk b;uint32_t i,j,pass,done=0;unsigned char ready[8192];float local[12];
 if(!get(m,"BONE",64,&b)||b.count>8192||cap<(size_t)b.count*12||!out)return 0;
 memset(ready,0,b.count);
 for(pass=0;pass<=b.count&&done<b.count;pass++)for(i=0;i<b.count;i++)if(!ready[i]){
  int32_t p=i32(b.data+i*64);if(p==(int32_t)i)p=-1;
  if(p<0||ready[p]){rawmat(b.data+i*64+8,0,local);
   if(p<0)memcpy(out+i*12,local,48);else mul(out+p*12,local,out+i*12);ready[i]=1;done++;}}
 for(j=0;j<b.count*12;j++)if(!isfinite(out[j]))return 0;return done==b.count;
}
int oa_am_palette(const oa_am_model*m,uint32_t ai,const float*bones,uint32_t n,const float*root,float*out,size_t cap){
 oa_am_surface s;uint32_t i;float ent[12],off[12],mat[12];
 if(!oa_am_surface_get(m,ai,&s)||!bones||!out||cap<(size_t)s.palette_count*12)return 0;
 if(root)memcpy(ent,root,48);else ident(ent);
 if(s.weighted){if(!s.palette_count)return 0;
  for(i=0;i<s.palette_count;i++){const unsigned char*r=s.remaps52+i*52;int32_t bi=i32(r+48);
   if(bi<0||(uint32_t)bi>=n)return 0;rawmat(r,1,off);mul(bones+bi*12,off,mat);mul(ent,mat,out+i*12);}
 }else{if(s.rigid_bone<0||(uint32_t)s.rigid_bone>=n)return 0;mul(ent,bones+s.rigid_bone*12,out);}
 return 1;
}

uint32_t oa_am_child_map_count(const oa_am_model*m){oa_am_chunk c;return get(m,"CMAP",32,&c)?c.count:0;}
int oa_am_child_map_get(const oa_am_model*m,uint32_t i,oa_am_child_map*out){
 oa_am_chunk c,p;const unsigned char*d;uint32_t first,n;
 if(!out||!get(m,"CMAP",32,&c)||!get(m,"CPAI",12,&p)||i>=c.count)return 0;
 d=c.data+i*32;first=u32(d);n=u32(d+4);if(first>p.count||n>p.count-first)return 0;
 out->pairs12=p.data+first*12;out->count=n;out->mount_key=u32(d+8);out->slot_key=u32(d+12);out->flags=u32(d+16);return 1;
}
int oa_am_local_pose(const oa_am_model*m,const float*local,uint32_t n,float*out,size_t cap){
 oa_am_chunk b;uint32_t i,pass,done=0;unsigned char ready[8192];float lm[12];
 if(!get(m,"BONE",64,&b)||b.count>8192||n!=b.count||cap<(size_t)b.count*12||!out||!local)return 0;
 memset(ready,0,b.count);
 for(pass=0;pass<=b.count&&done<b.count;pass++)for(i=0;i<b.count;i++)if(!ready[i]){
  int32_t p=i32(b.data+i*64);if(p==(int32_t)i)p=-1;
  if(p<0||ready[p]){oa_am_source_tqs_matrix(local+i*12,local+i*12+4,local+i*12+8,lm);
   if(p<0)memcpy(out+i*12,lm,48);else mul(out+p*12,lm,out+i*12);ready[i]=1;done++;}}
 return done==b.count;
}
int oa_am_child_pose(const oa_am_model*parent,uint32_t mi,const float*pw,uint32_t pn,
 const oa_am_model*child,float*cw,size_t cap){
 oa_am_child_map map;oa_am_chunk b;uint32_t i,pass,done=0;unsigned char ready[8192];float lm[12];
 if(!pw||!cw||!oa_am_child_map_get(parent,mi,&map)||!get(child,"BONE",64,&b)||
 b.count>8192||cap<(size_t)b.count*12)return 0;
 if(!oa_am_rest_world(child,cw,cap))return 0;memset(ready,0,b.count);
 for(i=0;i<map.count;i++){int32_t pi=i32(map.pairs12+i*12),ci=i32(map.pairs12+i*12+4);
  if(pi<0||(uint32_t)pi>=pn||ci<0||(uint32_t)ci>=b.count||ready[ci])return 0;
  memcpy(cw+ci*12,pw+pi*12,48);ready[ci]=1;done++;
 }
 for(pass=0;pass<=b.count&&done<b.count;pass++)for(i=0;i<b.count;i++)if(!ready[i]){
  int32_t p=i32(b.data+i*64);if(p==(int32_t)i)p=-1;
  if(p<0||ready[p]){rawmat(b.data+i*64+8,0,lm);
   if(p<0)memcpy(cw+i*12,lm,48);else mul(cw+p*12,lm,cw+i*12);ready[i]=1;done++;}}
 return done==b.count;
}
