# Shared Veil Unicode text — staged, frozen

Integration files (only):
- oa_ui.c / oa_ui.h: replace the same shared Veil units together; OAUI0002 assets unchanged.
- oa_ui_text_win32.c / .h: desktop provider. Existing gdi32/user32 linkage is sufficient; Uniscribe is loaded only by absolute System32 path. Do not compile this Windows unit for Android.
- Android provider: root-owned; see ANDROID_PROVIDER_CONTRACT.md.

After successful oa_ui_open, while the GL context is current:
    oa_ui_set_text_provider(ui, oa_ui_text_win32, NULL);
Call oa_ui_begin/end normally. Call oa_ui_close before destroying the GL context. If replacing/disabling a provider, call set_text_provider outside an active batch. The provider's user context remains caller-owned and must outlive clearing/closing UI caches. Shared measure remains const in signature but updates the pointed-to private cache; all UI calls remain render-thread only.

## Coverage and layout

Printable ASCII U+0020..007E uses the ORIGINAL font atlas, metrics and geometry path, with no provider calls or font-bank changes. All95glyphs, all8source default names, multiple sizes/alignments, fractional size and a400character ASCII string are checked against the untouched legacy C. The1024x640ANGLE result is byte-exact across2621440RGBA bytes, and generated vertices/measures are exact.

A string containing any non-ASCII scalar is passed WHOLE to the provider, including its ASCII substring. No byte-per-glyph rendering, shaping segmentation, normalization or replacement of stored text occurs. Measurement and drawing reuse exactly the same raster and advance, including rounded integer pixel-size. Anchor y is the top of the font linebox, matching the existing UI convention; bitmap origin is relative to that anchor. Alignment uses logical advance, not padded bitmap width.

The provider uses system SegoeUI/semibold plus Uniscribe shaping/font linking/fallback. Native ASCII font identities remain unchanged; non-ASCII inspection fonts are explicitly system fonts. Installed fonts determine glyph coverage. Windows emoji sample is monochrome. This is not a universal-font or original-game typography parity claim.

Strict malformed/overlong/surrogate/out-of-range UTF8 and ASCIIcontrol/DEL strings fail closed (measure0, no draw, no provider call). Printable ASCII retains the pre-existing unbounded C-string path subject to original vertex capacity; extended cache strings are limited to1024bytes/256scalars and1..256rounded pixels. The public text_classify helper applies the bounded contract even for ASCII; do not substitute it for the creator's separate16scalar/64byte name validator.

## Batching, ownership and bounds

64whole-string entries, aggregate16MiB bitmap-or-GPU pixel storage, max1M pixels/4MiB each, max4096width/height, max512text draw segments per batch. A provider may transiently create one4MiB candidate before eviction; providers must obey the output bounds themselves. String keys are bounded to1024bytes. All copied provider bitmaps have explicit release callbacks. The UI frees CPU pixels immediately after uploading; unuploaded measure-only rasters are freed on eviction/close. All cached GPU textures are deleted on eviction/close. Unsupported/failed rasterization or exhausted current-frame cache space fails closed without fallback byte markers.

Non-ASCII quads are marked in the existing shared vertex array. end() submits atlas/solid prefixes and shaped-text segments in exact emission order, binding shaped texture only for its segment. No viewport is needed during measure/text calls. Current-frame used textures are pinned, so eviction cannot invalidate queued draws. The private segment list and counts reset on begin/end. Existing main GL state behavior is retained; shaped sampler uses texture unit3, active unit0 restored at end.

The main struct gains a private pointer, so rebuild all users with the staged header. The unmodified legacy snapshot and wrapper are test-only, not production files.

## Verification

build_and_run.cmd uses the installed VS18 BuildTools and existing ANGLE DLLs; no toolchain installation. Last build has no compiler warnings/errors.
- ASCII C/vertex/GLpixel identity to original, including source defaults and all95printable characters.
- é, decomposed e+combining acute, CJK中文, non-BMP U+1F600, Arabic whole-string sampling with exact cached measure/draw agreement.
- Composed/decomposed accent rasters bit-exact on this Windows font stack; input bytes are not normalized.
- Overlong UTF8, lone continuation, truncation, surrogate, out-of-range and old5byte encodings rejected.
- Exact later-solid-over-earlier-Unicode occlusion; later Unicode remains visible.
-64distinct current-frame strings pinned;16overflow strings safely skipped.
-100cross-frame evictions;170provider allocations/170releases;64GPU textures verified deleted at close.
-200independent GDI rasters leave GDI resource delta0.
- GL0 on NVIDIA RTX4080SUPER ANGLE D3D11/ES3.0. See renderer.txt/test-output.txt.
- unicode-samples.png, unicode-ordering.png, ascii-new.png and ascii-legacy.png are from actual offscreen GLreadback. unicode-samples.png was inspected: accented variants, Chinese, emoji and connected Arabic render visibly, rather than byte markers.

No live/shared source, assets, original game, saves or databases were changed. Root owns input/IME and live integration; this delivery does not claim either platform's name-entry integration is already complete.
