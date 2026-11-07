#include "opem_collision.h"
#include <float.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>

#define MAX_TRIANGLES 4000000u
#define MAX_QUERY 4096u
#define LEAF_SIZE 8u
typedef struct vec {double x,y,z;} vec;
typedef struct tri {float p[9],lo[3],hi[3],normal[3];} tri;
typedef struct node {float lo[3],hi[3];uint32_t left,right,start,count;} node;
struct opem_collision_world {
    tri *triangles;node *nodes;uint32_t *order;
    uint32_t count,node_count,degenerate;size_t bytes;
    uint64_t build_work;int build_failed;
};
typedef struct hit {double t;vec normal;int found;} hit;
typedef struct query {uint32_t ids[MAX_QUERY],count;} query;

static vec V(double x,double y,double z){vec r={x,y,z};return r;}
static vec add(vec a,vec b){return V(a.x+b.x,a.y+b.y,a.z+b.z);}
static vec sub(vec a,vec b){return V(a.x-b.x,a.y-b.y,a.z-b.z);}
static vec mul(vec a,double b){return V(a.x*b,a.y*b,a.z*b);}
static double dot(vec a,vec b){return a.x*b.x+a.y*b.y+a.z*b.z;}
static vec cross(vec a,vec b){return V(a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x);}
static double length(vec a){return sqrt(dot(a,a));}
static double clamp(double x,double a,double b){return x<a?a:x>b?b:x;}
static vec from(const float *p){return V(p[0],p[1],p[2]);}
static void store(float *p,vec a){p[0]=(float)a.x;p[1]=(float)a.y;p[2]=(float)a.z;}
static double component(vec p,int axis){return axis==0?p.x:axis==1?p.y:p.z;}
static int number(double x){return x==x&&x<=DBL_MAX&&x>=-DBL_MAX;}
static int vector_ok(vec p){return number(p.x)&&number(p.y)&&number(p.z)&&fabs(p.x)<=1e6&&fabs(p.y)<=1e6&&fabs(p.z)<=1e6;}
static void message(char *p,size_t n,const char *s){if(p&&n){size_t k=strlen(s);if(k>=n)k=n-1;memcpy(p,s,k);p[k]=0;}}
static int config_ok(const opem_controller_config *c){
    return c&&number(c->radius)&&number(c->height)&&number(c->skin)&&number(c->step_height)&&number(c->ground_snap)
        &&number(c->max_slope_cos)&&number(c->gravity)&&number(c->max_speed)&&number(c->max_fall_distance)&&number(c->max_ceiling_height)
        &&c->radius>=1&&c->radius<=100&&c->height>=2*c->radius&&c->height<=500
        &&c->skin>=.01&&c->skin<=2&&c->step_height>=0&&c->step_height<=c->radius
        &&c->ground_snap>=0&&c->ground_snap<=20&&c->max_slope_cos>=.5&&c->max_slope_cos<=1
        &&c->gravity>0&&c->gravity<=5000&&c->max_speed>0&&c->max_speed<=1000
        &&c->max_fall_distance>=c->step_height&&c->max_fall_distance<=1000
        &&c->max_ceiling_height>=c->height&&c->max_ceiling_height<=3000;
}
void opem_controller_config_default(opem_controller_config *c){if(c){
    c->radius=32;c->height=170;c->skin=.25f;c->step_height=25;c->ground_snap=6;
    c->max_slope_cos=.70710678f;c->gravity=980;c->max_speed=240;c->max_fall_distance=250;
    c->max_ceiling_height=1000;c->require_ceiling=1;
}}
void opem_collision_destroy(opem_collision_world *w){if(w){free(w->triangles);free(w->nodes);free(w->order);free(w);}}
static int before(const opem_collision_world *w,uint32_t a,uint32_t b,int axis){
    const tri *x=w->triangles+a,*y=w->triangles+b;
    double u=(double)x->p[axis]+x->p[axis+3]+x->p[axis+6],v=(double)y->p[axis]+y->p[axis+3]+y->p[axis+6];
    return u<v||(u==v&&a<b);
}
static void median(opem_collision_world *w,int lo,int hi,int target,int axis){
    while(lo<hi){int i=lo,j=hi;uint32_t pivot=w->order[lo+(hi-lo)/2];
        while(i<=j){
            while(before(w,w->order[i],pivot,axis))i++;
            while(before(w,pivot,w->order[j],axis))j--;
            if(i<=j){uint32_t t=w->order[i];w->order[i++]=w->order[j];w->order[j--]=t;}
            if(++w->build_work>(uint64_t)w->count*128u){w->build_failed=1;return;}
        }
        if(target<=j)hi=j;else if(target>=i)lo=i;else return;
    }
}
static uint32_t build_node(opem_collision_world *w,uint32_t start,uint32_t count,unsigned depth){
    uint32_t index=w->node_count++,i;node *n=w->nodes+index;int a,axis=0;
    for(a=0;a<3;a++){n->lo[a]=FLT_MAX;n->hi[a]=-FLT_MAX;}
    for(i=start;i<start+count;i++){const tri *t=w->triangles+w->order[i];for(a=0;a<3;a++){
        if(t->lo[a]<n->lo[a])n->lo[a]=t->lo[a];if(t->hi[a]>n->hi[a])n->hi[a]=t->hi[a];}}
    n->start=start;n->count=count;n->left=n->right=0;
    if(count<=LEAF_SIZE)return index;
    if(depth>=60){w->build_failed=1;return index;}
    for(a=1;a<3;a++)if(n->hi[a]-n->lo[a]>n->hi[axis]-n->lo[axis])axis=a;
    median(w,(int)start,(int)(start+count-1),(int)(start+count/2),axis);
    if(w->build_failed)return index;
    n->count=0;n->left=build_node(w,start,count/2,depth+1);
    n->right=build_node(w,start+count/2,count-count/2,depth+1);return index;
}
int opem_collision_create(opem_collision_world **out,const float *vertices,uint32_t count,uint32_t stride,char *error,size_t cap){
    opem_collision_world *w;uint32_t i,j;int a;
    message(error,cap,"");
    if(!out||*out||!vertices||!count||count%3||count/3>MAX_TRIANGLES||stride<3||stride>64){message(error,cap,"invalid collision mesh admission");return 0;}
    w=(opem_collision_world*)calloc(1,sizeof(*w));if(!w){message(error,cap,"collision allocation failed");return 0;}
    w->count=count/3;w->bytes=sizeof(*w)+(size_t)w->count*(sizeof(tri)+2*sizeof(node)+sizeof(uint32_t));
    w->triangles=(tri*)calloc(w->count,sizeof(tri));w->nodes=(node*)calloc((size_t)w->count*2,sizeof(node));w->order=(uint32_t*)malloc((size_t)w->count*sizeof(uint32_t));
    if(!w->triangles||!w->nodes||!w->order){message(error,cap,"collision allocation failed");goto fail;}
    for(i=0;i<w->count;i++){tri *t=w->triangles+i;vec normal;double norm;w->order[i]=i;
        for(a=0;a<3;a++){t->lo[a]=FLT_MAX;t->hi[a]=-FLT_MAX;}
        for(j=0;j<3;j++){const float *p=vertices+((size_t)i*3+j)*stride;
            if(!vector_ok(from(p))){message(error,cap,"collision position outside finite domain");goto fail;}
            for(a=0;a<3;a++){t->p[j*3+a]=p[a];if(p[a]<t->lo[a])t->lo[a]=p[a];if(p[a]>t->hi[a])t->hi[a]=p[a];}}
        normal=cross(sub(from(t->p+3),from(t->p)),sub(from(t->p+6),from(t->p)));norm=length(normal);
        if(norm<1e-9){w->degenerate++;store(t->normal,V(0,0,0));}else store(t->normal,mul(normal,1/norm));
    }
    build_node(w,0,w->count,0);
    if(w->build_failed){message(error,cap,"collision build work budget exceeded");goto fail;}
    *out=w;return 1;
fail:opem_collision_destroy(w);return 0;
}
void opem_collision_get_stats(const opem_collision_world *w,opem_collision_stats *s){if(s){memset(s,0,sizeof(*s));if(w){
    s->triangles=w->count;s->nodes=w->node_count;s->degenerate_triangles=w->degenerate;s->allocated_bytes=w->bytes;
    memcpy(s->bounds_min,w->nodes[0].lo,12);memcpy(s->bounds_max,w->nodes[0].hi,12);
}}}
static int overlap(const float *lo,const float *hi,vec a,vec b){return hi[0]>=a.x&&lo[0]<=b.x&&hi[1]>=a.y&&lo[1]<=b.y&&hi[2]>=a.z&&lo[2]<=b.z;}
static int candidates(const opem_collision_world *w,vec lo,vec hi,query *q){
    uint32_t stack[64],top=0,visits=0;q->count=0;stack[top++]=0;
    while(top){const node *n=w->nodes+stack[--top];uint32_t i;
        if(++visits>w->node_count)return 0;
        if(!overlap(n->lo,n->hi,lo,hi))continue;
        if(n->count){for(i=n->start;i<n->start+n->count;i++){uint32_t id=w->order[i];const tri *t=w->triangles+id;
            if(overlap(t->lo,t->hi,lo,hi)){if(q->count==MAX_QUERY)return 0;q->ids[q->count++]=id;}}}
        else{if(top+2>64)return 0;stack[top++]=n->right;stack[top++]=n->left;}
    }return 1;
}
static vec point_segment(vec p,vec a,vec b){vec d=sub(b,a);double l=dot(d,d);return l<1e-20?a:add(a,mul(d,clamp(dot(sub(p,a),d)/l,0,1)));}
int opem_collision_ray(const opem_collision_world *w,const float eye[3],const float direction[3],float reach,float *distance){
 query q;uint32_t i;vec origin,d,end,lo,hi;double best=reach;
 if(!w||!eye||!direction||!distance||!number(reach)||reach<=0||reach>1000)return 0;origin=from(eye);d=from(direction);if(!vector_ok(origin)||!vector_ok(d)||fabs(dot(d,d)-1)>.002)return 0;
 end=add(origin,mul(d,reach));lo=V(fmin(origin.x,end.x)-.01,fmin(origin.y,end.y)-.01,fmin(origin.z,end.z)-.01);hi=V(fmax(origin.x,end.x)+.01,fmax(origin.y,end.y)+.01,fmax(origin.z,end.z)+.01);if(!candidates(w,lo,hi,&q))return 0;
 for(i=0;i<q.count;i++){const tri *t=w->triangles+q.ids[i];vec a=from(t->p),e1=sub(from(t->p+3),a),e2=sub(from(t->p+6),a),p=cross(d,e2),s=sub(origin,a),v;double det=dot(e1,p),u,k,at;if(fabs(det)<1e-10)continue;u=dot(s,p)/det;if(u<0||u>1)continue;v=cross(s,e1);k=dot(d,v)/det;if(k<0||u+k>1)continue;at=dot(e2,v)/det;if(at>.01&&at<best)best=at;}
 *distance=(float)best;return 1;
}
static int triangle_inside(vec p,vec a,vec b,vec c){
    vec u=sub(b,a),v=sub(c,a),q=sub(p,a);double aa=dot(u,u),ab=dot(u,v),bb=dot(v,v),qa=dot(q,u),qb=dot(q,v),den=aa*bb-ab*ab,x,y;
    if(den<=1e-20)return 0;x=(qa*bb-qb*ab)/den;y=(qb*aa-qa*ab)/den;
    return x>=-1e-9&&y>=-1e-9&&x+y<=1+1e-9;
}
static vec point_triangle(vec p,vec a,vec b,vec c){
    vec n=cross(sub(b,a),sub(c,a)),q,best;double n2=dot(n,n),d,bestd;
    if(n2>1e-20){q=sub(p,mul(n,dot(sub(p,a),n)/n2));if(triangle_inside(q,a,b,c))return q;}
    best=point_segment(p,a,b);bestd=dot(sub(p,best),sub(p,best));q=point_segment(p,b,c);d=dot(sub(p,q),sub(p,q));
    if(d<bestd){best=q;bestd=d;}q=point_segment(p,c,a);d=dot(sub(p,q),sub(p,q));if(d<bestd)best=q;return best;
}
static void segments(vec p,vec q,vec a,vec b,vec *x,vec *y){
    vec d=sub(q,p),e=sub(b,a),r=sub(p,a);double aa=dot(d,d),ee=dot(e,e),f=dot(e,r),s,t;
    if(aa<1e-20&&ee<1e-20){*x=p;*y=a;return;}
    if(aa<1e-20){s=0;t=clamp(f/ee,0,1);}else{double c=dot(d,r);
        if(ee<1e-20){t=0;s=clamp(-c/aa,0,1);}else{double de=dot(d,e),den=aa*ee-de*de;
            s=den>1e-20?clamp((de*f-c*ee)/den,0,1):0;t=(de*s+f)/ee;
            if(t<0){t=0;s=clamp(-c/aa,0,1);}else if(t>1){t=1;s=clamp((de-c)/aa,0,1);}
        }}*x=add(p,mul(d,s));*y=add(a,mul(e,t));
}
static double capsule_triangle(vec feet,const opem_controller_config *c,const tri *t,vec motion,vec *normal){
    vec p=add(feet,V(0,0,c->radius)),q=add(feet,V(0,0,c->height-c->radius));
    vec a=from(t->p),b=from(t->p+3),d=from(t->p+6),bestx=p,besty=point_triangle(p,a,b,d),x,y,n;
    double best=dot(sub(bestx,besty),sub(bestx,besty)),value;int i;vec ends[3];
    x=q;y=point_triangle(q,a,b,d);value=dot(sub(x,y),sub(x,y));if(value<best){best=value;bestx=x;besty=y;}
    ends[0]=a;ends[1]=b;ends[2]=d;
    for(i=0;i<3;i++){segments(p,q,ends[i],ends[(i+1)%3],&x,&y);value=dot(sub(x,y),sub(x,y));if(value<best){best=value;bestx=x;besty=y;}}
    n=cross(sub(b,a),sub(d,a));value=dot(n,sub(q,p));
    if(fabs(value)>1e-15){double u=dot(n,sub(a,p))/value;if(u>=0&&u<=1){x=add(p,mul(sub(q,p),u));if(triangle_inside(x,a,b,d)){best=0;bestx=besty=x;}}}
    value=sqrt(best<0?0:best);
    if(value>1e-10)*normal=mul(sub(bestx,besty),1/value);
    else{*normal=from(t->normal);if(length(*normal)<.5){double m=length(motion);*normal=m>1e-10?mul(motion,-1/m):V(0,0,1);}else if(dot(*normal,motion)>0)*normal=mul(*normal,-1);}
    return value;
}
static int clearance(const opem_collision_world *w,const opem_controller_config *c,vec feet,uint32_t *queries){
    query q;uint32_t i;double r=c->radius+c->skin;vec normal;
    if(queries)(*queries)++;
    if(!candidates(w,add(feet,V(-r,-r,-c->skin)),add(feet,V(r,r,c->height+c->skin)),&q))return -1;
    /* Keep half the skin as a real separation margin while allowing float
     * storage to round contact positions; never admit actual radius overlap. */
    for(i=0;i<q.count;i++)if(capsule_triangle(feet,c,w->triangles+q.ids[i],V(0,0,0),&normal)<c->radius+c->skin*.5)return 0;
    return 1;
}
int opem_controller_clear(const opem_collision_world *w,const opem_controller_config *c,const float feet[3],char *error,size_t cap){
    int status;message(error,cap,"");if(!w||!config_ok(c)||!feet||!vector_ok(from(feet))){message(error,cap,"invalid capsule query");return 0;}
    status=clearance(w,c,from(feet),NULL);if(status!=1)message(error,cap,status<0?"collision query budget exceeded":"capsule overlaps geometry");return status==1;
}
static int sweep(const opem_collision_world *w,const opem_controller_config *c,vec feet,vec delta,hit *out,uint32_t *queries){
    query q;uint32_t i;vec end=add(feet,delta),lo,hi;double r=c->radius+c->skin;out->found=0;out->t=1;out->normal=V(0,0,0);
    if(queries)(*queries)++;
    lo=V(fmin(feet.x,end.x)-r,fmin(feet.y,end.y)-r,fmin(feet.z,end.z)-c->skin);
    hi=V(fmax(feet.x,end.x)+r,fmax(feet.y,end.y)+r,fmax(feet.z,end.z)+c->height+c->skin);
    if(!candidates(w,lo,hi,&q))return 0;
    if(length(delta)<1e-10)return 1;
    for(i=0;i<q.count;i++){double at=0;unsigned iteration;const tri *triangle=w->triangles+q.ids[i];
        for(iteration=0;iteration<48;iteration++){vec normal;double distance=capsule_triangle(add(feet,mul(delta,at)),c,triangle,delta,&normal);
            double closing=-dot(delta,normal),gap=distance-r,advance;
            if(gap<=1e-6){
                if(at==0&&closing<=1e-8)break;
                if(at<=out->t){out->found=1;out->t=at;out->normal=normal;}break;
            }
            if(closing<=1e-10)break;
            advance=.95*gap/closing;
            if(advance<1e-9){if(at<=out->t){out->found=1;out->t=at;out->normal=normal;}break;}
            at+=advance;if(at>out->t||at>1)break;
        }
        if(iteration==48)return 0; /* Unknown convergence freezes the whole step. */
    }return 1;
}
static int slide(const opem_collision_world *w,const opem_controller_config *c,vec start,vec delta,vec *result,int *blocked,uint32_t *contacts,uint32_t *queries){
    vec p=start,remaining=delta;unsigned i;*blocked=0;
    for(i=0;i<6&&length(remaining)>1e-6;i++){hit h;vec normal;double into;
        if(!sweep(w,c,p,remaining,&h,queries))return 0;
        p=add(p,mul(remaining,h.t));if(!h.found){remaining=V(0,0,0);break;}
        (*contacts)++;*blocked=1;remaining=mul(remaining,1-h.t);normal=h.normal;
        /* Steep surfaces cannot turn horizontal walking into upward climbing. */
        if(normal.z>0&&normal.z<c->max_slope_cos&&fabs(delta.z)<1e-8){double l=sqrt(normal.x*normal.x+normal.y*normal.y);if(l>1e-8)normal=V(normal.x/l,normal.y/l,0);}
        into=dot(remaining,normal);if(into<0)remaining=sub(remaining,mul(normal,into));
        else break;
    }*result=p;return 1; /* Residual motion after contact cap is discarded safely. */
}
static int ceiling(const opem_collision_world *w,const opem_controller_config *c,vec feet,uint32_t *queries){
    query q;uint32_t i;double bottom=feet.z+c->height+c->skin,top=feet.z+c->max_ceiling_height;
    if(queries)(*queries)++;
    if(!candidates(w,V(feet.x,feet.y,bottom),V(feet.x,feet.y,top),&q))return -1;
    for(i=0;i<q.count;i++){const tri *t=w->triangles+q.ids[i];vec a=from(t->p),b=from(t->p+3),d=from(t->p+6),n=cross(sub(b,a),sub(d,a)),p;
        double z;if(fabs(n.z)<1e-12)continue;z=a.z-(n.x*(feet.x-a.x)+n.y*(feet.y-a.y))/n.z;
        p=V(feet.x,feet.y,z);if(z>=bottom&&z<=top&&triangle_inside(p,a,b,d))return 1;
    }return 0;
}
typedef struct spawn_candidate {vec p;double score;uint32_t triangle;} spawn_candidate;
static int spawn_compare(const void *a,const void *b){const spawn_candidate *x=(const spawn_candidate*)a,*y=(const spawn_candidate*)b;
    if(x->score<y->score)return -1;if(x->score>y->score)return 1;return x->triangle<y->triangle?-1:x->triangle>y->triangle;
}
int opem_controller_spawn(const opem_collision_world *w,const opem_controller_config *c,const float hint[3],opem_controller *controller,char *error,size_t cap){
    spawn_candidate *list;uint32_t count=0,i,checks=0;vec center;opem_controller result;message(error,cap,"");
    if(!w||!config_ok(c)||!controller||(hint&&!vector_ok(from(hint)))){message(error,cap,"invalid spawn inputs");return 0;}
    center=hint?from(hint):V(((double)w->nodes[0].lo[0]+w->nodes[0].hi[0])*.5,((double)w->nodes[0].lo[1]+w->nodes[0].hi[1])*.5,w->nodes[0].lo[2]);
    list=(spawn_candidate*)malloc((size_t)w->count*2*sizeof(*list));if(!list){message(error,cap,"spawn allocation failed");return 0;}
    for(i=0;i<w->count;i++){const tri *t=w->triangles+i;vec a=from(t->p),b=from(t->p+3),d=from(t->p+6),p,n=cross(sub(b,a),sub(d,a));double area=length(n),score;
        if(area<c->radius*c->radius*.5||fabs(t->normal[2])<c->max_slope_cos)continue;
        /* First consider the closest actual surface point to the requested hint.
         * A broad floor triangle centroid can lie across a railing or room.
         * Both candidates retain the complete clearance/ceiling/floor checks. */
        p=point_triangle(center,a,b,d);p.z+=c->skin+.002;
        score=(p.x-center.x)*(p.x-center.x)+(p.y-center.y)*(p.y-center.y)+4*(p.z-center.z)*(p.z-center.z);
        list[count].p=p;list[count].score=score;list[count++].triangle=i;
        p=mul(add(add(a,b),d),1.0/3);p.z+=c->skin+.002;
        score=(p.x-center.x)*(p.x-center.x)+(p.y-center.y)*(p.y-center.y)+4*(p.z-center.z)*(p.z-center.z);
        list[count].p=p;list[count].score=score;list[count++].triangle=i;
    }
    qsort(list,count,sizeof(*list),spawn_compare);memset(&result,0,sizeof(result));
    for(i=0;i<count&&checks<4096;i++,checks++){vec p=list[i].p;int clear=clearance(w,c,p,&result.queries_last_step),roof;
        if(clear<0){free(list);message(error,cap,"spawn query budget exceeded");return 0;}
        if(!clear)continue;
        roof=c->require_ceiling?ceiling(w,c,p,&result.queries_last_step):1;
        if(roof<0){free(list);message(error,cap,"spawn ceiling query budget exceeded");return 0;}
        if(!roof)continue;
        {hit floor;if(!sweep(w,c,add(p,V(0,0,.02)),V(0,0,-c->ground_snap-.04),&floor,&result.queries_last_step)){free(list);message(error,cap,"spawn floor query budget exceeded");return 0;}
            if(!floor.found||floor.normal.z<c->max_slope_cos)continue;
            p=add(add(p,V(0,0,.02)),mul(V(0,0,-c->ground_snap-.04),floor.t));}
        store(result.feet,p);store(result.last_safe_feet,p);result.grounded=1;result.valid=1;
        *controller=result;free(list);return 1;
    }free(list);message(error,cap,"no bounded indoor floor candidate has full capsule clearance");return 0;
}
static int elevated_tread(const opem_collision_world *w,const opem_controller_config *c,vec feet,vec direction,uint32_t *queries){
    query q;uint32_t i;double l=length(direction);vec at;
    if(l<1e-10)return 0;at=add(feet,mul(direction,c->radius/l));(*queries)++;
    if(!candidates(w,V(at.x,at.y,feet.z+1),V(at.x,at.y,feet.z+c->step_height+c->skin),&q))return -1;
    for(i=0;i<q.count;i++){const tri *t=w->triangles+q.ids[i];vec a=from(t->p),b=from(t->p+3),d=from(t->p+6),n=from(t->normal),p;double z;
        if(fabs(n.z)<c->max_slope_cos)continue;z=a.z-(n.x*(at.x-a.x)+n.y*(at.y-a.y))/n.z;p=V(at.x,at.y,z);
        if(z>feet.z+1&&z<=feet.z+c->step_height+c->skin&&triangle_inside(p,a,b,d))return 1;
    }return 0;
}
/* Admit rounded capsule contact at a descending curb only when a nearby
 * walkable tread exists within the configured drop distance. */
static int lower_tread(const opem_collision_world *w,const opem_controller_config *c,vec feet,vec direction,uint32_t *queries){
    query q;uint32_t i;double l=length(direction);vec at;
    if(l<1e-10)return 0;at=add(feet,mul(direction,c->radius/l));(*queries)++;
    if(!candidates(w,V(at.x,at.y,feet.z-c->step_height-c->skin),V(at.x,at.y,feet.z),&q))return -1;
    for(i=0;i<q.count;i++){const tri *t=w->triangles+q.ids[i];vec a=from(t->p),b=from(t->p+3),d=from(t->p+6),n=from(t->normal),p;double z;
        if(fabs(n.z)<c->max_slope_cos)continue;z=a.z-(n.x*(at.x-a.x)+n.y*(at.y-a.y))/n.z;p=V(at.x,at.y,z);
        if(z>=feet.z-c->step_height-c->skin&&z<feet.z-c->skin&&triangle_inside(p,a,b,d))return 1;
    }return 0;
}
static int step_once(const opem_collision_world *w,const opem_controller_config *c,opem_controller *s,double vx,double vy,double dt){
    vec start=from(s->feet),p,delta=V(vx*dt,vy*dt,0);int blocked,stepped_ground=0;hit h;
    if(!slide(w,c,start,delta,&p,&blocked,&s->contacts_last_step,&s->queries_last_step))return 0;
    if(blocked&&s->grounded&&c->step_height>0&&length(delta)>1e-6){hit up,down;vec raised,stepped;int stepblocked;
        if(!sweep(w,c,start,V(0,0,c->step_height),&up,&s->queries_last_step))return 0;
        if(!up.found){raised=add(start,V(0,0,c->step_height));
            if(!slide(w,c,raised,delta,&stepped,&stepblocked,&s->contacts_last_step,&s->queries_last_step))return 0;
            if(!sweep(w,c,stepped,V(0,0,-c->step_height-c->ground_snap),&down,&s->queries_last_step))return 0;
            if(down.found&&down.normal.z>.01){vec landed=add(stepped,mul(V(0,0,-c->step_height-c->ground_snap),down.t));
                double old=(p.x-start.x)*(p.x-start.x)+(p.y-start.y)*(p.y-start.y),better=(landed.x-start.x)*(landed.x-start.x)+(landed.y-start.y)*(landed.y-start.y);
                if(better>old+1e-8&&landed.z-start.z<=c->step_height+.01){int tread=1;
                    if(down.normal.z<c->max_slope_cos)tread=elevated_tread(w,c,start,delta,&s->queries_last_step);
                    if(tread<0)return 0;if(tread){p=landed;stepped_ground=1;}
                }
            }
        }
    }
    /* Render geometry is not a complete native collision asset. A grounded
     * walker may descend a low step, but may not walk into an unsupported hole.
     * This deliberately disallows authored drop-offs as well as missing floors. */
    if(s->grounded&&length(delta)>1e-6){hit support;double reach=fmax(c->step_height,c->ground_snap)+c->skin;
        if(!sweep(w,c,p,V(0,0,-reach),&support,&s->queries_last_step))return 0;
        if(support.found&&support.normal.z>.01&&support.normal.z<c->max_slope_cos&&!stepped_ground){
            int tread=lower_tread(w,c,start,delta,&s->queries_last_step);if(tread<0)return 0;if(tread)stepped_ground=1;
        }
        if(support.found&&(support.normal.z>=c->max_slope_cos||(stepped_ground&&support.normal.z>.01)))
            p=add(p,mul(V(0,0,-reach),support.t));
        else{p=start;stepped_ground=0;s->edge_blocks_last_step++;}
    }
    s->grounded=0;
    if(!sweep(w,c,p,V(0,0,-c->ground_snap),&h,&s->queries_last_step))return 0;
    if(h.found&&(h.normal.z>=c->max_slope_cos||(stepped_ground&&h.normal.z>.01))){p=add(p,mul(V(0,0,-c->ground_snap),h.t));s->grounded=1;s->velocity_z=0;}
    else{
        s->velocity_z=(float)fmax(-1500,(double)s->velocity_z-c->gravity*dt);
        if(!sweep(w,c,p,V(0,0,s->velocity_z*dt),&h,&s->queries_last_step))return 0;
        p=add(p,mul(V(0,0,s->velocity_z*dt),h.t));
        if(h.found){s->contacts_last_step++;if(h.normal.z>=c->max_slope_cos){s->grounded=1;s->velocity_z=0;}
            else{vec slid;int stopped;if(!slide(w,c,p,V(0,0,s->velocity_z*dt*(1-h.t)),&slid,&stopped,&s->contacts_last_step,&s->queries_last_step))return 0;p=slid;}}
    }
    if(!vector_ok(p))return 0;
    store(s->feet,p);
    if(s->grounded){store(s->last_safe_feet,p);}
    else if(p.z<s->last_safe_feet[2]-c->max_fall_distance||p.z<w->nodes[0].lo[2]-2*c->radius){
        memcpy(s->feet,s->last_safe_feet,sizeof(s->feet));s->velocity_z=0;s->grounded=1;s->recovered_last_step=1;
    }
    return 1;
}
int opem_controller_step(const opem_collision_world *w,const opem_controller_config *c,opem_controller *controller,float vx,float vy,float dt,char *error,size_t cap){
    opem_controller result;double speed;unsigned steps,i;int clear;message(error,cap,"");
    if(!w||!config_ok(c)||!controller||!controller->valid||!vector_ok(from(controller->feet))||!vector_ok(from(controller->last_safe_feet))
        ||!number(controller->velocity_z)||!number(vx)||!number(vy)||!number(dt)||dt<0||dt>.1000001f){message(error,cap,"invalid bounded movement inputs");return 0;}
    result=*controller;result.contacts_last_step=0;result.queries_last_step=0;result.edge_blocks_last_step=0;result.recovered_last_step=0;
    clear=clearance(w,c,from(result.feet),&result.queries_last_step);
    if(clear!=1){message(error,cap,clear<0?"movement query budget exceeded":"movement begins inside geometry");return 0;}
    if(dt==0){*controller=result;return 1;}
    speed=sqrt((double)vx*vx+(double)vy*vy);if(speed>c->max_speed){vx=(float)(vx*c->max_speed/speed);vy=(float)(vy*c->max_speed/speed);}
    steps=(unsigned)ceil((double)dt*120);if(steps>13){message(error,cap,"movement substep budget exceeded");return 0;}
    for(i=0;i<steps;i++)if(!step_once(w,c,&result,vx,vy,(double)dt/steps)){message(error,cap,"movement sweep budget exceeded; position preserved");return 0;}
    clear=clearance(w,c,from(result.feet),&result.queries_last_step);
    if(clear!=1){message(error,cap,clear<0?"final collision budget exceeded":"movement contact validation failed; position preserved");return 0;}
    *controller=result;return 1;
}
