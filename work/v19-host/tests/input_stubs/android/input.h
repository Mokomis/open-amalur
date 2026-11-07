#ifndef TEST_ANDROID_INPUT_H
#define TEST_ANDROID_INPUT_H
#include <stddef.h>
#include <stdint.h>
/* Synthetic event transport for portable control tests, never linked in APK. */
typedef struct AInputEvent {int family,type,device,action,key,repeat,flags,buttons;size_t count;int ids[4];float x[4],y[4],axes[32];} AInputEvent;
enum {AINPUT_EVENT_TYPE_KEY=1,AINPUT_EVENT_TYPE_MOTION=2,AKEY_EVENT_ACTION_DOWN=0,AKEY_EVENT_ACTION_UP=1,AKEY_EVENT_FLAG_CANCELED=32,
AMOTION_EVENT_ACTION_DOWN=0,AMOTION_EVENT_ACTION_UP=1,AMOTION_EVENT_ACTION_MOVE=2,AMOTION_EVENT_ACTION_CANCEL=3,AMOTION_EVENT_ACTION_POINTER_DOWN=5,AMOTION_EVENT_ACTION_POINTER_UP=6,
AMOTION_EVENT_ACTION_MASK=255,AMOTION_EVENT_ACTION_POINTER_INDEX_SHIFT=8,AMOTION_EVENT_AXIS_X=0,AMOTION_EVENT_AXIS_Y=1,AMOTION_EVENT_AXIS_Z=11,AMOTION_EVENT_AXIS_RZ=14,AMOTION_EVENT_AXIS_VSCROLL=9,AMOTION_EVENT_AXIS_HAT_X=15,AMOTION_EVENT_AXIS_HAT_Y=16,AMOTION_EVENT_AXIS_RTRIGGER=18,AMOTION_EVENT_AXIS_GAS=22,AMOTION_EVENT_ACTION_HOVER_MOVE=7,AMOTION_EVENT_ACTION_SCROLL=8,AMOTION_EVENT_BUTTON_PRIMARY=1,AMOTION_EVENT_BUTTON_SECONDARY=2};
static inline int32_t AMotionEvent_getButtonState(const AInputEvent *e){return e->buttons;}
static inline int32_t AInputEvent_getType(const AInputEvent *e){return e->type;}
static inline int32_t AInputEvent_getDeviceId(const AInputEvent *e){return e->device;}
static inline int32_t AMotionEvent_getAction(const AInputEvent *e){return e->action;}
static inline size_t AMotionEvent_getPointerCount(const AInputEvent *e){return e->count;}
static inline int32_t AMotionEvent_getPointerId(const AInputEvent *e,size_t i){return e->ids[i];}
static inline float AMotionEvent_getX(const AInputEvent *e,size_t i){return e->x[i];}
static inline float AMotionEvent_getY(const AInputEvent *e,size_t i){return e->y[i];}
static inline float AMotionEvent_getAxisValue(const AInputEvent *e,int32_t axis,size_t i){(void)i;return e->axes[axis];}
static inline int32_t AKeyEvent_getKeyCode(const AInputEvent *e){return e->key;}
static inline int32_t AKeyEvent_getAction(const AInputEvent *e){return e->action;}
static inline int32_t AKeyEvent_getRepeatCount(const AInputEvent *e){return e->repeat;}
static inline int32_t AKeyEvent_getFlags(const AInputEvent *e){return e->flags;}
#endif
