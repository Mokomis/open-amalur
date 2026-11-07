#include "oa_menu.h"
#include "oa_creation_draft.h"
#include "oa_creation_gameplay.h"
static void creation_begin_edit(oa_menu *m);
static void creation_begin_new(oa_menu *m);
static int creation_name_key(oa_menu *m,int key,int down);
#include "android_input_probe.h"
#include <android/keycodes.h>
#include <math.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>
/* Design units are 1/840 of screen height, so a 3:2 tablet is 1260 wide. */
#define SCALE(h) ((float)(h)/840.0f)
static const struct{const char *name;float w,h,x,y;int on;}HUD[OA_HUD_COUNT]={
 {"Compass",560,58,.5f,.056f,1},{"Location",240,54,.105f,.056f,1},{"Health",380,20,.5f,.958f,1},{"Mana and Fate",380,10,.5f,.928f,0},{"Enemy",460,50,.5f,.142f,1},
 {"Prompt",320,48,.5f,.86f,1},{"Move Stick",150,150,.1f,.82f,1},{"Attack",116,116,.925f,.84f,1},{"Menu Button",60,60,.958f,.06f,1},{"Crosshair",24,24,.5f,.5f,0}};
static const int RATES[5]={0,60,90,120,144};
static const float PAPER[4]={.937f,.902f,.824f,1},DIM[4]={.84f,.81f,.73f,1},GOLD[4]={.902f,.812f,.58f,1},LINE[4]={.788f,.655f,.396f,.75f},SHADE[4]={.024f,.031f,.035f,.72f},CLEAR[4]={.024f,.031f,.035f,0},GLOW[4]={.788f,.655f,.396f,.3f},GLOW0[4]={.788f,.655f,.396f,0};
const char *oa_hud_name(int i){return i>=0&&i<OA_HUD_COUNT?HUD[i].name:"";}
static float clampf_(float v,float a,float b){return !isfinite(v)?a:v<a?a:v>b?b:v;}
void oa_settings_default(oa_settings *s){int i;memset(s,0,sizeof(*s));for(i=0;i<OA_HUD_COUNT;i++){s->hud[i].on=HUD[i].on;s->hud[i].scale=1;s->hud[i].x=HUD[i].x;s->hud[i].y=HUD[i].y;}s->opacity=1;s->look_speed=1;s->shadows=1;s->canopy_dense=0;}
void oa_settings_sanitize(oa_settings *s){int i;for(i=0;i<OA_HUD_COUNT;i++){s->hud[i].on=!!s->hud[i].on;s->hud[i].scale=clampf_(s->hud[i].scale,.5f,2);s->hud[i].x=clampf_(s->hud[i].x,0,1);s->hud[i].y=clampf_(s->hud[i].y,0,1);}
 s->opacity=clampf_(s->opacity,.3f,1);s->look_speed=clampf_(s->look_speed,.25f,3);s->invert_look=!!s->invert_look;s->shadows=!!s->shadows;s->canopy_dense=!!s->canopy_dense;if(s->rate<0||s->rate>4)s->rate=0;}
static const char SET_MAGIC[8]={'O','A','S','E','T','0','0','2'},SAVE_MAGIC[8]={'O','A','S','A','V','0','0','2'};
int oa_settings_save(const oa_settings *s,const char *path){FILE *f=fopen(path,"wb");int ok;if(!f)return 0;ok=fwrite(SET_MAGIC,8,1,f)==1&&fwrite(s,sizeof(*s),1,f)==1;return fclose(f)==0&&ok;}
int oa_settings_load(oa_settings *s,const char *path){FILE *f=fopen(path,"rb");char magic[8];oa_settings t;int ok;size_t bytes=0;oa_settings_default(s);if(!f)return 0;oa_settings_default(&t);
 /* Keep OASET002 and its existing prefix: older readers ignore appended fields.
  * Legacy files stop before shadows (184B file) or canopy_dense (188B file).
  * Default missing fields before reading so existing HUD/look/rate choices survive. */
 ok=fread(magic,8,1,f)==1&&!memcmp(magic,SET_MAGIC,8);if(ok){bytes=fread(&t,1,sizeof(t),f);ok=!ferror(f)&&(bytes==offsetof(oa_settings,shadows)||bytes==offsetof(oa_settings,canopy_dense)||bytes==sizeof(t));if(ok)ok=fgetc(f)==EOF&&!ferror(f);}fclose(f);if(!ok)return 0;*s=t;oa_settings_sanitize(s);return 1;}
int oa_save_write(const oa_save *save,const char *path){oa_save t=*save;FILE *f;int ok;if(t.space>0x0fffffffu)return 0;memcpy(t.magic,SAVE_MAGIC,8);f=fopen(path,"wb");if(!f)return 0;ok=fwrite(&t,sizeof(t),1,f)==1;return fclose(f)==0&&ok;}
int oa_save_read(oa_save *save,const char *path){FILE *f=fopen(path,"rb");oa_save t;size_t bytes;int ok,i;if(!f)return 0;memset(&t,0,sizeof(t));bytes=fread(&t,1,sizeof(t),f);ok=!ferror(f)&&(bytes==offsetof(oa_save,space)||bytes==sizeof(t));if(ok)ok=fgetc(f)==EOF&&!ferror(f);fclose(f);if(!ok||memcmp(t.magic,SAVE_MAGIC,8)||t.world<0||t.world>1||t.space>0x0fffffffu)return 0;for(i=0;i<3;i++)if(!isfinite(t.feet[i]))return 0;if(!isfinite(t.yaw)||!isfinite(t.pitch)||!isfinite(t.health))return 0;oa_bag_sanitize(&t.bag);*save=t;return 1;}
void oa_menu_init(oa_menu *m,const char *dir,int start_in_game){oa_save probe;memset(m,0,sizeof(*m));m->pointer_id=-1;snprintf(m->settings_path,sizeof(m->settings_path),"%s/opem-settings-v1.bin",dir);snprintf(m->save_path,sizeof(m->save_path),"%s/opem-save-v1.bin",dir);
 snprintf(m->creation_path,sizeof m->creation_path,"%s/wellofsouls.creator-draft-v1.bin",dir);
 oa_settings_load(&m->settings,m->settings_path);m->has_save=oa_save_read(&probe,m->save_path);m->screen=start_in_game?OA_SCREEN_GAME:OA_SCREEN_TITLE;m->from=OA_SCREEN_TITLE;oa_bag_new(&m->bag);m->inv_sort=1;m->inv_dir=-1;}
void oa_menu_open(oa_menu *m,oa_screen s){if(s==OA_SCREEN_OPTIONS&&m->screen!=OA_SCREEN_LAYOUT)m->from=m->screen;if(s==OA_SCREEN_INVENTORY){m->inv_from=m->screen;m->inv_row=0;m->inv_scroll=0;}m->screen=s;m->focus=0;m->count=0;m->pointer_down=m->pressed=m->released=0;m->pointer_id=-1;m->dragging=0;m->mouse_look=0;m->selected=0;}
int oa_menu_rate(const oa_menu *m){return RATES[m->settings.rate];}
int oa_menu_canopy_dense(const oa_menu *m){return m?!!m->settings.canopy_dense:0;}
void oa_menu_status(oa_menu *m,const char *t){m->status=t;m->status_time=2.5f;}
void oa_hud_rect(const oa_menu *m,int i,int w,int h,float r[4]){float s=SCALE(h)*m->settings.hud[i].scale;r[2]=HUD[i].w*s;r[3]=HUD[i].h*s;r[0]=m->settings.hud[i].x*w-r[2]*.5f;r[1]=m->settings.hud[i].y*h-r[3]*.5f;}
static int inside(const float r[4],float x,float y){return x>=r[0]&&y>=r[1]&&x<r[0]+r[2]&&y<r[1]+r[3];}
static void pointer(oa_menu *m,AInputEvent *e,int mouse){
 int raw=AMotionEvent_getAction(e),action=raw&AMOTION_EVENT_ACTION_MASK;size_t index=(unsigned)raw>>AMOTION_EVENT_ACTION_POINTER_INDEX_SHIFT,count=AMotionEvent_getPointerCount(e),i;
 m->device=mouse?OA_DEVICE_KEYBOARD:OA_DEVICE_TOUCH;if(!count)return;
 if(action==AMOTION_EVENT_ACTION_CANCEL){m->pointer_down=0;m->pointer_id=-1;m->dragging=0;return;}
 if(index>=count)index=0;
 if((action==AMOTION_EVENT_ACTION_DOWN||action==AMOTION_EVENT_ACTION_POINTER_DOWN)&&m->pointer_id<0){float x=AMotionEvent_getX(e,index),y=AMotionEvent_getY(e,index);if(!isfinite(x)||!isfinite(y))return;m->pointer_id=AMotionEvent_getPointerId(e,index);m->pointer_down=m->pressed=1;m->px=m->press_x=m->last_x=x;m->py=m->press_y=m->last_y=y;return;}
 if(action==AMOTION_EVENT_ACTION_UP||action==AMOTION_EVENT_ACTION_POINTER_UP){if(AMotionEvent_getPointerId(e,index)==m->pointer_id){float x=AMotionEvent_getX(e,index),y=AMotionEvent_getY(e,index);if(isfinite(x)&&isfinite(y)){m->px=x;m->py=y;}m->pointer_down=0;m->released=1;m->pointer_id=-1;}return;}
 if(action==AMOTION_EVENT_ACTION_MOVE){for(i=0;i<count;i++)if(AMotionEvent_getPointerId(e,i)==m->pointer_id){float x=AMotionEvent_getX(e,i),y=AMotionEvent_getY(e,i);if(isfinite(x)&&isfinite(y)){m->px=x;m->py=y;}}return;}
 if(mouse&&action==AMOTION_EVENT_ACTION_HOVER_MOVE){float x=AMotionEvent_getX(e,0),y=AMotionEvent_getY(e,0);if(isfinite(x)&&isfinite(y)){m->px=x;m->py=y;m->hovered=1;}return;}
 if(mouse&&action==AMOTION_EVENT_ACTION_SCROLL){float v=AMotionEvent_getAxisValue(e,AMOTION_EVENT_AXIS_VSCROLL,0);if(isfinite(v))m->wheel+=v;}
}
static float stick(float v){return isfinite(v)?v:0;}
/* Takes held-key state for moving a HUD element in the layout screen: 1 W, 2 S, 4 A, 8 D. */
static int key_event(oa_menu *m,int key,int down,int repeat){
 unsigned bit=0;
 if(m->screen==OA_SCREEN_CREATION_NAME&&m->device==OA_DEVICE_KEYBOARD&&creation_name_key(m,key,down))return 1;
 switch(key){case AKEYCODE_W:bit=1;break;case AKEYCODE_S:bit=2;break;case AKEYCODE_A:bit=4;break;case AKEYCODE_D:bit=8;break;default:break;}
 if(bit&&m->screen==OA_SCREEN_LAYOUT){if(down)m->keys_move|=(int)bit;else m->keys_move&=~(int)bit;return 1;}
 if(!down)return key==AKEYCODE_DPAD_UP||key==AKEYCODE_DPAD_DOWN||key==AKEYCODE_DPAD_LEFT||key==AKEYCODE_DPAD_RIGHT||key==AKEYCODE_ENTER||key==AKEYCODE_SPACE||key==AKEYCODE_BUTTON_A||key==AKEYCODE_BUTTON_B||key==AKEYCODE_BACK||key==AKEYCODE_ESCAPE;
 switch(key){
  case AKEYCODE_BUTTON_L1:case AKEYCODE_Q:m->tab_step=-1;return 1;
  case AKEYCODE_BUTTON_R1:case AKEYCODE_E:case AKEYCODE_TAB:m->tab_step=1;return 1;
  case AKEYCODE_BUTTON_Y:case AKEYCODE_X:if(!repeat)m->sort_step=1;return 1;
  case AKEYCODE_DPAD_UP:case AKEYCODE_W:m->nav_y=-1;return 1;
  case AKEYCODE_DPAD_DOWN:case AKEYCODE_S:m->nav_y=1;return 1;
  case AKEYCODE_DPAD_LEFT:case AKEYCODE_MINUS:m->nav_x=-1;return 1;
  case AKEYCODE_DPAD_RIGHT:case AKEYCODE_EQUALS:case AKEYCODE_PLUS:m->nav_x=1;return 1;
  case AKEYCODE_ENTER:case AKEYCODE_SPACE:case AKEYCODE_DPAD_CENTER:case AKEYCODE_BUTTON_A:if(!repeat)m->accept=1;return 1;
  case AKEYCODE_BACK:case AKEYCODE_ESCAPE:case AKEYCODE_BUTTON_B:case AKEYCODE_BUTTON_START:case AKEYCODE_MENU:if(!repeat)m->back=1;return 1;
  case AKEYCODE_BUTTON_X:if(!repeat)m->reset=1;return 1;
  default:return 1;}
}
int oa_menu_event(oa_menu *m,AInputEvent *e,int w,int h,exploration_input *play){
 enum opem_input_family family=opem_android_event_family(e);int type=AInputEvent_getType(e);
 if(type==AINPUT_EVENT_TYPE_KEY){int key=AKeyEvent_getKeyCode(e),down=AKeyEvent_getAction(e)==AKEY_EVENT_ACTION_DOWN,repeat=AKeyEvent_getRepeatCount(e);
  if(AKeyEvent_getFlags(e)&AKEY_EVENT_FLAG_CANCELED)return 0;
  if(family==OPEM_INPUT_GAMEPAD)m->device=OA_DEVICE_PAD;else m->device=key==AKEYCODE_BACK?m->device:OA_DEVICE_KEYBOARD;
  if(m->screen!=OA_SCREEN_GAME)return key_event(m,key,down,repeat);
  switch(key){
   case AKEYCODE_BACK:case AKEYCODE_ESCAPE:case AKEYCODE_BUTTON_START:case AKEYCODE_MENU:if(down&&!repeat)oa_menu_open(m,OA_SCREEN_PAUSE);return 1;
   case AKEYCODE_BUTTON_SELECT:case AKEYCODE_I:if(down&&!repeat)oa_menu_open(m,OA_SCREEN_INVENTORY);return 1;
   case AKEYCODE_BUTTON_R1:case AKEYCODE_BUTTON_R2:if(down&&!repeat)play->attack_requested=1;return 1;
   /* Comparison and debug bindings now live in Options. */
   case AKEYCODE_BUTTON_Y:case AKEYCODE_L:case AKEYCODE_R:case AKEYCODE_V:return 1;
   default:return 0;}
 }
 if(type!=AINPUT_EVENT_TYPE_MOTION)return 0;
 if(family==OPEM_INPUT_JOYSTICK){int action=AMotionEvent_getAction(e)&AMOTION_EVENT_ACTION_MASK;float x=stick(AMotionEvent_getAxisValue(e,AMOTION_EVENT_AXIS_X,0)),y=stick(AMotionEvent_getAxisValue(e,AMOTION_EVENT_AXIS_Y,0)),hx=stick(AMotionEvent_getAxisValue(e,AMOTION_EVENT_AXIS_HAT_X,0)),hy=stick(AMotionEvent_getAxisValue(e,AMOTION_EVENT_AXIS_HAT_Y,0)),rt=stick(AMotionEvent_getAxisValue(e,AMOTION_EVENT_AXIS_RTRIGGER,0)),gas=stick(AMotionEvent_getAxisValue(e,AMOTION_EVENT_AXIS_GAS,0));
  m->device=OA_DEVICE_PAD;
  if(action==AMOTION_EVENT_ACTION_CANCEL){m->axis_x=m->axis_y=m->hat_x=m->hat_y=0;return m->screen!=OA_SCREEN_GAME;}
  m->axis_x=x;m->axis_y=y;m->hat_x=hx;m->hat_y=hy;
  if(m->screen==OA_SCREEN_GAME){int held=rt>.5f||gas>.5f;if(held&&!m->trigger)play->attack_requested=1;m->trigger=held;return 0;}
  return 1;}
 if(family==OPEM_INPUT_MOUSE){int action=AMotionEvent_getAction(e)&AMOTION_EVENT_ACTION_MASK;
  if(m->screen!=OA_SCREEN_GAME){pointer(m,e,1);return 1;}
  {int buttons=AMotionEvent_getButtonState(e);float x=AMotionEvent_getX(e,0),y=AMotionEvent_getY(e,0);float menu[4];if(!isfinite(x)||!isfinite(y))return 1;m->device=OA_DEVICE_KEYBOARD;
   /* Some mice and injected taps report no button on press. */
   if(action==AMOTION_EVENT_ACTION_DOWN&&(!buttons||(buttons&AMOTION_EVENT_BUTTON_PRIMARY))){oa_hud_rect(m,OA_HUD_MENU,w,h,menu);if(m->settings.hud[OA_HUD_MENU].on&&inside(menu,x,y))oa_menu_open(m,OA_SCREEN_PAUSE);else play->attack_requested=1;}
   /* NativeActivity has no pointer capture, so looking holds the right button. */
   if(action==AMOTION_EVENT_ACTION_DOWN&&(buttons&AMOTION_EVENT_BUTTON_SECONDARY)){m->mouse_look=1;m->last_x=x;m->last_y=y;}
   else if(action==AMOTION_EVENT_ACTION_MOVE&&m->mouse_look&&w>0&&h>0){play->look_dx+=(x-m->last_x)/(float)w*3;play->look_dy+=(y-m->last_y)/(float)h*2;m->last_x=x;m->last_y=y;}
   else if(action==AMOTION_EVENT_ACTION_UP||!(buttons&AMOTION_EVENT_BUTTON_SECONDARY))m->mouse_look=0;}
  return 1;}
 if(family==OPEM_INPUT_TOUCH&&m->screen!=OA_SCREEN_GAME){pointer(m,e,0);return 1;}
 return 0;
}
/* Widgets */
typedef struct frame{oa_menu *m;oa_ui *u;int w,h;float s;int next;}frame;
static int axis_nav(float value){return fabsf(value)>.6f?(value>0?1:-1):0;}
static int widget(frame *f,const float r[4]){oa_menu *m=f->m;int id=f->next++,hit;
 if(m->hovered&&inside(r,m->px,m->py)&&m->screen!=OA_SCREEN_LAYOUT)m->focus=id;
 hit=m->released&&inside(r,m->px,m->py)&&inside(r,m->press_x,m->press_y);
 if(hit){m->focus=id;return 1;}
 return m->accept&&m->focus==id;}
static int focused(const frame *f,int id){return f->m->focus==id;}
static int show_focus(const oa_menu *m){return m->device!=OA_DEVICE_TOUCH;}
static void highlight(frame *f,float x,float y,float w,float h){float s=f->s;oa_ui_fade(f->u,x,y,w,h,GLOW,GLOW0);oa_ui_rect(f->u,x,y,2*s,h,GOLD);}
static int menu_row(frame *f,float x,float y,float w,float h,float px,const char *label,int primary){float r[4];int id=f->next,hit;r[0]=x;r[1]=y;r[2]=w;r[3]=h;hit=widget(f,r);
 if(primary||(focused(f,id)&&show_focus(f->m)))highlight(f,x,y,w,h);
 oa_ui_text(f->u,OA_FONT_HEAD,x+20*f->s,y+(h-px*f->s*1.3f)*.5f,px*f->s,OA_ALIGN_LEFT,focused(f,id)&&show_focus(f->m)?PAPER:primary?PAPER:DIM,label);return hit;}
static void hint(frame *f,const char *touch,const char *pad,const char *keys){const char *t=f->m->device==OA_DEVICE_PAD?pad:f->m->device==OA_DEVICE_KEYBOARD?keys:touch;if(t&&*t)oa_ui_text(f->u,OA_FONT_BODY,f->w*.5f,f->h-44*f->s,19*f->s,OA_ALIGN_CENTER,DIM,t);}
static void text_shadowed(frame *f,int font,float x,float y,float px,int align,const float c[4],const char *t,float alpha){float k[4]={.02f,.02f,.02f,.75f*alpha},d[4];d[0]=c[0];d[1]=c[1];d[2]=c[2];d[3]=c[3]*alpha;oa_ui_text(f->u,font,x+f->s*1.2f,y+f->s*1.4f,px,align,k,t);oa_ui_text(f->u,font,x,y,px,align,d,t);}
/* HUD elements draw inside their configured rectangle, so size and place come from the settings alone. */
static void draw_compass(frame *f,const float r[4],const oa_hud_view *v,float a){
 static const struct{float angle;const char *label;}MARKS[8]={{0,"N"},{.7853982f,"NE"},{1.570796f,"E"},{2.356194f,"SE"},{3.141593f,"S"},{-2.356194f,"SW"},{-1.570796f,"W"},{-.7853982f,"NW"}};
 float k=r[3]/58.f,cx=r[0]+r[2]*.5f,y=r[1]+r[3]*.52f,half=r[2]*.5f,heading=1.570796f-v->yaw;int i;float line0[4]={LINE[0],LINE[1],LINE[2],0},line1[4]={LINE[0],LINE[1],LINE[2],LINE[3]*a};
 oa_ui_fade(f->u,r[0],y,half,1.5f*k,line0,line1);oa_ui_fade(f->u,cx,y,half,1.5f*k,line1,line0);
 for(i=-12;i<=12;i++){float off=i*.1308997f,base=remainderf(off-remainderf(heading,.1308997f),6.283185f),x=cx+base/1.570796f*half;float tick[4]={PAPER[0],PAPER[1],PAPER[2],.5f*a};if(fabsf(base)<1.45f)oa_ui_rect(f->u,x,y-4*k,1*k,9*k,tick);}
 for(i=0;i<8;i++){float d=remainderf(MARKS[i].angle-heading,6.283185f);if(fabsf(d)<1.5f){int cardinal=!(i&1);text_shadowed(f,OA_FONT_HEAD,cx+d/1.570796f*half,y-(cardinal?27:22)*k,(cardinal?17:12)*k,OA_ALIGN_CENTER,!i?GOLD:DIM,MARKS[i].label,a);}}
 if(v->has_target){float dx=v->target_x-v->feet_x,dy=v->target_y-v->feet_y,d=remainderf(atan2f(dx,dy)-heading,6.283185f),x=cx+clampf_(d/1.570796f,-1,1)*half;char b[32];float c[4]={1,1,1,a};oa_ui_sprite(f->u,OA_SPR_DIAMOND,x-10*k,y-9*k,20*k,18*k,1,c);snprintf(b,sizeof(b),"%d m",(int)(sqrtf(dx*dx+dy*dy)/100.f+.5f));text_shadowed(f,OA_FONT_BODY,x,y+9*k,14*k,OA_ALIGN_CENTER,PAPER,b,a);}
}
static void bar(frame *f,const float r[4],int sprite,float fraction,const float back[4],float a){float c[4]={1,1,1,a},edge[4]={LINE[0],LINE[1],LINE[2],LINE[3]*a},b[4]={back[0],back[1],back[2],back[3]*a};float t=fmaxf(1,f->s);
 oa_ui_rect(f->u,r[0],r[1],r[2],r[3],b);oa_ui_sprite(f->u,sprite,r[0]+t,r[1]+t,r[2]-2*t,r[3]-2*t,fraction,c);
 oa_ui_rect(f->u,r[0],r[1],r[2],t,edge);oa_ui_rect(f->u,r[0],r[1]+r[3]-t,r[2],t,edge);oa_ui_rect(f->u,r[0],r[1],t,r[3],edge);oa_ui_rect(f->u,r[0]+r[2]-t,r[1],t,r[3],edge);}
static void draw_item(frame *f,int i,const float r[4],const oa_hud_view *v,float a,int sample){
 const float dark[4]={.024f,.031f,.035f,.78f};float k=r[3]/HUD[i].h;float edge[4]={LINE[0],LINE[1],LINE[2],LINE[3]*a},fill[4]={.03f,.04f,.043f,.44f*a},soft[4]={PAPER[0],PAPER[1],PAPER[2],.36f*a},white[4]={1,1,1,a};
 switch(i){
  case OA_HUD_COMPASS:draw_compass(f,r,v,a);break;
  case OA_HUD_LOCATION:if(v->location){text_shadowed(f,OA_FONT_HEAD,r[0],r[1]+4*k,22*k,OA_ALIGN_LEFT,PAPER,v->location,a);text_shadowed(f,OA_FONT_BODY,r[0],r[1]+30*k,16*k,OA_ALIGN_LEFT,DIM,v->zone?v->zone:"",a);}break;
  case OA_HUD_HEALTH:bar(f,r,OA_SPR_HEALTH,v->health,dark,a);break;
  case OA_HUD_RESOURCES:{float l[4]={r[0],r[1],r[2]*.49f,r[3]},q[4]={r[0]+r[2]*.51f,r[1],r[2]*.49f,r[3]};bar(f,l,OA_SPR_MANA,1,dark,a);bar(f,q,OA_SPR_FATE,0,dark,a);break;}
  case OA_HUD_ENEMY:if(v->foe>=0||sample){float q[4]={r[0],r[1]+30*k,r[2],r[3]-30*k};const char *foe_name=v->foe_name?v->foe_name:"Bandit";float t=oa_ui_measure(f->u,OA_FONT_HEAD,19*k,foe_name);oa_ui_sprite(f->u,OA_SPR_SKULL,r[0]+r[2]*.5f-t*.5f-30*k,r[1]+1*k,22*k,24*k,1,white);text_shadowed(f,OA_FONT_HEAD,r[0]+r[2]*.5f,r[1],19*k,OA_ALIGN_CENTER,PAPER,foe_name,a);bar(f,q,OA_SPR_HEALTH,v->foe>=0?v->foe:.6f,dark,a);}break;
  case OA_HUD_PROMPT:if(v->prompt||sample){float b[4]={SHADE[0],SHADE[1],SHADE[2],SHADE[3]*a},c0[4]={CLEAR[0],CLEAR[1],CLEAR[2],0},l0[4]={LINE[0],LINE[1],LINE[2],0};float q=r[2]*.2f;const char *t=v->prompt?v->prompt:"Enter Shop";
    oa_ui_fade(f->u,r[0],r[1],q,r[3],c0,b);oa_ui_rect(f->u,r[0]+q,r[1],r[2]-2*q,r[3],b);oa_ui_fade(f->u,r[0]+r[2]-q,r[1],q,r[3],b,c0);
    oa_ui_fade(f->u,r[0],r[1],q,1,l0,edge);oa_ui_rect(f->u,r[0]+q,r[1],r[2]-2*q,1,edge);oa_ui_fade(f->u,r[0]+r[2]-q,r[1],q,1,edge,l0);oa_ui_fade(f->u,r[0],r[1]+r[3],q,1,l0,edge);oa_ui_rect(f->u,r[0]+q,r[1]+r[3],r[2]-2*q,1,edge);oa_ui_fade(f->u,r[0]+r[2]-q,r[1]+r[3],q,1,edge,l0);
    oa_ui_text(f->u,OA_FONT_HEAD,r[0]+r[2]*.5f,r[1]+r[3]*.5f-11*k,16*k,OA_ALIGN_CENTER,white,t);}break;
  case OA_HUD_STICK:{float R=r[2]*.5f,x=r[0]+R,y=r[1]+R;if(v->move_active){x=v->move_origin_x;y=v->move_origin_y;}oa_ui_ring(f->u,x,y,R,1.5f*k,soft);{float knob[4]={PAPER[0],PAPER[1],PAPER[2],.2f*a};oa_ui_disk(f->u,x+v->move_x*R,y-v->move_y*R,R*.36f,knob);oa_ui_ring(f->u,x+v->move_x*R,y-v->move_y*R,R*.36f,1.2f*k,soft);}break;}
  case OA_HUD_ATTACK:{float R=r[2]*.5f;oa_ui_disk(f->u,r[0]+R,r[1]+R,R,fill);oa_ui_ring(f->u,r[0]+R,r[1]+R,R,1.8f*k,edge);oa_ui_sprite(f->u,OA_SPR_SWORDS,r[0]+R-R*.62f,r[1]+R-R*.62f,R*1.24f,R*1.24f,1,white);break;}
  case OA_HUD_MENU:{float R=r[2]*.5f,w=R*.8f,cx=r[0]+R,cy=r[1]+R,t=fmaxf(1,1.6f*k);oa_ui_disk(f->u,cx,cy,R,fill);oa_ui_ring(f->u,cx,cy,R,1.4f*k,edge);oa_ui_rect(f->u,cx-w*.5f,cy-R*.34f,w,t,edge);oa_ui_rect(f->u,cx-w*.5f,cy,w,t,edge);oa_ui_rect(f->u,cx-w*.5f,cy+R*.34f,w,t,edge);break;}
  case OA_HUD_CROSSHAIR:{float cx=r[0]+r[2]*.5f,cy=r[1]+r[3]*.5f,t=fmaxf(1,1.5f*k);oa_ui_rect(f->u,cx-r[2]*.3f,cy-t*.5f,r[2]*.6f,t,white);oa_ui_rect(f->u,cx-t*.5f,cy-r[3]*.3f,t,r[3]*.6f,white);break;}
  default:break;}
}
static void draw_hud(frame *f,const oa_hud_view *v,int all){int i;for(i=0;i<OA_HUD_COUNT;i++){float r[4];if(!f->m->settings.hud[i].on)continue;oa_hud_rect(f->m,i,f->w,f->h,r);draw_item(f,i,r,v,f->m->settings.opacity,all);}}
static void set_zones(const oa_menu *m,int w,int h,const oa_hud_view *v){float a[4]={0,0,0,0},b[4]={0,0,0,0},c[4]={0,0,0,0};
 if(m->settings.hud[OA_HUD_ATTACK].on)oa_hud_rect(m,OA_HUD_ATTACK,w,h,a);if(v->prompt&&m->settings.hud[OA_HUD_PROMPT].on)oa_hud_rect(m,OA_HUD_PROMPT,w,h,b);if(m->settings.hud[OA_HUD_MENU].on)oa_hud_rect(m,OA_HUD_MENU,w,h,c);exploration_input_set_zones(a,b,c);}
static void title_screen(frame *f){oa_menu *m=f->m;float s=f->s,x=76*s,y=318*s,w=420*s;const float l[4]={.024f,.031f,.035f,.9f},mid[4]={.024f,.031f,.035f,.6f},r[4]={.024f,.031f,.035f,0};
 oa_ui_title(f->u,0,0,(float)f->w,(float)f->h);oa_ui_fade(f->u,0,0,f->w*.34f,(float)f->h,l,mid);oa_ui_fade(f->u,f->w*.34f,0,f->w*.3f,(float)f->h,mid,r);
 oa_ui_text(f->u,OA_FONT_HEAD,x,110*s,60*s,OA_ALIGN_LEFT,PAPER,"Open");oa_ui_text(f->u,OA_FONT_HEAD,x,174*s,60*s,OA_ALIGN_LEFT,PAPER,"Amalur");
 {float c[4]={1,1,1,1};oa_ui_fade(f->u,x,272*s,150*s,1,GLOW0,LINE);oa_ui_sprite(f->u,OA_SPR_DIAMOND,x+158*s,263*s,20*s,18*s,1,c);oa_ui_fade(f->u,x+186*s,272*s,150*s,1,LINE,GLOW0);}
 if(m->has_save){if(menu_row(f,x,y,w,84*s,25,"Continue",m->focus==0))m->action=OA_ACTION_LOAD;y+=88*s;}
 if(menu_row(f,x,y,w,58*s,20,"New Game",!m->has_save&&m->focus==0)){if(m->creation_enabled)creation_begin_new(m);else m->action=OA_ACTION_NEW_GAME;}y+=62*s;
 if(m->creation_enabled){if(menu_row(f,x,y,w,58*s,20,"Character Draft",0))creation_begin_edit(m);y+=62*s;}
 if(menu_row(f,x,y,w,58*s,20,"Options",0))oa_menu_open(m,OA_SCREEN_OPTIONS);y+=62*s;
 if(menu_row(f,x,y,w,58*s,20,"Exit",0))m->action=OA_ACTION_EXIT;
 oa_ui_text(f->u,OA_FONT_BODY,f->w-36*s,f->h-46*s,16*s,OA_ALIGN_RIGHT,DIM,"v0.39.1");
}
static void pause_screen(frame *f,const oa_hud_view *v){oa_menu *m=f->m;float s=f->s,x=48*s,y=122*s,w=330*s;static const char *TABS[7]={"Inventory","Quests","Map","Character","Abilities","Destinies","Options"};const float l[4]={.024f,.031f,.035f,.88f},mid[4]={.024f,.031f,.035f,.4f};int i;char b[64];float tab_x;
 oa_ui_fade(f->u,0,0,f->w*.4f,(float)f->h,l,mid);oa_ui_fade(f->u,f->w*.4f,0,f->w*.6f,(float)f->h,mid,l);
 oa_ui_rect(f->u,0,0,(float)f->w,84*s,SHADE);oa_ui_rect(f->u,0,84*s,(float)f->w,1,LINE);
 {float total=0,gap=44*s;for(i=0;i<7;i++)total+=oa_ui_measure(f->u,OA_FONT_HEAD,17*s,TABS[i])+gap;tab_x=f->w*.5f-(total-gap)*.5f;
  for(i=0;i<7;i++){const float muted[4]={DIM[0],DIM[1],DIM[2],.45f};{float wide=oa_ui_measure(f->u,OA_FONT_HEAD,17*s,TABS[i]);float hit[4]={tab_x-20*s,0,wide+40*s,84*s};if(i==0&&m->released&&inside(hit,m->px,m->py)&&inside(hit,m->press_x,m->press_y))oa_menu_open(m,OA_SCREEN_INVENTORY);}oa_ui_text(f->u,OA_FONT_HEAD,tab_x,30*s,17*s,OA_ALIGN_LEFT,i==0?PAPER:muted,TABS[i]);tab_x+=oa_ui_measure(f->u,OA_FONT_HEAD,17*s,TABS[i])+gap;}}
 {int intro=v->created_player&&!v->created_player->gameplay.lua.cinematic_flags;
  if(menu_row(f,x,y,w,64*s,22,intro?"Skip Introduction":"Resume",m->focus==0)){if(intro)m->action=OA_ACTION_SKIP_INTRO;else oa_menu_open(m,OA_SCREEN_GAME);}y+=68*s;}
 if(menu_row(f,x,y,w,56*s,18,"Inventory",0))oa_menu_open(m,OA_SCREEN_INVENTORY);y+=60*s;
 if(m->creation_enabled){if(menu_row(f,x,y,w,56*s,18,"Character Draft",0))creation_begin_edit(m);y+=60*s;}
 if(menu_row(f,x,y,w,56*s,18,m->checkpoint_only?"Save Checkpoint":"Save Game",0))m->action=OA_ACTION_SAVE;y+=60*s;
 if(m->has_save){if(menu_row(f,x,y,w,56*s,18,m->has_character_save?"Load Character":m->checkpoint_only?"Load Checkpoint":"Load Game",0))m->action=OA_ACTION_LOAD;y+=60*s;}
 if(menu_row(f,x,y,w,56*s,18,"Options",0))oa_menu_open(m,OA_SCREEN_OPTIONS);y+=60*s;
 if(menu_row(f,x,y,w,56*s,18,"Exit to Title",0))oa_menu_open(m,OA_SCREEN_TITLE);
 x=f->w-394*s;y=122*s;oa_ui_text(f->u,OA_FONT_HEAD,x,y,25*s,OA_ALIGN_LEFT,PAPER,v->player_name?v->player_name:"Fateless One");y+=36*s;
 if(v->player_name){oa_ui_text(f->u,OA_FONT_BODY,x,y,16*s,OA_ALIGN_LEFT,DIM,v->player_title?v->player_title:"Fateless One");y+=24*s;}else y+=10*s;oa_ui_rect(f->u,x,y,350*s,1,LINE);y+=12*s;
 oa_ui_text(f->u,OA_FONT_BODY,x,y,19*s,OA_ALIGN_LEFT,DIM,"Health");snprintf(b,sizeof(b),"%.0f / %.0f",v->health_now,v->health_max);oa_ui_text(f->u,OA_FONT_BODY,x+350*s,y,19*s,OA_ALIGN_RIGHT,PAPER,b);y+=38*s;
 oa_ui_text(f->u,OA_FONT_BODY,x,y,19*s,OA_ALIGN_LEFT,DIM,"Location");oa_ui_text(f->u,OA_FONT_BODY,x+350*s,y,19*s,OA_ALIGN_RIGHT,PAPER,v->location?v->location:"");y+=38*s;
 hint(f,"","A Select    B Resume","Enter Select    Esc Resume");
}
static void value_row(frame *f,float x,float y,float w,float h,const char *label,const char *value,int *delta){oa_menu *m=f->m;float s=f->s,r[4],minus[4],plus[4];int id=f->next;r[0]=x;r[1]=y;r[2]=w;r[3]=h;
 minus[0]=x+w-210*s;minus[1]=y;minus[2]=60*s;minus[3]=h;plus[0]=x+w-60*s;plus[1]=y;plus[2]=60*s;plus[3]=h;*delta=0;
 if(m->released&&inside(minus,m->px,m->py)&&inside(minus,m->press_x,m->press_y))*delta=-1;else if(m->released&&inside(plus,m->px,m->py)&&inside(plus,m->press_x,m->press_y))*delta=1;
 if(widget(f,r)&&!*delta)*delta=1;if(focused(f,id)&&m->nav_x)*delta=m->nav_x;
 if(focused(f,id)&&show_focus(m))highlight(f,x,y,w,h);
 oa_ui_text(f->u,OA_FONT_HEAD,x+20*s,y+h*.5f-13*s,18*s,OA_ALIGN_LEFT,PAPER,label);
 oa_ui_text(f->u,OA_FONT_HEAD,minus[0]+30*s,y+h*.5f-15*s,22*s,OA_ALIGN_CENTER,GOLD,"-");oa_ui_text(f->u,OA_FONT_BODY,x+w-105*s,y+h*.5f-13*s,19*s,OA_ALIGN_CENTER,PAPER,value);oa_ui_text(f->u,OA_FONT_HEAD,plus[0]+30*s,y+h*.5f-15*s,22*s,OA_ALIGN_CENTER,GOLD,"+");
 oa_ui_rect(f->u,x,y+h,w,1,GLOW);}
#include "oa_creation_ui.inc"
static void options_screen(frame *f,const oa_hud_view *v){oa_menu *m=f->m;float s=f->s,x=f->w*.5f-330*s,y=118*s,w=660*s,h=56*s;oa_settings *c=&m->settings;char b[32];int d;const float back[4]={.024f,.031f,.035f,.92f};
 if(m->from==OA_SCREEN_TITLE)oa_ui_title(f->u,0,0,(float)f->w,(float)f->h);oa_ui_rect(f->u,0,0,(float)f->w,(float)f->h,back);
 oa_ui_text(f->u,OA_FONT_HEAD,x,50*s,28*s,OA_ALIGN_LEFT,PAPER,"Options");oa_ui_rect(f->u,x,100*s,w,1,LINE);
 if(menu_row(f,x,y,w,h,18,"HUD Layout",0))oa_menu_open(m,OA_SCREEN_LAYOUT);y+=h+6*s;
 snprintf(b,sizeof(b),"%d%%",(int)(c->opacity*100+.5f));value_row(f,x,y,w,h,"HUD Opacity",b,&d);if(d){c->opacity=clampf_(roundf((c->opacity+d*.1f)*10)/10,.3f,1);m->dirty=1;}y+=h+6*s;
 snprintf(b,sizeof(b),"%d%%",(int)(c->look_speed*100+.5f));value_row(f,x,y,w,h,"Look Speed",b,&d);if(d){c->look_speed=clampf_(roundf((c->look_speed+d*.25f)*4)/4,.25f,3);m->dirty=1;}y+=h+6*s;
 value_row(f,x,y,w,h,"Invert Look",c->invert_look?"On":"Off",&d);if(d){c->invert_look=!c->invert_look;m->dirty=1;}y+=h+6*s;
 if(c->rate)snprintf(b,sizeof(b),"%d Hz",RATES[c->rate]);else snprintf(b,sizeof(b),"Automatic");value_row(f,x,y,w,h,"Refresh Rate",b,&d);if(d){c->rate=(c->rate+d+5)%5;m->dirty=1;m->action=OA_ACTION_APPLY_RATE;}y+=h+6*s;
 value_row(f,x,y,w,h,"Shadows",c->shadows?"On":"Off",&d);if(d){c->shadows=!c->shadows;m->dirty=1;}y+=h+6*s;
 value_row(f,x,y,w,h,"Canopy",c->canopy_dense?"Dense":"Corrected",&d);if(d){c->canopy_dense=!c->canopy_dense;m->dirty=1;}y+=h+6*s;
 value_row(f,x,y,w,h,"Lighting Test",v->room_lighting?"Room":"Preview",&d);if(d)m->action=OA_ACTION_TOGGLE_LIGHTING;y+=h+6*s;
 if(menu_row(f,x,y,w,h,18,"Reset to Defaults",0)){oa_settings_default(c);m->dirty=1;m->action=OA_ACTION_APPLY_RATE;oa_menu_status(m,"Defaults restored");}y+=h+6*s;
 if(menu_row(f,x,y,w,h,18,"Back",0))oa_menu_open(m,m->from);
 hint(f,"","A Select    D-pad Change    B Back","Enter Select    Arrows Change    Esc Back");
}
static void move_item(oa_menu *m,int item,float dx,float dy,int w,int h){float r[4],hw,hh;oa_hud_item *i=m->settings.hud+item;oa_hud_rect(m,item,w,h,r);hw=r[2]*.5f/(float)w;hh=r[3]*.5f/(float)h;i->x=clampf_(i->x+dx,fminf(hw,.5f),fmaxf(1-hw,.5f));i->y=clampf_(i->y+dy,fminf(hh,.5f),fmaxf(1-hh,.5f));m->dirty=1;}
static void layout_screen(frame *f,const oa_hud_view *v,float dt){oa_menu *m=f->m;float s=f->s,rect[4],pw=372*s,ph=790*s,px,py=25*s,y,rowh=50*s;int i,left;oa_hud_item *sel;const float panel[4]={.024f,.031f,.035f,.9f};char b[32];
 if(m->selected<0||m->selected>=OA_HUD_COUNT)m->selected=0;sel=m->settings.hud+m->selected;
 draw_hud(f,v,1);
 for(i=0;i<OA_HUD_COUNT;i++){float t=fmaxf(1,1.2f*s);const float *c=i==m->selected?GOLD:GLOW;if(!m->settings.hud[i].on&&i!=m->selected)continue;oa_hud_rect(m,i,f->w,f->h,rect);oa_ui_rect(f->u,rect[0],rect[1],rect[2],t,c);oa_ui_rect(f->u,rect[0],rect[1]+rect[3]-t,rect[2],t,c);oa_ui_rect(f->u,rect[0],rect[1],t,rect[3],c);oa_ui_rect(f->u,rect[0]+rect[2]-t,rect[1],t,rect[3],c);}
 /* Keep the panel off whatever is being placed, moving it only when the other side is clearer. */
 oa_hud_rect(m,m->selected,f->w,f->h,rect);
 if(!m->dragging){float a=24*s,b=f->w-pw-24*s,on_left=fminf(rect[0]+rect[2],a+pw)-fmaxf(rect[0],a),on_right=fminf(rect[0]+rect[2],b+pw)-fmaxf(rect[0],b);on_left=fmaxf(on_left,0);on_right=fmaxf(on_right,0);if(m->panel_left?on_left>on_right:on_right>on_left)m->panel_left=!m->panel_left;}
 left=m->panel_left;px=left?24*s:f->w-pw-24*s;
 /* Drag on the play area, not through the panel. */
 {float p[4]={px,py,pw,ph};
  if(m->pressed&&!inside(p,m->press_x,m->press_y)){int found=-1;for(i=OA_HUD_COUNT-1;i>=0&&found<0;i--){float g[4];oa_hud_rect(m,i,f->w,f->h,g);g[0]-=8*s;g[1]-=8*s;g[2]+=16*s;g[3]+=16*s;if(m->settings.hud[i].on&&inside(g,m->press_x,m->press_y))found=i;}if(found>=0){m->selected=found;m->focus=found;m->dragging=1;m->last_x=m->px;m->last_y=m->py;sel=m->settings.hud+found;}}
  if(m->dragging){if(m->pointer_down){move_item(m,m->selected,(m->px-m->last_x)/(float)f->w,(m->py-m->last_y)/(float)f->h,f->w,f->h);m->last_x=m->px;m->last_y=m->py;}else m->dragging=0;}}
 oa_ui_rect(f->u,px,py,pw,ph,panel);oa_ui_rect(f->u,px,py,pw,1,LINE);oa_ui_rect(f->u,px,py+ph,pw,1,LINE);
 oa_ui_text(f->u,OA_FONT_HEAD,px+20*s,py+14*s,22*s,OA_ALIGN_LEFT,PAPER,"HUD Layout");y=py+56*s;
 for(i=0;i<OA_HUD_COUNT;i++){float r[4]={px,y,pw,rowh},sw[4]={px+pw-92*s,y,92*s,rowh};int id=f->next,toggled=m->released&&inside(sw,m->px,m->py)&&inside(sw,m->press_x,m->press_y);int hit=widget(f,r);
  if(focused(f,id)&&(m->nav_y||m->accept||m->released)&&m->selected!=i){m->selected=i;}
  if(id==m->focus&&m->selected!=i)m->selected=i;
  if(toggled||(hit&&m->accept)){m->settings.hud[i].on=!m->settings.hud[i].on;m->dirty=1;}
  if(m->selected==i)highlight(f,px,y,pw,rowh);
  {float muted[4]={DIM[0],DIM[1],DIM[2],m->settings.hud[i].on?1.f:.55f};oa_ui_text(f->u,OA_FONT_BODY,px+20*s,y+rowh*.5f-13*s,20*s,OA_ALIGN_LEFT,m->settings.hud[i].on?PAPER:muted,HUD[i].name);oa_ui_text(f->u,OA_FONT_HEAD,px+pw-20*s,y+rowh*.5f-11*s,14*s,OA_ALIGN_RIGHT,m->settings.hud[i].on?GOLD:muted,m->settings.hud[i].on?"On":"Off");}
  y+=rowh;}
 y+=10*s;oa_ui_rect(f->u,px+14*s,y,pw-28*s,1,GLOW);y+=8*s;
 {float minus[4]={px,y,92*s,54*s},plus[4]={px+pw-92*s,y,92*s,54*s};int d=0;
  if(m->released&&inside(minus,m->px,m->py)&&inside(minus,m->press_x,m->press_y))d=-1;if(m->released&&inside(plus,m->px,m->py)&&inside(plus,m->press_x,m->press_y))d=1;
  if(m->nav_x&&m->focus<OA_HUD_COUNT)d=m->nav_x;if(m->wheel!=0){d=m->wheel>0?1:-1;}
  if(d){sel->scale=clampf_(roundf((sel->scale+d*.1f)*10)/10,.5f,2);move_item(m,m->selected,0,0,f->w,f->h);m->dirty=1;}
  oa_ui_text(f->u,OA_FONT_HEAD,minus[0]+46*s,y+11*s,24*s,OA_ALIGN_CENTER,GOLD,"-");oa_ui_text(f->u,OA_FONT_HEAD,plus[0]+46*s,y+11*s,24*s,OA_ALIGN_CENTER,GOLD,"+");
  snprintf(b,sizeof(b),"Size %d%%",(int)(sel->scale*100+.5f));oa_ui_text(f->u,OA_FONT_BODY,px+pw*.5f,y+14*s,20*s,OA_ALIGN_CENTER,PAPER,b);y+=60*s;}
 if(menu_row(f,px,y,pw,50*s,15,"Reset Element",0)){sel->scale=1;sel->x=HUD[m->selected].x;sel->y=HUD[m->selected].y;sel->on=HUD[m->selected].on;m->dirty=1;}y+=52*s;
 if(menu_row(f,px,y,pw,50*s,15,"Done",0))oa_menu_open(m,OA_SCREEN_OPTIONS);
 /* Hold to move: left stick on a controller, WASD on a keyboard. */
 {float ax=fabsf(m->axis_x)>.2f?m->axis_x:0,ay=fabsf(m->axis_y)>.2f?m->axis_y:0;if(m->keys_move&8)ax+=1;if(m->keys_move&4)ax-=1;if(m->keys_move&2)ay+=1;if(m->keys_move&1)ay-=1;if(ax!=0||ay!=0)move_item(m,m->selected,ax*.35f*dt,ay*.35f*dt,f->w,f->h);}
 if(m->device==OA_DEVICE_PAD)oa_ui_text(f->u,OA_FONT_BODY,left?f->w-360*s:360*s,f->h*.24f,18*s,OA_ALIGN_CENTER,PAPER,"A On/Off    Left/Right Size    Stick Move    B Done");
 else if(m->device==OA_DEVICE_KEYBOARD)oa_ui_text(f->u,OA_FONT_BODY,left?f->w-360*s:360*s,f->h*.24f,18*s,OA_ALIGN_CENTER,PAPER,"Enter On/Off    -/+ or Wheel Size    WASD or Drag Move    Esc Done");
 else oa_ui_text(f->u,OA_FONT_BODY,left?f->w-360*s:360*s,f->h*.24f,18*s,OA_ALIGN_CENTER,PAPER,"Drag an element to move it");
}
/* Rows are items for every tab but Reagents, whose rows index view->reagents. */
static int inv_rows(const oa_menu *m,const oa_hud_view *v,int *rows){int i,n=0;
 if(m->inv_tab==OA_TAB_REAGENTS){for(i=0;i<v->reagent_count&&n<128;i++)rows[n++]=i;return n;}
 for(i=0;i<OA_ITEM_COUNT;i++){const oa_item_def *d=oa_item_get(i);if(!m->bag.count[i])continue;
  if(m->inv_tab==OA_TAB_WEAPONS&&d->slot!=OA_SLOT_WEAPON)continue;if(m->inv_tab==OA_TAB_ARMOR&&(d->slot==OA_SLOT_WEAPON||d->slot==OA_SLOT_NONE))continue;if(m->inv_tab==OA_TAB_CONSUMABLES&&d->slot!=OA_SLOT_NONE)continue;rows[n++]=i;}
 {int a,b;for(a=1;a<n;a++){int k=rows[a];const oa_item_def *x=oa_item_get(k);for(b=a-1;b>=0;b--){const oa_item_def *y=oa_item_get(rows[b]);int c=m->inv_sort==0?strcmp(y->name,x->name):m->inv_sort==1?y->power-x->power:y->value-x->value;if(m->inv_dir<0)c=-c;if(c<=0)break;rows[b+1]=rows[b];}rows[b+1]=k;}}
 return n;}
static void created_inventory_screen(frame *f,const oa_hud_view *v){
 const oa_creation_active *a=v->created_player;const oa_creation_source_type *type=oa_creation_source(a->profile.race,a->profile.sex);
 float s=f->s,x=80*s,y=90*s,right=f->w*.56f;unsigned i;char b[128];const float bg[4]={.024f,.031f,.035f,.98f};
 oa_ui_rect(f->u,0,0,(float)f->w,(float)f->h,bg);oa_ui_text(f->u,OA_FONT_HEAD,x,36*s,30*s,OA_ALIGN_LEFT,PAPER,"Character & Equipment");
 oa_ui_text(f->u,OA_FONT_HEAD,x,y,26*s,OA_ALIGN_LEFT,PAPER,a->profile.name);y+=42*s;
 snprintf(b,sizeof(b),"%s / %s / %s",type->race,type->sex,oa_creation_source_patron(a->profile.race,a->profile.patron)->name);
 oa_ui_text(f->u,OA_FONT_BODY,x,y,19*s,OA_ALIGN_LEFT,DIM,b);y+=38*s;
 snprintf(b,sizeof(b),"Health %u / %u",a->owner.health,a->owner.max_health);oa_ui_text(f->u,OA_FONT_BODY,x,y,22*s,OA_ALIGN_LEFT,PAPER,b);y+=62*s;
 oa_ui_text(f->u,OA_FONT_HEAD,x,y,22*s,OA_ALIGN_LEFT,GOLD,"Equipped");y+=40*s;
 for(i=0;i<a->owner.item_count;i++)if(a->owner.items[i].equipped_slot>=0){
  const char *label=NULL;switch(a->owner.items[i].type){case 1321542:label="Tatters - torso";break;case 1321543:label="Tatters - legs";break;case 1330206:label="Unarmed - primary";break;case 1330207:label="Unarmed - secondary";break;case 1381439:label="No shield";break;default:label="Equipment";break;}
  oa_ui_text(f->u,OA_FONT_BODY,x,y,20*s,OA_ALIGN_LEFT,PAPER,label);y+=35*s;
 }
 snprintf(b,sizeof(b),"Starting items: %u",a->owner.item_count);oa_ui_text(f->u,OA_FONT_BODY,x,y+24*s,18*s,OA_ALIGN_LEFT,DIM,b);
 oa_ui_text(f->u,OA_FONT_BODY,x,y+60*s,17*s,OA_ALIGN_LEFT,DIM,"Equipment changes are not available in this opening build.");
 y=96*s;oa_ui_text(f->u,OA_FONT_HEAD,right,y,24*s,OA_ALIGN_LEFT,GOLD,"Skills");y+=52*s;
 for(i=0;i<OA_CREATION_SKILLS;i++){
  const char *name=!strcmp(oa_creation_skill_names[i],"DetectHidden")?"Detect Hidden":oa_creation_skill_names[i];
  oa_ui_text(f->u,OA_FONT_BODY,right,y,19*s,OA_ALIGN_LEFT,DIM,name);snprintf(b,sizeof(b),"%.1f",a->owner.skill_raw[i]/10.f);
  oa_ui_text(f->u,OA_FONT_BODY,f->w-80*s,y,19*s,OA_ALIGN_RIGHT,PAPER,b);y+=42*s;
 }
 if(menu_row(f,x,f->h-126*s,280*s,52*s,19,"Back",0))oa_menu_open(f->m,f->m->inv_from);
 hint(f,"Tap Back to return","B Back","Esc Back");
}
static void inventory_screen(frame *f,const oa_hud_view *v){oa_menu *m=f->m;float s=f->s,lx=112*s,ly=137*s,lw=680*s,rh=56*s,lh=560*s,cx=824*s,cw=f->w-cx-24*s;int rows[128],n,i,visible;char b[64];
 if(v->created_player){created_inventory_screen(f,v);return;}
 static const struct{int sprite;const char *label;}TABS[OA_TAB_COUNT]={{OA_SPR_DRAGON,"All"},{OA_SPR_SWORDS,"Weapons"},{OA_SPR_ARMOR,"Armor"},{OA_SPR_I_POTION,"Consumables"},{OA_SPR_MORTAR,"Reagents"}};
 static const float RARE[4][4]={{.937f,.902f,.824f,1},{.608f,.863f,.522f,1},{.549f,.753f,1,1},{.812f,.663f,1,1}};
 const float back[4]={.024f,.031f,.035f,.95f},back2[4]={.024f,.031f,.035f,.72f},white[4]={1,1,1,1};
 oa_ui_fade(f->u,0,0,(float)f->w,(float)f->h,back,back2);oa_ui_rect(f->u,88*s,0,1,(float)f->h,GLOW);
 /* Tabs: rail on the left, L1/R1, Q/E, or left and right. */
 {int step=m->tab_step?m->tab_step:m->nav_x;if(step){m->inv_tab=(m->inv_tab+step+OA_TAB_COUNT)%OA_TAB_COUNT;m->inv_row=0;m->inv_scroll=0;}}
 for(i=0;i<OA_TAB_COUNT;i++){float y=(96+i*72)*s,r[4]={12*s,y,64*s,64*s},c[4]={1,1,1,i==m->inv_tab?1.f:.68f};if(m->released&&inside(r,m->px,m->py)&&inside(r,m->press_x,m->press_y)){m->inv_tab=i;m->inv_row=0;m->inv_scroll=0;}
  if(i==m->inv_tab){oa_ui_disk(f->u,44*s,y+32*s,32*s,GLOW);oa_ui_ring(f->u,44*s,y+32*s,32*s,1.4f*s,GOLD);}oa_ui_sprite(f->u,TABS[i].sprite,20*s,y+8*s,48*s,48*s,1,c);}
 oa_ui_text(f->u,OA_FONT_HEAD,lx,28*s,28*s,OA_ALIGN_LEFT,PAPER,"Inventory");oa_ui_text(f->u,OA_FONT_BODY,lx+lw,36*s,20*s,OA_ALIGN_RIGHT,GOLD,TABS[m->inv_tab].label);
 /* Column headers sort when tapped; X, Y or the X key cycles them. */
 {static const char *HEAD[3]={"Name","Power","Value"};float hx[3]={lx+56*s,lx+lw-180*s,lx+lw-90*s},hw[3]={lw-240*s,90*s,90*s};int reag=m->inv_tab==OA_TAB_REAGENTS;
  if(m->sort_step&&!reag){m->inv_sort=(m->inv_sort+1)%3;m->inv_dir=m->inv_sort==0?1:-1;}
  for(i=0;i<3;i++){float r[4]={hx[i],92*s,hw[i],44*s};const char *mark="";char label[24];if(reag&&i)continue;if(!reag&&m->released&&inside(r,m->px,m->py)&&inside(r,m->press_x,m->press_y)){if(m->inv_sort==i)m->inv_dir=-m->inv_dir;else{m->inv_sort=i;m->inv_dir=i==0?1:-1;}}
   if(!reag&&m->inv_sort==i)mark=m->inv_dir>0?" ^":" v";snprintf(label,sizeof(label),"%s%s",HEAD[i],mark);oa_ui_text(f->u,OA_FONT_HEAD,i?hx[i]+hw[i]:hx[i],104*s,13*s,i?OA_ALIGN_RIGHT:OA_ALIGN_LEFT,!reag&&m->inv_sort==i?PAPER:GOLD,label);}}
 if(m->inv_tab==OA_TAB_REAGENTS)oa_ui_text(f->u,OA_FONT_HEAD,lx+lw,104*s,13*s,OA_ALIGN_RIGHT,GOLD,"Count");
 oa_ui_rect(f->u,lx,136*s,lw,1,LINE);
 n=inv_rows(m,v,rows);visible=(int)(lh/rh);
 /* Scrolling: drag, wheel, or moving the selection. */
 {float limit=fmaxf(0,n*rh-lh),list[4]={lx,ly,lw,lh};
  if(m->pointer_down&&inside(list,m->press_x,m->press_y)){if(fabsf(m->py-m->press_y)>10*s)m->inv_scroll_drag=1;if(m->inv_scroll_drag){m->inv_scroll-=m->py-m->last_y;}m->last_y=m->py;}
  if(m->pressed)m->last_y=m->py;
  if(m->wheel!=0)m->inv_scroll-=m->wheel*rh;
  if(n&&m->nav_y){m->inv_row=(m->inv_row+m->nav_y+n)%n;if(m->inv_row*rh<m->inv_scroll)m->inv_scroll=m->inv_row*rh;if((m->inv_row+1)*rh>m->inv_scroll+lh)m->inv_scroll=(m->inv_row+1)*rh-lh;}
  m->inv_scroll=clampf_(m->inv_scroll,0,limit);if(m->inv_row>=n)m->inv_row=n?n-1:0;(void)visible;}
 if(!n)oa_ui_text(f->u,OA_FONT_BODY,lx+lw*.5f,ly+60*s,20*s,OA_ALIGN_CENTER,DIM,m->inv_tab==OA_TAB_REAGENTS?"No reagents yet":"Nothing here");
 for(i=0;i<n;i++){float y=ly+i*rh-m->inv_scroll,r[4]={lx,y,lw,rh};int sel=i==m->inv_row;const float *name=PAPER;
  if(y+rh<=ly||y>=ly+lh)continue;
  if(m->released&&!m->inv_scroll_drag&&inside(r,m->px,m->py)&&inside(r,m->press_x,m->press_y)&&m->py<ly+lh&&m->py>=ly){m->inv_row=i;sel=1;}
  if(y<ly||y+rh>ly+lh)continue;
  if(sel)oa_ui_fade(f->u,lx,y,lw,rh,GLOW,GLOW0);oa_ui_rect(f->u,lx,y+rh-1,lw,1,GLOW0);
  if(m->inv_tab==OA_TAB_REAGENTS){oa_ui_text(f->u,OA_FONT_BODY,lx+56*s,y+14*s,20*s,OA_ALIGN_LEFT,PAPER,v->reagents[rows[i]].name);snprintf(b,sizeof(b),"%u",v->reagents[rows[i]].count);oa_ui_text(f->u,OA_FONT_BODY,lx+lw,y+14*s,20*s,OA_ALIGN_RIGHT,DIM,b);oa_ui_sprite(f->u,OA_SPR_MORTAR,lx+6*s,y+8*s,40*s,40*s,1,white);continue;}
  {const oa_item_def *d=oa_item_get(rows[i]);float tx=lx+56*s,tw;name=RARE[d->rarity];oa_ui_sprite(f->u,d->sprite,lx+2*s,y+4*s,48*s,48*s,1,white);
   if(m->bag.count[rows[i]]>1)snprintf(b,sizeof(b),"%s (%u)",d->name,m->bag.count[rows[i]]);else snprintf(b,sizeof(b),"%s",d->name);oa_ui_text(f->u,OA_FONT_BODY,tx,y+14*s,20*s,OA_ALIGN_LEFT,name,b);tw=oa_ui_measure(f->u,OA_FONT_BODY,20*s,b);
   if(oa_bag_is_equipped(&m->bag,rows[i]))oa_ui_sprite(f->u,OA_SPR_DIAMOND,tx+tw+10*s,y+20*s,16*s,14*s,1,white);
   if(d->power){snprintf(b,sizeof(b),"%d",d->power);oa_ui_text(f->u,OA_FONT_BODY,lx+lw-90*s,y+14*s,20*s,OA_ALIGN_RIGHT,PAPER,b);}snprintf(b,sizeof(b),"%d",d->value);oa_ui_text(f->u,OA_FONT_BODY,lx+lw,y+14*s,20*s,OA_ALIGN_RIGHT,DIM,b);}}
 /* Footer */
 oa_ui_rect(f->u,lx,f->h-132*s,lw,1,GLOW);oa_ui_sprite(f->u,OA_SPR_GOLD,lx,f->h-120*s,28*s,28*s,1,white);snprintf(b,sizeof(b),"%u",m->bag.gold);oa_ui_text(f->u,OA_FONT_BODY,lx+36*s,f->h-120*s,20*s,OA_ALIGN_LEFT,PAPER,b);
 snprintf(b,sizeof(b),"Damage %.0f    Armor %d",oa_bag_damage(&m->bag),oa_bag_armor(&m->bag));oa_ui_text(f->u,OA_FONT_BODY,lx+lw*.5f,f->h-120*s,20*s,OA_ALIGN_CENTER,DIM,b);
 {float r[4]={lx+lw-96*s,f->h-130*s,96*s,48*s};if(m->released&&inside(r,m->px,m->py)&&inside(r,m->press_x,m->press_y))m->back=1;oa_ui_text(f->u,OA_FONT_HEAD,lx+lw,f->h-120*s,17*s,OA_ALIGN_RIGHT,GOLD,"Back");}
 /* Item card */
 if(n&&m->inv_tab!=OA_TAB_REAGENTS){int item=rows[m->inv_row];const oa_item_def *d=oa_item_get(item);int eq=oa_bag_is_equipped(&m->bag,item);float y=24*s;const char *label;int can=1;float r[4]={cx,f->h-142*s,cw,64*s};
  oa_ui_sprite(f->u,d->sprite,cx,y,96*s,96*s,1,white);oa_ui_text(f->u,OA_FONT_HEAD,cx+106*s,y+18*s,20*s,OA_ALIGN_LEFT,RARE[d->rarity],d->name);oa_ui_text(f->u,OA_FONT_BODY,cx+106*s,y+50*s,18*s,OA_ALIGN_LEFT,DIM,d->kind);
  y+=108*s;oa_ui_rect(f->u,cx,y,cw,1,LINE);y+=16*s;
  if(d->slot==OA_SLOT_NONE){oa_ui_text(f->u,OA_FONT_HEAD,cx,y,13*s,OA_ALIGN_LEFT,GOLD,"Restores Health");snprintf(b,sizeof(b),"%d",d->heal);oa_ui_text(f->u,OA_FONT_HEAD,cx,y+18*s,44*s,OA_ALIGN_LEFT,PAPER,b);snprintf(b,sizeof(b),"%.0f / %.0f now",v->health_now,v->health_max);oa_ui_text(f->u,OA_FONT_BODY,cx+cw,y+34*s,18*s,OA_ALIGN_RIGHT,DIM,b);}
  else{const oa_item_def *cur=oa_item_get(m->bag.equipped[d->slot]);oa_ui_text(f->u,OA_FONT_HEAD,cx,y,13*s,OA_ALIGN_LEFT,GOLD,d->slot==OA_SLOT_WEAPON?"Physical Damage":"Armor");snprintf(b,sizeof(b),"%d",d->power);oa_ui_text(f->u,OA_FONT_HEAD,cx,y+18*s,44*s,OA_ALIGN_LEFT,PAPER,b);
   if(eq)oa_ui_text(f->u,OA_FONT_BODY,cx+cw,y+28*s,20*s,OA_ALIGN_RIGHT,GOLD,"Equipped");
   else{int delta=d->power-(cur?cur->power:0);const float up[4]={.56f,.88f,.81f,1},down[4]={1,.6f,.48f,1};snprintf(b,sizeof(b),"vs %s",cur?cur->name:"nothing");oa_ui_text(f->u,OA_FONT_BODY,cx+cw,y+10*s,16*s,OA_ALIGN_RIGHT,DIM,b);snprintf(b,sizeof(b),"%s %+d",delta>=0?"^":"v",delta);oa_ui_text(f->u,OA_FONT_BODY,cx+cw,y+34*s,26*s,OA_ALIGN_RIGHT,delta>=0?up:down,b);}}
  y+=80*s;oa_ui_rect(f->u,cx,y,cw,1,GLOW);y+=8*s;oa_ui_text(f->u,OA_FONT_BODY,cx,y,18*s,OA_ALIGN_LEFT,DIM,"Value");snprintf(b,sizeof(b),"%d gold",d->value);oa_ui_text(f->u,OA_FONT_BODY,cx+cw,y,18*s,OA_ALIGN_RIGHT,PAPER,b);
  if(d->slot==OA_SLOT_NONE){label="Use";can=v->health_now<v->health_max&&v->health_now>0;}else if(eq&&d->slot==OA_SLOT_WEAPON){label="Equipped";can=0;}else label=eq?"Unequip":"Equip";
  {const float box[4]={.788f,.655f,.396f,.22f},off[4]={.5f,.5f,.5f,.12f};const float *col=can?PAPER:DIM;oa_ui_rect(f->u,r[0],r[1],r[2],r[3],can?box:off);oa_ui_rect(f->u,r[0],r[1],r[2],1,LINE);oa_ui_rect(f->u,r[0],r[1]+r[3],r[2],1,LINE);oa_ui_text(f->u,OA_FONT_HEAD,r[0]+r[2]*.5f,r[1]+18*s,18*s,OA_ALIGN_CENTER,col,label);}
  if(can&&(m->accept||(m->released&&inside(r,m->px,m->py)&&inside(r,m->press_x,m->press_y)))){if(d->slot==OA_SLOT_NONE){float gained=oa_bag_use(&m->bag,item,v->health_now,v->health_max);if(gained>0){m->heal_request+=gained;oa_menu_status(m,"Health restored");}}else if(eq)oa_bag_unequip(&m->bag,item);else oa_bag_equip(&m->bag,item);}
 }
 else if(m->inv_tab==OA_TAB_REAGENTS){oa_ui_text(f->u,OA_FONT_BODY,cx,60*s,20*s,OA_ALIGN_LEFT,DIM,"Used at an alchemy workbench.");}
 hint(f,"","A Use or Equip    L1/R1 Tab    Y Sort    B Back","Enter Use or Equip    Q/E Tab    X Sort    Esc Back");
 if(!m->pointer_down)m->inv_scroll_drag=0;
}
void oa_menu_frame(oa_menu *m,oa_ui *u,int w,int h,const oa_hud_view *v,float dt){
 frame f;oa_screen before=m->screen;f.m=m;f.u=u;f.w=w;f.h=h;f.s=SCALE(h);f.next=0;
 /* Stick and hat navigation with auto-repeat. The layout screen keeps the stick for moving. */
 {int ny=m->screen==OA_SCREEN_LAYOUT||m->screen==OA_SCREEN_GAME?0:axis_nav(m->axis_y),nx=m->screen==OA_SCREEN_LAYOUT||m->screen==OA_SCREEN_GAME?0:axis_nav(m->axis_x),hy=m->screen==OA_SCREEN_GAME?0:axis_nav(m->hat_y),hx=m->screen==OA_SCREEN_GAME?0:axis_nav(m->hat_x),dy=hy?hy:ny,dx=hx?hx:nx;
  if(dy!=m->axis_nav_y||dx!=m->axis_nav_x){m->axis_nav_y=dy;m->axis_nav_x=dx;m->nav_timer=.35f;if(dy)m->nav_y=dy;if(dx)m->nav_x=dx;}
  else if(dx||dy){m->nav_timer-=dt;if(m->nav_timer<=0){m->nav_timer=.12f;if(dy)m->nav_y=dy;if(dx)m->nav_x=dx;}}}
 if(m->count>0&&m->nav_y)m->focus=(m->focus+m->nav_y*(m->screen==OA_SCREEN_CREATION_NAME?10:1)+m->count)%m->count;
 if(m->status_time>0)m->status_time-=dt;
 switch(m->screen){
  case OA_SCREEN_GAME:if(v->show_hud)draw_hud(&f,v,0);set_zones(m,w,h,v);break;
  case OA_SCREEN_TITLE:title_screen(&f);break;
  case OA_SCREEN_PAUSE:pause_screen(&f,v);break;
  case OA_SCREEN_OPTIONS:options_screen(&f,v);break;
  case OA_SCREEN_LAYOUT:layout_screen(&f,v,dt);break;
  case OA_SCREEN_INVENTORY:inventory_screen(&f,v);break;
  case OA_SCREEN_CREATION:creation_screen(&f,v);break;
  case OA_SCREEN_CREATION_NAME:creation_name_screen(&f);break;}
 if(m->screen==before){m->count=f.next;if(m->focus>=m->count&&m->count>0)m->focus=m->count-1;}
 if(m->back&&m->screen==before){switch(m->screen){case OA_SCREEN_PAUSE:oa_menu_open(m,OA_SCREEN_GAME);break;case OA_SCREEN_OPTIONS:oa_menu_open(m,m->from);break;case OA_SCREEN_LAYOUT:oa_menu_open(m,OA_SCREEN_OPTIONS);break;case OA_SCREEN_CREATION:oa_menu_open(m,m->creation_from);break;case OA_SCREEN_CREATION_NAME:oa_menu_open(m,OA_SCREEN_CREATION);break;case OA_SCREEN_INVENTORY:{oa_screen to=m->inv_from;oa_menu_open(m,to);break;}default:break;}}
 if(m->status&&m->status_time>0){float s=f.s;oa_ui_text(u,OA_FONT_BODY,w*.5f,h-86*s,20*s,OA_ALIGN_CENTER,GOLD,m->status);}
 /* Held moves change settings every frame, so the layout screen writes them at most twice a second. */
 if(m->dirty){m->dirty_age+=dt;if(!m->dragging&&(m->screen!=OA_SCREEN_LAYOUT||m->dirty_age>.5f)){oa_settings_sanitize(&m->settings);oa_settings_save(&m->settings,m->settings_path);m->dirty=0;m->dirty_age=0;}}
 m->tab_step=m->sort_step=0;m->pressed=m->released=m->hovered=m->accept=m->back=m->reset=m->nav_x=m->nav_y=0;m->wheel=0;
}
