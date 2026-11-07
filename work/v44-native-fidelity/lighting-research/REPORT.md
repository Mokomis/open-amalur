# Active bridge lighting, native bloom and AO contracts

Read-only capture/artifact analysis, 2026-11-05. New files only in this research directory. No original game, live renderer, UI, database mutation, helper inference or installation. Canonical project instructions and REA skill read; existing exported evidence reused. Capture identity: `72c3524703435311542d555dc419771d820f6baf81c84676ef2c6dc28c367209`.

## Integration artifacts and verification

- `oa_native_bloom.c/.h`: independent GLES3 module, calls existing `oa_post_program`. Seven RGBA8 targets, exact active sequence. `oa_native_bloom_open(p,fullWidth,fullHeight)`, `oa_native_bloom_render(p,scene,exposureMinInverseRange)` returns quarter-size bloom texture; merge coefficient is applied separately. `close` releases resources. Both shaders and standalone deferred helper pass glslangValidator300ES; C compile result in validation.json. The module does not change existing core files.
- `native_deferred_combine.glsl`: concise algebraic translation of active fragment1895, proven by phase106/draw72932, not just a related shipped candidate.
- `native-1910.frag`: mechanical straight-line GLSL translation of ACTIVE AO fragment1910; native top-left coordinates, texture-fetch orientation, derivativeY and zero outside image adapters included. `native-1926.frag`: active bilateral filter similarly translated. Both compile with glslangValidator. The translator retains SPIR-V IDs per instruction and fails on unsupported operations. These are syntax-verified translations; no GPU equivalence or visual parity is claimed.
- `native_ao_shaders.h`: embeddable C strings for both translations. `ao-constants.json` and three raw128-byte buffers preserve reference parameters. `ao-vertices.bin` preserves the actual6fullscreen triangles from final memory129 FillMemory. These are not canned near/far guesses.
- `phase-contracts.json`, `resources-used.json`, shader modules/SPIR-V disassembly, raw uniform slices and manifest retain resource/stage/sampler/pipeline bindings. `inspect.py` reads existing JSONL/capture-index/memory52. `vertices.py` decompresses memory129 from existing recording; it does not acquire a new frame.

## Deferred combine: concrete correction

Native active pipeline7543, fragment1895, phase106/draw72932 samples normal+gloss(view157), albedo+specularStrength(view160), ambient+wrappedFlag(view163), localLight(view166), and AO+shadow(view181). Global buffer is memory52[360896:362272]. This active SPIR-V corroborates shipped `d2e799a101bdaddd.asm`, including the denominator epsilon that the old textual DXBC rounds to0.

Let d=N dot sunDir, A=AOshadow.r, H=AOshadow.g. For ordinary material: `lambert=saturate(d)`. If ambient.a>.5, `lambert=saturate(d+.5239999890327454)*.6561679840087891`.

```
front = min(lambert, 1 + shadowColor.a*(H-1))
backScale = A*backlightScale          // captured .11999999731779099
D = front + saturate(-d)*backScale
shadowAmbient = (1-front)*shadowColor.rgb
finalDiffuse = (shadowAmbient*albedo + ambientGBuffer)*A
             + (sunRGB*D + localLight.rgb)*albedo
```

Shadow uses **min**, not Lambert*shadow. Global SSAO must affect ambient/shadow, not the entire scene/direct/local light. Current custom whole-scene AO is therefore a wrong contract. Adding native AO means consuming it in material shading or native deferred combine, not restoring the old final-scene multiplier.

For incident camera-to-fragment I (use `-normalize(eye-W)`), R=reflect(I,N), exponent=storedGloss*.25. Front spec=`pow(max(saturate(dot(L,R)),.00001),exponent)*float(d>=0)`; back spec=`pow(max(saturate(-dot(L,R)),.00001),exponent)*backScale`. Sun spec=`frontSpec*D+backSpec`. Local specRGB=`localLight.a*localLight.rgb/(dot(localLight.rgb,(.2126,.7152,.0722))+1.0000000116860974e-7)`. Add `(sunRGB*sunSpec+localSpecRGB)*storedSpecStrength`. Existing independent point-light Blinn highlights are not this aggregated native light-buffer contract.

Native G-buffer quantizes material strength/gloss/ambient. Helper expects sampled native values; unquantized forward inputs and custom point-light attenuation remain differences. Native wrap is a G-buffer material flag; do not universally enable it for foliage without that producer's proof. Do not retune already matched sun/fog/sky globals.

## Native bloom: exact graph and kernel

Every target below is RGBA8_UNORM, with linear min/mag, nearest mip selection, clamp-to-edge sampler153. Every viewport covers the entire target with regular normalized UV and no half-texel override. Copy/downsample shaders1844 and1853 sample RGB once and output alpha0; extract1851 also outputs alpha0. Four weighted bilinear taps in1847 are used in instruction order `nearNegative,farNegative,nearPositive,farPositive`:

```
0.390625 * sample(uv - axis*.6000000238418579)
+0.109375 * sample(uv - axis*2.1428571939468384)
+0.390625 * sample(uv + axis*.6000000238418579)
+0.109375 * sample(uv + axis*2.1428571939468384)
```

Here axis is1/sourceWidth or1/sourceHeight; exact captured normalized offsets are in phase-contracts.json. Equivalent infinite-precision discrete weights are `[1,6,15,20,15,6,1]/64`, but the four captured linear taps preserve their original float operation pattern. Module uses these original four taps.

| Phases | Operation | Source -> destination |
| --- | --- | --- |
|118|one linear downsample|scene1536x864/view175 -> half768x432/view199|
|119|luminance extraction|half -> quarter384x216/view205|
|120..121|H then V blur|quarter205->208->205|
|122|one linear downsample|quarter205->eighth192x108/view211|
|123..124|H then V blur|eighth211->214->211|
|125|one linear downsample|eighth211->sixteenth96x54/view217|
|126..131|THREE H/V pairs|sixteenth217->220->217 repeated3|
|132|linear upsample ADD|sixteenth217 into preserved blurred eighth211|
|133|linear upsample ADD|reconstructed eighth211 into preserved blurred quarter205|

Upsampling pipeline7594 uses ONE+ONE ADD, attachments LOAD their existing blurred content. Reconstruction is additive across3scales, not replacement or an average. Saturation/quantization happens at EACH RGBA8 write. A constant low-intensity bloom field therefore approximately triples before final coefficient; the current one-scale floating Gaussian does not match this energy. Full-scene source must also match native RGBA8 clipping/quantization, otherwise module alone is still partial fidelity. Different renderer resolution scales targets and sample widths; it is not a new capture proof.

Native extract/merge already recovered in v43 follow-up remain unchanged: exposure.8277000188827515 only bloom branch, minLum.1738000065088272, inverseRange1.2103606462478638, finalMerge.4306860566139221. No authored cutoff.43 in active extractor.

## Native SSAO: depth-only reconstruction, no normals MRT needed

Phase94 draw66878/pipeline7514/fragment1910 reads D24_UNORM view169 full1536x864, writes RGBA8 view175. Uniform memory52offset642304/range128 (only first96bytes consumed). Native shader reconstructs position and derives the normal from its derivatives; it does not sample the G-buffer normal image. The active version is a9sample spiral, depth-only un-mipped fetch, cubic radius falloff, derivative correction, and nonlinear AO shaping. This is the SAO-family shader whose shipped textual candidate7ea3870161cf5d4e.asm agrees in instruction flow; active SPIR-V is the authoritative source. Mechanical GLSL is provided to avoid replacing that flow with a newly-designed approximation.

Captured reconstruction:

```
Z = -26.1875 / (hardwareDepth - 1.0000499486923218)
ray.xy = (-.7627148628234863,.42902708053588867)
       + (nativeTopLeftPixel.xy + .5)
         *(.0009931182721629739,-.0009931182721629739)
P = vec3(ray.xy,1)*Z
```

`hardwareDepth` is the sampled stored0..1 value. Do NOT convert it with2*d-1 before this equation. A GL projection already remapped from D3D0..1 to GL clip-1..1 writes the same hardwareDepth. If input is an NDC value rather than a sampled depth texture, convert that NDC to hardware0..1 first.

Constants: intensity8, aoClamp1.3999999762, bias2, epsilon.400000006; projScale302.0785217285; gameUnits1; depthThresholdRcp1/524288; fadeStart5800, visibleRangeRcp.004999999888; radius120, radiusSquared14400, radiusToSixth2985984000000, scale2.6791839146528273e-12. Some fields are inactive in this selected variant (intensity is not separately multiplied); use raw block and shader semantics, not every field name as an independent multiplier. The reference ray/projScale must be recomputed from the current projection and dimensions when the camera changes.

AO+packedDepth are written only for geometry hardwareDepth<.995685338973999. A second draw7518 outputs white on hardwareDepth>=that value. Both fullscreen triangles use native clipZ=.995685338974, no depth writes; compare GREATER and LESS_OR_EQUAL respectively. To reproduce this with screen-space GL passes, run the full shader derivative calculation, then apply equivalent near/far coverage using sampled depth or preserve matching depth test.

Phase95 draw66888 fragment1926 bilateral filters view175->178, c0axis=(.001953125,0), edgeSharpness35. Vertex colourRGBA bytesff000000 => (1,0,0,0), preserving centre packedDepth in yzw. Phase96 draw66898 filters view178->181, c0axis=(0,.003472222248), colour00ffffff => (0,1,1,1), writes yzw1 and leaves AO inR. Both also have the complementary far-depth flat-white draw. Bilateral weights centre.398943007; distance1 .541971028;2 .353991002;3 .304432005;4 .300134003; nonlinear depth-edge weight. DO NOT treat this as the bloom binomial kernel.

The translated bilateral fragment accepts `passthrough`: phase95(1,0,0,0), phase96(0,1,1,1). Both use full-size nativeExtent, source linear? See sampler145 in resources: native bilateral uses nearest/clamp sampler145 (verified binding16). Axis steps are3pixels. The fragment accepts uniform `c[8]`, set all32floats from relevant128-byte block; only c0 is consumed by bilateral shader.

AO output final view181 is later reused as AO(R)+shadow(G). Shadow passes100/102/104 update its shadow channel; direct shadow filtering is separate work. Thus a standalone custom AO texture should supply AO independently while keeping its existing shadow texture path explicit. SSAO can now be implemented from a depth-only prepass, but native raster coverage, geometric depth, projection and shadow producer parity still need implementation/runtime checking.

## Colour-space audit

Main captured phase97 material799draws overwhelmingly sample BC1_RGBA_UNORM/BC3_UNORM maps. Phase98 four vegetation draws use BC1_RGBA_UNORM diffuse/norm/spec. Terrain's first active shader791/792 samples UNORM maps33..40. The only11sRGB occurrences in phase97 all use binding36/view3412, a4x4BC1_RGBA_SRGB texture, in fragments592 and844. A global change of all diffuse maps to sRGB is unsupported by this evidence. Exact file identity of that exceptional4x4map remains unresolved; do not assume it is ordinary diffuse. `srgb-main-draws.json` preserves all occurrences.

## Remaining boundaries

The native final module1860 is an antialias/filter stage with branching and luminance-alpha input; current plain LUT output differs. Full native sky mapping, exact directional shadow filter and dynamic local-light buffer construction remain unresolved here. Provided lighting/bloom/AO evidence is concrete and actionable, but source changes/GPU compilation/render comparisons belong to root integration. No visual parity or game playability is claimed.

## Integration follow-up: full-size AO wrapper and dynamic projection

`oa_native_ao.c/.h` now owns three nearest/clamp RGBA8 targets at the current full scene extent and the two active shader programs. APIs: `open(p,w,h)`, `render(p,depth,glVP)`, `render_constants(p,depth,c[32],hardwareDepthCut)`, `close(p)`. OutputR is AO and yzw1. It gates far/sky pixels AFTER all derivative calculations, equivalent to the native complementary white coverage without attaching the sampled depth texture as a framebuffer attachment. Current colour mask must permitRGBA writes. It leaves ordinary post rendering state/bindings changed; root owns rebinding scene state. It never changes or owns the input depth image. AO upload count is6float4 for activeAO and1float4 for bilateral, matching actual consumed array extents.

`oa_native_ao_math.h` derives current projection constants from a column-majorGL VP (or pureGL projection matrix), correctly decomposes asymmetric/frustum centre offsets, and rejects orthographic/degenerate/skew projection. DepthA andB are derived after GL clip[-1,1] to hardware[0,1] mapping; physical fade6000 and radius120 are retained. Native builder `FUN_00c982f0` sets config+0x40 radiusScale from `DAT_0196622c=.30000001192092896`; `FUN_00c74280` packs field6 as `height/(2*tan(FOV*.5))*radiusScale`. The shared mathhelper reconstructs that projection factor from current matrix rows; it agrees with captured302.0785217285 within1.1ppm because the original FOV and rounded combined matrix are not bit-identical representations. Dynamic wrapper uses this source-backed equation, not a silent reference constant. For an exact fixed reference, caller can explicitly upload the captured128-byte block and .995685338974 via `render_constants`.

Pure projection input is preferable when available: recoveringB by subtracting terms in a world-translated float VP can lose precision already absent from that VP. Double arithmetic reduces additional cancellation but cannot recover lost source bits. `ao-validation.json` records translated/rotated/asymmetric camera checks at3resolutions and orthographic rejection. Gated shaders passGLSL300ES syntax checks; WindowsC compile and header consumption are recorded separately. No renderer was launched.

## Follow-up wrap and exceptional sRGB semantics

Plain-dot3 shipped ba5e's output ambient.a reads **cb4[15].w**, not globalcb1+252. CB4 is `g_dynamicbuffer`, whose header explicitly calls offset252 `luminanceShiftId`. In all799phase97 G-buffer draws, actual dynamic binding4/68 plus252 is .1875(701draws), .0625(68), or .4375(30); all are below the active deferred-combine wrapped threshold .5. All4phase98vegetation dynamic blocks also contain .1875 (their pixel alpha producers still need their family proof). For the measured bridge dot3 instances, no wrapped diffuse is supported. Globalbuffer+252 is unrelated windPalette.w and must not be substituted. `dynamic-wrap-fields.json` preserves every original draw, stage modules, binding and offset.

The11sRGB4x4map occurrences are also resolved by active use: PS592's binding36 sample%206.green times materialc[1].x supplies GBufferAlbedoSpec.alpha. PS844's binding36 sample%195.green times materialc[1].x, then vertexalpha, supplies the same alpha. Their ordinary diffuse samples are binding33UNORM. Therefore this exceptional map is a **specular map**, not diffuse and not a cube. Shipped resource nomenclature consistent with this contract is `g_specular...SpecularMap` t4; exact authored shader-name-to-module association remains unproven.


## Native AO builder proof

`FUN_00c982f0.c`, `FUN_00c74280.c`, `ao-builder-globals.json` preserve read-only export/body and executabledata provenance. Configuration globals:01966214bias2,01966218aoClamp1.4,0196621cfadeRange200,01966220farAO6000,01966224epsilon.4,01966228intensity8,0196622cradiusScale.3,01966230radius120,01966238edgeSharpness35,0196623cblurScale3. Builder fills uniformfields0..31; field6 screenradius factor uses halfFOVtan, then configradiusScale. FUN_011bf5a0's fallback `FUN_011bf5f8` explicitly calls x87fptan; FUN_011c44f0 fallback uses fpatan in cameraaspect conversion. Decoder avoids treating the adjacentfloatvalues asfloat64constants; the JSON retains raw8bytes and both interpretations for datareview. Root should use f32 for configglobals, f64 for mathematical1/.5/2constants. Native builder uses the configuredFOV field before floatmatrixrounding, so fixed-reference rawconstants remain the exact consumption.
