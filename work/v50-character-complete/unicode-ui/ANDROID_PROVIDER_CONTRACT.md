# Android whole-string provider contract

Use oa_ui_text_provider from oa_ui.h, returning1only after a complete valid bitmap is ready. This is a synchronous render-thread call:
    int provider(void *user,int font,unsigned integer_pixel_size,
                 const char *utf8,oa_ui_text_bitmap *out);

Inputs already pass shared strict UTF8 validation and size bounds. Convert UTF8 to UTF16 by scalar value (preserve surrogate pairs), never by byte casting or JNI NewStringUTF (modifiedUTF8 differs for non-BMP). An explicit JNI NewString with correct UTF16 is suitable. Preserve the original string in the creator/profile.

Render the ENTIRE string in one system text operation with shaping/font fallback (e.g.Android Canvas/Paint or an equivalent platform text layout). Font IDs0/1 correspond to head/body styles. Pixel size is physical pixels, not sp/dp; avoid applying density twice. Do not add per-glyph spacing or split combining/RTL sequences. No normalized/changed string is returned.

Return a tightly packed TOP-DOWN straight-alpha RGBA allocation, width/height plus finite advance/origin_x/origin_y. y anchor is top of the font linebox: for Canvas baseline drawing, choose baseline=-fontMetrics.ascent plus padding, and return origin_y=-padding. White RGB plus coverage permits UI tint; actual color glyph RGB may be retained. Convert Android's premultiplied output to STRAIGHT alpha before returning; transparent pixels can have RGBwhite or0. Ensure no LCD/color fringing alpha assumption. Padding must contain relevant glyph overhang. Use actual whole-string advance for alignment.

Output limits: eachdimension<=4096, total<=1M pixels, advance0..8192, abs(origin)<=4096. Must clear output on failure. If a failed provider allocated memory, still provide release callback+pixels so shared UI can release them. UI retains pixels on a measure-only request, uploads during draw, then calls release(user,pixels). Use an independent native allocation whose release works synchronously on the render thread; do not retain a locked Java bitmap. Release Java local/global refs and temporary arrays within the provider/owner lifecycle.

Calls occur only with a valid UI and current GL context on the render thread. The provider itself must not mutate shared UI or its GL bindings and must not call measure/draw recursively. Caller-owned user context lives until oa_ui_set_text_provider(ui,NULL,NULL) or oa_ui_close has completed.

Cache key is exact UTF8 string +font +roundedintegerpx. Runtime font/style/locale changes require clearing/replacing the provider before rendering the next batch. No universal glyph coverage is promised; system installed fallback decides. Shared code deliberately rejects malformed text rather than displaying question marks per input byte.

Root separately owns platform committedUTF8/IME composition and the16scalar/64byte name policy. This callback only measures/rasterizes.
