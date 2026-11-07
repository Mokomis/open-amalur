#ifndef OA_UI_TEXT_WIN32_H
#define OA_UI_TEXT_WIN32_H
#include "oa_ui.h"
#ifdef __cplusplus
extern "C" {
#endif
/* Uses Windows GDI + system Uniscribe whole-string shaping/font linking.
   No DLL ownership retained; no imports beyond existing user32/gdi32/kernel32.
   user is unused. Raster ownership is malloc/free, released by UI. */
int oa_ui_text_win32(void *user,int font,unsigned pixel_size,
 const char *utf8,oa_ui_text_bitmap *out);
#ifdef __cplusplus
}
#endif
#endif
