#include "opem_collision.h"
#include "amalur_scene_mesh.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
int main(int argc,char **argv){
    FILE *f;long size;void *bytes;amalur_scene_mesh mesh={0};opem_collision_world *world=NULL;opem_controller_config config;opem_controller spawn,again,p;opem_collision_stats stats;
    char error[256];float hint[3]={-350,380,0};int direction,frame,failed=0,total_recoveries=0;clock_t start;double seconds,best=0;unsigned long long queries=0,contacts=0,edge_blocks=0;
    if(argc!=2){fprintf(stderr,"usage: walk_scene.exe scene.bin\n");return 2;}f=fopen(argv[1],"rb");if(!f)return 3;
    if(fseek(f,0,SEEK_END)||((size=ftell(f))<=0)||(unsigned long)size>AMALUR_SCENE_MAX_BYTES||fseek(f,0,SEEK_SET)){fclose(f);return 3;}
    bytes=malloc((size_t)size);if(!bytes){fclose(f);return 3;}if(fread(bytes,1,(size_t)size,f)!=(size_t)size){free(bytes);fclose(f);return 3;}fclose(f);
    if(!amalur_scene_mesh_parse(bytes,(size_t)size,&mesh,error,sizeof(error))){fprintf(stderr,"mesh: %s\n",error);free(bytes);return 4;}free(bytes);start=clock();
    if(!opem_collision_create(&world,mesh.vertices,mesh.vertex_count,9,error,sizeof(error))){fprintf(stderr,"collision: %s\n",error);amalur_scene_mesh_clear(&mesh);return 5;}
    seconds=(double)(clock()-start)/CLOCKS_PER_SEC;amalur_scene_mesh_clear(&mesh);opem_collision_get_stats(world,&stats);opem_controller_config_default(&config);memset(&spawn,0,sizeof(spawn));
    if(!opem_controller_spawn(world,&config,hint,&spawn,error,sizeof(error))){fprintf(stderr,"spawn: %s\n",error);opem_collision_destroy(world);return 6;}
    memset(&again,0,sizeof(again));if(!opem_controller_spawn(world,&config,hint,&again,error,sizeof(error))||memcmp(&spawn,&again,sizeof(spawn))){fprintf(stderr,"spawn nondeterministic\n");opem_collision_destroy(world);return 7;}
    printf("{\"scope\":\"authored approximate render-mesh collision; not native physics\",\"triangles\":%u,\"nodes\":%u,\"degenerate\":%u,\"allocated_bytes\":%llu,\"build_seconds\":%.6f,\"spawn\":[%.6f,%.6f,%.6f],\"spawn_deterministic\":true,\"trials\":[",stats.triangles,stats.nodes,stats.degenerate_triangles,(unsigned long long)stats.allocated_bytes,seconds,spawn.feet[0],spawn.feet[1],spawn.feet[2]);
    for(direction=0;direction<8;direction++){
        double angle=direction*3.14159265358979323846/4,travel=0;int recoveries=0;float vx=(float)(cos(angle)*config.max_speed),vy=(float)(sin(angle)*config.max_speed);p=spawn;
        printf("%s{\"heading\":%d,\"samples\":[",direction?",":"",direction);for(frame=0;frame<360;frame++){
            float old[3];memcpy(old,p.feet,sizeof(old));if(!opem_controller_step(world,&config,&p,vx,vy,1.f/60,error,sizeof(error))){fprintf(stderr,"trial%d frame%d: %s\n",direction,frame,error);failed=1;break;}
            queries+=p.queries_last_step;contacts+=p.contacts_last_step;edge_blocks+=p.edge_blocks_last_step;if(p.recovered_last_step)recoveries++;else travel+=sqrt((p.feet[0]-old[0])*(p.feet[0]-old[0])+(p.feet[1]-old[1])*(p.feet[1]-old[1]));
            if(frame%60==0)printf("%s[%.5f,%.5f,%.5f]",frame?",":"",p.feet[0],p.feet[1],p.feet[2]);
            if(!opem_controller_clear(world,&config,p.feet,error,sizeof(error))){fprintf(stderr,"clearance: %s\n",error);failed=1;break;}
        }
        if(travel>best)best=travel;total_recoveries+=recoveries;
        printf("],\"frames\":%d,\"travel\":%.6f,\"recoveries\":%d,\"end\":[%.6f,%.6f,%.6f]}",frame,travel,recoveries,p.feet[0],p.feet[1],p.feet[2]);
    }
    printf("],\"queries\":%llu,\"contacts\":%llu,\"edge_blocks\":%llu,\"best_travel\":%.6f,\"recoveries\":%d,\"failures\":%d}\n",queries,contacts,edge_blocks,best,total_recoveries,failed);opem_collision_destroy(world);return failed?8:best<100?9:0;
}
