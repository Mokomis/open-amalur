#include "exploration_input.h"
#include "android_input_probe.h"
#include <android/keycodes.h>
#include <math.h>
#include <string.h>
static float bounded(float v){return isfinite(v)?fmaxf(-1,fminf(1,v)):0;}
static float deadzone(float v){v=bounded(v);return fabsf(v)<0.18f?0:copysignf((fabsf(v)-0.18f)/0.82f,v);}
float exploration_ui_scale(int w,int h){return fmaxf(1.0f,fminf((float)w/960.0f,(float)h/540.0f));}
void exploration_input_clear(exploration_input *s){memset(s,0,sizeof(*s));s->move_id=s->look_id=s->keyboard_device=s->pad_device=-1;}
static int touch(exploration_input *s,AInputEvent *e,int w,int h){
    int raw=AMotionEvent_getAction(e),action=raw&AMOTION_EVENT_ACTION_MASK;
    size_t count=AMotionEvent_getPointerCount(e),index=(unsigned)raw>>AMOTION_EVENT_ACTION_POINTER_INDEX_SHIFT,i;
    float scale=exploration_ui_scale(w,h),radius=70*scale;
    if(action==AMOTION_EVENT_ACTION_CANCEL){exploration_input_clear(s);return 1;}
    if(!count||index>=count||w<=0||h<=0)return 0;
    if(action==AMOTION_EVENT_ACTION_DOWN){s->move_id=s->look_id=-1;s->move_x=s->move_y=0;}
    if(action==AMOTION_EVENT_ACTION_DOWN||action==AMOTION_EVENT_ACTION_POINTER_DOWN){
        int id=AMotionEvent_getPointerId(e,index);float x=AMotionEvent_getX(e,index),y=AMotionEvent_getY(e,index);
        if(!isfinite(x)||!isfinite(y))return 0;
        if(y>h-112*scale&&y<h-60*scale&&fabsf(x-w*.5f)<160*scale){s->interact_requested=1;return 1;}
        if(y<68*scale&&x>w-400*scale&&x<w-272*scale){s->lighting_requested=1;return 1;}
        if(y<68*scale&&x>w-260*scale&&x<w-140*scale){s->reset_requested=1;return 1;}
        if(y<68*scale&&x>=w-140*scale){s->toggle_requested=1;return 1;}
        if(x<w*.45f&&s->move_id<0){s->move_id=id;s->move_origin_x=x;s->move_origin_y=y;s->move_x=s->move_y=0;}
        else if(x>=w*.45f&&s->look_id<0){s->look_id=id;s->look_x=x;s->look_y=y;}
    }
    if(action==AMOTION_EVENT_ACTION_UP||action==AMOTION_EVENT_ACTION_POINTER_UP){
        int id=AMotionEvent_getPointerId(e,index);
        if(id==s->move_id){s->move_id=-1;s->move_x=s->move_y=0;}
        if(id==s->look_id)s->look_id=-1;
        return 1;
    }
    if(action==AMOTION_EVENT_ACTION_MOVE)for(i=0;i<count;++i){
        int id=AMotionEvent_getPointerId(e,i);float x=AMotionEvent_getX(e,i),y=AMotionEvent_getY(e,i);
        if(!isfinite(x)||!isfinite(y)){exploration_input_clear(s);return 1;}
        if(id==s->move_id){double dx=((double)x-s->move_origin_x)/radius,dy=((double)y-s->move_origin_y)/radius,n=sqrt(dx*dx+dy*dy);if(n>1){dx/=n;dy/=n;}s->move_x=(float)dx;s->move_y=(float)-dy;}
        if(id==s->look_id){s->look_dx+=bounded((x-s->look_x)/(float)w)*3.0f;s->look_dy+=bounded((y-s->look_y)/(float)h)*2.0f;s->look_x=x;s->look_y=y;}
    }
    return 1;
}
int exploration_input_event(exploration_input *s,AInputEvent *e,int w,int h){
    enum opem_input_family family=opem_android_event_family(e);int type=AInputEvent_getType(e),device=AInputEvent_getDeviceId(e);
    if(family==OPEM_INPUT_TOUCH)return touch(s,e,w,h);
    if(family==OPEM_INPUT_JOYSTICK&&type==AINPUT_EVENT_TYPE_MOTION){
        if((AMotionEvent_getAction(e)&AMOTION_EVENT_ACTION_MASK)==AMOTION_EVENT_ACTION_CANCEL){exploration_input_clear(s);return 1;}
        s->pad_device=device;s->pad_x=deadzone(AMotionEvent_getAxisValue(e,AMOTION_EVENT_AXIS_X,0));s->pad_y=-deadzone(AMotionEvent_getAxisValue(e,AMOTION_EVENT_AXIS_Y,0));
        s->pad_look_x=deadzone(AMotionEvent_getAxisValue(e,AMOTION_EVENT_AXIS_Z,0));s->pad_look_y=-deadzone(AMotionEvent_getAxisValue(e,AMOTION_EVENT_AXIS_RZ,0));return 1;
    }
    if(type==AINPUT_EVENT_TYPE_KEY&&(family==OPEM_INPUT_KEYBOARD||family==OPEM_INPUT_GAMEPAD)){
        int key=AKeyEvent_getKeyCode(e),action=AKeyEvent_getAction(e);unsigned bit=0;
        if(AKeyEvent_getFlags(e)&AKEY_EVENT_FLAG_CANCELED){exploration_input_clear(s);return 1;}
        switch(key){case AKEYCODE_L:case AKEYCODE_BUTTON_Y:if(action==AKEY_EVENT_ACTION_DOWN&&!AKeyEvent_getRepeatCount(e))s->lighting_requested=1;return 1;
          case AKEYCODE_W:bit=1;break;case AKEYCODE_S:bit=2;break;case AKEYCODE_A:bit=4;break;case AKEYCODE_D:bit=8;break;
          case AKEYCODE_E:case AKEYCODE_BUTTON_A:if(action==AKEY_EVENT_ACTION_DOWN&&!AKeyEvent_getRepeatCount(e))s->interact_requested=1;return 1;
          case AKEYCODE_DPAD_LEFT:bit=16;break;case AKEYCODE_DPAD_RIGHT:bit=32;break;case AKEYCODE_DPAD_UP:bit=64;break;case AKEYCODE_DPAD_DOWN:bit=128;break;
          case AKEYCODE_R:case AKEYCODE_BUTTON_SELECT:if(action==AKEY_EVENT_ACTION_DOWN&&!AKeyEvent_getRepeatCount(e))s->reset_requested=1;return 1;
          case AKEYCODE_V:case AKEYCODE_BUTTON_START:if(action==AKEY_EVENT_ACTION_DOWN&&!AKeyEvent_getRepeatCount(e))s->toggle_requested=1;return 1;default:return 0;}
        /* One active keyboard, so releasing another device cannot leave an old held key. */
        if(s->keyboard_device!=device){s->keys=0;s->keyboard_device=device;}
        if(action==AKEY_EVENT_ACTION_DOWN)s->keys|=bit;else if(action==AKEY_EVENT_ACTION_UP)s->keys&=~bit;return 1;
    }
    return 0;
}
void exploration_input_axes(exploration_input *s,float *right,float *forward,float *yaw,float *pitch){
    float x=s->move_x+s->pad_x+!!(s->keys&8)-!!(s->keys&4),y=s->move_y+s->pad_y+!!(s->keys&1)-!!(s->keys&2),n=sqrtf(x*x+y*y);
    if(n>1){x/=n;y/=n;}*right=x;*forward=y;
    *yaw=bounded(s->pad_look_x+!!(s->keys&32)-!!(s->keys&16))*1.7f;
    *pitch=bounded(s->pad_look_y+!!(s->keys&64)-!!(s->keys&128))*1.4f;
}
