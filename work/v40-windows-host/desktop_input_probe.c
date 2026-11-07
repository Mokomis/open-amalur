#include "android_input_probe.h"
#include <math.h>
#include <string.h>

static int has_source(int32_t sources, int32_t mask) {
    return (sources & mask) == mask;
}

enum opem_input_family opem_android_event_family(const AInputEvent *event) {
    int32_t source, type;
    if (!event) return OPEM_INPUT_OTHER;
    source = AInputEvent_getSource(event);
    type = AInputEvent_getType(event);
    if (type == AINPUT_EVENT_TYPE_MOTION) {
        if (has_source(source, AINPUT_SOURCE_JOYSTICK)) return OPEM_INPUT_JOYSTICK;
        if (has_source(source, AINPUT_SOURCE_MOUSE)) return OPEM_INPUT_MOUSE;
        if (has_source(source, AINPUT_SOURCE_TOUCHSCREEN)) return OPEM_INPUT_TOUCH;
    }
    if (type == AINPUT_EVENT_TYPE_KEY) {
        if (has_source(source, AINPUT_SOURCE_GAMEPAD)) return OPEM_INPUT_GAMEPAD;
        if (has_source(source, AINPUT_SOURCE_KEYBOARD)) return OPEM_INPUT_KEYBOARD;
    }
    return OPEM_INPUT_OTHER;
}

int opem_android_observe(const AInputEvent *event, opem_input_observation *out) {
    size_t i;
    static const int32_t axes[10] = {
        AMOTION_EVENT_AXIS_X, AMOTION_EVENT_AXIS_Y,
        AMOTION_EVENT_AXIS_Z, AMOTION_EVENT_AXIS_RZ,
        AMOTION_EVENT_AXIS_HAT_X, AMOTION_EVENT_AXIS_HAT_Y,
        AMOTION_EVENT_AXIS_LTRIGGER, AMOTION_EVENT_AXIS_RTRIGGER,
        AMOTION_EVENT_AXIS_BRAKE, AMOTION_EVENT_AXIS_GAS
    };
    if (!out) return 0;
    memset(out, 0, sizeof(*out));
    if (!event) return 0;
    out->family = opem_android_event_family(event);
    out->device_id = AInputEvent_getDeviceId(event);
    out->source = AInputEvent_getSource(event);
    out->type = AInputEvent_getType(event);
    if (out->type == AINPUT_EVENT_TYPE_KEY) {
        out->action = AKeyEvent_getAction(event);
        out->keycode = AKeyEvent_getKeyCode(event);
        out->scancode = AKeyEvent_getScanCode(event);
        out->repeat_count = AKeyEvent_getRepeatCount(event);
        out->flags = AKeyEvent_getFlags(event);
        out->event_time_ns = AKeyEvent_getEventTime(event);
    } else if (out->type == AINPUT_EVENT_TYPE_MOTION) {
        out->action = AMotionEvent_getAction(event);
        out->event_time_ns = AMotionEvent_getEventTime(event);
        if (out->family == OPEM_INPUT_JOYSTICK && AMotionEvent_getPointerCount(event)) {
            for (i = 0; i < 10; ++i) {
                out->axes[i] = AMotionEvent_getAxisValue(event, axes[i], 0);
                if (!isfinite(out->axes[i])) {
                    memset(out, 0, sizeof(*out));
                    return 0;
                }
            }
        }
    }
    return out->family != OPEM_INPUT_OTHER;
}

int opem_android_inventory_read(JNIEnv *env,opem_android_inventory *out){(void)env;memset(out,0,sizeof(*out));out->count=2;out->devices[0].is_virtual=1;out->devices[1].is_virtual=1;out->devices[0].id=1;out->devices[0].sources=AINPUT_SOURCE_KEYBOARD;out->devices[1].id=2;out->devices[1].sources=AINPUT_SOURCE_MOUSE;return 1;}
