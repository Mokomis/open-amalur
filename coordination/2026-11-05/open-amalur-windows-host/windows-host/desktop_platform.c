/* Win32 host for the unmodified custom engine sources. No game simulation lives here. */
#include "desktop_compat.h"
#include <stdio.h>
#include <stdlib.h>
#include <stdarg.h>
#include <string.h>
#include <windowsx.h>
#include <mmsystem.h>
#include <process.h>
#include <android/native_activity.h>
#include <android/looper.h>
#include <android/log.h>
#include <android/keycodes.h>
#include <aaudio/AAudio.h>
#undef eglSwapBuffers
#include <EGL/egl.h>
#include <GLES3/gl3.h>

static ANativeActivity activity;
static ANativeActivityCallbacks callbacks;
static HWND window;
static HANDLE wake_event;
static CRITICAL_SECTION queue_lock,log_lock;
static char user_dir[2048],capture_path[2048],property_path[2048];
static unsigned frame_count,capture_frame=120,stop_frames;
static FILE *log_file;
static AInputEvent events[1024],current_event;
static unsigned head,tail;
struct AInputQueue{int attached;};static struct AInputQueue input_queue;
struct ALooper{int unused;};static struct ALooper looper;

int clock_gettime(int which,struct timespec *t){LARGE_INTEGER q,f;(void)which;QueryPerformanceCounter(&q);QueryPerformanceFrequency(&f);t->tv_sec=(time_t)(q.QuadPart/f.QuadPart);t->tv_nsec=(long)((q.QuadPart%f.QuadPart)*1000000000LL/f.QuadPart);return 0;}
static int64_t clock_ns(void){struct timespec t;clock_gettime(1,&t);return (int64_t)t.tv_sec*1000000000LL+t.tv_nsec;}
int __android_log_print(int level,const char *tag,const char *fmt,...){char b[8192];va_list a;int n;va_start(a,fmt);n=vsnprintf(b,sizeof(b),fmt,a);va_end(a);EnterCriticalSection(&log_lock);if(log_file){fprintf(log_file,"%.3f %d %s: %s\n",clock_ns()/1e9,level,tag,b);fflush(log_file);}fprintf(stdout,"%s: %s\n",tag,b);fflush(stdout);LeaveCriticalSection(&log_lock);return n;}
int __system_property_get(const char *name,char *out){DWORD n=GetEnvironmentVariableA(name,out,92);if(!n||n>=92)n=GetPrivateProfileStringA("properties",name,"",out,92,property_path);if(n>=92){out[0]=0;return 0;}return (int)n;}

struct AAsset{FILE *file;int64_t size;void *buffer;};
AAsset *AAssetManager_open(AAssetManager *m,const char *name,int mode){char path[4096];AAsset *a;(void)mode;if(!m||!name||strstr(name,"..")||strchr(name,':')||name[0]=='/'||name[0]=='\\')return NULL;snprintf(path,sizeof(path),"%s/%s",m->root,name);a=calloc(1,sizeof(*a));if(!a)return NULL;a->file=fopen(path,"rb");if(!a->file){free(a);return NULL;}_fseeki64(a->file,0,SEEK_END);a->size=_ftelli64(a->file);_fseeki64(a->file,0,SEEK_SET);if(a->size<0){AAsset_close(a);return NULL;}return a;}
int AAsset_read(AAsset *a,void *p,size_t n){if(n>0x7fffffff)n=0x7fffffff;return (int)fread(p,1,n,a->file);}
off_t AAsset_getLength(AAsset *a){return (off_t)a->size;}
off64_t AAsset_getLength64(AAsset *a){return a->size;}
const void *AAsset_getBuffer(AAsset *a){int64_t pos;if(!a->buffer){pos=_ftelli64(a->file);a->buffer=malloc((size_t)a->size+1);if(!a->buffer)return NULL;_fseeki64(a->file,0,SEEK_SET);if(fread(a->buffer,1,(size_t)a->size,a->file)!=(size_t)a->size){free(a->buffer);a->buffer=NULL;}_fseeki64(a->file,pos,SEEK_SET);}return a->buffer;}
void AAsset_close(AAsset *a){if(a){if(a->file)fclose(a->file);free(a->buffer);free(a);}}
int ANativeWindow_getWidth(ANativeWindow *w){RECT r;GetClientRect((HWND)w,&r);return r.right;}
int ANativeWindow_getHeight(ANativeWindow *w){RECT r;GetClientRect((HWND)w,&r);return r.bottom;}
int ANativeWindow_setBuffersGeometry(ANativeWindow *w,int x,int y,int format){(void)format;return (!x&&!y)||(x==ANativeWindow_getWidth(w)&&y==ANativeWindow_getHeight(w))?0:-1;}
void ANativeWindow_acquire(ANativeWindow *w){(void)w;}
void ANativeWindow_release(ANativeWindow *w){(void)w;}
ALooper *ALooper_prepare(int flags){(void)flags;return &looper;}
void ALooper_acquire(ALooper *l){(void)l;}
void ALooper_release(ALooper *l){(void)l;}
void ALooper_wake(ALooper *l){(void)l;SetEvent(wake_event);}
static int queued(void){int n;EnterCriticalSection(&queue_lock);n=head!=tail;LeaveCriticalSection(&queue_lock);return n;}
int ALooper_pollOnce(int ms,int *fd,int *ev,void **data){(void)fd;(void)ev;(void)data;if(queued())return 1;WaitForSingleObject(wake_event,ms<0?INFINITE:(DWORD)ms);return queued()?1:-1;}
int AInputQueue_getEvent(AInputQueue *q,AInputEvent **e){int ok=0;(void)q;EnterCriticalSection(&queue_lock);if(head!=tail){current_event=events[tail++%1024];*e=&current_event;ok=1;}LeaveCriticalSection(&queue_lock);return ok?0:-1;}
int AInputQueue_preDispatchEvent(AInputQueue *q,AInputEvent *e){(void)q;(void)e;return 0;}
void AInputQueue_finishEvent(AInputQueue *q,AInputEvent *e,int handled){(void)q;(void)e;(void)handled;}
void AInputQueue_attachLooper(AInputQueue *q,ALooper *l,int id,void *cb,void *data){(void)l;(void)id;(void)cb;(void)data;q->attached=1;}
void AInputQueue_detachLooper(AInputQueue *q){q->attached=0;}
static void push(AInputEvent e){e.time_ns=clock_ns();EnterCriticalSection(&queue_lock);if(head-tail<1024)events[head++%1024]=e;else __android_log_print(6,"Win32","Input queue overflow; event dropped");LeaveCriticalSection(&queue_lock);SetEvent(wake_event);}
static int keycode(WPARAM k){if(k>='A'&&k<='Z')return AKEYCODE_A+(int)(k-'A');if(k>='0'&&k<='9')return AKEYCODE_0+(int)(k-'0');switch(k){case VK_RETURN:return AKEYCODE_ENTER;case VK_SPACE:return AKEYCODE_SPACE;case VK_ESCAPE:return AKEYCODE_ESCAPE;case VK_TAB:return AKEYCODE_TAB;case VK_UP:return AKEYCODE_DPAD_UP;case VK_DOWN:return AKEYCODE_DPAD_DOWN;case VK_LEFT:return AKEYCODE_DPAD_LEFT;case VK_RIGHT:return AKEYCODE_DPAD_RIGHT;case VK_OEM_MINUS:return AKEYCODE_MINUS;case VK_OEM_PLUS:return AKEYCODE_EQUALS;}return 0;}
static void mouse_event(UINT msg,WPARAM w,LPARAM l){AInputEvent e={0};e.type=AINPUT_EVENT_TYPE_MOTION;e.source=AINPUT_SOURCE_MOUSE;e.device=2;e.count=1;e.x[0]=(float)GET_X_LPARAM(l);e.y[0]=(float)GET_Y_LPARAM(l);e.buttons=(w&MK_LBUTTON?1:0)|(w&MK_RBUTTON?2:0);e.action=(msg==WM_LBUTTONDOWN||msg==WM_RBUTTONDOWN)?AMOTION_EVENT_ACTION_DOWN:(msg==WM_LBUTTONUP||msg==WM_RBUTTONUP)?AMOTION_EVENT_ACTION_UP:AMOTION_EVENT_ACTION_MOVE;push(e);}
void ANativeActivity_finish(ANativeActivity *a){(void)a;PostMessageA(window,WM_CLOSE,0,0);}
static jint vm_env(JavaVM *v,void **e,jint ver){(void)v;(void)ver;*e=(void*)1;return JNI_OK;}
static jint vm_attach(JavaVM *v,JNIEnv **e,void *a){(void)a;return vm_env(v,(void**)e,0);}
static jint vm_detach(JavaVM *v){(void)v;return JNI_OK;}
static struct oa_jvm vm_table={vm_env,vm_attach,vm_detach};static JavaVM vm=&vm_table;

static LRESULT CALLBACK wndproc(HWND w,UINT msg,WPARAM wp,LPARAM lp){
 if(msg==WM_CLOSE){if(activity.instance){callbacks.onPause(&activity);callbacks.onWindowFocusChanged(&activity,0);callbacks.onInputQueueDestroyed(&activity,&input_queue);callbacks.onNativeWindowDestroyed(&activity,(ANativeWindow*)w);callbacks.onDestroy(&activity);}DestroyWindow(w);return 0;}
 if(msg==WM_DESTROY){PostQuitMessage(0);return 0;}
 if(msg==WM_SETFOCUS||msg==WM_KILLFOCUS){if(activity.instance)callbacks.onWindowFocusChanged(&activity,msg==WM_SETFOCUS);return 0;}
 if(msg==WM_KEYDOWN||msg==WM_KEYUP){AInputEvent e={0};int key=keycode(wp);if(key){e.type=AINPUT_EVENT_TYPE_KEY;e.source=AINPUT_SOURCE_KEYBOARD;e.device=1;e.action=msg==WM_KEYDOWN?0:1;e.key=key;e.repeat=(lp&(1LL<<30))&&msg==WM_KEYDOWN?1:0;push(e);}if(wp==VK_F9&&msg==WM_KEYDOWN)capture_frame=frame_count+1;return 0;}
 if(msg==WM_LBUTTONDOWN||msg==WM_LBUTTONUP||msg==WM_RBUTTONDOWN||msg==WM_RBUTTONUP||msg==WM_MOUSEMOVE){if(msg==WM_LBUTTONDOWN||msg==WM_RBUTTONDOWN)SetCapture(w);if(msg==WM_LBUTTONUP||msg==WM_RBUTTONUP)ReleaseCapture();mouse_event(msg,wp,lp);return 0;}
 return DefWindowProcA(w,msg,wp,lp);
}
static int screenshot(int width,int height){FILE *f;BITMAPFILEHEADER b={0};BITMAPINFOHEADER i={0};unsigned char *pixels;size_t n=(size_t)width*height*4;if(!capture_path[0])return 0;pixels=malloc(n);if(!pixels)return 0;glReadPixels(0,0,width,height,GL_RGBA,GL_UNSIGNED_BYTE,pixels);if(glGetError()!=GL_NO_ERROR){free(pixels);return 0;}for(size_t j=0;j<n;j+=4){unsigned char t=pixels[j];pixels[j]=pixels[j+2];pixels[j+2]=t;}f=fopen(capture_path,"wb");if(!f){free(pixels);return 0;}b.bfType=0x4d42;b.bfOffBits=sizeof(b)+sizeof(i);b.bfSize=(DWORD)(b.bfOffBits+n);i.biSize=sizeof(i);i.biWidth=width;i.biHeight=height;i.biPlanes=1;i.biBitCount=32;i.biSizeImage=(DWORD)n;fwrite(&b,1,sizeof(b),f);fwrite(&i,1,sizeof(i),f);fwrite(pixels,1,n,f);fclose(f);free(pixels);__android_log_print(4,"Win32","Captured frame=%u size=%dx%d path=%s",frame_count,width,height,capture_path);return 1;}
EGLBoolean oa_desktop_swap(EGLDisplay d,EGLSurface s){EGLint w=0,h=0;static unsigned errors;GLenum err=glGetError();frame_count++;if(err&&errors++<12)__android_log_print(6,"Win32","GL error before swap frame=%u code=0x%x",frame_count,err);if(frame_count==1)__android_log_print(4,"Win32","Renderer=%s GL=%s GLSL=%s",glGetString(GL_RENDERER),glGetString(GL_VERSION),glGetString(GL_SHADING_LANGUAGE_VERSION));if(frame_count==capture_frame){eglQuerySurface(d,s,EGL_WIDTH,&w);eglQuerySurface(d,s,EGL_HEIGHT,&h);screenshot(w,h);}if(stop_frames&&frame_count==stop_frames)PostMessageA(window,WM_CLOSE,0,0);return eglSwapBuffers(d,s);}

/* Original mixer/decoder, with a WinMM float PCM output device instead of AAudio. */
struct AAudioStreamBuilder{oa_audio_cb cb;void *user;int rate,channels;};
struct AAudioStream{oa_audio_cb cb;void *user;int rate,channels;HWAVEOUT device;HANDLE thread;volatile LONG running;WAVEHDR headers[4];float samples[4][512*2];};
int AAudio_createStreamBuilder(AAudioStreamBuilder **b){*b=calloc(1,sizeof(**b));return *b?0:-1;}
void AAudioStreamBuilder_setFormat(AAudioStreamBuilder *b,int f){(void)b;(void)f;}
void AAudioStreamBuilder_setChannelCount(AAudioStreamBuilder *b,int n){b->channels=n;}
void AAudioStreamBuilder_setSampleRate(AAudioStreamBuilder *b,int n){b->rate=n;}
void AAudioStreamBuilder_setPerformanceMode(AAudioStreamBuilder *b,int n){(void)b;(void)n;}
void AAudioStreamBuilder_setDataCallback(AAudioStreamBuilder *b,oa_audio_cb cb,void *u){b->cb=cb;b->user=u;}
void AAudioStreamBuilder_delete(AAudioStreamBuilder *b){free(b);}
int AAudioStreamBuilder_openStream(AAudioStreamBuilder *b,AAudioStream **out){WAVEFORMATEX f={0};AAudioStream *s=calloc(1,sizeof(*s));if(!s||b->channels!=2||!b->cb){free(s);return -1;}s->cb=b->cb;s->user=b->user;s->rate=b->rate;s->channels=2;f.wFormatTag=WAVE_FORMAT_IEEE_FLOAT;f.nChannels=2;f.nSamplesPerSec=b->rate;f.wBitsPerSample=32;f.nBlockAlign=8;f.nAvgBytesPerSec=f.nSamplesPerSec*8;if(waveOutOpen(&s->device,WAVE_MAPPER,&f,0,0,CALLBACK_NULL)!=MMSYSERR_NOERROR){free(s);return -1;}*out=s;return 0;}
static unsigned __stdcall audio_pump(void *v){AAudioStream *s=v;for(int j=0;j<4;j++){WAVEHDR *h=s->headers+j;h->lpData=(LPSTR)s->samples[j];h->dwBufferLength=sizeof(s->samples[j]);waveOutPrepareHeader(s->device,h,sizeof(*h));s->cb(s,s->user,s->samples[j],512);waveOutWrite(s->device,h,sizeof(*h));}while(InterlockedCompareExchange(&s->running,0,0)){for(int j=0;j<4;j++)if(s->headers[j].dwFlags&WHDR_DONE){s->cb(s,s->user,s->samples[j],512);waveOutWrite(s->device,s->headers+j,sizeof(WAVEHDR));}Sleep(2);}waveOutReset(s->device);for(int j=0;j<4;j++)waveOutUnprepareHeader(s->device,s->headers+j,sizeof(WAVEHDR));return 0;}
int AAudioStream_requestStart(AAudioStream *s){InterlockedExchange(&s->running,1);s->thread=(HANDLE)_beginthreadex(NULL,0,audio_pump,s,0,NULL);return s->thread?0:-1;}
int AAudioStream_requestStop(AAudioStream *s){InterlockedExchange(&s->running,0);if(s->thread){WaitForSingleObject(s->thread,INFINITE);CloseHandle(s->thread);s->thread=NULL;}return 0;}
int AAudioStream_close(AAudioStream *s){AAudioStream_requestStop(s);waveOutClose(s->device);free(s);return 0;}
int AAudioStream_getSampleRate(AAudioStream *s){return s->rate;}
int AAudioStream_getXRunCount(AAudioStream *s){(void)s;return 0;/* WinMM does not expose the AAudio underrun counter. */}

int main(int argc,char **argv){AAssetManager assets={0};char base[2048],log_path[2200];WNDCLASSA wc={0};RECT rect={0,0,1536,864};MSG msg;GetModuleFileNameA(NULL,base,sizeof(base));*strrchr(base,'\\')=0;*strrchr(base,'\\')=0;snprintf(assets.root,sizeof(assets.root),"%s/assets",base);snprintf(user_dir,sizeof(user_dir),"%s/user-data",base);snprintf(capture_path,sizeof(capture_path),"%s/frame.bmp",base);
 for(int j=1;j<argc;j++){if(!strcmp(argv[j],"--assets")&&j+1<argc)snprintf(assets.root,sizeof(assets.root),"%s",argv[++j]);else if(!strcmp(argv[j],"--user-data")&&j+1<argc)snprintf(user_dir,sizeof(user_dir),"%s",argv[++j]);else if(!strcmp(argv[j],"--capture")&&j+1<argc)snprintf(capture_path,sizeof(capture_path),"%s",argv[++j]);else if(!strcmp(argv[j],"--capture-frame")&&j+1<argc)capture_frame=(unsigned)atoi(argv[++j]);else if(!strcmp(argv[j],"--frames")&&j+1<argc)stop_frames=(unsigned)atoi(argv[++j]);else if(!strcmp(argv[j],"--town"))SetEnvironmentVariableA("debug.opem.world","town");}
 CreateDirectoryA(user_dir,NULL);snprintf(log_path,sizeof(log_path),"%s/desktop.log",user_dir);snprintf(property_path,sizeof(property_path),"%s/properties.ini",user_dir);InitializeCriticalSection(&queue_lock);InitializeCriticalSection(&log_lock);wake_event=CreateEventA(NULL,FALSE,FALSE,NULL);log_file=fopen(log_path,"w");SetProcessDPIAware();wc.lpfnWndProc=wndproc;wc.hInstance=GetModuleHandleA(NULL);wc.lpszClassName="OpenAmalurCustomWindows";wc.hCursor=LoadCursor(NULL,IDC_ARROW);RegisterClassA(&wc);AdjustWindowRect(&rect,WS_OVERLAPPED|WS_CAPTION|WS_SYSMENU|WS_MINIMIZEBOX,FALSE);window=CreateWindowA(wc.lpszClassName,"Open Amalur - Custom Engine (Windows)",WS_OVERLAPPED|WS_CAPTION|WS_SYSMENU|WS_MINIMIZEBOX,CW_USEDEFAULT,CW_USEDEFAULT,rect.right-rect.left,rect.bottom-rect.top,NULL,NULL,wc.hInstance,NULL);if(!window)return 2;
 activity.callbacks=&callbacks;activity.vm=&vm;activity.assetManager=&assets;activity.internalDataPath=user_dir;__android_log_print(4,"Win32","Custom engine desktop host assets=%s userdata=%s logical_input_policy=shared_Android_keys audio=WinMM",assets.root,user_dir);ANativeActivity_onCreate(&activity,NULL,0);ShowWindow(window,SW_SHOW);SetForegroundWindow(window);callbacks.onInputQueueCreated(&activity,&input_queue);callbacks.onNativeWindowCreated(&activity,(ANativeWindow*)window);callbacks.onResume(&activity);callbacks.onWindowFocusChanged(&activity,1);
 while(GetMessageA(&msg,NULL,0,0)>0){TranslateMessage(&msg);DispatchMessageA(&msg);}__android_log_print(4,"Win32","Clean exit frames=%u",frame_count);if(log_file)fclose(log_file);CloseHandle(wake_event);return 0;}
