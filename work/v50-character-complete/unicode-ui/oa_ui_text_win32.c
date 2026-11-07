#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <usp10.h>
#include <stdlib.h>
#include <string.h>
#include "oa_ui_text_win32.h"
typedef HRESULT (WINAPI *Analyze)(HDC,const void*,int,int,int,DWORD,int,
 SCRIPT_CONTROL*,SCRIPT_STATE*,const int*,SCRIPT_TABDEF*,const BYTE*,SCRIPT_STRING_ANALYSIS*);
typedef const SIZE* (WINAPI *GetSize)(SCRIPT_STRING_ANALYSIS);
typedef HRESULT (WINAPI *Output)(SCRIPT_STRING_ANALYSIS,int,int,UINT,const RECT*,int,int,BOOL);
typedef HRESULT (WINAPI *FreeAnalysis)(SCRIPT_STRING_ANALYSIS*);
static void release_pixels(void *u,uint8_t*p){(void)u;free(p);}
int oa_ui_text_win32(void *user,int font,unsigned px,const char*s,oa_ui_text_bitmap*out){
 HMODULE dll=NULL;HDC dc=NULL;HFONT hf=NULL;HBITMAP bm=NULL;
 HGDIOBJ oldfont=NULL,oldbm=NULL;SCRIPT_STRING_ANALYSIS a=NULL;
 Analyze analyze=NULL;GetSize getsize=NULL;Output output=NULL;FreeAnalysis freea=NULL;
 wchar_t *wide=NULL;void*bits=NULL;BITMAPINFO bi;const SIZE*sz;
 unsigned w=0,h=0,x,y,pad;int n,ok=0;size_t bytes;uint8_t*rgba=NULL;
 (void)user;if(!out)return 0;memset(out,0,sizeof(*out));
 if(font<0||font>1||px<1||px>256||!oa_ui_text_classify(s))return 0;
 n=MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,s,-1,NULL,0);
 if(n<=1||n>1025)return 0;wide=(wchar_t*)malloc((size_t)n*sizeof(wchar_t));
 if(!wide||MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,s,-1,wide,n)!=n)goto done;
 /* Restrict dynamic loading to System32, never current/search directories. */
 {wchar_t path[MAX_PATH];UINT z=GetSystemDirectoryW(path,MAX_PATH);
  if(!z||z+11>=MAX_PATH)goto done;memcpy(path+z,L"\\usp10.dll",11*sizeof(wchar_t));dll=LoadLibraryW(path);}
 if(!dll)goto done;
 analyze=(Analyze)GetProcAddress(dll,"ScriptStringAnalyse");getsize=(GetSize)GetProcAddress(dll,"ScriptString_pSize");
 output=(Output)GetProcAddress(dll,"ScriptStringOut");freea=(FreeAnalysis)GetProcAddress(dll,"ScriptStringFree");
 if(!analyze||!getsize||!output||!freea)goto done;
 dc=CreateCompatibleDC(NULL);if(!dc)goto done;
 hf=CreateFontW(-(int)px,0,0,0,font==OA_FONT_HEAD?FW_SEMIBOLD:FW_NORMAL,FALSE,FALSE,FALSE,
 DEFAULT_CHARSET,OUT_DEFAULT_PRECIS,CLIP_DEFAULT_PRECIS,ANTIALIASED_QUALITY,
 DEFAULT_PITCH|FF_DONTCARE,L"Segoe UI");
 if(!hf)goto done;oldfont=SelectObject(dc,hf);
 if(FAILED(analyze(dc,wide,n-1,0,-1,SSA_GLYPHS|SSA_FALLBACK|SSA_LINK,0,NULL,NULL,NULL,NULL,NULL,&a)))goto done;
 sz=getsize(a);if(!sz||sz->cx<0||sz->cy<=0||sz->cx>4000||sz->cy>4000)goto done;
 pad=px/4+4;w=(unsigned)sz->cx+2*pad;h=(unsigned)sz->cy+2*pad;
 if(w>4096||h>4096||(size_t)w*h>1024*1024)goto done;bytes=(size_t)w*h*4;
 memset(&bi,0,sizeof bi);bi.bmiHeader.biSize=sizeof(BITMAPINFOHEADER);
 bi.bmiHeader.biWidth=(LONG)w;bi.bmiHeader.biHeight=-(LONG)h;bi.bmiHeader.biPlanes=1;
 bi.bmiHeader.biBitCount=32;bi.bmiHeader.biCompression=BI_RGB;
 bm=CreateDIBSection(dc,&bi,DIB_RGB_COLORS,&bits,NULL,0);if(!bm||!bits)goto done;
 oldbm=SelectObject(dc,bm);memset(bits,0,bytes);
 SetBkMode(dc,TRANSPARENT);SetTextColor(dc,RGB(255,255,255));
 if(FAILED(output(a,(int)pad,(int)pad,0,NULL,0,0,FALSE)))goto done;
 GdiFlush();rgba=(uint8_t*)malloc(bytes);if(!rgba)goto done;
 for(y=0;y<h;y++)for(x=0;x<w;x++){
  size_t i=((size_t)y*w+x)*4;const uint8_t*b=(const uint8_t*)bits+i;
  unsigned c=b[0]>b[1]?b[0]:b[1];if(b[2]>c)c=b[2];
  rgba[i]=rgba[i+1]=rgba[i+2]=255;rgba[i+3]=(uint8_t)c;
 }
 out->rgba=rgba;rgba=NULL;out->width=w;out->height=h;out->advance=(float)sz->cx;
 out->origin_x=-(float)pad;out->origin_y=-(float)pad;
 out->release=release_pixels;out->release_user=NULL;ok=1;
done:
 free(rgba);
 if(a)freea(&a);
 if(oldbm)SelectObject(dc,oldbm);if(bm)DeleteObject(bm);
 if(oldfont)SelectObject(dc,oldfont);if(hf)DeleteObject(hf);
 if(dc)DeleteDC(dc);if(dll)FreeLibrary(dll);free(wide);return ok;
}
