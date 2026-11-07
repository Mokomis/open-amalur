#include "native_light_volume_weights.h"
#include <math.h>
/* Match native mixed precision in ac1720: component products round to float,
 * then the matrix-vector sum uses double and rounds to float at the output. */
static double fp(float a, float b) { return (double)(a*b); }
int oa_light_volume_distance(const oa_light_volume *v,const float point[3],float *out)
{
    float delta[3],local[3],outside[3],q[4],half,squared;
    double norm; size_t k;
    if(!v||!point||!out||!isfinite(v->fade))return 0;
    norm=0.0;
    for(k=0;k<4;k++){
        if(!isfinite(v->quaternion[k]))return 0;
        norm+=(double)v->quaternion[k]*v->quaternion[k];
        q[k]=k<3?-v->quaternion[k]:v->quaternion[k];
    }
    if(fabs(norm-1.0)>0.002)return 0;
    for(k=0;k<3;k++){
        if(!isfinite(point[k])||!isfinite(v->translation[k])||
           !isfinite(v->scale[k])||v->scale[k]<0.0f)return 0;
        delta[k]=point[k]-v->translation[k];
    }
    /* db2820 conjugates sourceQ(ac11b0), then ac1720 applies its inverse-
     * Hamilton convention. Combined operation is R(sourceQ)*delta. */
    local[0]=(float)(((fp(q[2],q[0])-fp(q[3],q[1]))*delta[2]+
                      (fp(q[3],q[2])+fp(q[1],q[0]))*delta[1])*2.0+
                     (1.0-(fp(q[2],q[2])+fp(q[1],q[1]))*2.0)*delta[0]);
    local[1]=(float)(((fp(q[3],q[0])+fp(q[2],q[1]))*delta[2]+
                      (fp(q[1],q[0])-fp(q[3],q[2]))*delta[0])*2.0+
                     (1.0-(fp(q[2],q[2])+fp(q[0],q[0]))*2.0)*delta[1]);
    local[2]=(float)(((fp(q[2],q[1])-fp(q[3],q[0]))*delta[1]+
                      (fp(q[3],q[1])+fp(q[2],q[0]))*delta[0])*2.0+
                     (1.0-(fp(q[1],q[1])+fp(q[0],q[0]))*2.0)*delta[2]);
    for(k=0;k<3;k++){
        half=(float)((double)v->scale[k]*1000.0)*0.5f;
        outside[k]=fmaxf(fabsf(local[k])-half,0.0f);
    }
    squared=(float)((double)outside[0]*outside[0]+
                    (double)outside[1]*outside[1]+
                    (double)outside[2]*outside[2]);
    *out=(float)sqrt((double)squared);
    return isfinite(*out)?1:0;
}
float oa_light_volume_fade_weight(float distance,float fade,float space_weight)
{
    float amount,weight;
    if(!isfinite(distance)||distance<0.0f||!isfinite(fade)||
       !isfinite(space_weight)||space_weight<=0.0f)return 0.0f;
    amount=fade>0.0f?distance/fade:(distance<=0.0f?0.0f:1.0f);
    amount=fminf(fmaxf(amount,0.0f),1.0f);
    weight=(float)(1.0-(double)amount)*space_weight;
    return weight>0.0f?weight:0.0f;
}
oa_light_volume_status oa_light_volume_weights(
 const oa_light_volume *volumes,size_t count,const float point[3],
 float space_weight,oa_light_volume_mode mode,float *weights,
 oa_light_volume_result *result)
{
    size_t i; float distance,total=0.0f,base,den,inverse;
    if(mode==OA_LIGHT_HARD_OVERRIDE)return OA_LIGHT_HARD_INPUT_REQUIRED;
    if((mode!=OA_LIGHT_NORMAL&&mode!=OA_LIGHT_ADDITIONAL_OVERRIDE)||
       !result||!point||(count&&(!volumes||!weights))||
       !isfinite(space_weight))return OA_LIGHT_INVALID;
    for(i=0;i<count;i++){
        if(!oa_light_volume_distance(volumes+i,point,&distance))return OA_LIGHT_INVALID;
        weights[i]=oa_light_volume_fade_weight(distance,volumes[i].fade,space_weight);
        total+=weights[i];
    }
    base=(float)(1.0-(double)total);if(base<0.0f)base=0.0f;
    den=total+base;
    if(!isfinite(den)||den<=0.0f)return OA_LIGHT_INVALID;
    inverse=(float)(1.0/(double)den);
    for(i=0;i<count;i++)weights[i]*=inverse;
    result->raw_local_total=total;result->base_residual=base;
    result->normalization_total=den;result->normalized_base=base*inverse;
    return mode==OA_LIGHT_ADDITIONAL_OVERRIDE?
        OA_LIGHT_ADDITIONAL_INPUT_REQUIRED:OA_LIGHT_NORMAL_READY;
}
