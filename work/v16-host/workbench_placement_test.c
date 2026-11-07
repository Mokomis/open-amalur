#include "opem_collision.h"
#include "interaction_state.h"
#include "amalur_scene_mesh.h"
#include "workbench_placement.inc"
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
int main(int argc,char **argv){
 FILE *f;long length;char *bytes;char error[256];amalur_scene_mesh mesh={0};opem_collision_world *w=NULL;opem_controller_config c;opem_controller body={0};oa_registry registry;oa_handle h;float hint[3]={oa_workbench_position[0],oa_workbench_position[1]-240,oa_workbench_position[2]};double distance;
 if(argc<2)return 2;f=fopen(argv[1],"rb");if(!f)return 2;fseek(f,0,SEEK_END);length=ftell(f);rewind(f);if(length<1||length>256*1024*1024){fclose(f);return 2;}bytes=(char*)malloc((size_t)length);if(!bytes){fclose(f);return 2;}if(fread(bytes,1,(size_t)length,f)!=(size_t)length){free(bytes);fclose(f);return 2;}fclose(f);
 if(!amalur_scene_mesh_parse(bytes,(size_t)length,&mesh,error,sizeof(error))){fprintf(stderr,"%s\n",error);free(bytes);return 3;}free(bytes);if(!opem_collision_create(&w,mesh.vertices,mesh.vertex_count,9,error,sizeof(error)))return 3;amalur_scene_mesh_clear(&mesh);opem_controller_config_default(&c);if(argc>2)c.require_ceiling=0;
 if(!opem_controller_spawn(w,&c,hint,&body,error,sizeof(error))){fprintf(stderr,"spawn: %s\n",error);return 4;}
 oa_registry_init(&registry);h=oa_object_create(&registry,OA_WORKBENCH_SOURCE,OA_WORKBENCH_TYPE,OA_WORKBENCH_SCRIPT,oa_workbench_position);distance=hypot(body.feet[0]-oa_workbench_position[0],body.feet[1]-oa_workbench_position[1]);
 printf("{\"spawn\":[%.6f,%.6f,%.6f],\"workbench_distance\":%.6f,\"in_reach\":%s,\"capsule_clear\":%s}\n",body.feet[0],body.feet[1],body.feet[2],distance,oa_workbench_in_reach(&registry,h,body.feet,1.5707963f)?"true":"false",opem_controller_clear(w,&c,body.feet,error,sizeof(error))?"true":"false");opem_collision_destroy(w);return distance<=300?0:5;
}
