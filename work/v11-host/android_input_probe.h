#ifndef OPEM_ANDROID_INPUT_PROBE_H
#define OPEM_ANDROID_INPUT_PROBE_H
#include <android/input.h>
#include <jni.h>
#include <stdint.h>
#include <stddef.h>

/* These are host classifications, NEVER Amalur controller-kind values. */
enum opem_input_family {
    OPEM_INPUT_OTHER, OPEM_INPUT_TOUCH, OPEM_INPUT_GAMEPAD,
    OPEM_INPUT_JOYSTICK, OPEM_INPUT_KEYBOARD
};
typedef struct opem_input_observation {
    enum opem_input_family family;
    int32_t device_id, source, type, action;
    int32_t keycode, scancode, repeat_count, flags;
    int64_t event_time_ns;
    /* Raw Android joystick axes: X,Y,Z,RZ,HAT_X,HAT_Y,LTRIGGER,RTRIGGER,
       BRAKE,GAS. Missing axes read zero; zero does not prove capability. */
    float axes[10];
} opem_input_observation;

enum opem_input_family opem_android_event_family(const AInputEvent *event);
/* Copies observations only. Return 1 means recognized, NOT consumed/handled.
 * Caller may retain result but must not retain the AInputEvent pointer. */
int opem_android_observe(const AInputEvent *event, opem_input_observation *out);

#define OPEM_INPUT_MAX_DEVICES 128
typedef struct opem_android_device {
    int32_t id, sources;
    int is_virtual;
} opem_android_device;
typedef struct opem_android_inventory {
    size_t count;
    opem_android_device devices[OPEM_INPUT_MAX_DEVICES];
} opem_android_inventory;
/* Call on an attached JNI thread. Returns 1 for a complete snapshot, 0 for
 * failure/race/overflow. On failure output is cleared, not a known empty
 * inventory. Errors raised by this query are cleared; preexisting exceptions
 * are preserved. Caller supplies known/unknown and refresh timestamp fields. */
int opem_android_inventory_read(JNIEnv *env, opem_android_inventory *out);
#endif
