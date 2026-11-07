#include "opem_collision.h"
#include "interaction_pick.h"
#include "amalur_scene_mesh.h"
#include "workbench_visual.inc"
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
static int load(const char *path,amalur_scene_mesh *m){FILE *f=fopen(path,"rb");long n;char *b,error[256];int okay;if(!f)return 0;fseek(f,0,SEEK_END);n=ftell(f);rewind(f);if(n<1||n>128*1024*1024){fclose(f);return 0;}b=(char*)malloc((size_t)n);if(!b){fclose(f);return 0;}if(fread(b,1,(size_t)n,f)!=(size_t)n){free(b);fclose(f);return 0;}fclose(f);okay=amalur_scene_mesh_parse(b,(size_t)n,m,error,sizeof(error));free(b);return okay;}
int main(int argc,char **argv){
 amalur_scene_mesh collision={0},visual={0};opem_collision_world *world=NULL;opem_controller_config config;opem_controller body={0};char error[256];float eye[3],direction[3],hit[3],distance=0,occlusion=0;int i,found=0;float chosen=0;
 if(argc!=3||!load(argv[1],&collision)||!load(argv[2],&visual))return 2;
 if(!opem_collision_create(&world,collision.vertices,collision.vertex_count,9,error,sizeof(error)))return 3;opem_controller_config_default(&config);config.require_ceiling=0;
 if(!opem_controller_spawn(world,&config,oa_workbench_spawn_hint,&body,error,sizeof(error))||!opem_controller_clear(world,&config,body.feet,error,sizeof(error))){fprintf(stderr,"%s\n",error);return 4;}
 for(i=0;i<3;i++)eye[i]=body.feet[i];eye[2]+=config.height*.9f;
 for(i=0;i<9;i++){float pitch=(i-4)*.1f;direction[0]=0;direction[1]=cosf(pitch);direction[2]=sinf(pitch);if(oa_mesh_pick(visual.vertices,visual.vertex_count,OA_WORKBENCH_FIRST_VERTEX,OA_WORKBENCH_VERTEX_COUNT,eye,direction,300,hit,&distance)&&opem_collision_ray(world,eye,direction,300,&occlusion)&&occlusion+.5f>=distance){found=1;chosen=pitch;if(i==4)break;}}
 printf("{\"spawn\":[%.6f,%.6f,%.6f],\"capsule_clear\":true,\"visible_table_hit\":%s,\"hit_distance\":%.6f,\"occlusion_distance\":%.6f,\"tested_pitch\":%.5f}\n",body.feet[0],body.feet[1],body.feet[2],found?"true":"false",distance,occlusion,chosen);
 opem_collision_destroy(world);amalur_scene_mesh_clear(&collision);amalur_scene_mesh_clear(&visual);return found?0:5;
}
