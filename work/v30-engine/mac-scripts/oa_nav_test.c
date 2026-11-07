#include "oa_nav.h"
#include <math.h>
#include <stdio.h>
#include <string.h>
static int checks,failed;
#define CHECK(x) do{checks++;if(!(x)){failed++;printf("FAILED line %d: %s\n",__LINE__,#x);}}while(0)
enum{W=100,H=100};
static uint8_t bits[(W*H)/8+1];
static void block(int x,int y){size_t i=(size_t)y*W+(size_t)x;bits[i>>3]|=(uint8_t)(1u<<(i&7));}
int main(void){oa_nav n={W,H,-1000.f,-1000.f,200.f,bits};float p[32][2],from[2]={-900,1000},to[2]={11000,1000};int c,i,y;
 memset(bits,0,sizeof(bits));
 c=oa_nav_path(&n,from,to,p,32);CHECK(c==1);CHECK(p[0][0]==to[0]&&p[0][1]==to[1]);
 CHECK(!oa_nav_blocked(&n,0,0));CHECK(oa_nav_blocked(&n,-5000,0));
 /* A wall with one gap: the path must go through the gap. */
 for(y=0;y<H;y++)if(y<70||y>72)block(50,y);
 CHECK(oa_nav_blocked(&n,9100,1000));CHECK(!oa_nav_blocked(&n,9100,13100));
 c=oa_nav_path(&n,from,to,p,32);CHECK(c>=2);
 {float px=from[0],py=from[1],far=0,up=0;for(i=0;i<c;i++){int k;for(k=1;k<=64;k++){float t=(float)k/64.f,x=px+(p[i][0]-px)*t,y2=py+(p[i][1]-py)*t;CHECK(!oa_nav_blocked(&n,x,y2));if(x>far)far=x;}if(p[i][1]>up)up=p[i][1];px=p[i][0];py=p[i][1];}CHECK(fabsf(px-to[0])<400.f);CHECK(up>12000.f);}
 /* Sealed off, no route. */
 block(50,70);block(50,71);block(50,72);
 CHECK(oa_nav_path(&n,from,to,p,32)==0);
 /* A goal inside a wall moves to the nearest open cell. */
 {float ins[2]={9100,1000},near[2]={8700,1000};c=oa_nav_path(&n,near,ins,p,32);CHECK(c>=1);}
 /* The waypoint limit holds. */
 memset(bits,0,sizeof(bits));for(i=0;i<9;i++)for(y=0;y<H;y++)if((i%2==0&&y<H-4)||(i%2==1&&y>3))block(10+i*4,y);
 {float a[2]={100,9000},b[2]={9000,9000};c=oa_nav_path(&n,a,b,p,3);CHECK(c==0||c==3);}
 printf("nav checks %d failed %d\n",checks,failed);return failed!=0;}
