#ifndef OA_UI_H
#define OA_UI_H
/* Veil UI drawing: one batched draw of game sprites, baked text and solid shapes. */
#include <stddef.h>
#include <stdint.h>
enum{OA_SPR_HEALTH,OA_SPR_MANA,OA_SPR_FATE,OA_SPR_DIAMOND,OA_SPR_GOLD,OA_SPR_SKULL,OA_SPR_SWORDS,OA_SPR_ARMOR,OA_SPR_COINS,OA_SPR_DRAGON,OA_SPR_HAMMER,OA_SPR_MORTAR,
 OA_SPR_I_IRON,OA_SPR_I_STEEL,OA_SPR_I_AZURITE,OA_SPR_I_SYLVANITE,OA_SPR_I_PRISMERE,OA_SPR_I_HELM,OA_SPR_I_HELM2,OA_SPR_I_CUIRASS,OA_SPR_I_CUIRASS2,OA_SPR_I_GAUNT,OA_SPR_I_GAUNT2,OA_SPR_I_LEGS,OA_SPR_I_LEGS2,OA_SPR_I_BOOTS,OA_SPR_I_BOOTS2,OA_SPR_I_POTION,OA_SPR_I_POTION2,OA_SPR_I_POTION3,OA_SPR_COUNT};
enum{OA_FONT_HEAD,OA_FONT_BODY};
enum{OA_ALIGN_LEFT,OA_ALIGN_CENTER,OA_ALIGN_RIGHT};
typedef struct oa_ui oa_ui;

/* Non-ASCII is rasterized as ONE shaped string. Pixel origin is relative to the
   supplied text anchor (top of font line box, as the existing atlas path).
   Pixels are tightly packed TOP-DOWN straight-alpha RGBA. Tintable glyphs use
   white RGB + coverage; a provider may retain actual RGB for color glyphs.
   Success transfers pixel ownership to UI until release(user,pixels); failures
   must also return any allocated pixels with a release callback. Provider user
   remains caller-owned. Callbacks are synchronous on the render thread. */
typedef struct oa_ui_text_bitmap {
 uint8_t *rgba;
 unsigned width,height;
 float advance,origin_x,origin_y;
 void (*release)(void *user,uint8_t *rgba);
 void *release_user;
} oa_ui_text_bitmap;
typedef int (*oa_ui_text_provider)(void *user,int font,unsigned pixel_size,
 const char *utf8,oa_ui_text_bitmap *out);
/* Must be called after open, with current GL context, outside an active batch.
   NULL disables the provider; replacing it clears CPU/GPU cached text. */
int oa_ui_set_text_provider(oa_ui *u,oa_ui_text_provider provider,void *user);
/* Strict bounded UTF8: no surrogate/overlong/out-of-range/control sequences.
   Returns1 validASCII,2 validnonASCII,0 invalid; max1024bytes/256scalars. */
int oa_ui_text_classify(const char *utf8);
typedef struct oa_ui_unicode oa_ui_unicode;

void oa_ui_rect(oa_ui *u,float x,float y,float w,float h,const float c[4]);
/* Colors run left to right. */
void oa_ui_fade(oa_ui *u,float x,float y,float w,float h,const float left[4],const float right[4]);
/* Colors run top to bottom. */
void oa_ui_fade_v(oa_ui *u,float x,float y,float w,float h,const float top[4],const float bottom[4]);
/* fraction crops the sprite from its right edge without squashing it. */
void oa_ui_sprite(oa_ui *u,int sprite,float x,float y,float w,float h,float fraction,const float c[4]);
void oa_ui_disk(oa_ui *u,float x,float y,float radius,const float c[4]);
void oa_ui_ring(oa_ui *u,float x,float y,float radius,float thickness,const float c[4]);
void oa_ui_title(oa_ui *u,float x,float y,float w,float h);
float oa_ui_measure(const oa_ui *u,int font,float px,const char *text);
void oa_ui_text(oa_ui *u,int font,float x,float y,float px,int align,const float c[4],const char *text);
#ifdef GL_ES_VERSION_3_0
struct oa_ui{GLuint program,array,buffer,atlas,field,title;GLint screen;float *vertices;unsigned count;int ready;
 uint16_t sprites[OA_SPR_COUNT][4];float atlas_w,atlas_h,field_w,field_h;
 struct{float px,ascent,line;struct{uint16_t x,y,w,h;int16_t ox,oy;float advance;}glyphs[95];}fonts[2];
 oa_ui_unicode *unicode;};
int oa_ui_open(oa_ui *u,const uint8_t *bytes,size_t size);
void oa_ui_close(oa_ui *u);
void oa_ui_begin(oa_ui *u);
void oa_ui_end(oa_ui *u,int width,int height);
#endif
#endif
