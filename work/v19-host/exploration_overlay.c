/* Authored pixel glyphs; no bundled font or synthetic game asset. */
#include "exploration_overlay.h"
#include <string.h>
#include <math.h>
#include <stdlib.h>
#include <stdio.h>
#include <ctype.h>
#define OVERLAY_FLOATS 262144u
static GLuint compile(GLenum type,const char *s){GLuint x=glCreateShader(type);GLint ok;glShaderSource(x,1,&s,0);glCompileShader(x);glGetShaderiv(x,GL_COMPILE_STATUS,&ok);if(!ok){glDeleteShader(x);return 0;}return x;}
int exploration_overlay_open(exploration_overlay *o){
 const char *v="#version 300 es\nlayout(location=0)in vec2 p;layout(location=1)in vec4 c;uniform vec2 screen;out vec4 color;void main(){gl_Position=vec4(p.x/screen.x*2.0-1.0,1.0-p.y/screen.y*2.0,0,1);color=c;}";
 const char *f="#version 300 es\nprecision mediump float;in vec4 color;out vec4 frag;void main(){frag=color;}";
 GLuint vs=compile(GL_VERTEX_SHADER,v),fs=compile(GL_FRAGMENT_SHADER,f);GLint ok=0;
 if(vs&&fs){o->program=glCreateProgram();glAttachShader(o->program,vs);glAttachShader(o->program,fs);glLinkProgram(o->program);glGetProgramiv(o->program,GL_LINK_STATUS,&ok);}if(vs)glDeleteShader(vs);if(fs)glDeleteShader(fs);if(!ok){exploration_overlay_close(o);return 0;}
 o->vertices=(float*)malloc(OVERLAY_FLOATS*sizeof(float));if(!o->vertices){exploration_overlay_close(o);return 0;}
 o->screen=glGetUniformLocation(o->program,"screen");glGenVertexArrays(1,&o->array);glBindVertexArray(o->array);glGenBuffers(1,&o->buffer);glBindBuffer(GL_ARRAY_BUFFER,o->buffer);
 glEnableVertexAttribArray(0);glVertexAttribPointer(0,2,GL_FLOAT,GL_FALSE,24,0);glEnableVertexAttribArray(1);glVertexAttribPointer(1,4,GL_FLOAT,GL_FALSE,24,(void*)8);glBindVertexArray(0);return glGetError()==GL_NO_ERROR;
}
void exploration_overlay_close(exploration_overlay *o){if(o->buffer)glDeleteBuffers(1,&o->buffer);if(o->array)glDeleteVertexArrays(1,&o->array);if(o->program)glDeleteProgram(o->program);free(o->vertices);memset(o,0,sizeof(*o));}
static void point(exploration_overlay *o,float x,float y,const float c[4]){if(o->count+6>OVERLAY_FLOATS)return;o->vertices[o->count++]=x;o->vertices[o->count++]=y;memcpy(o->vertices+o->count,c,16);o->count+=4;}
static void rect(exploration_overlay *o,float x,float y,float w,float h,const float c[4]){if(o->count+36>OVERLAY_FLOATS)return;point(o,x,y,c);point(o,x+w,y,c);point(o,x+w,y+h,c);point(o,x,y,c);point(o,x+w,y+h,c);point(o,x,y+h,c);}
static const unsigned char glyphs[26][7]={
 {14,17,17,31,17,17,17},{30,17,17,30,17,17,30},{14,17,16,16,16,17,14},{30,17,17,17,17,17,30},{31,16,16,30,16,16,31},{31,16,16,30,16,16,16},
 {14,17,16,23,17,17,15},{17,17,17,31,17,17,17},{31,4,4,4,4,4,31},{7,2,2,2,18,18,12},{17,18,20,24,20,18,17},{16,16,16,16,16,16,31},
 {17,27,21,21,17,17,17},{17,25,21,19,17,17,17},{14,17,17,17,17,17,14},{30,17,17,30,16,16,16},{14,17,17,17,21,18,13},{30,17,17,30,20,18,17},
 {15,16,16,14,1,1,30},{31,4,4,4,4,4,4},{17,17,17,17,17,17,14},{17,17,17,17,17,10,4},{17,17,17,21,21,21,10},{17,17,10,4,10,17,17},{17,17,10,4,4,4,4},{31,1,2,4,8,16,31}};
static const unsigned char digits[10][7]={{14,17,19,21,25,17,14},{4,12,4,4,4,4,14},{14,17,1,2,4,8,31},{30,1,1,14,1,1,30},{2,6,10,18,31,2,2},{31,16,16,30,1,1,30},{14,16,16,30,17,17,14},{31,1,2,4,8,8,8},{14,17,17,14,17,17,14},{14,17,17,15,1,1,14}};
static void text(exploration_overlay *o,float x,float y,float size,const char *s,const float c[4]){for(;*s;s++,x+=size*6){int row,col;unsigned char ch=(unsigned char)toupper((unsigned char)*s);const unsigned char *g=NULL;if(ch>='A'&&ch<='Z')g=glyphs[ch-'A'];else if(ch>='0'&&ch<='9')g=digits[ch-'0'];if(g)for(row=0;row<7;row++)for(col=0;col<5;col++)if(g[row]&(16>>col))rect(o,x+col*size,y+row*size,size,size,c);if(ch=='-'||ch=='_')rect(o,x,y+(ch=='-'?3:6)*size,5*size,size,c);if(ch==':'){rect(o,x+2*size,y+2*size,size,size,c);rect(o,x+2*size,y+5*size,size,size,c);}if(ch=='/')for(row=0;row<7;row++)rect(o,x+(4-row*4/6)*size,y+row*size,size,size,c);}}
static void submit(exploration_overlay *o,int w,int h){glDisable(GL_DEPTH_TEST);glEnable(GL_BLEND);glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA);glUseProgram(o->program);glUniform2f(o->screen,(float)w,(float)h);glBindVertexArray(o->array);glBindBuffer(GL_ARRAY_BUFFER,o->buffer);glBufferData(GL_ARRAY_BUFFER,o->count*sizeof(float),o->vertices,GL_STREAM_DRAW);glDrawArrays(GL_TRIANGLES,0,(GLsizei)(o->count/6));glBindVertexArray(0);glDisable(GL_BLEND);glEnable(GL_DEPTH_TEST);}
static void alchemy(exploration_overlay *o,int w,int h,const oa_interaction *a){
 const float white[4]={.95f,.97f,1,1},dark[4]={.02f,.035f,.05f,.97f},blue[4]={.12f,.25f,.33f,1},dim[4]={.6f,.7f,.75f,1},gold[4]={1,.8f,.4f,1};float s=exploration_ui_scale(w,h);char b[160];int row;size_t total=a->tab?a->catalog.formula_count:a->catalog.reagent_count;
 rect(o,12*s,12*s,w-24*s,h-24*s,dark);text(o,32*s,28*s,3*s,"ALCHEMY WORKBENCH",gold);rect(o,w-140*s,20*s,108*s,36*s,blue);text(o,w-128*s,30*s,2*s,"CLOSE",white);
 text(o,32*s,61*s,1.5f*s,"ANDROID PROTOTYPE INVENTORY - NO NATIVE SAVE IMPORT",dim);
 rect(o,32*s,88*s,220*s,36*s,a->tab?dark:blue);text(o,44*s,100*s,2*s,"REAGENTS",white);rect(o,264*s,88*s,220*s,36*s,a->tab?blue:dark);text(o,276*s,100*s,2*s,"RECIPE CATALOG",white);
 snprintf(b,sizeof(b),"ALCHEMY SKILL %u   INVENTORY %u ITEMS",a->inventory.alchemy_skill,a->inventory.count);text(o,32*s,137*s,1.7f*s,b,white);
 for(row=0;row<6;row++){size_t idx=(size_t)a->page*6+(unsigned)row;float y=(169+row*37)*s;if(idx>=total)break;
  if(a->tab){const oa_formula *f=a->catalog.formulas+idx;if((int)idx==a->recipe_selected)rect(o,28*s,y-6*s,w-56*s,33*s,blue);snprintf(b,sizeof(b),"%.44s  OWNED %u",f->symbol,oa_inventory_count(&a->inventory,f->id));}
  else{const oa_reagent *r=a->catalog.reagents+idx;snprintf(b,sizeof(b),"%.36s  COUNT %u",r->symbol,oa_inventory_count(&a->inventory,r->id));}
  text(o,40*s,y,1.7f*s,b,white);
 }
 text(o,32*s,h-134*s,1.5f*s,a->status,gold);
 rect(o,32*s,h-100*s,140*s,42*s,blue);text(o,46*s,h-85*s,2*s,"PREV",white);snprintf(b,sizeof(b),"PAGE %u OF %u",a->page+1,(unsigned)((total+5)/6));text(o,190*s,h-85*s,1.7f*s,b,white);
 rect(o,390*s,h-100*s,140*s,42*s,blue);text(o,404*s,h-85*s,2*s,"NEXT",white);
 if(a->tab){rect(o,w-240*s,h-100*s,208*s,42*s,blue);text(o,w-225*s,h-85*s,2*s,"CRAFT UNAVAILABLE",white);}
 text(o,32*s,h-42*s,1.5f*s,"CATALOG ENTRIES ARE NOT OWNED RECIPES - B TO CLOSE",dim);
}
static void disk(exploration_overlay *o,float x,float y,float radius,const float c[4]){int i;for(i=0;i<32;i++){float a=i*.19634954f,b=(i+1)*.19634954f;if(o->count+18>OVERLAY_FLOATS)return;point(o,x,y,c);point(o,x+radius*cosf(a),y+radius*sinf(a),c);point(o,x+radius*cosf(b),y+radius*sinf(b),c);}}
void exploration_overlay_draw(exploration_overlay *o,int w,int h,const exploration_input *in,int walking,int collision_ready,const oa_interaction *interaction,int room_lighting,const char *door_prompt,const float *health){
 const float white[4]={.95f,.97f,1,1},dark[4]={.025f,.04f,.06f,.8f},muted[4]={.45f,.65f,.8f,.3f},knob[4]={.7f,.85f,1,.65f};float s=exploration_ui_scale(w,h),x,y;
 if(!o->program||w<=0||h<=0)return;o->count=0;
 if(interaction&&interaction->window_open){alchemy(o,w,h,interaction);submit(o,w,h);return;}
 if(interaction&&interaction->ready&&oa_object_resolve(&interaction->registry,interaction->selected)){rect(o,w*.5f-160*s,h-112*s,320*s,52*s,dark);text(o,w*.5f-148*s,h-94*s,2*s,"ALCHEMY - INTERACT",white);}
else if(door_prompt){rect(o,w*.5f-160*s,h-112*s,320*s,52*s,dark);text(o,w*.5f-148*s,h-94*s,2*s,door_prompt,white);}
 /* health: player fraction, enemy fraction or negative to hide, message flag. */
 if(health){const float red[4]={.78f,.13f,.13f,.95f},orange[4]={.85f,.45f,.1f,.95f};
  rect(o,135*s,14*s,300*s,20*s,dark);rect(o,139*s,18*s,292*s*health[0],12*s,red);
  if(health[1]>=0){rect(o,135*s,40*s,240*s,16*s,dark);rect(o,139*s,43*s,232*s*health[1],10*s,orange);}
  rect(o,w-180*s,h-205*s,168*s,90*s,dark);text(o,w-162*s,h-170*s,2*s,"ATTACK",white);
  if(health[2]>0){rect(o,w*.5f-140*s,h*.4f,280*s,52*s,dark);text(o,w*.5f-124*s,h*.4f+18*s,2*s,"YOU HAVE FALLEN",white);}}
 rect(o,12*s,12*s,(collision_ready?110:310)*s,44*s,dark);text(o,24*s,27*s,2*s,collision_ready?(walking?"WALK":"OVERVIEW"):"MOVEMENT UNAVAILABLE",white);
 rect(o,w-400*s,12*s,128*s,44*s,dark);text(o,w-388*s,27*s,2*s,room_lighting?"ROOM":"PREVIEW",white);
 rect(o,w-260*s,12*s,112*s,44*s,dark);text(o,w-248*s,27*s,2*s,"RESET",white);
 rect(o,w-140*s,12*s,128*s,44*s,dark);text(o,w-128*s,27*s,2*s,"VIEW",white);
 rect(o,12*s,h-44*s,112*s,32*s,dark);text(o,24*s,h-35*s,2*s,"MOVE",white);rect(o,w-124*s,h-44*s,112*s,32*s,dark);text(o,w-112*s,h-35*s,2*s,"LOOK",white);
 x=in->move_id>=0?in->move_origin_x:100*s;y=in->move_id>=0?in->move_origin_y:h-140*s;
 disk(o,x,y,70*s,muted);disk(o,x+in->move_x*70*s,y-in->move_y*70*s,22*s,knob);
 if(walking){rect(o,w*.5f-5*s,h*.5f-s,10*s,2*s,white);rect(o,w*.5f-s,h*.5f-5*s,2*s,10*s,white);}
 submit(o,w,h);
}
