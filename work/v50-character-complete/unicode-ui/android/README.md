# Android whole-string text provider — staging only

Production files:
- oa_ui_text_android.c/.h
- private headers oa_ui_text_utf16.h and oa_ui_text_pixels.h
- java/org/opemamalur/scene/TextRasterizer.java, including ALL generated nested classes.

The already-validated shared parent oa_ui.c/h and Windows provider remain unchanged.

## Integration

Compile oa_ui_text_android.c into the Android native engine (C99) and link jnigraphics. Existing android/log/m libraries are also required and already used by the engine. This is not a separate production shared library: liboa-ui-text-android-check.so is an isolated link/ABI check only.

After opening VeilUI with a current GL context and a live Activity:
    oa_ui_text_android_context *text = oa_ui_text_android_open(app->activity);
    if (text && !oa_ui_set_text_provider(ui, oa_ui_text_android, text)) {
        oa_ui_text_android_close(text); text = NULL;
    }

On teardown, stop provider calls and close/clear VeilUI while the GL context is current, THEN:
    oa_ui_text_android_close(text);

Alternatively set_text_provider(ui,NULL,NULL) outside an active batch before closing the context. Context owns3JNIglobalrefs(Activity/helper/Resultclass); close releases them. Static Java font cache holds only2Typefaces, not an Activity. Provider calls are synchronous and serial; no callback may race close.

The caller's existing render-thread attachment is reused. GetEnv is queried each call. A thread is detached only if this provider itself attached it. Everycall uses a bounded JNILocalFrame and pops all references. App helper classes are loaded through Activity.getClassLoader().loadClass, so attached native-worker FindClass loader ambiguity is avoided.

## JavaDEX packaging

Compile this Java source alongside the root's IME/input helper sources with the installed SDK35 android.jar/JDK21. Run D8 on the COMBINED class JAR(s) to produce the application's classes.dex. Do not replace the app DEX with this fixture's standalone DEX; it contains only TextRasterizer. Include all nested/synthetic classes (Result,Api29,Api35,and$1). If a future shrinker is introduced, keep TextRasterizer and its nested classes, render signature and Result fields.

Standalone reproducible check:
    build_checks.cmd

It emits text-rasterizer.jar and dex/classes.dex (DEX038/minAPI26), plus javac/D8logs. java-signatures.txt independently records the exact descriptors used by JNI:
render(Activity,String,int,int)->TextRasterizer$Result;
Result.bitmap:Bitmap, advance/originX/originY:float.

Root asset packaging must include the existing font files, without re-downloading:
- assets/fonts/Cinzel.ttf from work/v21-ui/fonts/Cinzel.ttf,125468B
- assets/fonts/Alegreya.ttf from work/v21-ui/fonts/Alegreya.ttf,425288B
- preserve Cinzel-OFL.txt and Alegreya-OFL.txt alongside the distributed fonts/licenses.
Exact source SHA values are in receipt.json. No font or license assets are copied/changed by this stage.

## Rendering/metrics/ownership

Entire valid text is passed to one StaticLayout/Canvas draw, with combining marks, bidi and system shaping/fallback. Source Cinzel weight600(head) and Alegreya500(body) are loaded from app assets. API29+ explicitly uses Typeface.CustomFallbackBuilder with sans-serif system fallback. API26–28 uses the framework asset-Typeface fallback path. There is no replacement generic font if the packaged source fonts are missing: provider returns failure.

Pixel size is actual pixels, never dp/sp. Layout advance is measured once by Layout.getDesiredWidth using the same TextPaint/Typeface. Output origins preserve logical font-linebox anchor and any shaped glyph overhang. API35+ uses computeDrawingBoundingBox for actual shaped/fallback ink; older APIs use textbounds plus half-em padding and have an explicit exotic-overhang limit. No clipping/one-line truncation is intentionally imposed; bitmap size budgets can instead reject the whole request. No ellipsizing, normalization or stored-name mutation.

Java returns an exclusive software ARGB8888 Bitmap and metrics. JNI validates dimensions/stride/format, locks only while copying, respects row stride, converts PREMULTIPLIED nativeRGBA to tightly-packed STRAIGHT RGBA, unlocks, recycles the JavaBitmap, pops local refs and returns an independent malloc buffer with free callback. hasAlpha/isPremultiplied are queried from Java rather than assuming API30bitmap-info flags on older Android.

Source UTF8 is decoded strictly into real UTF16 and passed through NewString. NewStringUTF is used ONLY for ASCIIclass-name literals, never for user text. Non-BMP input becomes the correct surrogate pair. Malformed/overlong/surrogate/out-of-range UTF8, ASCIIcontrol/DEL, empty or excessive requests fail closed. Shared cache/name policies remain separate: this provider allows<=1024UTF8bytes/256scalars; root's creator remains16scalars/64bytes.

## Checks and limits

PASS SDK35 javac/JDK21 target8 and D8 min26; no source/DEX warnings.
PASS NDKr30 aarch64 API26 -std=c99 -Wall -Wextra -Werror compile+standalone link.
ELF64 AArch64 exports all3APIfunctions and links libjnigraphics; see elf-validation.txt.
PASS executed pureC conversion cases: ASCII,composedé,decomposed e+acute,CJK,non-BMP,U+10FFFF; correct surrogatepairs;256nonBMP=>512UTF16units.13invalid byte sequences plus NULL/control/empty/capacity/257scalar cases reject.
PASS executed pixel conversion: rowstride,premul alpha0/128/255,saturation,colorchannels,already-straight and opaque rows.
CPU test source is exactly the private helpers compiled by the production Android C provider.

No Android VM/runtime/font-visual/GL/device test was executed here. Root owns actual packaged APK/Activity classloader/font availability/IME/tablet checks. Installed system fallback determines coverage; no universal Unicode glyph coverage, identical Android/Windows typography, or original-game font parity is promised. The source ASCII atlas path is untouched.

All writes are confined to this new android subfolder. No live/default assets, shared sealed renderer, device settings, saves or DB changes.
