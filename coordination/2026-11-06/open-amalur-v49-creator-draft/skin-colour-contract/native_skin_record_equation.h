#ifndef OA_NATIVE_SKIN_RECORD_EQUATION_H
#define OA_NATIVE_SKIN_RECORD_EQUATION_H
#include <stdint.h>
/* REFERENCE EQUATION ONLY, not a renderer or fresh-state default.
 * Validated caller selects a real SkinTone20B record. existing_argb is required;
 * the original setter preserves ITS high8bits, not the palette's alpha.
 * Source authored IDs below are for the custom asset lookup; native loading may
 * replace corresponding runtime record refs with resource handles. */
typedef struct oa_native_skin_record_result {uint32_t option_key,packed_argb,head_diffuse_asset,body_diffuse_asset;float skin_color[4];} oa_native_skin_record_result;
static void oa_native_skin_record_equation(const uint32_t words[5],uint32_t existing_argb,oa_native_skin_record_result*out){
 const double native_scale=0.0039215688593685626983642578125;
 uint32_t c=(words[1]&UINT32_C(0x00ffffff))|(existing_argb&UINT32_C(0xff000000));
 out->option_key=words[0];out->packed_argb=c;
 out->head_diffuse_asset=words[3];out->body_diffuse_asset=words[4];
 out->skin_color[0]=(float)((double)((c>>16)&255u)*native_scale);
 out->skin_color[1]=(float)((double)((c>>8)&255u)*native_scale);
 out->skin_color[2]=(float)((double)(c&255u)*native_scale);
 out->skin_color[3]=(float)((double)(c>>24)*native_scale);
 /* words[2] is not consumed by native set_skin_color. */
}
#endif
