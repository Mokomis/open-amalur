#ifndef OA_UI_TEXT_ANDROID_H
#define OA_UI_TEXT_ANDROID_H
#include <android/native_activity.h>
#include "../oa_ui.h"
#ifdef __cplusplus
extern "C" {
#endif
typedef struct oa_ui_text_android_context oa_ui_text_android_context;
/* Call while Activity/VM are alive; helper must be in Activity's classloader.
   Context owns global refs, not Activity lifecycle. All calls serial/render-thread.
   Threads attached by the caller are never detached by this provider. */
oa_ui_text_android_context *oa_ui_text_android_open(ANativeActivity *activity);
int oa_ui_text_android(void *context,int font,unsigned pixel_size,
 const char *utf8,oa_ui_text_bitmap *out);
/* Clear/close shared UI text cache BEFORE closing context; release bitmap callback
   itself is independent free(), but no provider call may race this close. */
void oa_ui_text_android_close(oa_ui_text_android_context *context);
#ifdef __cplusplus
}
#endif
#endif
