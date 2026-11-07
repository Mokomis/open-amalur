#include <EGL/egl.h>
#include <EGL/eglext.h>
#include <GLES3/gl3.h>
#include <windows.h>
#include <stdio.h>
#include <stdarg.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include "oa_ui.h"
#include "oa_ui_text_win32.h"
int __android_log_print(int l,const char*t,const char*f,...){va_list a;(void)l;(void)t;va_start(a,f);vfprintf(stderr,f,a);va_end(a);fputc('\n',stderr);return 0;}
#include "oa_ui.c"
int legacy_ui_open(oa_ui*,const uint8_t*,size_t);
void legacy_ui_close(oa_ui*);void legacy_ui_begin(oa_ui*);void legacy_ui_end(oa_ui*,int,int);
void legacy_ui_text(oa_ui*,int,float,float,float,int,const float*,const char*);
void legacy_ui_rect(oa_ui*,float,float,float,float,const float*);
void legacy_ui_fade(oa_ui*,float,float,float,float,const float*,const float*);
float legacy_ui_measure(const oa_ui*,int,float,const char*);
enum{W=1024,H=640};
static unsigned calls,releases;
static void(*base_release)(void*,uint8_t*);
static void counted_release(void*u,uint8_t*p){(void)u;releases++;base_release(NULL,p);}
static int provider(void*u,int f,unsigned p,const char*s,oa_ui_text_bitmap*b){
 int ok;(void)u;calls++;ok=oa_ui_text_win32(NULL,f,p,s,b);
 if(b->rgba){base_release=b->release;b->release=counted_release;}return ok;
}
static void die(const char*s){fprintf(stderr,"FAIL %s GL=%x EGL=%x\n",s,glGetError(),eglGetError());exit(2);}
#define CHECK(x,msg) do{if(!(x))die(msg);}while(0)
static uint8_t*readfile(const char*s,size_t*n){FILE*f=fopen(s,"rb");long z;uint8_t*b;CHECK(f,"bank file");fseek(f,0,SEEK_END);z=ftell(f);rewind(f);b=(uint8_t*)malloc((size_t)z);CHECK(b,"bank malloc");CHECK(fread(b,1,(size_t)z,f)==(size_t)z,"bank read");fclose(f);*n=(size_t)z;return b;}
static void capture(uint8_t*b,const char*name){FILE*f;glReadPixels(0,0,W,H,GL_RGBA,GL_UNSIGNED_BYTE,b);if(name){f=fopen(name,"wb");CHECK(f,"capture write");fwrite(b,1,W*H*4,f);fclose(f);}}
static const float white[4]={1,1,1,1},gold[4]={.9f,.75f,.4f,1},bg[4]={.03f,.04f,.06f,1};
static void clear(void){glClearColor(bg[0],bg[1],bg[2],1);glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);}
int main(void){
 EGLDisplay d;EGLConfig cfg;EGLSurface surf;EGLContext ctx;EGLint n,ma,mi;
 const EGLint ca[]={EGL_SURFACE_TYPE,EGL_PBUFFER_BIT,EGL_RENDERABLE_TYPE,EGL_OPENGL_ES3_BIT_KHR,EGL_RED_SIZE,8,EGL_GREEN_SIZE,8,EGL_BLUE_SIZE,8,EGL_ALPHA_SIZE,8,EGL_NONE},sa[]={EGL_WIDTH,W,EGL_HEIGHT,H,EGL_NONE},xa[]={EGL_CONTEXT_CLIENT_VERSION,3,EGL_NONE};
 oa_ui a={0},b={0};uint8_t*bank,*p,*old;size_t bytes;unsigned i,k,nonzero,seen;FILE*f;
 const char*valid[]={"ASCII","\xc3\xa9","e\xcc\x81","\xe4\xb8\xad\xe6\x96\x87","\xf0\x9f\x98\x80","\xd8\xa7\xd9\x84\xd8\xb9\xd8\xb1\xd8\xa8\xd9\x8a\xd8\xa9"};
 const char*bad[]={"\xc0\xaf","\xed\xa0\x80","\xf4\x90\x80\x80","\xe2\x82","\x80","\xf8\x88\x80\x80\x80","a\nb"};
 d=eglGetDisplay(EGL_DEFAULT_DISPLAY);CHECK(eglInitialize(d,&ma,&mi)&&eglBindAPI(EGL_OPENGL_ES_API)&&eglChooseConfig(d,ca,&cfg,1,&n)&&n,"EGL init");
 surf=eglCreatePbufferSurface(d,cfg,sa);ctx=eglCreateContext(d,cfg,EGL_NO_CONTEXT,xa);CHECK(eglMakeCurrent(d,surf,surf,ctx),"EGL context");glViewport(0,0,W,H);
 f=fopen("renderer.txt","w");fprintf(f,"%s\n%s\n%s\n",glGetString(GL_VENDOR),glGetString(GL_RENDERER),glGetString(GL_VERSION));fclose(f);
 for(i=0;i<6;i++)CHECK(oa_ui_text_classify(valid[i])==(i?2:1),"valid UTF8 classify");
 for(i=0;i<7;i++)CHECK(!oa_ui_text_classify(bad[i]),"malformed classify");
 CHECK(!oa_ui_text_classify(NULL),"NULL classify");
 {char text[1026];memset(text,'x',1025);text[1025]=0;CHECK(!oa_ui_text_classify(text),"bounded UTF8");}
 bank=readfile("C:\\Users\\rwill\\Documents\\Opem Amalur\\work\\v21-ui\\oa_ui.bin",&bytes);
 CHECK(oa_ui_open(&a,bank,bytes)&&legacy_ui_open(&b,bank,bytes),"UI load");free(bank);
 p=(uint8_t*)malloc(W*H*4);old=(uint8_t*)malloc(W*H*4);CHECK(p&&old,"pixels malloc");
 CHECK(oa_ui_set_text_provider(&a,provider,NULL),"set provider");
 /* Exact original ASCII vertex/matrix/texture pipeline regression on ANGLE. */
 oa_ui_begin(&a);legacy_ui_begin(&b);
 oa_ui_rect(&a,10,10,700,350,bg);legacy_ui_rect(&b,10,10,700,350,bg);
 oa_ui_fade(&a,300,110,550,100,bg,gold);legacy_ui_fade(&b,300,110,550,100,bg,gold);
 for(i=0;i<2;i++)for(k=0;k<3;k++){
  float sz=18.f+13.f*k,ax=70.f+300.f*k,ay=40.f+150.f*i;
  float n1=oa_ui_measure(&a,(int)i,sz,"Elrid - Name 16"),n2=legacy_ui_measure(&b,(int)i,sz,"Elrid - Name 16");
  CHECK(memcmp(&n1,&n2,4)==0,"ASCII measure exact");
  oa_ui_text(&a,(int)i,ax,ay,sz,(int)k,gold,"Elrid - Name 16");
  legacy_ui_text(&b,(int)i,ax,ay,sz,(int)k,gold,"Elrid - Name 16");
 }
 {
  char ascii[96];const char*names[]={"Elrid","Aidith","Stigandr","Isolda","Lorcan","Siobhan","Caerwyn","Niah"};
  for(i=0;i<95;i++)ascii[i]=(char)(i+32);ascii[95]=0;
  for(i=0;i<2;i++){
   float m1=oa_ui_measure(&a,(int)i,14.5f,ascii),m2=legacy_ui_measure(&b,(int)i,14.5f,ascii);CHECK(m1==m2,"all95 ASCII measure");
   oa_ui_text(&a,(int)i,20,380.f+70*i,14.5f,0,white,ascii);legacy_ui_text(&b,(int)i,20,380.f+70*i,14.5f,0,white,ascii);
   for(k=0;k<8;k++){
    oa_ui_text(&a,(int)i,30.f+120*k,520.f+50*i,22,0,gold,names[k]);
    legacy_ui_text(&b,(int)i,30.f+120*k,520.f+50*i,22,0,gold,names[k]);
   }
  }
 }
 {
  char long_ascii[401];float m1,m2;memset(long_ascii,'A',400);long_ascii[400]=0;
  m1=oa_ui_measure(&a,1,12,long_ascii);m2=legacy_ui_measure(&b,1,12,long_ascii);CHECK(m1==m2,"legacy longASCII measurement preserved");
  oa_ui_text(&a,1,0,620,12,0,white,long_ascii);legacy_ui_text(&b,1,0,620,12,0,white,long_ascii);
 }
 CHECK(a.count==b.count&&!memcmp(a.vertices,b.vertices,a.count*sizeof(float)),"ASCII vertices exact");
 CHECK(calls==0,"ASCII no system callback");clear();legacy_ui_end(&b,W,H);capture(old,"ascii-legacy.rgba");
 clear();oa_ui_end(&a,W,H);capture(p,"ascii-new.rgba");CHECK(!memcmp(p,old,W*H*4),"ASCII pixels exact");
 printf("PASS ASCII measures, vertices and %u RGBA bytes exact to untouched legacy UI; provider calls0\n",W*H*4);
 /* Whole-string sample paths. */
 clear();oa_ui_begin(&a);oa_ui_text(&a,0,30,18,26,0,gold,"System-font names / original ASCII unchanged");
 for(i=1;i<6;i++){
  unsigned before=calls;float m1,m2;unsigned preCount;
  m1=oa_ui_measure(&a,1,40,valid[i]);CHECK(m1>0&&calls==before+1,"provider measure");m2=oa_ui_measure(&a,1,40,valid[i]);
  CHECK(m1==m2&&calls==before+1,"measure cached");preCount=a.count;
  oa_ui_text(&a,1,430,50.f+80.f*i,40,OA_ALIGN_CENTER,white,valid[i]);
  CHECK(a.count==preCount+54&&calls==before+1,"draw shares measurement raster");
  CHECK(a.unicode->runs[a.unicode->count-1].first==preCount/9,"ordered run offset");
  oa_ui_rect(&a,430-m1*.5f,99.f+80.f*i,m1,1,gold);
 }
 for(i=0;i<7;i++){unsigned c=a.count,before=calls;CHECK(oa_ui_measure(&a,1,30,bad[i])==0,"invalid measure closed");oa_ui_text(&a,1,20,20,30,0,white,bad[i]);CHECK(a.count==c&&calls==before,"invalid no draw/provider");}
 oa_ui_end(&a,W,H);capture(p,"unicode-samples.rgba");
 CHECK(glGetError()==GL_NO_ERROR,"unicode GL");
 nonzero=0;for(i=0;i<W*H;i++)if(p[4*i]>80)nonzero++;CHECK(nonzero>1000,"sample coverage");
 printf("PASS composed/decomposed, CJK, nonBMP, Arabic whole-string raster/consistent measure/draw; invalid UTF8 closed. Coverage pixels=%u\n",nonzero);
 {
  oa_ui_text_bitmap c1,c2;
  CHECK(oa_ui_text_win32(NULL,1,40,valid[1],&c1)&&oa_ui_text_win32(NULL,1,40,valid[2],&c2),"canonical equivalent shaping");
  CHECK(c1.width==c2.width&&c1.height==c2.height&&c1.advance==c2.advance&&!memcmp(c1.rgba,c2.rgba,(size_t)c1.width*c1.height*4),"composed vs decomposed pixels equal");
  c1.release(c1.release_user,c1.rgba);c2.release(c2.release_user,c2.rgba);
  puts("PASS composed/decomposed accent system rasters bit-exact (input bytes not normalized)");
 }
 /* Overlap ordering: later solid must cover unicode; later unicode must show. */
 clear();oa_ui_begin(&a);oa_ui_text(&a,1,50,100,48,0,white,valid[1]);
 {const float red[4]={1,0,0,1};oa_ui_rect(&a,0,0,300,300,red);}
 oa_ui_text(&a,1,400,100,48,0,white,valid[1]);oa_ui_end(&a,W,H);capture(p,"unicode-ordering.rgba");
 for(i=0;i<300;i++)for(k=0;k<300;k++){size_t z=((size_t)(H-1-i)*W+k)*4;CHECK(p[z]==255&&p[z+1]==0&&p[z+2]==0,"ordered solid overlap");}
 printf("PASS exact draw ordering across Unicode/atlas/solid segments\n");
 /* More distinct strings than cache entries in one batch must not evict textures
    referenced by already queued quads. Unknown strings fail closed this frame. */
 oa_ui_begin(&a);
 for(i=0;i<80;i++){char s[80];snprintf(s,sizeof s,"Pinned %u \xc3\xa9",i);oa_ui_text(&a,1,10,10,16,0,white,s);}
 CHECK(a.unicode->count==64,"pinned cache no eviction/dangling queued textures");
 oa_ui_end(&a,W,H);CHECK(glGetError()==GL_NO_ERROR,"pinned GL");
 puts("PASS64 pending distinct strings pinned; overflow16 strings fail closed without stale texture IDs");
 /* LRU cache, CPU release, cross-frame eviction and close GPU resources. */
 for(i=0;i<100;i++){char s[80];snprintf(s,sizeof s,"Name %u \xc3\xa9",i);oa_ui_begin(&a);oa_ui_text(&a,1,20,20,20,0,white,s);oa_ui_end(&a,W,H);CHECK(glGetError()==GL_NO_ERROR,"LRU GL");}
 CHECK(a.unicode->bytes<=TEXT_BUDGET,"cache budget");seen=0;
 {GLuint ids[TEXT_CACHE];for(i=0;i<TEXT_CACHE;i++){ids[i]=a.unicode->cache[i].texture;if(ids[i])seen++;}
  CHECK(seen==TEXT_CACHE,"cache bounded64");oa_ui_close(&a);for(i=0;i<TEXT_CACHE;i++)CHECK(!glIsTexture(ids[i]),"cache GPU released");}
 CHECK(calls==releases,"CPU provider bitmaps released");
 {DWORD before=GetGuiResources(GetCurrentProcess(),GR_GDIOBJECTS),after;
  for(i=0;i<200;i++){oa_ui_text_bitmap rb;CHECK(oa_ui_text_win32(NULL,1,32,valid[i%5+1],&rb),"GDI repeated");rb.release(rb.release_user,rb.rgba);}
  after=GetGuiResources(GetCurrentProcess(),GR_GDIOBJECTS);printf("GDI resource delta after200 independent rasters=%ld\n",(long)after-(long)before);CHECK(after==before,"GDI resources released");}
 printf("PASS bounded64 cache eviction/close: providerCalls%u releases%u textures%u deleted; GL0\n",calls,releases,seen);
 legacy_ui_close(&b);free(p);free(old);
 eglMakeCurrent(d,EGL_NO_SURFACE,EGL_NO_SURFACE,EGL_NO_CONTEXT);eglDestroyContext(d,ctx);eglDestroySurface(d,surf);eglTerminate(d);
 return 0;
}
