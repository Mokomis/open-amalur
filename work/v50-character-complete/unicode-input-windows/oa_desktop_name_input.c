#include "oa_desktop_name_input.h"
#include <stdint.h>
#include <string.h>
#include <wchar.h>
#include <imm.h>
#ifndef WM_UNICHAR
#define WM_UNICHAR 0x0109
#endif
#ifndef UNICODE_NOCHAR
#define UNICODE_NOCHAR 0xffff
#endif
#define NAME_BYTES 64
#define NAME_SCALARS 16
#define EDIT_WIDE_LIMIT 256

typedef struct name_event {char text[65];uint64_t revision;int ready,confirmed;} name_event;
static struct {
 SRWLOCK lock;HWND parent;DWORD gui_thread;
 int ready,posted,desired_active;uint64_t request,epoch,ack_revision,request_ack,revision;
 char requested[65];name_event change,terminal;
} shared={SRWLOCK_INIT};
/* GUI-only fields are never read by render worker. */
static struct {
 HWND parent,edit;WNDPROC previous;void *focus_context;void(*focus)(void*,int);
 int active,setting,composing,enter_down,escape_down,shutting;
 WCHAR pending_high,accepted[33];char utf8[65];
 DWORD previous_start,previous_end;uint64_t request,epoch;
} gui;

static int utf8_to_wide(const char *s,WCHAR w[33]){
 size_t at=0,wi=0;unsigned count=0;
 if(!s)return 0;
 while(at<=NAME_BYTES&&s[at]){
  uint32_t cp;unsigned n,j;unsigned char a=(unsigned char)s[at];
  if(a<0x80){cp=a;n=1;}
  else if(a>=0xc2&&a<=0xdf){cp=a&31u;n=2;}
  else if(a>=0xe0&&a<=0xef){cp=a&15u;n=3;}
  else if(a>=0xf0&&a<=0xf4){cp=a&7u;n=4;}
  else return 0;
  if(at+n>NAME_BYTES)return 0;
  for(j=1;j<n;j++){unsigned char b=(unsigned char)s[at+j];if(b<0x80||b>0xbf)return 0;cp=(cp<<6)|(b&63u);}
  if((n==2&&cp<0x80)||(n==3&&cp<0x800)||(n==4&&cp<0x10000)||cp>0x10ffff||(cp>=0xd800&&cp<=0xdfff)||cp<32||cp==127||++count>NAME_SCALARS)return 0;
  if(cp<0x10000)w[wi++]=(WCHAR)cp;else{cp-=0x10000;w[wi++]=(WCHAR)(0xd800+(cp>>10));w[wi++]=(WCHAR)(0xdc00+(cp&1023));}at+=n;
 }
 if(at>NAME_BYTES)return 0;w[wi]=0;return 1;
}
static int wide_to_utf8(const WCHAR *w,size_t len,char out[65]){
 size_t i=0,at=0;unsigned count=0;
 while(i<len){uint32_t cp=w[i++];unsigned n;
  if(cp>=0xd800&&cp<=0xdbff){uint32_t low;if(i>=len)return 0;low=w[i++];if(low<0xdc00||low>0xdfff)return 0;cp=0x10000+((cp-0xd800)<<10)+(low-0xdc00);}
  else if(cp>=0xdc00&&cp<=0xdfff)return 0;
  if(!cp||cp<32||cp==127||++count>NAME_SCALARS)return 0;
  n=cp<0x80?1:cp<0x800?2:cp<0x10000?3:4;if(at+n>NAME_BYTES)return 0;
  if(n==1)out[at++]=(char)cp;
  else if(n==2){out[at++]=(char)(0xc0|(cp>>6));out[at++]=(char)(0x80|(cp&63));}
  else if(n==3){out[at++]=(char)(0xe0|(cp>>12));out[at++]=(char)(0x80|((cp>>6)&63));out[at++]=(char)(0x80|(cp&63));}
  else{out[at++]=(char)(0xf0|(cp>>18));out[at++]=(char)(0x80|((cp>>12)&63));out[at++]=(char)(0x80|((cp>>6)&63));out[at++]=(char)(0x80|(cp&63));}
 }
 out[at]=0;return 1;
}
static void post_update_locked(void){
 if(shared.ready&&!shared.posted){shared.posted=1;if(!PostMessageW(shared.parent,OA_DESKTOP_NAME_UPDATE,0,0))shared.posted=0;}
}
int oa_desktop_name_input(int active,const char *text){
 WCHAR check[33];if((active!=0&&active!=1)||(active&&!utf8_to_wide(text,check)))return -1;
 AcquireSRWLockExclusive(&shared.lock);
 if(!shared.ready){ReleaseSRWLockExclusive(&shared.lock);return -1;}
 if(active==shared.desired_active&&(!active||!strcmp(text,shared.requested))&&shared.request_ack==shared.ack_revision){ReleaseSRWLockExclusive(&shared.lock);return 0;}
 if(active&&!shared.desired_active){shared.epoch++;shared.change.ready=shared.terminal.ready=0;}
 if(!active){shared.change.ready=shared.terminal.ready=0;shared.ack_revision=shared.revision;}
 shared.desired_active=active;
 if(active)memcpy(shared.requested,text,strlen(text)+1);
 shared.request_ack=shared.ack_revision;shared.request++;post_update_locked();ReleaseSRWLockExclusive(&shared.lock);return 0;
}
int oa_desktop_name_poll(char *out,size_t cap,int *confirmed){
 name_event *event;size_t n;if(!out||!confirmed)return -1;
 AcquireSRWLockExclusive(&shared.lock);event=shared.terminal.ready?&shared.terminal:shared.change.ready?&shared.change:NULL;
 if(!event){ReleaseSRWLockExclusive(&shared.lock);return 0;}
 n=strlen(event->text)+1;if(n>cap){ReleaseSRWLockExclusive(&shared.lock);return -1;}
 memcpy(out,event->text,n);*confirmed=event->confirmed;shared.ack_revision=event->revision;
 if(event==&shared.terminal&&shared.change.ready&&shared.change.revision<=event->revision)shared.change.ready=0;
 event->ready=0;ReleaseSRWLockExclusive(&shared.lock);return 1;
}
static void selection_before(void){SendMessageW(gui.edit,EM_GETSEL,(WPARAM)&gui.previous_start,(LPARAM)&gui.previous_end);}
static void restore_accepted(void){
 gui.setting=1;SetWindowTextW(gui.edit,gui.accepted);
 SendMessageW(gui.edit,EM_SETSEL,gui.previous_start,gui.previous_end);gui.setting=0;gui.pending_high=0;
}
static void enqueue(int confirmed){
 name_event *event;AcquireSRWLockExclusive(&shared.lock);
 if(shared.ready&&shared.desired_active){
  event=confirmed?&shared.terminal:&shared.change;
  /* Never overwrite a pending terminal. Latest ordinary change is coalesced. */
  if(!confirmed||!event->ready){memcpy(event->text,gui.utf8,strlen(gui.utf8)+1);event->revision=++shared.revision;event->confirmed=confirmed;event->ready=1;}
 }
 ReleaseSRWLockExclusive(&shared.lock);
}
static void accept_edit(void){
 WCHAR w[EDIT_WIDE_LIMIT+1];char text[65];int len;
 if(gui.setting||gui.composing||!gui.active)return;
 len=GetWindowTextLengthW(gui.edit);
 if(len<0||len>EDIT_WIDE_LIMIT||GetWindowTextW(gui.edit,w,EDIT_WIDE_LIMIT+1)!=len||!wide_to_utf8(w,(size_t)len,text)){restore_accepted();return;}
 if(!strcmp(text,gui.utf8))return;
 memcpy(gui.accepted,w,((size_t)len+1)*sizeof(WCHAR));memcpy(gui.utf8,text,strlen(text)+1);enqueue(0);
}
static void terminal(int confirmed){gui.pending_high=0;accept_edit();enqueue(confirmed);}
static int in_parent(HWND h){return h&&(h==gui.parent||IsChild(gui.parent,h));}
static void insert_scalar(uint32_t cp){
 WCHAR w[3];if(cp<32||cp==127||cp>0x10ffff||(cp>=0xd800&&cp<=0xdfff))return;
 if(cp<0x10000){w[0]=(WCHAR)cp;w[1]=0;}else{cp-=0x10000;w[0]=(WCHAR)(0xd800+(cp>>10));w[1]=(WCHAR)(0xdc00+(cp&1023));w[2]=0;}
 SendMessageW(gui.edit,EM_REPLACESEL,TRUE,(LPARAM)w);
}
static LRESULT CALLBACK edit_proc(HWND h,UINT msg,WPARAM wp,LPARAM lp){
 LRESULT result;
 if(msg==WM_GETDLGCODE)return DLGC_WANTALLKEYS|DLGC_WANTCHARS|DLGC_WANTARROWS;
 if(msg==WM_SETFOCUS){if(gui.focus&&!in_parent((HWND)wp))gui.focus(gui.focus_context,1);}
 if(msg==WM_KILLFOCUS){gui.pending_high=0;if(gui.focus&&!in_parent((HWND)wp))gui.focus(gui.focus_context,0);}
 if(msg==WM_IME_STARTCOMPOSITION){gui.composing=1;gui.pending_high=0;}
 if(msg==WM_IME_ENDCOMPOSITION){result=CallWindowProcW(gui.previous,h,msg,wp,lp);gui.composing=0;accept_edit();AcquireSRWLockExclusive(&shared.lock);post_update_locked();ReleaseSRWLockExclusive(&shared.lock);return result;}
 if(msg==WM_UNICHAR){if(wp==UNICODE_NOCHAR)return TRUE;selection_before();insert_scalar((uint32_t)wp);return 0;}
 if(msg==WM_KEYDOWN||msg==WM_KEYUP){
  if(wp==VK_F9){PostMessageW(gui.parent,msg,wp,lp);return 0;}
  if(!gui.composing&&(wp==VK_RETURN||wp==VK_ESCAPE)){
   int *held=wp==VK_RETURN?&gui.enter_down:&gui.escape_down;
   if(msg==WM_KEYUP)*held=0;else if(!*held){*held=1;terminal(wp==VK_RETURN?1:-1);}return 0;
  }
  if(msg==WM_KEYDOWN&&wp=='A'&&(GetKeyState(VK_CONTROL)&0x8000)){SendMessageW(h,EM_SETSEL,0,-1);return 0;}
 }
 if(msg==WM_CHAR&&!gui.composing){
  WCHAR c=(WCHAR)wp;
  if(c==L'\r'||c==27){int *held=c==L'\r'?&gui.enter_down:&gui.escape_down;if(!*held){*held=1;terminal(c==L'\r'?1:-1);}return 0;}
  if(c>=0xd800&&c<=0xdbff){gui.pending_high=c;return 0;}
  if(gui.pending_high){uint32_t high=gui.pending_high;gui.pending_high=0;if(c>=0xdc00&&c<=0xdfff){selection_before();insert_scalar(0x10000+((high-0xd800)<<10)+(c-0xdc00));}return 0;}
  if(c>=0xdc00&&c<=0xdfff)return 0;
 }
 if(msg==WM_CHAR||msg==WM_PASTE||msg==WM_CUT||msg==WM_CLEAR||msg==WM_UNDO||msg==EM_REPLACESEL||msg==WM_SETTEXT||msg==WM_KEYDOWN)selection_before();
 return CallWindowProcW(gui.previous,h,msg,wp,lp);
}
static void apply_request(void){
 char text[65];WCHAR wide[33];int active,new_epoch;uint64_t request,epoch,ack,revision;
 AcquireSRWLockExclusive(&shared.lock);shared.posted=0;
 if(!shared.ready){ReleaseSRWLockExclusive(&shared.lock);return;}
 active=shared.desired_active;request=shared.request;epoch=shared.epoch;ack=shared.request_ack;revision=shared.revision;
 memcpy(text,shared.requested,sizeof(text));ReleaseSRWLockExclusive(&shared.lock);
 if(!active){gui.active=0;gui.pending_high=0;gui.enter_down=gui.escape_down=0;gui.composing=0;if(GetFocus()==gui.edit)SetFocus(gui.parent);gui.request=request;return;}
 new_epoch=epoch!=gui.epoch;
 if(new_epoch){gui.epoch=epoch;gui.pending_high=0;gui.enter_down=gui.escape_down=0;gui.composing=0;gui.utf8[0]=0;gui.accepted[0]=0;}
 gui.active=1;
 /* A render snapshot older than unpolled native edits must never undo them. */
 if(!gui.composing&&(new_epoch||ack>=revision||!gui.request)){
  if((new_epoch||strcmp(text,gui.utf8))&&utf8_to_wide(text,wide)){
   size_t length=wcslen(wide);gui.setting=1;SetWindowTextW(gui.edit,wide);SendMessageW(gui.edit,EM_SETSEL,(WPARAM)length,(LPARAM)length);gui.setting=0;
   memcpy(gui.accepted,wide,(wcslen(wide)+1)*sizeof(WCHAR));memcpy(gui.utf8,text,strlen(text)+1);
  }
 }
 gui.request=request;
 if(GetFocus()==gui.parent)SetFocus(gui.edit);
}
int oa_desktop_name_gui_attach(HWND parent,void *context,void(*focus)(void*,int)){
 HRGN region;HWND edit;WNDPROC previous;
 if(!parent||GetWindowThreadProcessId(parent,NULL)!=GetCurrentThreadId())return -1;
 AcquireSRWLockExclusive(&shared.lock);if(shared.ready){ReleaseSRWLockExclusive(&shared.lock);return -1;}ReleaseSRWLockExclusive(&shared.lock);
 memset(&gui,0,sizeof(gui));gui.parent=parent;gui.focus_context=context;gui.focus=focus;
 edit=CreateWindowExW(0,L"EDIT",L"",WS_CHILD|WS_VISIBLE|ES_AUTOHSCROLL,0,0,1024,32,parent,(HMENU)(INT_PTR)OA_DESKTOP_NAME_EDIT_ID,GetModuleHandleW(NULL),NULL);
 if(!edit||!IsWindowUnicode(edit)){if(edit)DestroyWindow(edit);memset(&gui,0,sizeof(gui));return -1;}
 gui.edit=edit;SetLastError(0);previous=(WNDPROC)SetWindowLongPtrW(edit,GWLP_WNDPROC,(LONG_PTR)edit_proc);
 if(!previous){DestroyWindow(edit);memset(&gui,0,sizeof(gui));return -1;}gui.previous=previous;
 region=CreateRectRgn(0,0,0,0);if(!region||!SetWindowRgn(edit,region,FALSE)){if(region)DeleteObject(region);DestroyWindow(edit);memset(&gui,0,sizeof(gui));return -1;}
 SendMessageW(edit,EM_SETLIMITTEXT,EDIT_WIDE_LIMIT,0);SendMessageW(edit,WM_SETFONT,(WPARAM)GetStockObject(DEFAULT_GUI_FONT),FALSE);
 AcquireSRWLockExclusive(&shared.lock);shared.parent=parent;shared.gui_thread=GetCurrentThreadId();shared.ready=1;shared.posted=shared.desired_active=0;shared.request++;shared.epoch++;shared.ack_revision=shared.request_ack=shared.revision;shared.change.ready=shared.terminal.ready=0;shared.requested[0]=0;ReleaseSRWLockExclusive(&shared.lock);return 0;
}
void oa_desktop_name_gui_shutdown(void){
 HWND edit;if(!gui.parent||GetWindowThreadProcessId(gui.parent,NULL)!=GetCurrentThreadId())return;
 AcquireSRWLockExclusive(&shared.lock);shared.ready=0;shared.parent=NULL;shared.desired_active=shared.posted=0;shared.change.ready=shared.terminal.ready=0;ReleaseSRWLockExclusive(&shared.lock);
 gui.shutting=1;gui.focus=NULL;edit=gui.edit;if(edit)DestroyWindow(edit);memset(&gui,0,sizeof(gui));
}
int oa_desktop_name_gui_message(HWND parent,UINT msg,WPARAM wp,LPARAM lp,LRESULT *out){
 if(parent!=gui.parent||!out)return 0;
 if(msg==OA_DESKTOP_NAME_UPDATE){apply_request();*out=0;return 1;}
 if(msg==WM_CLOSE||msg==WM_NCDESTROY){oa_desktop_name_gui_shutdown();return 0;}
 if(msg==WM_COMMAND&&(HWND)lp==gui.edit){if(HIWORD(wp)==EN_CHANGE)accept_edit();*out=0;return 1;}
 if(msg==WM_KILLFOCUS&&(HWND)wp==gui.edit){*out=0;return 1;}
 if(msg==WM_SETFOCUS&&gui.active){AcquireSRWLockExclusive(&shared.lock);post_update_locked();ReleaseSRWLockExclusive(&shared.lock);return 0;}
 if(gui.active&&(msg==WM_KEYDOWN||msg==WM_KEYUP||msg==WM_CHAR||msg==WM_UNICHAR)){
  if((msg==WM_KEYDOWN||msg==WM_KEYUP)&&wp==VK_F9)return 0;
  *out=SendMessageW(gui.edit,msg,wp,lp);return 1;
 }
 return 0;
}
