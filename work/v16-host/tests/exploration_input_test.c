#include "exploration_input.h"
#include "android_input_probe.h"
#include <android/keycodes.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
static unsigned checks;
#define CHECK(v) do{++checks;if(!(v)){fprintf(stderr,"input check failed line %d: %s\n",__LINE__,#v);return 1;}}while(0)
enum opem_input_family opem_android_event_family(const AInputEvent *e){return (enum opem_input_family)e->family;}
static int near(float a,float b){return fabsf(a-b)<.0001f;}
int main(void){
 exploration_input s;AInputEvent e={0};float x,y,yaw,pitch;exploration_input_clear(&s);
 CHECK(s.move_id==-1&&s.look_id==-1&&s.pad_device==-1&&s.keyboard_device==-1);
 exploration_input_axes(&s,&x,&y,&yaw,&pitch);CHECK(x==0&&y==0&&yaw==0&&pitch==0);
 e.family=OPEM_INPUT_KEYBOARD;e.type=AINPUT_EVENT_TYPE_KEY;e.device=7;e.key=AKEYCODE_W;
 CHECK(exploration_input_event(&s,&e,960,540));exploration_input_axes(&s,&x,&y,&yaw,&pitch);CHECK(y==1&&x==0);
 e.key=AKEYCODE_D;CHECK(exploration_input_event(&s,&e,960,540));exploration_input_axes(&s,&x,&y,&yaw,&pitch);CHECK(near(x*x+y*y,1)&&x>0&&y>0);
 e.action=AKEY_EVENT_ACTION_UP;e.key=AKEYCODE_W;CHECK(exploration_input_event(&s,&e,960,540));exploration_input_axes(&s,&x,&y,&yaw,&pitch);CHECK(x==1&&y==0);
 e.device=8;e.key=AKEYCODE_A;e.action=AKEY_EVENT_ACTION_DOWN;CHECK(exploration_input_event(&s,&e,960,540));CHECK(s.keys==4&&s.keyboard_device==8);
 e.flags=AKEY_EVENT_FLAG_CANCELED;CHECK(exploration_input_event(&s,&e,960,540));CHECK(s.keys==0&&s.keyboard_device==-1);e.flags=0;
 e.key=999;CHECK(!exploration_input_event(&s,&e,960,540));
 e.key=AKEYCODE_R;e.repeat=1;CHECK(exploration_input_event(&s,&e,960,540));CHECK(!s.reset_requested);e.repeat=0;exploration_input_event(&s,&e,960,540);CHECK(s.reset_requested);
 exploration_input_clear(&s);e=(AInputEvent){0};e.family=OPEM_INPUT_JOYSTICK;e.type=AINPUT_EVENT_TYPE_MOTION;e.device=9;e.action=AMOTION_EVENT_ACTION_MOVE;
 e.axes[AMOTION_EVENT_AXIS_X]=.1f;e.axes[AMOTION_EVENT_AXIS_Y]=-1;e.axes[AMOTION_EVENT_AXIS_Z]=1;e.axes[AMOTION_EVENT_AXIS_RZ]=-1;
 CHECK(exploration_input_event(&s,&e,960,540));exploration_input_axes(&s,&x,&y,&yaw,&pitch);CHECK(x==0&&y==1&&near(yaw,1.7f)&&near(pitch,1.4f));
 e.axes[AMOTION_EVENT_AXIS_X]=NAN;e.axes[AMOTION_EVENT_AXIS_Y]=INFINITY;exploration_input_event(&s,&e,960,540);CHECK(s.pad_x==0&&s.pad_y==0);
 e.action=AMOTION_EVENT_ACTION_CANCEL;exploration_input_event(&s,&e,960,540);CHECK(s.pad_device==-1&&s.pad_look_x==0);
 e=(AInputEvent){0};e.family=OPEM_INPUT_TOUCH;e.type=AINPUT_EVENT_TYPE_MOTION;e.count=1;e.ids[0]=17;e.x[0]=100;e.y[0]=300;
 CHECK(exploration_input_event(&s,&e,960,540));CHECK(s.move_id==17&&s.look_id==-1);
 e.count=2;e.ids[1]=42;e.x[1]=700;e.y[1]=300;e.action=AMOTION_EVENT_ACTION_POINTER_DOWN|(1<<8);
 CHECK(exploration_input_event(&s,&e,960,540));CHECK(s.look_id==42&&s.move_id==17);
 /* Reordered pointer indices must preserve each finger's role. */
 e.ids[0]=42;e.x[0]=730;e.y[0]=310;e.ids[1]=17;e.x[1]=170;e.y[1]=230;e.action=AMOTION_EVENT_ACTION_MOVE;
 CHECK(exploration_input_event(&s,&e,960,540));CHECK(s.look_dx>0&&s.look_dy>0);exploration_input_axes(&s,&x,&y,&yaw,&pitch);CHECK(near(x*x+y*y,1)&&x>0&&y>0);
 e.action=AMOTION_EVENT_ACTION_POINTER_UP|(1<<8);exploration_input_event(&s,&e,960,540);CHECK(s.move_id==-1&&s.look_id==42&&s.move_x==0&&s.move_y==0);
 e.count=1;e.action=AMOTION_EVENT_ACTION_MOVE;e.x[0]=NAN;exploration_input_event(&s,&e,960,540);CHECK(s.look_id==-1&&s.look_dx==0);
 e=(AInputEvent){0};e.family=OPEM_INPUT_TOUCH;e.type=AINPUT_EVENT_TYPE_MOTION;e.count=1;e.x[0]=750;e.y[0]=30;exploration_input_event(&s,&e,960,540);CHECK(s.reset_requested&&s.move_id==-1&&s.look_id==-1);
 exploration_input_clear(&s);e.x[0]=900;exploration_input_event(&s,&e,960,540);CHECK(s.toggle_requested&&s.move_id==-1&&s.look_id==-1);
 exploration_input_clear(&s);e.action=AMOTION_EVENT_ACTION_CANCEL;CHECK(exploration_input_event(&s,&e,960,540));CHECK(!s.toggle_requested&&!s.reset_requested);
 e.family=OPEM_INPUT_OTHER;CHECK(!exploration_input_event(&s,&e,960,540));CHECK(near(exploration_ui_scale(1920,1080),2));
 printf("exploration-input-test: %u checks passed\n",checks);return 0;
}
