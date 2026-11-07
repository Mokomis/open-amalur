#ifndef OA_DESKTOP_NAME_INPUT_H
#define OA_DESKTOP_NAME_INPUT_H
#include <windows.h>
#include <stddef.h>
#define OA_DESKTOP_NAME_UPDATE (WM_APP+0x61a)
#define OA_DESKTOP_NAME_EDIT_ID 0x7a42
/* GUI thread: attach before starting render worker; filter FIRST in parent
 * WndProc; shutdown before host onDestroy joins worker. Unicode message loop is
 * mandatory (GetMessageW/DispatchMessageW). No visible application widget added.
 * focus callback reports actual child-to-external focus changes; parent->EDIT
 * internal transfer is consumed to avoid pausing the renderer for text input.
 */
int oa_desktop_name_gui_attach(HWND,void *context,void (*focus_changed)(void*,int));
int oa_desktop_name_gui_message(HWND,UINT,WPARAM,LPARAM,LRESULT *result);
void oa_desktop_name_gui_shutdown(void);
/* Render worker: queued, never SendMessage/cross-thread wait. Return0 accepted,
 * -1 invalid UTF8/over16scalars/over64bytes/unavailable. Empty is allowed DURING
 * editing; final existing profile-name validation still decides confirmation.
 * Deactivate when leaving name screen. Sync after applying poll/Veil keyboard.
 * Unchanged sync never sets EDIT text/selection or resets caret/undo/IME.
 */
int oa_desktop_name_input(int active,const char *current_utf8);
/* Return1 event,0 none,-1 invalid/capacity (event retained; outputs untouched).
 * confirmed:1 Enter,-1 Escape,0 latest complete change. Cancel does not undo
 * changes already delivered; host owns its draft/cancel policy. Intermediate
 * IME composition/incomplete UTF16 never becomes an event. Terminal snapshot
 * takes priority over coalesced change; later changes remain queued if active.
 */
int oa_desktop_name_poll(char *utf8,size_t cap,int *confirmed);
#endif
