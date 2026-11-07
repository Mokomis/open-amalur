# Exact captured bridge post-processing constants

2026-11-05 bounded follow-up. Read-only analysis of existing full frame recording and existing decoder outputs. Only this new post-followup directory was written. No original game/UI execution, core source edits or installations.

## Actionable result

Use the native luminance-based bright extraction below for the measured reference. The captured final bloom merge coefficient is **0.4306860566139221**, not the authored bloom_strength0.6298 or older Odarath coefficient0.5376. Exposure **0.8277000188827515 belongs in bloom extraction only**: do not multiply the main scene by it again in the final merge.

These are the original bridge frame's consumed bytes and active shader instructions. Current authored Gaussian blur/downsample and AO still differ from the original pipeline. Replacing extraction and merge constants provides scoped fidelity improvements, not complete post-processing parity or a general time-of-day adaptation implementation.

## Source identity and byte verification

Full payload was already available on the Mac in `2026-11-05/open-amalur-native-camera/memory-52.bin` (33554432bytes), produced by existing `oa-extract-uniforms.py` from `capture-index.json`. The prefix alone ended at1764816, just before the useful bloom/post range. Earlier zero post candidates were pre-trim recorded command definitions, not the active frame's final draw offsets.

`extract_post.py` reused the existing source recipe, sought precisely to the final memory52 FillMemory payload, decoded its LZ4 bytes once, compared all32MiB byte-for-byte with the saved full memory image, and wrote only the required small slices. Comparison passed. Recording SHA256 matches the validated original frame:
`72c3524703435311542d555dc419771d820f6baf81c84676ef2c6dc28c367209`.

FillMemory block73631, payload file offset525920194, stored10516740bytes, metadata36bytes, decompressed33554432bytes. `post-constants.json` includes hashes, exact records and raw float arrays. This CPU memory fill follows recorded command definitions before their GPU submission; the descriptors below select its effective ranges for the active phase.

| Function | Active draw index / phase | Pipeline / PS module | Memory52 offset | Bytes |
| --- | --- | --- | ---: | ---: |
| Bright extraction |73280 /119|7584 /1851|1764928|16|
| Colour-table generation |73395 /134|7599 /1855|1765632|64|
| Scene/bloom/effects merge and colour table |73404 /135|7603 /1858|1765696|48|
| Final output filter |73411 /136|7607 /1860|1765760|48|

`active-bindings.json` records exact descriptor writes/binds and sampled image formats/extents. `pipelines.json` links each pipeline to its actual captured SPIR-V stage modules. The raw .spv and `spirv-dis` output are preserved alongside the buffer slices. This avoids assuming an unrelated shipped shader hash was the active variant.

## Bright extraction: exact equation

Fragment module1851 uses the16-byte buffer at1764928, binding0:

```glsl
// Captured values: exposure, minimum luminance, reciprocal luminance range.
vec3 x = texture(source, uv).rgb * 0.8277000188827515;
float L = max(dot(x, vec3(0.2126, 0.7152, 0.0722)),
              0.1738000065088272);
float factor = clamp((L - 0.1738000065088272) *
                     1.2103606462478638, 0.0, 1.0) / L;
vec3 bright = x * factor;
// Native output alpha is zero.
```

The denominator uses the clamped luminanceL, not raw source luminance. It is safe for this measured scene because minLum is positive. Reciprocal range equals approximately1/(1-.1738), consistent with authored maxLum1. The measured constants should be retained rather than recomputed at lower precision.

The source at descriptor binding32/view199 is **768x432 R8G8B8A8_UNORM**, an ordinary downsampled scene. Exposure is applied by this shader to its bloom extraction sample. Its output then enters the original multiscale downsample/blur/reconstruction chain. There is no evidence to multiply base scene RGB by exposure in the final pass. The current custom `maxRGB`/`smoothstep(.43,.68,...)` extraction is a different operation; authored cutoff.43 is not consumed by this active native extractor.

## Merge: exact input contracts and equation

Active pipeline7603, fragment module1858, binding0/48bytes at1765696 contains:

```text
rawUVadjust      = (.05859375, .9375, .001953125, .03125)
transitionAmounts= (0, 0, 16, .0625)
bloomStrength    = .4306860566139221
padding          = (0,0,0)
```

Active images:

| Binding | Role established by shader use | Image view | Format / dimensions |
| --- | --- | ---: | --- |
|32|Correction-table atlas|1864|UNORM256x16|
|33|Base scene|175|UNORM1536x864|
|34|Effects/composite layer|178|UNORM1536x864|
|35|Reconstructed bloom|205|UNORM384x216|

Module1858's operations before table lookup are exactly:

```glsl
vec3 bloom = texture(bloomSource, uv).rgb * 0.4306860566139221;
vec4 effect = texture(effectSource, uv);
vec3 scene = texture(sceneSource, uv).rgb;
vec3 c = clamp(bloom + effect.rgb * effect.a +
               scene * (1.0 - effect.a), 0.0, 1.0);
// Then sample the generated correction-table atlas with native interpolation.
```

Thus with an absent/transparent effects layer (`effect.a=0`) the native pre-table expression is `clamp(scene + bloomTexture*.4306860566,0,1)`. Exposure has already affected the **bloom branch**. It has not been applied a second time to the scene. Bloom is added independently of the effects alpha. If the custom path already composites FX into its scene texture, do not add that FX layer a second time.

The native atlas has16 blue slices arranged across256x16; rawUVadjust mapsred to one16-wide slice while green/blue use half-texel(.9375,.03125). The atlas sample implements blue-slice interpolation; this is consistent with a16^3 table sampled at `c*.9375+.03125` when the table content is equivalent. This pass computes output alpha as luminance dot(.299,.587,.114), while RGB is table output. Final module1860 filters already-corrected RGB; it is not another exposure or tone-map stage.

At phase134 the table-generation inputs are16^3 **sRGB** image views, and the generated atlas isUNORM. `lut-generator.bin` preserves the64-byte generation constants, with neutral-looking weights/gamma terms. This pass has not fully interpreted every generator field; the existing sRGB table-decode implementation should not be altered merely to match unrelated bytes.

## Minimal useful shared change and limits

1. Replace custom bright extraction with the exact luminance formula and measured exposure/minimum/reciprocal-range uniforms.
2. Drive final bloom merge with measured.4306860566 for this bridge reference, while keeping base scene exposure unchanged. Preserve current FX compositing ownership.
3. Keep unsupported blur/downsample/AO behaviour explicitly described as partial. The native bloom branch usesUNORM targets and a multiscale chain; current float quarter-resolution extraction plus authored Gaussian blur differs. The coefficient is exact for the original reconstructed bloom input, so changing it alone is not proof that the custom bloom's total energy matches.

These captured settings are a reference-frame contract. Their runtime adaptation/time-key derivation was not recovered here. Do not claim.4306860566 is a universal region constant or that authored.6298 is corrupt. It is simply not the consumed final coefficient for this frame.

No missing payload blocker remains for this question. The useful span was memory52[1764928,1765808), available in the full recording. Report questions on exact bridge extraction, exposure placement, merge coefficient and LUT input contract are answered; native multiscale filter reproduction and adaptation producer remain separate work.
