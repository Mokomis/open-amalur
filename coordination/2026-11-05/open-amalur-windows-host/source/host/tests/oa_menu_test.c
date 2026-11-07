#include "oa_menu.h"
#include "android_input_probe.h"
#include <android/keycodes.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static unsigned checks;
#define CHECK(v) do{++checks;if(!(v)){fprintf(stderr,"menu check failed line %d: %s\n",__LINE__,#v);return 1;}}while(0)
enum opem_input_family opem_android_event_family(const AInputEvent *e){return (enum opem_input_family)e->family;}
void oa_ui_rect(oa_ui *u,float x,float y,float w,float h,const float c[4]){(void)u;(void)x;(void)y;(void)w;(void)h;(void)c;}
void oa_ui_fade(oa_ui *u,float x,float y,float w,float h,const float l[4],const float r[4]){(void)u;(void)x;(void)y;(void)w;(void)h;(void)l;(void)r;}
void oa_ui_fade_v(oa_ui *u,float x,float y,float w,float h,const float l[4],const float r[4]){(void)u;(void)x;(void)y;(void)w;(void)h;(void)l;(void)r;}
void oa_ui_sprite(oa_ui *u,int i,float x,float y,float w,float h,float f,const float c[4]){(void)u;(void)i;(void)x;(void)y;(void)w;(void)h;(void)f;(void)c;}
void oa_ui_disk(oa_ui *u,float x,float y,float r,const float c[4]){(void)u;(void)x;(void)y;(void)r;(void)c;}
void oa_ui_ring(oa_ui *u,float x,float y,float r,float t,const float c[4]){(void)u;(void)x;(void)y;(void)r;(void)t;(void)c;}
void oa_ui_title(oa_ui *u,float x,float y,float w,float h){(void)u;(void)x;(void)y;(void)w;(void)h;}
float oa_ui_measure(const oa_ui *u,int f,float px,const char *t){(void)u;(void)f;return (float)strlen(t)*px*.5f;}
void oa_ui_text(oa_ui *u,int f,float x,float y,float px,int a,const float c[4],const char *t){(void)u;(void)f;(void)x;(void)y;(void)px;(void)a;(void)c;(void)t;}
static AInputEvent key(int family,int code,int action){AInputEvent e;memset(&e,0,sizeof(e));e.family=family;e.type=AINPUT_EVENT_TYPE_KEY;e.key=code;e.action=action;return e;}
static AInputEvent touch(int action,float x,float y){AInputEvent e;memset(&e,0,sizeof(e));e.family=OPEM_INPUT_TOUCH;e.type=AINPUT_EVENT_TYPE_MOTION;e.action=action;e.count=1;e.x[0]=x;e.y[0]=y;return e;}
static const int W=1260,H=840;
static oa_hud_view view;
static exploration_input play;
static void frame(oa_menu *m){oa_menu_frame(m,NULL,W,H,&view,.016f);}
static void press(oa_menu *m,int family,int code){AInputEvent e=key(family,code,AKEY_EVENT_ACTION_DOWN);oa_menu_event(m,&e,W,H,&play);e.action=AKEY_EVENT_ACTION_UP;oa_menu_event(m,&e,W,H,&play);frame(m);}
static void tap(oa_menu *m,float x,float y){AInputEvent e=touch(AMOTION_EVENT_ACTION_DOWN,x,y);oa_menu_event(m,&e,W,H,&play);e.action=AMOTION_EVENT_ACTION_UP;oa_menu_event(m,&e,W,H,&play);frame(m);}
int main(int argc,char **argv){
 const char *dir=argc>1?argv[1]:".";static oa_menu m;oa_settings s,t;oa_save save,back;char path[1100];AInputEvent e;float r[4],before;
 memset(&view,0,sizeof(view));view.health=.5f;view.foe=-1;view.location="Gorhart";view.health_now=50;view.health_max=100;exploration_input_clear(&play);
 /* Settings */
 oa_settings_default(&s);CHECK(s.hud[OA_HUD_COMPASS].on&&!s.hud[OA_HUD_CROSSHAIR].on&&!s.hud[OA_HUD_RESOURCES].on&&s.opacity==1);
 s.hud[0].scale=NAN;s.hud[1].scale=9;s.hud[2].x=-3;s.opacity=0;s.rate=99;s.look_speed=INFINITY;oa_settings_sanitize(&s);CHECK(s.hud[0].scale==.5f&&s.hud[1].scale==2&&s.hud[2].x==0&&s.opacity==.3f&&s.rate==0&&s.look_speed==.25f);
 snprintf(path,sizeof(path),"%s/oa-menu-test-settings.bin",dir);oa_settings_default(&s);s.hud[OA_HUD_ATTACK].x=.2f;s.hud[OA_HUD_ATTACK].on=0;s.invert_look=1;CHECK(oa_settings_save(&s,path));CHECK(oa_settings_load(&t,path));CHECK(t.hud[OA_HUD_ATTACK].x==.2f&&!t.hud[OA_HUD_ATTACK].on&&t.invert_look);
 {FILE *f=fopen(path,"wb");fputs("garbage",f);fclose(f);}CHECK(!oa_settings_load(&t,path));CHECK(t.hud[OA_HUD_ATTACK].on);remove(path);
 /* Saves */
 snprintf(path,sizeof(path),"%s/oa-menu-test-save.bin",dir);memset(&save,0,sizeof(save));save.world=1;save.feet[0]=12;save.yaw=1.5f;save.health=77;CHECK(oa_save_write(&save,path));CHECK(oa_save_read(&back,path));CHECK(back.world==1&&back.feet[0]==12&&back.health==77);
 save.feet[1]=NAN;CHECK(oa_save_write(&save,path));CHECK(!oa_save_read(&back,path));save.feet[1]=0;save.world=7;CHECK(oa_save_write(&save,path));CHECK(!oa_save_read(&back,path));remove(path);
 /* Title navigation by keyboard */
 snprintf(path,sizeof(path),"%s/oa-menu-test-empty",dir);oa_menu_init(&m,dir,0);remove(m.settings_path);remove(m.save_path);oa_menu_init(&m,dir,0);CHECK(m.screen==OA_SCREEN_TITLE&&!m.has_save);frame(&m);CHECK(m.count==3);
 press(&m,OPEM_INPUT_KEYBOARD,AKEYCODE_ENTER);CHECK(m.action==OA_ACTION_NEW_GAME);m.action=OA_ACTION_NONE;
 press(&m,OPEM_INPUT_KEYBOARD,AKEYCODE_DPAD_DOWN);CHECK(m.focus==1);press(&m,OPEM_INPUT_KEYBOARD,AKEYCODE_ENTER);CHECK(m.screen==OA_SCREEN_OPTIONS&&m.from==OA_SCREEN_TITLE);frame(&m);
 press(&m,OPEM_INPUT_KEYBOARD,AKEYCODE_ESCAPE);CHECK(m.screen==OA_SCREEN_TITLE);frame(&m);
 press(&m,OPEM_INPUT_KEYBOARD,AKEYCODE_DPAD_UP);CHECK(m.focus==2);press(&m,OPEM_INPUT_KEYBOARD,AKEYCODE_ENTER);CHECK(m.action==OA_ACTION_EXIT);m.action=OA_ACTION_NONE;
 /* Controller: hat repeats at one step per edge and A accepts. */
 oa_menu_open(&m,OA_SCREEN_TITLE);frame(&m);memset(&e,0,sizeof(e));e.family=OPEM_INPUT_JOYSTICK;e.type=AINPUT_EVENT_TYPE_MOTION;e.action=AMOTION_EVENT_ACTION_MOVE;e.axes[AMOTION_EVENT_AXIS_HAT_Y]=1;CHECK(oa_menu_event(&m,&e,W,H,&play));frame(&m);CHECK(m.focus==1&&m.device==OA_DEVICE_PAD);frame(&m);CHECK(m.focus==1);
 e.axes[AMOTION_EVENT_AXIS_HAT_Y]=0;oa_menu_event(&m,&e,W,H,&play);frame(&m);press(&m,OPEM_INPUT_GAMEPAD,AKEYCODE_BUTTON_A);CHECK(m.screen==OA_SCREEN_OPTIONS);frame(&m);
 press(&m,OPEM_INPUT_GAMEPAD,AKEYCODE_BUTTON_B);CHECK(m.screen==OA_SCREEN_TITLE);
 /* Touch */
 oa_menu_open(&m,OA_SCREEN_TITLE);frame(&m);tap(&m,200,350);CHECK(m.action==OA_ACTION_NEW_GAME);m.action=OA_ACTION_NONE;tap(&m,900,350);CHECK(m.action==OA_ACTION_NONE&&m.screen==OA_SCREEN_TITLE);
 /* A press that slides off a row does not activate it. */
 e=touch(AMOTION_EVENT_ACTION_DOWN,200,350);oa_menu_event(&m,&e,W,H,&play);e.action=AMOTION_EVENT_ACTION_MOVE;e.x[0]=900;oa_menu_event(&m,&e,W,H,&play);e.action=AMOTION_EVENT_ACTION_UP;oa_menu_event(&m,&e,W,H,&play);frame(&m);CHECK(m.action==OA_ACTION_NONE);
 /* Play routing */
 oa_menu_open(&m,OA_SCREEN_GAME);frame(&m);e=key(OPEM_INPUT_KEYBOARD,AKEYCODE_W,AKEY_EVENT_ACTION_DOWN);CHECK(!oa_menu_event(&m,&e,W,H,&play));
 e=key(OPEM_INPUT_GAMEPAD,AKEYCODE_BUTTON_R2,AKEY_EVENT_ACTION_DOWN);CHECK(oa_menu_event(&m,&e,W,H,&play));CHECK(play.attack_requested);play.attack_requested=0;
 e=key(OPEM_INPUT_GAMEPAD,AKEYCODE_BUTTON_Y,AKEY_EVENT_ACTION_DOWN);CHECK(oa_menu_event(&m,&e,W,H,&play));CHECK(!play.lighting_requested);
 memset(&e,0,sizeof(e));e.family=OPEM_INPUT_JOYSTICK;e.type=AINPUT_EVENT_TYPE_MOTION;e.action=AMOTION_EVENT_ACTION_MOVE;e.axes[AMOTION_EVENT_AXIS_RTRIGGER]=1;CHECK(!oa_menu_event(&m,&e,W,H,&play));CHECK(play.attack_requested);play.attack_requested=0;oa_menu_event(&m,&e,W,H,&play);CHECK(!play.attack_requested);e.axes[AMOTION_EVENT_AXIS_RTRIGGER]=0;oa_menu_event(&m,&e,W,H,&play);
 press(&m,OPEM_INPUT_GAMEPAD,AKEYCODE_BUTTON_START);CHECK(m.screen==OA_SCREEN_PAUSE);frame(&m);press(&m,OPEM_INPUT_GAMEPAD,AKEYCODE_BUTTON_B);CHECK(m.screen==OA_SCREEN_GAME);
 e=key(OPEM_INPUT_KEYBOARD,AKEYCODE_BACK,AKEY_EVENT_ACTION_DOWN);CHECK(oa_menu_event(&m,&e,W,H,&play));CHECK(m.screen==OA_SCREEN_PAUSE);oa_menu_open(&m,OA_SCREEN_GAME);frame(&m);
 /* Mouse: left attacks, right drag looks, the menu button opens the menu. */
 memset(&e,0,sizeof(e));e.family=OPEM_INPUT_MOUSE;e.type=AINPUT_EVENT_TYPE_MOTION;e.action=AMOTION_EVENT_ACTION_DOWN;e.count=1;e.x[0]=500;e.y[0]=400;e.buttons=AMOTION_EVENT_BUTTON_PRIMARY;CHECK(oa_menu_event(&m,&e,W,H,&play));CHECK(play.attack_requested);play.attack_requested=0;
 e.buttons=AMOTION_EVENT_BUTTON_SECONDARY;oa_menu_event(&m,&e,W,H,&play);e.action=AMOTION_EVENT_ACTION_MOVE;e.x[0]=626;oa_menu_event(&m,&e,W,H,&play);CHECK(play.look_dx>.29f&&!play.attack_requested);e.action=AMOTION_EVENT_ACTION_UP;e.buttons=0;oa_menu_event(&m,&e,W,H,&play);CHECK(!m.mouse_look);play.look_dx=0;
 oa_hud_rect(&m,OA_HUD_MENU,W,H,r);e.action=AMOTION_EVENT_ACTION_DOWN;e.buttons=AMOTION_EVENT_BUTTON_PRIMARY;e.x[0]=r[0]+5;e.y[0]=r[1]+5;oa_menu_event(&m,&e,W,H,&play);CHECK(m.screen==OA_SCREEN_PAUSE);oa_menu_open(&m,OA_SCREEN_GAME);frame(&m);
 /* Touch zones follow the configured HUD. */
 oa_hud_rect(&m,OA_HUD_ATTACK,W,H,r);e=touch(AMOTION_EVENT_ACTION_DOWN,r[0]+r[2]*.5f,r[1]+r[3]*.5f);CHECK(exploration_input_event(&play,&e,W,H));CHECK(play.attack_requested&&play.look_id<0);exploration_input_clear(&play);
 oa_hud_rect(&m,OA_HUD_MENU,W,H,r);e=touch(AMOTION_EVENT_ACTION_DOWN,r[0]+r[2]*.5f,r[1]+r[3]*.5f);CHECK(exploration_input_event(&play,&e,W,H));CHECK(play.menu_requested);exploration_input_clear(&play);
 m.settings.hud[OA_HUD_ATTACK].on=0;frame(&m);oa_hud_rect(&m,OA_HUD_ATTACK,W,H,r);e=touch(AMOTION_EVENT_ACTION_DOWN,r[0]+r[2]*.5f,r[1]+r[3]*.5f);exploration_input_event(&play,&e,W,H);CHECK(!play.attack_requested&&play.look_id==0);exploration_input_clear(&play);m.settings.hud[OA_HUD_ATTACK].on=1;
 m.settings.hud[OA_HUD_ATTACK].x=.2f;m.settings.hud[OA_HUD_ATTACK].y=.2f;frame(&m);oa_hud_rect(&m,OA_HUD_ATTACK,W,H,r);e=touch(AMOTION_EVENT_ACTION_DOWN,r[0]+r[2]*.5f,r[1]+r[3]*.5f);exploration_input_event(&play,&e,W,H);CHECK(play.attack_requested);exploration_input_clear(&play);oa_settings_default(&m.settings);
 /* The prompt zone exists only while a prompt shows. */
 frame(&m);oa_hud_rect(&m,OA_HUD_PROMPT,W,H,r);e=touch(AMOTION_EVENT_ACTION_DOWN,r[0]+r[2]*.5f,r[1]+r[3]*.5f);exploration_input_event(&play,&e,W,H);CHECK(!play.interact_requested);exploration_input_clear(&play);
 view.prompt="Enter Shop";frame(&m);exploration_input_event(&play,&e,W,H);CHECK(play.interact_requested);exploration_input_clear(&play);view.prompt=NULL;
 /* Layout editor by controller */
 oa_menu_open(&m,OA_SCREEN_OPTIONS);frame(&m);press(&m,OPEM_INPUT_GAMEPAD,AKEYCODE_BUTTON_A);CHECK(m.screen==OA_SCREEN_LAYOUT);frame(&m);CHECK(m.count==OA_HUD_COUNT+2);
 CHECK(m.selected==0&&m.settings.hud[0].on);press(&m,OPEM_INPUT_GAMEPAD,AKEYCODE_BUTTON_A);CHECK(!m.settings.hud[0].on);press(&m,OPEM_INPUT_GAMEPAD,AKEYCODE_BUTTON_A);CHECK(m.settings.hud[0].on);
 press(&m,OPEM_INPUT_GAMEPAD,AKEYCODE_DPAD_RIGHT);CHECK(fabsf(m.settings.hud[0].scale-1.1f)<.001f);
 press(&m,OPEM_INPUT_GAMEPAD,AKEYCODE_DPAD_DOWN);frame(&m);CHECK(m.selected==1);
 before=m.settings.hud[1].x;memset(&e,0,sizeof(e));e.family=OPEM_INPUT_JOYSTICK;e.type=AINPUT_EVENT_TYPE_MOTION;e.action=AMOTION_EVENT_ACTION_MOVE;e.axes[AMOTION_EVENT_AXIS_X]=1;oa_menu_event(&m,&e,W,H,&play);frame(&m);CHECK(m.settings.hud[1].x>before&&m.selected==1);
 {int i;for(i=0;i<2000;i++)frame(&m);oa_hud_rect(&m,1,W,H,r);CHECK(r[0]+r[2]<=W+.5f);}e.axes[AMOTION_EVENT_AXIS_X]=0;oa_menu_event(&m,&e,W,H,&play);
 {int i;for(i=0;i<40;i++)press(&m,OPEM_INPUT_GAMEPAD,AKEYCODE_DPAD_RIGHT);CHECK(m.settings.hud[1].scale==2);for(i=0;i<40;i++)press(&m,OPEM_INPUT_GAMEPAD,AKEYCODE_DPAD_LEFT);CHECK(m.settings.hud[1].scale==.5f);}
 /* Layout editor by touch: drag the attack button, then keyboard WASD. */
 oa_settings_default(&m.settings);frame(&m);oa_hud_rect(&m,OA_HUD_ATTACK,W,H,r);before=m.settings.hud[OA_HUD_ATTACK].x;
 m.settings.hud[OA_HUD_ATTACK].x=.5f;oa_hud_rect(&m,OA_HUD_ATTACK,W,H,r);e=touch(AMOTION_EVENT_ACTION_DOWN,r[0]+r[2]*.5f,r[1]+r[3]*.5f);oa_menu_event(&m,&e,W,H,&play);frame(&m);CHECK(m.selected==OA_HUD_ATTACK&&m.dragging);
 e.action=AMOTION_EVENT_ACTION_MOVE;e.x[0]-=126;oa_menu_event(&m,&e,W,H,&play);frame(&m);CHECK(fabsf(m.settings.hud[OA_HUD_ATTACK].x-.4f)<.002f);e.action=AMOTION_EVENT_ACTION_UP;oa_menu_event(&m,&e,W,H,&play);frame(&m);CHECK(!m.dragging);
 before=m.settings.hud[OA_HUD_ATTACK].y;e=key(OPEM_INPUT_KEYBOARD,AKEYCODE_S,AKEY_EVENT_ACTION_DOWN);oa_menu_event(&m,&e,W,H,&play);frame(&m);CHECK(m.settings.hud[OA_HUD_ATTACK].y>before);e.action=AKEY_EVENT_ACTION_UP;oa_menu_event(&m,&e,W,H,&play);before=m.settings.hud[OA_HUD_ATTACK].y;frame(&m);CHECK(m.settings.hud[OA_HUD_ATTACK].y==before);
 /* Leaving the layout persists it. */
 press(&m,OPEM_INPUT_KEYBOARD,AKEYCODE_ESCAPE);CHECK(m.screen==OA_SCREEN_OPTIONS);frame(&m);CHECK(oa_settings_load(&t,m.settings_path));CHECK(fabsf(t.hud[OA_HUD_ATTACK].x-.4f)<.002f);remove(m.settings_path);
 CHECK(oa_menu_rate(&m)==0);m.settings.rate=3;CHECK(oa_menu_rate(&m)==120);
 /* Items */
 {oa_bag b;oa_bag_new(&b);CHECK(oa_bag_damage(&b)==22&&oa_bag_weapon_model(&b)==0&&oa_bag_armor(&b)==61);CHECK(oa_bag_equip(&b,OA_ITEM_IRON));CHECK(oa_bag_damage(&b)==14&&oa_bag_weapon_model(&b)==1);
  CHECK(!oa_bag_equip(&b,OA_ITEM_PRISMERE));CHECK(!oa_bag_unequip(&b,OA_ITEM_IRON));CHECK(oa_bag_unequip(&b,OA_ITEM_VIGILANT_CUIRASS));CHECK(oa_bag_armor(&b)==31);CHECK(!oa_bag_is_equipped(&b,OA_ITEM_VIGILANT_CUIRASS));
  CHECK(oa_bag_use(&b,OA_ITEM_MINOR_POTION,90,100)==10&&b.count[OA_ITEM_MINOR_POTION]==2);CHECK(oa_bag_use(&b,OA_ITEM_MINOR_POTION,100,100)==0&&b.count[OA_ITEM_MINOR_POTION]==2);CHECK(oa_bag_use(&b,OA_ITEM_MINOR_POTION,0,100)==0);CHECK(oa_bag_use(&b,OA_ITEM_IRON,50,100)==0);
  CHECK(fabsf(oa_armor_scale(100)-.5f)<.001f);b.equipped[OA_SLOT_WEAPON]=999;b.equipped[OA_SLOT_HEAD]=OA_ITEM_IRON;oa_bag_sanitize(&b);CHECK(b.equipped[OA_SLOT_WEAPON]==OA_ITEM_STEEL&&b.equipped[OA_SLOT_HEAD]==-1);
  oa_bag_add(&b,OA_ITEM_PRISMERE,1);CHECK(b.count[OA_ITEM_PRISMERE]==1);CHECK(oa_bag_equip(&b,OA_ITEM_PRISMERE)&&oa_bag_weapon_model(&b)==4);}
 /* Inventory screen by controller: opens from play, tabs, sorts, equips, returns. */
 {oa_reagent_row rr[1]={{"Damage",4}};view.reagents=rr;view.reagent_count=1;view.health_now=50;view.health_max=100;oa_bag_new(&m.bag);oa_menu_open(&m,OA_SCREEN_GAME);frame(&m);
  press(&m,OPEM_INPUT_GAMEPAD,AKEYCODE_BUTTON_SELECT);CHECK(m.screen==OA_SCREEN_INVENTORY&&m.inv_tab==OA_TAB_ALL);frame(&m);
  press(&m,OPEM_INPUT_GAMEPAD,AKEYCODE_BUTTON_R1);CHECK(m.inv_tab==OA_TAB_WEAPONS);frame(&m);
  /* Sorted by power: steel first, then iron. */
  CHECK(m.inv_row==0);press(&m,OPEM_INPUT_GAMEPAD,AKEYCODE_DPAD_DOWN);CHECK(m.inv_row==1);press(&m,OPEM_INPUT_GAMEPAD,AKEYCODE_BUTTON_A);CHECK(m.bag.equipped[OA_SLOT_WEAPON]==OA_ITEM_IRON);
  press(&m,OPEM_INPUT_GAMEPAD,AKEYCODE_BUTTON_A);CHECK(m.bag.equipped[OA_SLOT_WEAPON]==OA_ITEM_IRON);
  press(&m,OPEM_INPUT_GAMEPAD,AKEYCODE_DPAD_RIGHT);CHECK(m.inv_tab==OA_TAB_ARMOR);press(&m,OPEM_INPUT_GAMEPAD,AKEYCODE_DPAD_RIGHT);CHECK(m.inv_tab==OA_TAB_CONSUMABLES);frame(&m);
  press(&m,OPEM_INPUT_GAMEPAD,AKEYCODE_BUTTON_A);CHECK(m.bag.count[OA_ITEM_MINOR_POTION]==2&&m.heal_request==25);m.heal_request=0;
  view.health_now=100;press(&m,OPEM_INPUT_GAMEPAD,AKEYCODE_BUTTON_A);CHECK(m.bag.count[OA_ITEM_MINOR_POTION]==2);view.health_now=50;
  press(&m,OPEM_INPUT_GAMEPAD,AKEYCODE_BUTTON_L1);press(&m,OPEM_INPUT_GAMEPAD,AKEYCODE_BUTTON_L1);press(&m,OPEM_INPUT_GAMEPAD,AKEYCODE_BUTTON_L1);press(&m,OPEM_INPUT_GAMEPAD,AKEYCODE_BUTTON_L1);CHECK(m.inv_tab==OA_TAB_REAGENTS);frame(&m);
  press(&m,OPEM_INPUT_GAMEPAD,AKEYCODE_BUTTON_B);CHECK(m.screen==OA_SCREEN_GAME);
  /* Opened from pause, back returns to pause; keyboard I and touch rail and rows. */
  oa_menu_open(&m,OA_SCREEN_PAUSE);frame(&m);press(&m,OPEM_INPUT_KEYBOARD,AKEYCODE_DPAD_DOWN);press(&m,OPEM_INPUT_KEYBOARD,AKEYCODE_ENTER);CHECK(m.screen==OA_SCREEN_INVENTORY);frame(&m);press(&m,OPEM_INPUT_KEYBOARD,AKEYCODE_ESCAPE);CHECK(m.screen==OA_SCREEN_PAUSE);
  oa_menu_open(&m,OA_SCREEN_GAME);frame(&m);e=key(OPEM_INPUT_KEYBOARD,AKEYCODE_I,AKEY_EVENT_ACTION_DOWN);CHECK(oa_menu_event(&m,&e,W,H,&play));CHECK(m.screen==OA_SCREEN_INVENTORY);frame(&m);
  m.inv_tab=OA_TAB_ALL;tap(&m,44,96+72+32);CHECK(m.inv_tab==OA_TAB_WEAPONS);tap(&m,400,137+56+28);CHECK(m.inv_row==1);
  m.inv_sort=1;tap(&m,200,110);CHECK(m.inv_sort==0&&m.inv_dir==1);
  /* A scroll drag does not select. */
  m.inv_tab=OA_TAB_ALL;m.inv_row=0;frame(&m);e=touch(AMOTION_EVENT_ACTION_DOWN,400,300);oa_menu_event(&m,&e,W,H,&play);frame(&m);e.action=AMOTION_EVENT_ACTION_MOVE;e.y[0]=240;oa_menu_event(&m,&e,W,H,&play);frame(&m);e.action=AMOTION_EVENT_ACTION_UP;oa_menu_event(&m,&e,W,H,&play);frame(&m);CHECK(m.inv_row==0);view.reagents=NULL;view.reagent_count=0;}
 /* Save keeps the bag. */
 {oa_save a,c;snprintf(path,sizeof(path),"%s/oa-menu-test-save.bin",dir);memset(&a,0,sizeof(a));oa_bag_new(&a.bag);a.bag.gold=777;a.bag.equipped[OA_SLOT_WEAPON]=OA_ITEM_IRON;CHECK(oa_save_write(&a,path));CHECK(oa_save_read(&c,path));CHECK(c.bag.gold==777&&c.bag.equipped[OA_SLOT_WEAPON]==OA_ITEM_IRON);remove(path);}
 printf("oa-menu-test: %u checks passed\n",checks);return 0;
}
