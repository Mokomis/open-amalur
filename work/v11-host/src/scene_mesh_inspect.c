#include "amalur_scene_mesh.h"
#include <stdio.h>
#include <stdlib.h>
int main(int argc,char **argv){
    FILE *file;long length;unsigned char *bytes;char error[256];amalur_scene_mesh mesh={0};int okay;
    if(argc!=2){fprintf(stderr,"Usage: amalur-scene-mesh-inspect SCENE.bin\n");return 2;}
    file=fopen(argv[1],"rb");if(!file){fprintf(stderr,"Cannot open scene\n");return 1;}
    if(fseek(file,0,SEEK_END)||(length=ftell(file))<36||(uint64_t)length>AMALUR_SCENE_MAX_BYTES||fseek(file,0,SEEK_SET)){
        fprintf(stderr,"Invalid or unreadable scene length\n");fclose(file);return 1;}
    bytes=(unsigned char*)malloc((size_t)length);if(!bytes){fclose(file);return 1;}
    if(fread(bytes,1,(size_t)length,file)!=(size_t)length||fgetc(file)!=EOF||ferror(file)){free(bytes);fclose(file);return 1;}
    fclose(file);okay=amalur_scene_mesh_parse(bytes,(size_t)length,&mesh,error,sizeof(error));free(bytes);
    if(!okay){fprintf(stderr,"Scene validation failed:%s\n",error);return 1;}
    printf("{\"ok\":true,\"format\":\"authored-OMSC07\",\"vertices\":%u,\"triangles\":%u,\"bounds_min\":[%.9g,%.9g,%.9g],\"bounds_max\":[%.9g,%.9g,%.9g],\"device_rendering_verified\":false}\n",
        mesh.vertex_count,mesh.vertex_count/3,mesh.bounds_min[0],mesh.bounds_min[1],mesh.bounds_min[2],mesh.bounds_max[0],mesh.bounds_max[1],mesh.bounds_max[2]);
    amalur_scene_mesh_clear(&mesh);return 0;
}
