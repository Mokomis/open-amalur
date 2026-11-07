#ifndef OA_MENU_H
#define OA_MENU_H
/* Veil menus and configurable HUD for touch, controller, mouse and keyboard. */
#include "exploration_input.h"
#include "oa_ui.h"
#include "oa_items.h"
enum{OA_HUD_COMPASS,OA_HUD_LOCATION,OA_HUD_HEALTH,OA_HUD_RESOURCES,OA_HUD_ENEMY,OA_HUD_PROMPT,OA_HUD_STICK,OA_HUD_ATTACK,OA_HUD_MENU,OA_HUD_CROSSHAIR,OA_HUD_COUNT};
typedef enum oa_screen{OA_SCREEN_GAME,OA_SCREEN_TITLE,OA_SCREEN_PAUSE,OA_SCREEN_OPTIONS,OA_SCREEN_LAYOUT,OA_SCREEN_INVENTORY}oa_screen;
typedef enum oa_menu_action{OA_ACTION_NONE,OA_ACTION_NEW_GAME,OA_ACTION_LOAD,OA_ACTION_SAVE,OA_ACTION_EXIT,OA_ACTION_APPLY_RATE,OA_ACTION_TOGGLE_LIGHTING}oa_menu_action;
enum{OA_DEVICE_TOUCH,OA_DEVICE_PAD,OA_DEVICE_KEYBOARD};
typedef struct oa_hud_item{int on;float scale,x,y;}oa_hud_item;
typedef struct oa_settings{oa_hud_item hud[OA_HUD_COUNT];float opacity,look_speed;int invert_look,rate,shadows,canopy_dense;}oa_settings;
/* What the game tells the HUD this frame. */
typedef struct oa_reagent_row{const char *name;unsigned count;}oa_reagent_row;
typedef struct oa_hud_view{float health,foe,health_now,health_max,yaw,target_x,target_y,feet_x,feet_y;int dead,has_target,show_hud,room_lighting;const char *location,*zone,*prompt,*foe_name;int move_active;float move_origin_x,move_origin_y,move_x,move_y;const oa_reagent_row *reagents;int reagent_count;}oa_hud_view;
/* OASAV002 retains its legacy 88B prefix; appended Space 0 means unknown. */
typedef struct oa_save{char magic[8];int world;float feet[3],yaw,pitch,health;oa_bag bag;uint32_t space;}oa_save;
typedef struct oa_menu{
 oa_screen screen,from;
 oa_settings settings;
 oa_menu_action action;
 int focus,count,device,has_save,dirty;
 /* Pointer, touch or mouse, in pixels. */
 int pointer_id,pointer_down,pressed,released,hovered,mouse_look;float px,py,press_x,press_y,last_x,last_y;
 /* One-shot navigation from keys, sticks and hats. */
 int nav_x,nav_y,accept,back,reset,trigger;float wheel;
 float axis_x,axis_y,hat_x,hat_y,nav_timer;int axis_nav_x,axis_nav_y,keys_move;
 int selected,dragging,panel_left;float dirty_age;
 /* Inventory */
 oa_bag bag;oa_screen inv_from;int inv_tab,inv_row,inv_sort,inv_dir,tab_step,sort_step,inv_scroll_drag;float inv_scroll,heal_request;
 float status_time;const char *status;
 char settings_path[1024],save_path[1024];
}oa_menu;
const char *oa_hud_name(int item);
void oa_settings_default(oa_settings *s);
void oa_settings_sanitize(oa_settings *s);
int oa_settings_save(const oa_settings *s,const char *path);
int oa_settings_load(oa_settings *s,const char *path);
int oa_save_write(const oa_save *save,const char *path);
int oa_save_read(oa_save *save,const char *path);
void oa_menu_init(oa_menu *m,const char *data_dir,int start_in_game);
void oa_menu_open(oa_menu *m,oa_screen screen);
void oa_menu_status(oa_menu *m,const char *text);
int oa_menu_rate(const oa_menu *m);
/* Canopy selection: 0 Corrected (default), 1 Dense. Renderer owns the selector. */
int oa_menu_canopy_dense(const oa_menu *m);
/* Returns 1 when consumed. During play only menu, attack-trigger and mouse events are taken here. */
int oa_menu_event(oa_menu *m,AInputEvent *event,int width,int height,exploration_input *play);
void oa_hud_rect(const oa_menu *m,int item,int width,int height,float rect[4]);
void oa_menu_frame(oa_menu *m,oa_ui *u,int width,int height,const oa_hud_view *view,float dt);
#endif
