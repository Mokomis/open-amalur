/* Flood-fills walkable space with the real controller to test whether two spots connect.
 * Usage: reach_test collision.bin sx sy sz tx ty radius */
#include "opem_collision.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define MAX_NODES 400000
typedef struct node{opem_controller body;int key_x,key_y,key_z;}node;
static node *nodes;static int count;
static int *table;enum{TABLE=1<<21};
static unsigned hash(int x,int y,int z){return ((unsigned)x*73856093u^(unsigned)y*19349663u^(unsigned)z*83492791u)&(TABLE-1);}
static int visit(const opem_controller *b){
 int x=(int)floorf(b->feet[0]/50),y=(int)floorf(b->feet[1]/50),z=(int)floorf(b->feet[2]/60);unsigned h=hash(x,y,z);
 while(table[h]>=0){const node *n=nodes+table[h];if(n->key_x==x&&n->key_y==y&&n->key_z==z)return 0;h=(h+1)&(TABLE-1);}
 if(count>=MAX_NODES)return 0;table[h]=count;nodes[count].body=*b;nodes[count].key_x=x;nodes[count].key_y=y;nodes[count].key_z=z;count++;return 1;
}
int main(int argc,char **argv){
 FILE *f;long size;unsigned char *b;unsigned vertices;opem_collision_world *w=NULL;opem_controller_config config;opem_controller start;char error[256];float hint[3];int head=0,i;float best=1e30f,tx,ty,radius,best_z=0;
 if(argc!=8)return 2;f=fopen(argv[1],"rb");if(!f)return 2;fseek(f,0,SEEK_END);size=ftell(f);rewind(f);b=(unsigned char*)malloc((size_t)size);if(fread(b,1,(size_t)size,f)!=(size_t)size)return 2;fclose(f);
 memcpy(&vertices,b+8,4);{float *v=(float*)malloc((size_t)vertices*36);memcpy(v,b+36,(size_t)vertices*36);if(!opem_collision_create(&w,v,vertices,9,error,sizeof(error))){printf("collision: %s\n",error);return 3;}}
 opem_controller_config_default(&config);config.require_ceiling=0;hint[0]=(float)atof(argv[2]);hint[1]=(float)atof(argv[3]);hint[2]=(float)atof(argv[4]);tx=(float)atof(argv[5]);ty=(float)atof(argv[6]);radius=(float)atof(argv[7]);
 if(!opem_controller_spawn(w,&config,hint,&start,error,sizeof(error))){printf("spawn: %s\n",error);return 3;}
 nodes=(node*)malloc(sizeof(node)*MAX_NODES);table=(int*)malloc(sizeof(int)*TABLE);memset(table,-1,sizeof(int)*TABLE);visit(&start);
 printf("start (%.1f %.1f %.1f)\n",start.feet[0],start.feet[1],start.feet[2]);
 while(head<count){opem_controller from=nodes[head++].body;int dir;
  float d=hypotf(from.feet[0]-tx,from.feet[1]-ty);if(d<best){best=d;best_z=from.feet[2];}
  if(d<radius){printf("REACHED target after %d nodes at (%.1f %.1f %.1f)\n",head,from.feet[0],from.feet[1],from.feet[2]);return 0;}
  for(dir=0;dir<8;dir++){opem_controller next=from;float a=dir*.785398163f;int ok=1;
   for(i=0;i<20&&ok;i++)ok=opem_controller_step(w,&config,&next,cosf(a)*240,sinf(a)*240,1/60.f,error,sizeof(error));
   if(ok&&next.grounded)visit(&next);}}
 printf("NOT reached: explored %d nodes, closest %.1f units at z %.1f\n",count,best,best_z);
 return 1;
}
