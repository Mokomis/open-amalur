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

int opem_android_inventory_read(JNIEnv *env, opem_android_inventory *out) {
    jclass cls;
    jmethodID get_ids, get_device, get_sources, is_virtual;
    jintArray ids;
    jsize count, i;
    int okay = 0;
    if (!out) return 0;
    memset(out, 0, sizeof(*out));
    if (!env || (*env)->ExceptionCheck(env)) return 0;
    if ((*env)->PushLocalFrame(env, 8) < 0) {
        if ((*env)->ExceptionCheck(env)) (*env)->ExceptionClear(env);
        return 0;
    }
    cls = (*env)->FindClass(env, "android/view/InputDevice");
    if (!cls || (*env)->ExceptionCheck(env)) goto done;
    get_ids = (*env)->GetStaticMethodID(env, cls, "getDeviceIds", "()[I");
    if (!get_ids || (*env)->ExceptionCheck(env)) goto done;
    get_device = (*env)->GetStaticMethodID(env, cls, "getDevice", "(I)Landroid/view/InputDevice;");
    if (!get_device || (*env)->ExceptionCheck(env)) goto done;
    get_sources = (*env)->GetMethodID(env, cls, "getSources", "()I");
    if (!get_sources || (*env)->ExceptionCheck(env)) goto done;
    is_virtual = (*env)->GetMethodID(env, cls, "isVirtual", "()Z");
    if (!is_virtual || (*env)->ExceptionCheck(env)) goto done;
    ids = (jintArray)(*env)->CallStaticObjectMethod(env, cls, get_ids);
    if (!ids || (*env)->ExceptionCheck(env)) goto done;
    count = (*env)->GetArrayLength(env, ids);
    if ((*env)->ExceptionCheck(env) || count < 0 || count > OPEM_INPUT_MAX_DEVICES) goto done;
    for (i = 0; i < count; ++i) {
        jint id, sources;
        jboolean virtual_device;
        jobject device;
        (*env)->GetIntArrayRegion(env, ids, i, 1, &id);
        if ((*env)->ExceptionCheck(env)) goto done;
        device = (*env)->CallStaticObjectMethod(env, cls, get_device, id);
        /* Disconnection during enumeration produces an unknown snapshot. */
        if (!device || (*env)->ExceptionCheck(env)) goto done;
        sources = (*env)->CallIntMethod(env, device, get_sources);
        if ((*env)->ExceptionCheck(env)) goto done;
        virtual_device = (*env)->CallBooleanMethod(env, device, is_virtual);
        if ((*env)->ExceptionCheck(env)) goto done;
        out->devices[i].id = id;
        out->devices[i].sources = sources;
        out->devices[i].is_virtual = virtual_device == JNI_TRUE;
        (*env)->DeleteLocalRef(env, device);
    }
    out->count = (size_t)count;
    okay = 1;
done:
    if ((*env)->ExceptionCheck(env)) (*env)->ExceptionClear(env);
    (*env)->PopLocalFrame(env, NULL);
    if (!okay) memset(out, 0, sizeof(*out));
    return okay;
}
