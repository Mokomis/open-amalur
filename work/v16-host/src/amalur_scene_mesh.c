#include "amalur_scene_mesh.h"
#include <stdlib.h>
#include <string.h>
#include <float.h>
#include <math.h>

static void message(char *dst,size_t cap,const char *s){size_t n;if(!dst||!cap)return;n=strlen(s);if(n>=cap)n=cap-1;memcpy(dst,s,n);dst[n]=0;}
static uint32_t word(const unsigned char *p){return (uint32_t)p[0]|((uint32_t)p[1]<<8)|((uint32_t)p[2]<<16)|((uint32_t)p[3]<<24);}
static float number(const unsigned char *p){uint32_t u=word(p);float f;memcpy(&f,&u,4);return f;}
static int finite_float(float f){return f==f && f<=FLT_MAX && f>=-FLT_MAX;}
void amalur_scene_mesh_clear(amalur_scene_mesh *mesh){if(mesh){free(mesh->vertices);memset(mesh,0,sizeof(*mesh));}}
int amalur_scene_mesh_parse(const void *input,size_t length,amalur_scene_mesh *mesh,char *error,size_t cap){
    const unsigned char *bytes=(const unsigned char*)input;amalur_scene_mesh result={0};
    uint32_t count,i;size_t n;int axis;double diagonal2=0;
    message(error,cap,"");
    if(!mesh){message(error,cap,"scene output is required");return 0;}
    /* The output must be empty; preserve an already-owned result on rejection. */
    if(mesh->vertices){message(error,cap,"scene output already owns a mesh");return 0;}
    if(!bytes || length<36){message(error,cap,"truncated scene header");return 0;}
    if(length>AMALUR_SCENE_MAX_BYTES){message(error,cap,"scene exceeds256MiB admission limit");return 0;}
    if(memcmp(bytes,"OMSC07\0\0",8)){message(error,cap,"unsupported scene interchange magic");return 0;}
    if(sizeof(float)!=4 || FLT_RADIX!=2 || FLT_MANT_DIG!=24){message(error,cap,"IEEE754 binary32 host required");return 0;}
    count=word(bytes+8);
    if(!count || count%3){message(error,cap,"scene requires a nonempty triangle list");return 0;}
    if(36u+(uint64_t)count*36u!=(uint64_t)length){message(error,cap,"scene length differs from vertex count");return 0;}
    for(axis=0;axis<3;axis++){
        double width;
        result.bounds_min[axis]=number(bytes+12+axis*4);result.bounds_max[axis]=number(bytes+24+axis*4);
        if(!finite_float(result.bounds_min[axis]) || !finite_float(result.bounds_max[axis]) || result.bounds_min[axis]>result.bounds_max[axis]){
            message(error,cap,"invalid finite scene bounds");return 0;}
        if(fabs((double)result.bounds_min[axis])>1e9 || fabs((double)result.bounds_max[axis])>1e9){message(error,cap,"scene coordinate range exceeds viewer domain");return 0;}
        width=(double)result.bounds_max[axis]-result.bounds_min[axis];diagonal2+=width*width;
    }
    if(diagonal2<1e-12){message(error,cap,"scene bounds have no usable extent");return 0;}
    n=(size_t)count*9;
    result.vertices=(float*)malloc(n*sizeof(float));
    if(!result.vertices){message(error,cap,"scene vertex allocation failed");return 0;}
    result.vertex_count=count;
    for(i=0;i<count;i++){
        int component;
        for(component=0;component<9;component++){
            float value=number(bytes+36+(size_t)i*36+(size_t)component*4);
            if(!finite_float(value)){message(error,cap,"nonfinite scene vertex component");goto fail;}
            result.vertices[(size_t)i*9+(size_t)component]=value;
        }
        for(axis=0;axis<3;axis++){
            double value=result.vertices[(size_t)i*9+(size_t)axis];
            double tolerance=1e-4*(1.0+(double)result.bounds_max[axis]-result.bounds_min[axis]);
            if(value<(double)result.bounds_min[axis]-tolerance || value>(double)result.bounds_max[axis]+tolerance){
                message(error,cap,"scene vertex lies outside declared bounds");goto fail;}
        }
    }
    *mesh=result;return 1;
fail:amalur_scene_mesh_clear(&result);return 0;
}
