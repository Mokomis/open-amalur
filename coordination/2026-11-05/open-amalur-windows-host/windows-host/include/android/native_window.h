#ifndef OA_WIN_WINDOW_H
#define OA_WIN_WINDOW_H
#include "desktop_compat.h"
typedef struct HWND__ ANativeWindow;
int ANativeWindow_getWidth(ANativeWindow*);
int ANativeWindow_getHeight(ANativeWindow*);
int ANativeWindow_setBuffersGeometry(ANativeWindow*,int,int,int);
void ANativeWindow_acquire(ANativeWindow*);
void ANativeWindow_release(ANativeWindow*);
#endif
