#include "opem_collision.h"
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <math.h>
#include <string.h>
static opem_collision_world *load(const char*path){FILE*f=fopen(path,"rb");uint32_t n;float*p;char e[256]="";opem_collision_world*w=NULL;if(!f||fread(&n,4,1,f)!=1||n>300000)return NULL;p=(float*)malloc((size_t)n*36);if(!p||fread(p,36,n,f)!=n)return NULL;fclose(f);int ok=opem_collision_create(&w,p,n*3,3,e,sizeof(e));free(p);if(!ok)printf("create error %s\n",e);return w;}
int main(int argc,char**argv){
 if(argc!=3)return 1;opem_collision_world*old=load(argv[1]),*after=load(argv[2]);if(!old||!after)return 2;
 opem_controller_config config;opem_controller_config_default(&config);config.require_ceiling=0;config.max_speed=240;
 const float tx=6446.515625f,ty=-85881.1875f;const float offsets[]={150,200,250,300,350,400,450,500,600,700};int pass=0;
 for(int k=0;k<10&&!pass;k++){
  char e[256]="";float hint[3]={tx+offsets[k],ty,5857.75f};opem_controller before,now;
  /* Use an observed ray-hit floor in the real terrain, avoiding spawn-policy
     candidate selection that relocated the previous comparison. */
  float eye[3]={hint[0],hint[1],hint[2]+600},down[3]={0,0,-1},distance=1200;
  if(!opem_collision_ray(old,eye,down,1200,&distance)||distance>=1200)continue;
  memset(&before,0,sizeof(before));before.feet[0]=hint[0];before.feet[1]=hint[1];before.feet[2]=eye[2]-distance+.25f;
  before.valid=1;before.grounded=1;memcpy(before.last_safe_feet,before.feet,sizeof(before.feet));
  if(!opem_controller_clear(old,&config,before.feet,e,sizeof(e))||!opem_controller_clear(after,&config,before.feet,e,sizeof(e)))continue;
  now=before;float dx=tx-before.feet[0],dy=ty-before.feet[1],dist=sqrtf(dx*dx+dy*dy);if(dist<180)continue;
  float vx=dx/dist*240,vy=dy/dist*240;int frames=(int)ceilf((dist+150)/240*120);unsigned oldcontacts=0,newcontacts=0;int ok=1;
  printf("SHARED START %.5f %.5f %.5f frames=%d\n",before.feet[0],before.feet[1],before.feet[2],frames);
  for(int i=0;i<frames;i++){
   if(!opem_controller_step(old,&config,&before,vx,vy,1.0f/120,e,sizeof(e))||!opem_controller_step(after,&config,&now,vx,vy,1.0f/120,e,sizeof(e))){ok=0;printf("step failed %s\n",e);break;}
   oldcontacts+=before.contacts_last_step;newcontacts+=now.contacts_last_step;
  }
  float oldleft=(before.feet[0]-tx)*(-dx/dist)+(before.feet[1]-ty)*(-dy/dist);
  float newleft=(now.feet[0]-tx)*(-dx/dist)+(now.feet[1]-ty)*(-dy/dist);
  printf("BEFORE %.5f %.5f %.5f remaining=%.3f grounded=%d valid=%d contacts=%u\n",before.feet[0],before.feet[1],before.feet[2],oldleft,before.grounded,before.valid,oldcontacts);
  printf("AFTER %.5f %.5f %.5f remaining=%.3f grounded=%d valid=%d contacts=%u\n",now.feet[0],now.feet[1],now.feet[2],newleft,now.grounded,now.valid,newcontacts);
  pass=ok&&oldleft< -70&&newleft>50&&now.valid&&now.grounded;
 }
 opem_collision_destroy(old);opem_collision_destroy(after);printf("same-start blocking comparison: %s\n",pass?"PASS":"UNRESOLVED");return pass?0:3;
}
