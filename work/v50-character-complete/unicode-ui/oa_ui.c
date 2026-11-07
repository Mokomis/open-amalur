#include <GLES3/gl3.h>
#include "oa_ui.h"
#include <android/log.h>
#include <math.h>
#include <stdlib.h>
#include <string.h>
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR,"OpemAmalurScene",__VA_ARGS__)
enum{MAX_FLOATS=9*60000,MODE_SOLID=0,MODE_SPRITE=1,MODE_TEXT=2,MODE_TITLE=3,MODE_UNICODE=4};
static const char *vertex_source="#version 300 es\nlayout(location=0)in vec2 p;layout(location=1)in vec2 t;layout(location=2)in vec4 c;layout(location=3)in float m;uniform vec2 screen;out vec2 uv;out vec4 color;flat out int mode;void main(){gl_Position=vec4(p.x/screen.x*2.0-1.0,1.0-p.y/screen.y*2.0,0,1);uv=t;color=c;mode=int(m+.5);}";
static const char *fragment_source="#version 300 es\nprecision mediump float;in vec2 uv;in vec4 color;flat in int mode;uniform sampler2D atlas;uniform sampler2D field;uniform sampler2D title;uniform sampler2D shaped;out vec4 frag;void main(){"
 "if(mode==1)frag=texture(atlas,uv)*color;else if(mode==2){float d=texture(field,uv).r,w=max(fwidth(d)*.75,.02);frag=vec4(color.rgb,color.a*smoothstep(.5-w,.5+w,d));}else if(mode==3)frag=vec4(texture(title,uv).rgb,1)*color;else if(mode==4)frag=texture(shaped,uv)*color;else frag=color;}";
static GLuint compile(GLenum type,const char *source){GLint okay=0;GLuint s=glCreateShader(type);glShaderSource(s,1,&source,NULL);glCompileShader(s);glGetShaderiv(s,GL_COMPILE_STATUS,&okay);
 if(!okay){char log[1024];GLsizei n=0;glGetShaderInfoLog(s,sizeof(log)-1,&n,log);log[n]=0;LOGE("UI shader: %s",log);glDeleteShader(s);return 0;}return s;}
static GLuint texture(GLenum format,GLint internal,GLsizei w,GLsizei h,const void *pixels,int mips){GLuint t;glGenTextures(1,&t);glBindTexture(GL_TEXTURE_2D,t);glPixelStorei(GL_UNPACK_ALIGNMENT,1);glTexImage2D(GL_TEXTURE_2D,0,internal,w,h,0,format,GL_UNSIGNED_BYTE,pixels);
 if(mips)glGenerateMipmap(GL_TEXTURE_2D);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MIN_FILTER,mips?GL_LINEAR_MIPMAP_LINEAR:GL_LINEAR);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_MAG_FILTER,GL_LINEAR);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_S,GL_CLAMP_TO_EDGE);glTexParameteri(GL_TEXTURE_2D,GL_TEXTURE_WRAP_T,GL_CLAMP_TO_EDGE);glPixelStorei(GL_UNPACK_ALIGNMENT,4);return t;}
static int need(size_t size,size_t at,size_t count){return at<=size&&count<=size-at;}

enum {TEXT_CACHE=64,TEXT_RUNS=512,TEXT_BYTES=1024,TEXT_SCALARS=256,
 TEXT_MAX_PIXELS=1024*1024,TEXT_BUDGET=16*1024*1024};
typedef struct text_entry {
 char *key; int font;unsigned px;uint64_t used,pinned;
 oa_ui_text_bitmap bitmap;GLuint texture;size_t bytes;
} text_entry;
typedef struct text_run {unsigned first;GLuint texture;} text_run;
struct oa_ui_unicode {
 oa_ui_text_provider provider;void *user;
 text_entry cache[TEXT_CACHE];text_run runs[TEXT_RUNS];
 unsigned count;size_t bytes;uint64_t clock,frame;
};
int oa_ui_text_classify(const char *s){
 size_t i=0;unsigned scalars=0;int extended=0;
 if(!s)return 0;
 while(i<=TEXT_BYTES && s[i]){
  unsigned char c=(unsigned char)s[i++];uint32_t cp,min=0;unsigned n=0,j;
  if(c<128)cp=c;
  else if(c>=0xc2&&c<=0xdf){cp=c&31;n=1;min=0x80;extended=1;}
  else if(c>=0xe0&&c<=0xef){cp=c&15;n=2;min=0x800;extended=1;}
  else if(c>=0xf0&&c<=0xf4){cp=c&7;n=3;min=0x10000;extended=1;}
  else return 0;
  for(j=0;j<n;j++){
   unsigned char x;if(i>=TEXT_BYTES)return 0;x=(unsigned char)s[i++];
   if((x&0xc0)!=0x80)return 0;cp=(cp<<6)|(x&63);
  }
  if(cp<min||cp>0x10ffff||(cp>=0xd800&&cp<=0xdfff)||cp<32||cp==127)return 0;
  if(++scalars>TEXT_SCALARS)return 0;
 }
 return i<=TEXT_BYTES?(extended?2:1):0;
}
/* Printable ASCII retains the existing unbounded C-string path; only the
   system-raster cache has the new per-string bounds. */
static int text_dispatch(const char*s){
 const unsigned char*p=(const unsigned char*)s;if(!p)return 0;
 while(*p>=32&&*p<=126)++p;
 return !*p?1:oa_ui_text_classify(s);
}
static void bitmap_release(oa_ui_text_bitmap *b){
 if(b->rgba&&b->release)b->release(b->release_user,b->rgba);b->rgba=NULL;
}
static void text_drop(oa_ui_unicode *t,text_entry *e){
 if(e->texture)glDeleteTextures(1,&e->texture);
 bitmap_release(&e->bitmap);if(e->key)t->bytes-=e->bytes;free(e->key);memset(e,0,sizeof(*e));
}
static void text_close(oa_ui *u){
 unsigned i;if(!u->unicode)return;
 for(i=0;i<TEXT_CACHE;i++)text_drop(u->unicode,u->unicode->cache+i);
 free(u->unicode);u->unicode=NULL;
}
int oa_ui_set_text_provider(oa_ui *u,oa_ui_text_provider p,void *user){
 if(!u||!u->ready||u->count)return 0;text_close(u);
 if(!p)return 1;u->unicode=(oa_ui_unicode*)calloc(1,sizeof(*u->unicode));
 if(!u->unicode)return 0;u->unicode->provider=p;u->unicode->user=user;return 1;
}
static text_entry *text_evictable(oa_ui_unicode*t){
 unsigned i;text_entry *old=NULL;
 for(i=0;i<TEXT_CACHE;i++){
  text_entry *e=t->cache+i;if(!e->key)return e;
  if(e->pinned!=t->frame&&(!old||e->used<old->used))old=e;
 }return old;
}
static text_entry *text_get(const oa_ui *u,int font,float px,const char*s){
 oa_ui_unicode*t=u->unicode;text_entry*e;oa_ui_text_bitmap b;unsigned i,size;
 if(!t||!isfinite(px)||px<1||px>256)return NULL;size=(unsigned)floorf(px+.5f);
 for(i=0;i<TEXT_CACHE;i++){
  e=t->cache+i;if(e->key&&e->font==font&&e->px==size&&!strcmp(e->key,s)){e->used=++t->clock;return e;}
 }
 e=text_evictable(t);if(!e)return NULL;
 memset(&b,0,sizeof b);
 if(!t->provider(t->user,font,size,s,&b)||!b.rgba||!b.release||
  !b.width||!b.height||b.width>4096||b.height>4096||
  (size_t)b.width*b.height>TEXT_MAX_PIXELS||
  !isfinite(b.advance)||b.advance<0||b.advance>8192||
  !isfinite(b.origin_x)||!isfinite(b.origin_y)||
  fabsf(b.origin_x)>4096||fabsf(b.origin_y)>4096){bitmap_release(&b);return NULL;}
 {
  size_t bytes=(size_t)b.width*b.height*4;char*k=(char*)malloc(strlen(s)+1);
  if(!k){bitmap_release(&b);return NULL;}strcpy(k,s);
  text_drop(t,e);
  while(t->bytes+bytes>TEXT_BUDGET){
   text_entry*v=text_evictable(t);
   /* Empty slots do not release budget; scan occupied LRU instead. */
   if(v&&!v->key){
    v=NULL;for(i=0;i<TEXT_CACHE;i++){text_entry*a=t->cache+i;if(a->key&&a->pinned!=t->frame&&(!v||a->used<v->used))v=a;}
   }
   if(!v||!v->key){free(k);bitmap_release(&b);return NULL;}text_drop(t,v);
  }
  e->key=k;e->font=font;e->px=size;e->bitmap=b;e->bytes=bytes;e->used=++t->clock;t->bytes+=bytes;
 }
 return e;
}

int oa_ui_open(oa_ui *u,const uint8_t *b,size_t size){
 size_t at=8;uint32_t w,h,count;int f;GLint okay=0;GLuint vs,fs;memset(u,0,sizeof(*u));
 if(size<16||memcmp(b,"OAUI0002",8)){LOGE("UI asset invalid");return 0;}
 memcpy(&w,b+at,4);memcpy(&h,b+at+4,4);at+=8;if(w>4096||h>4096||!need(size,at,(size_t)w*h*4+4)){LOGE("UI atlas invalid");return 0;}
 {const uint8_t *pixels=b+at;at+=(size_t)w*h*4;memcpy(&count,b+at,4);at+=4;if(count!=OA_SPR_COUNT||!need(size,at,count*8u)){LOGE("UI sprites invalid");return 0;}
  memcpy(u->sprites,b+at,count*8u);at+=count*8u;u->atlas_w=(float)w;u->atlas_h=(float)h;u->atlas=texture(GL_RGBA,GL_RGBA8,(GLsizei)w,(GLsizei)h,pixels,1);}
 if(!need(size,at,8)){oa_ui_close(u);return 0;}memcpy(&w,b+at,4);memcpy(&h,b+at+4,4);at+=8;if(w>4096||h>4096||!need(size,at,(size_t)w*h)){LOGE("UI field invalid");oa_ui_close(u);return 0;}
 u->field_w=(float)w;u->field_h=(float)h;u->field=texture(GL_RED,GL_R8,(GLsizei)w,(GLsizei)h,b+at,0);at+=(size_t)w*h;
 for(f=0;f<2;f++){int i;if(!need(size,at,12+95*16)){LOGE("UI font invalid");oa_ui_close(u);return 0;}memcpy(&u->fonts[f].px,b+at,4);memcpy(&u->fonts[f].ascent,b+at+4,4);memcpy(&u->fonts[f].line,b+at+8,4);at+=12;
  for(i=0;i<95;i++,at+=16){memcpy(&u->fonts[f].glyphs[i],b+at,16);}}
 if(!need(size,at,8)){oa_ui_close(u);return 0;}memcpy(&w,b+at,4);memcpy(&h,b+at+4,4);at+=8;if(w>4096||h>4096||(size_t)w*h*3!=size-at){LOGE("UI title invalid");oa_ui_close(u);return 0;}
 u->title=texture(GL_RGB,GL_RGB8,(GLsizei)w,(GLsizei)h,b+at,0);
 vs=compile(GL_VERTEX_SHADER,vertex_source);fs=vs?compile(GL_FRAGMENT_SHADER,fragment_source):0;if(!fs){if(vs)glDeleteShader(vs);oa_ui_close(u);return 0;}
 u->program=glCreateProgram();glAttachShader(u->program,vs);glAttachShader(u->program,fs);glLinkProgram(u->program);glDeleteShader(vs);glDeleteShader(fs);glGetProgramiv(u->program,GL_LINK_STATUS,&okay);if(!okay){LOGE("UI link failed");oa_ui_close(u);return 0;}
 u->vertices=(float*)malloc(MAX_FLOATS*sizeof(float));if(!u->vertices){oa_ui_close(u);return 0;}
 u->screen=glGetUniformLocation(u->program,"screen");glUseProgram(u->program);glUniform1i(glGetUniformLocation(u->program,"atlas"),0);glUniform1i(glGetUniformLocation(u->program,"field"),1);glUniform1i(glGetUniformLocation(u->program,"title"),2);glUniform1i(glGetUniformLocation(u->program,"shaped"),3);
 glGenVertexArrays(1,&u->array);glGenBuffers(1,&u->buffer);glBindVertexArray(u->array);glBindBuffer(GL_ARRAY_BUFFER,u->buffer);
 glEnableVertexAttribArray(0);glVertexAttribPointer(0,2,GL_FLOAT,GL_FALSE,36,(void*)0);glEnableVertexAttribArray(1);glVertexAttribPointer(1,2,GL_FLOAT,GL_FALSE,36,(void*)8);glEnableVertexAttribArray(2);glVertexAttribPointer(2,4,GL_FLOAT,GL_FALSE,36,(void*)16);glEnableVertexAttribArray(3);glVertexAttribPointer(3,1,GL_FLOAT,GL_FALSE,36,(void*)32);glBindVertexArray(0);
 if(glGetError()!=GL_NO_ERROR){LOGE("UI upload failed");oa_ui_close(u);return 0;}
 u->ready=1;return 1;
}
void oa_ui_close(oa_ui *u){text_close(u);if(u->atlas)glDeleteTextures(1,&u->atlas);if(u->field)glDeleteTextures(1,&u->field);if(u->title)glDeleteTextures(1,&u->title);if(u->buffer)glDeleteBuffers(1,&u->buffer);if(u->array)glDeleteVertexArrays(1,&u->array);if(u->program)glDeleteProgram(u->program);free(u->vertices);memset(u,0,sizeof(*u));}
void oa_ui_begin(oa_ui *u){u->count=0;if(u->unicode){u->unicode->count=0;++u->unicode->frame;if(!u->unicode->frame)++u->unicode->frame;}}
void oa_ui_end(oa_ui *u,int width,int height){
 if(!u->ready||!u->count)return;
 glDisable(GL_DEPTH_TEST);glDepthMask(GL_FALSE);glEnable(GL_BLEND);glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA);glUseProgram(u->program);glUniform2f(u->screen,(float)width,(float)height);
 glActiveTexture(GL_TEXTURE2);glBindTexture(GL_TEXTURE_2D,u->title);glActiveTexture(GL_TEXTURE1);glBindTexture(GL_TEXTURE_2D,u->field);glActiveTexture(GL_TEXTURE0);glBindTexture(GL_TEXTURE_2D,u->atlas);
 glBindVertexArray(u->array);glBindBuffer(GL_ARRAY_BUFFER,u->buffer);glBufferData(GL_ARRAY_BUFFER,u->count*sizeof(float),u->vertices,GL_STREAM_DRAW);{
  unsigned at=0,k;oa_ui_unicode*t=u->unicode;
  if(t)for(k=0;k<t->count;k++){
   text_run*r=t->runs+k;
   if(r->first>at)glDrawArrays(GL_TRIANGLES,(GLint)at,(GLsizei)(r->first-at));
   glActiveTexture(GL_TEXTURE3);glBindTexture(GL_TEXTURE_2D,r->texture);
   glDrawArrays(GL_TRIANGLES,(GLint)r->first,6);at=r->first+6;
  }
  if(u->count/9>at)glDrawArrays(GL_TRIANGLES,(GLint)at,(GLsizei)(u->count/9-at));
 }glActiveTexture(GL_TEXTURE0);glBindVertexArray(0);
 glDisable(GL_BLEND);glDepthMask(GL_TRUE);glEnable(GL_DEPTH_TEST);u->count=0;if(u->unicode)u->unicode->count=0;
}
static void vertex(oa_ui *u,float x,float y,float s,float t,const float c[4],float mode){float *v=u->vertices+u->count;v[0]=x;v[1]=y;v[2]=s;v[3]=t;memcpy(v+4,c,16);v[8]=mode;u->count+=9;}
static int room(const oa_ui *u,unsigned vertices){return u->vertices&&u->count+vertices*9u<=MAX_FLOATS;}
static void quad(oa_ui *u,float x,float y,float w,float h,float s0,float t0,float s1,float t1,const float a[4],const float b[4],const float c[4],const float d[4],float mode){
 if(!room(u,6))return;vertex(u,x,y,s0,t0,a,mode);vertex(u,x+w,y,s1,t0,b,mode);vertex(u,x+w,y+h,s1,t1,c,mode);vertex(u,x,y,s0,t0,a,mode);vertex(u,x+w,y+h,s1,t1,c,mode);vertex(u,x,y+h,s0,t1,d,mode);}
void oa_ui_rect(oa_ui *u,float x,float y,float w,float h,const float c[4]){quad(u,x,y,w,h,0,0,0,0,c,c,c,c,MODE_SOLID);}
void oa_ui_fade(oa_ui *u,float x,float y,float w,float h,const float l[4],const float r[4]){quad(u,x,y,w,h,0,0,0,0,l,r,r,l,MODE_SOLID);}
void oa_ui_fade_v(oa_ui *u,float x,float y,float w,float h,const float t[4],const float b[4]){quad(u,x,y,w,h,0,0,0,0,t,t,b,b,MODE_SOLID);}
void oa_ui_sprite(oa_ui *u,int id,float x,float y,float w,float h,float fraction,const float c[4]){const uint16_t *s=u->sprites[id];float f=fraction<0?0:fraction>1?1:fraction;
 quad(u,x,y,w*f,h,(s[0]+.5f)/u->atlas_w,(s[1]+.5f)/u->atlas_h,(s[0]+(s[2]-1)*f+.5f)/u->atlas_w,(s[1]+s[3]-.5f)/u->atlas_h,c,c,c,c,MODE_SPRITE);}
void oa_ui_title(oa_ui *u,float x,float y,float w,float h){const float c[4]={1,1,1,1};quad(u,x,y,w,h,0,0,1,1,c,c,c,c,MODE_TITLE);}
void oa_ui_disk(oa_ui *u,float x,float y,float r,const float c[4]){int i;for(i=0;i<48;i++){float a=i*.1308997f,b=(i+1)*.1308997f;if(!room(u,3))return;vertex(u,x,y,0,0,c,0);vertex(u,x+r*cosf(a),y+r*sinf(a),0,0,c,0);vertex(u,x+r*cosf(b),y+r*sinf(b),0,0,c,0);}}
void oa_ui_ring(oa_ui *u,float x,float y,float r,float t,const float c[4]){int i;float q=r-t;for(i=0;i<64;i++){float a=i*.09817477f,b=(i+1)*.09817477f,ca=cosf(a),sa=sinf(a),cb=cosf(b),sb=sinf(b);if(!room(u,6))return;
 vertex(u,x+q*ca,y+q*sa,0,0,c,0);vertex(u,x+r*ca,y+r*sa,0,0,c,0);vertex(u,x+r*cb,y+r*sb,0,0,c,0);vertex(u,x+q*ca,y+q*sa,0,0,c,0);vertex(u,x+r*cb,y+r*sb,0,0,c,0);vertex(u,x+q*cb,y+q*sb,0,0,c,0);}}

float oa_ui_measure(const oa_ui *u,int font,float px,const char *s){
 float total=0,scale;int kind;
 if(!u||font<0||font>1||!isfinite(px)||px<=0||!(kind=text_dispatch(s)))return 0;
 if(kind==2){text_entry*e=text_get(u,font,px,s);return e?e->bitmap.advance:0;}
 scale=px/u->fonts[font].px;
 for(;*s;s++){unsigned c=(unsigned char)*s;if(c<32||c>126)c='?';total+=u->fonts[font].glyphs[c-32].advance*scale;}return total;
}
void oa_ui_text(oa_ui *u,int font,float x,float y,float px,int align,const float color[4],const char *s){
 float scale;int kind;
 if(!u||font<0||font>1||!isfinite(px)||px<=0||!(kind=text_dispatch(s)))return;
 if(kind==2){
  text_entry*e=text_get(u,font,px,s);oa_ui_unicode*t=u->unicode;text_run*r;
  if(!e||!t||t->count>=TEXT_RUNS||!room(u,6))return;
  if(!e->texture){
   GLint limit=0;glGetIntegerv(GL_MAX_TEXTURE_SIZE,&limit);
   if(e->bitmap.width>(unsigned)limit||e->bitmap.height>(unsigned)limit){text_drop(t,e);return;}
   e->texture=texture(GL_RGBA,GL_RGBA8,(GLsizei)e->bitmap.width,(GLsizei)e->bitmap.height,e->bitmap.rgba,0);bitmap_release(&e->bitmap);
  }
  if(!e->texture)return;
  if(align!=OA_ALIGN_LEFT)x-=align==OA_ALIGN_CENTER?e->bitmap.advance*.5f:e->bitmap.advance;
  r=t->runs+t->count++;r->first=u->count/9;r->texture=e->texture;e->pinned=t->frame;
  quad(u,x+e->bitmap.origin_x,y+e->bitmap.origin_y,(float)e->bitmap.width,(float)e->bitmap.height,0,0,1,1,color,color,color,color,MODE_UNICODE);return;
 }
 scale=px/u->fonts[font].px;
 if(align!=OA_ALIGN_LEFT){float m=oa_ui_measure(u,font,px,s);x-=align==OA_ALIGN_CENTER?m*.5f:m;}
 for(;*s;s++){unsigned c=(unsigned char)*s;if(c<32||c>126)c='?';
  {const float gx=x+u->fonts[font].glyphs[c-32].ox*scale,gy=y+u->fonts[font].glyphs[c-32].oy*scale,a=u->fonts[font].glyphs[c-32].x,b=u->fonts[font].glyphs[c-32].y,w=u->fonts[font].glyphs[c-32].w,h=u->fonts[font].glyphs[c-32].h;
   if(c!=32)quad(u,gx,gy,w*scale,h*scale,a/u->field_w,b/u->field_h,(a+w)/u->field_w,(b+h)/u->field_h,color,color,color,color,MODE_TEXT);
   x+=u->fonts[font].glyphs[c-32].advance*scale;}}
}
