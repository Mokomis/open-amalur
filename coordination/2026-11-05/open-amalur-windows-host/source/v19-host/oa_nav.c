#include "oa_nav.h"
#include <math.h>
#include <string.h>
enum{WINDOW=160,NODES=WINDOW*WINDOW,SEARCH_LIMIT=5000};
static int blocked_cell(const oa_nav *n,int x,int y){if(x<0||y<0||(uint32_t)x>=n->width||(uint32_t)y>=n->height)return 1;{size_t i=(size_t)y*n->width+(size_t)x;return (n->bits[i>>3]>>(i&7))&1;}}
int oa_nav_blocked(const oa_nav *n,float x,float y){return blocked_cell(n,(int)floorf((x-n->x0)/n->step),(int)floorf((y-n->y0)/n->step));}
static int free_near(const oa_nav *n,int *x,int *y){int d;for(d=0;d<8;d++){int dy;for(dy=-d;dy<=d;dy++){int dx;for(dx=-d;dx<=d;dx++)if((dx==d||dx==-d||dy==d||dy==-d)&&!blocked_cell(n,*x+dx,*y+dy)){*x+=dx;*y+=dy;return 1;}}}return 0;}
static int clear_line(const oa_nav *n,int x0,int y0,int x1,int y1){int dx=x1>x0?x1-x0:x0-x1,dy=y1>y0?y1-y0:y0-y1,sx=x1>x0?1:-1,sy=y1>y0?1:-1,e=dx-dy;for(;;){int e2;if(blocked_cell(n,x0,y0))return 0;if(x0==x1&&y0==y1)return 1;e2=2*e;if(e2>-dy){e-=dy;x0+=sx;}if(e2<dx){e+=dx;y0+=sy;}}}
/* The search runs on the game thread alone, so its tables can stay out of the stack. */
static float cost[NODES];static int16_t came[NODES];static uint8_t state[NODES];static int heap[NODES];static float rank[NODES];
static void push(int *count,int node,float r){int i=(*count)++;rank[node]=r;heap[i]=node;while(i>0){int p=(i-1)/2;if(rank[heap[p]]<=rank[heap[i]])break;{int t=heap[p];heap[p]=heap[i];heap[i]=t;}i=p;}}
static int pop(int *count){int top=heap[0],i=0;heap[0]=heap[--*count];for(;;){int l=2*i+1,r=l+1,m=i;if(l<*count&&rank[heap[l]]<rank[heap[m]])m=l;if(r<*count&&rank[heap[r]]<rank[heap[m]])m=r;if(m==i)break;{int t=heap[m];heap[m]=heap[i];heap[i]=t;}i=m;}return top;}
int oa_nav_path(const oa_nav *n,const float from[2],const float to[2],float (*out)[2],int max){
 static const int8_t DX[8]={1,-1,0,0,1,1,-1,-1},DY[8]={0,0,1,-1,1,-1,1,-1};static int stack[NODES];
 int sx=(int)floorf((from[0]-n->x0)/n->step),sy=(int)floorf((from[1]-n->y0)/n->step),gx=(int)floorf((to[0]-n->x0)/n->step),gy=(int)floorf((to[1]-n->y0)/n->step),ox,oy,count=0,visited=0,found=-1,len=0,w=0,at;
 if(max<1||!free_near(n,&sx,&sy)||!free_near(n,&gx,&gy))return 0;
 if(clear_line(n,sx,sy,gx,gy)){out[0][0]=to[0];out[0][1]=to[1];return 1;}
 ox=(sx+gx)/2-WINDOW/2;oy=(sy+gy)/2-WINDOW/2;
 if(sx<ox||sy<oy||gx<ox||gy<oy||sx>=ox+WINDOW||sy>=oy+WINDOW||gx>=ox+WINDOW||gy>=oy+WINDOW)return 0;
 memset(state,0,sizeof(state));
 {int s=(sy-oy)*WINDOW+(sx-ox);cost[s]=0;came[s]=-1;state[s]=1;push(&count,s,0);}
 while(count&&visited<SEARCH_LIMIT){int c=pop(&count),cx=c%WINDOW+ox,cy=c/WINDOW+oy,d;if(state[c]==2)continue;state[c]=2;visited++;
  if(cx==gx&&cy==gy){found=c;break;}
  for(d=0;d<8;d++){int x=cx+DX[d],y=cy+DY[d],q;float g,hx,hy;if(x<ox||y<oy||x>=ox+WINDOW||y>=oy+WINDOW||blocked_cell(n,x,y))continue;if(d>=4&&(blocked_cell(n,cx+DX[d],cy)||blocked_cell(n,cx,cy+DY[d])))continue;q=(y-oy)*WINDOW+(x-ox);if(state[q]==2)continue;g=cost[c]+(d<4?1.f:1.4142f);if(state[q]==1&&g>=cost[q])continue;cost[q]=g;came[q]=(int16_t)d;state[q]=1;hx=(float)(x-gx);hy=(float)(y-gy);push(&count,q,g+sqrtf(hx*hx+hy*hy));}}
 if(found<0)return 0;
 {int c=found;for(;;){stack[len++]=c;if(came[c]<0)break;{int d=came[c];c=((c/WINDOW)-DY[d])*WINDOW+((c%WINDOW)-DX[d]);}}}
 /* Keep only the corners. */
 at=len-1;while(at>0&&w<max){int next=at-1,t;for(t=0;t<at;t++){int a=stack[at],b=stack[t];if(clear_line(n,a%WINDOW+ox,a/WINDOW+oy,b%WINDOW+ox,b/WINDOW+oy)){next=t;break;}}
  out[w][0]=n->x0+((float)(stack[next]%WINDOW+ox)+.5f)*n->step;out[w][1]=n->y0+((float)(stack[next]/WINDOW+oy)+.5f)*n->step;w++;at=next;}
 return w;
}
