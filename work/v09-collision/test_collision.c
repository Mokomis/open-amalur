#include "opem_collision.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef struct soup {float *p;unsigned n,cap;} soup;
static unsigned checks,failures;
static char error[256];
#define CHECK(x) do{checks++;if(!(x)){failures++;fprintf(stderr,"FAIL line%d: %s (%s)\n",__LINE__,#x,error);}}while(0)
static void vertex(soup *s,float x,float y,float z){if(s->n+3>s->cap){s->cap=s->cap?s->cap*2:1024;s->p=(float*)realloc(s->p,s->cap*sizeof(float));if(!s->p)exit(3);}s->p[s->n++]=x;s->p[s->n++]=y;s->p[s->n++]=z;}
static void quad(soup *s,float ax,float ay,float az,float bx,float by,float bz,float cx,float cy,float cz,float dx,float dy,float dz){
    vertex(s,ax,ay,az);vertex(s,bx,by,bz);vertex(s,cx,cy,cz);vertex(s,ax,ay,az);vertex(s,cx,cy,cz);vertex(s,dx,dy,dz);
}
static void horizontal(soup *s,float xmin,float xmax,float ymin,float ymax,float z){quad(s,xmin,ymin,z,xmax,ymin,z,xmax,ymax,z,xmin,ymax,z);}
static void wall(soup *s,float x,float zlo,float zhi){quad(s,x,-500,zlo,x,500,zlo,x,500,zhi,x,-500,zhi);}
static opem_collision_world *build(soup *s){opem_collision_world *w=NULL;CHECK(opem_collision_create(&w,s->p,s->n/3,3,error,sizeof(error)));return w;}
static opem_controller pose(float x,float y,float z){opem_controller p;memset(&p,0,sizeof(p));p.feet[0]=p.last_safe_feet[0]=x;p.feet[1]=p.last_safe_feet[1]=y;p.feet[2]=p.last_safe_feet[2]=z;p.valid=p.grounded=1;return p;}
static int walk(opem_collision_world *w,opem_controller_config *c,opem_controller *p,float x,float y,int frames){int i;for(i=0;i<frames;i++)if(!opem_controller_step(w,c,p,x,y,1.f/60,error,sizeof(error)))return 0;return 1;}
int main(void){
    soup s={0};opem_collision_world *w;opem_controller_config c;opem_controller a,b,before;float hint[3]={0,0,0};int i,recovered=0,edge_blocks=0;opem_collision_stats stats;
    opem_controller_config_default(&c);
    horizontal(&s,-500,500,-500,500,0);horizontal(&s,-500,500,-500,500,250);wall(&s,100,0,250);w=build(&s);
    memset(&a,0,sizeof(a));memset(&b,0,sizeof(b));CHECK(opem_controller_spawn(w,&c,hint,&a,error,sizeof(error)));CHECK(opem_controller_spawn(w,&c,hint,&b,error,sizeof(error)));CHECK(!memcmp(&a,&b,sizeof(a)));CHECK(a.grounded&&a.valid);CHECK(opem_controller_clear(w,&c,a.feet,error,sizeof(error)));
    a=pose(-100,0,.251f);CHECK(walk(w,&c,&a,240,0,120));CHECK(a.feet[0]>60&&a.feet[0]<68);CHECK(fabs(a.feet[2]-.25)<.02);
    a=pose(60,-200,.251f);CHECK(walk(w,&c,&a,200,100,120));CHECK(a.feet[0]<68&&a.feet[1]>-50);CHECK(opem_controller_clear(w,&c,a.feet,error,sizeof(error)));
    before=a;CHECK(!opem_controller_step(w,&c,&a,0,0,1,error,sizeof(error)));CHECK(!memcmp(&a,&before,sizeof(a)));CHECK(!opem_controller_step(w,&c,&a,NAN,0,.01f,error,sizeof(error)));CHECK(!memcmp(&a,&before,sizeof(a)));
    opem_collision_get_stats(w,&stats);CHECK(stats.triangles==6&&stats.nodes>0);opem_collision_destroy(w);free(s.p);memset(&s,0,sizeof(s));
    /* Thin geometry remains solid even when travel in one frame exceeds radius. */
    horizontal(&s,-500,500,-500,500,0);wall(&s,20,0,250);w=build(&s);c.radius=10;c.height=80;c.step_height=0;c.max_speed=1000;c.require_ceiling=0;a=pose(0,0,.251f);CHECK(opem_controller_step(w,&c,&a,1000,0,.1f,error,sizeof(error)));CHECK(a.feet[0]<10&&a.feet[0]>9);opem_collision_destroy(w);free(s.p);memset(&s,0,sizeof(s));
    /* A low tread is traversable, but a waist-high ledge is not. */
    opem_controller_config_default(&c);c.require_ceiling=0;horizontal(&s,-500,500,-500,500,0);wall(&s,0,0,20);horizontal(&s,0,500,-500,500,20);w=build(&s);a=pose(-100,0,.251f);CHECK(walk(w,&c,&a,160,0,120));CHECK(a.feet[0]>100&&fabs(a.feet[2]-20.25)<.1);opem_collision_destroy(w);free(s.p);memset(&s,0,sizeof(s));
    horizontal(&s,-500,500,-500,500,0);wall(&s,0,0,80);horizontal(&s,0,500,-500,500,80);w=build(&s);a=pose(-100,0,.251f);CHECK(walk(w,&c,&a,160,0,120));CHECK(a.feet[0]<-31&&a.feet[2]<1);opem_collision_destroy(w);free(s.p);memset(&s,0,sizeof(s));
    /* Continuous ramps: a gentle surface is walkable; steep is not a staircase. */
    horizontal(&s,-500,0,-500,500,0);quad(&s,0,-500,0,400,-500,120,400,500,120,0,500,0);w=build(&s);a=pose(-100,0,.251f);CHECK(walk(w,&c,&a,160,0,120));CHECK(a.feet[0]>100&&a.feet[2]>30&&a.grounded);opem_collision_destroy(w);free(s.p);memset(&s,0,sizeof(s));
    horizontal(&s,-500,0,-500,500,0);quad(&s,0,-500,0,200,-500,400,200,500,400,0,500,0);w=build(&s);a=pose(-100,0,.251f);CHECK(walk(w,&c,&a,160,0,120));CHECK(a.feet[0]<5&&a.feet[2]<20);opem_collision_destroy(w);free(s.p);memset(&s,0,sizeof(s));
    /* A low room rejects standing spawn instead of silently shortening the body. */
    c.require_ceiling=1;horizontal(&s,-500,500,-500,500,0);horizontal(&s,-500,500,-500,500,100);w=build(&s);a=pose(11,12,13);before=a;CHECK(!opem_controller_spawn(w,&c,hint,&a,error,sizeof(error)));CHECK(!memcmp(&a,&before,sizeof(a)));opem_collision_destroy(w);free(s.p);memset(&s,0,sizeof(s));
    /* Missing rendered floors stop grounded walking rather than cycling falls. */
    c.require_ceiling=0;horizontal(&s,-500,0,-500,500,0);w=build(&s);a=pose(-100,0,.251f);for(i=0;i<300;i++){if(!opem_controller_step(w,&c,&a,160,0,1.f/60,error,sizeof(error)))break;if(a.recovered_last_step)recovered++;edge_blocks+=(int)a.edge_blocks_last_step;}CHECK(i==300);CHECK(recovered==0&&edge_blocks>0);CHECK(a.feet[2]>-10&&a.grounded);CHECK(a.feet[0]<c.radius);CHECK(opem_controller_clear(w,&c,a.feet,error,sizeof(error)));
    /* Explicitly airborne state still receives gravity and bounded recovery. */
    a=pose(-100,0,.251f);a.feet[0]=100;a.grounded=0;recovered=0;for(i=0;i<180;i++){if(!opem_controller_step(w,&c,&a,0,0,1.f/60,error,sizeof(error)))break;recovered+=a.recovered_last_step;}CHECK(i==180);CHECK(recovered==1&&a.grounded&&a.feet[0]<0);opem_collision_destroy(w);free(s.p);memset(&s,0,sizeof(s));
    /* The ledge guard allows a lower walkable tread within step height. */
    horizontal(&s,-500,0,-500,500,20);horizontal(&s,0,500,-500,500,0);wall(&s,0,0,20);w=build(&s);a=pose(-100,0,20.251f);CHECK(walk(w,&c,&a,160,0,120));CHECK(a.feet[0]>100&&fabs(a.feet[2]-.25)<.1&&a.grounded);opem_collision_destroy(w);free(s.p);memset(&s,0,sizeof(s));
    /* Broadphase overflow fails closed and leaves the exact prior state. */
    for(i=0;i<2050;i++)horizontal(&s,-500,500,-500,500,0);w=build(&s);a=pose(0,0,.251f);before=a;CHECK(!opem_controller_step(w,&c,&a,100,0,.01f,error,sizeof(error)));CHECK(!memcmp(&a,&before,sizeof(a)));opem_collision_destroy(w);free(s.p);memset(&s,0,sizeof(s));
    vertex(&s,0,0,0);vertex(&s,0,0,0);vertex(&s,0,0,0);w=build(&s);opem_collision_get_stats(w,&stats);CHECK(stats.degenerate_triangles==1);opem_collision_destroy(w);w=NULL;s.p[0]=NAN;CHECK(!opem_collision_create(&w,s.p,3,3,error,sizeof(error)));CHECK(w==NULL);free(s.p);
    printf("{\"checks\":%u,\"failures\":%u,\"scope\":\"authored approximate controller synthetic geometry\"}\n",checks,failures);return failures?1:0;
}
