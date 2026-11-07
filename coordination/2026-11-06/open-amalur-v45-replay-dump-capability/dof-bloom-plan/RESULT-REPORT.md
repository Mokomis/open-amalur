# Native DOF and bloom: bounded replay evidence

The reviewed9-event command ran once and succeeded first attempt, exit0 in2.391seconds. Output:18files,14,947,572bytes, below32MiB. No game/Steam launch, reference-app closure, extra replays or core edits. All outputs preserve raw native RGBA8 and top-left row order; orientation was established against the prior historical original screenshot.

## Exact native DOF-effect output

|Full-resolution pixel|NativeRGBA8|Parent currentRGBA8|Current minusnative|
|---|---|---|---|
|[800, 150]|[40, 37, 23, 29]|[73, 69, 43, 91]|[33, 32, 20, 62]|
|[980, 210]|[80, 80, 43, 94]|[74, 69, 37, 97]|[-6, -11, -6, 3]|
|[500, 35]|[64, 61, 37, 43]|[109, 125, 145, 178]|[45, 64, 108, 135]|

## Consumer-UV lower-resolution samples

Ideal native UV is(x+.5,y+.5)/(1536,864). Bilinear source coordinate is UV*sourceExtent−.5. The JSON records all four texels and exact rational interpolation weights; these values are U8-equivalent floats, normalized by255 for shader units.

|Pixel|Half-fuzz73253 RGBA bilinear|Final-quarter-bloom73386 RGBA bilinear|Final bloom nearest|
|---|---|---|---|
|[800, 150]|[29.25, 6.25, 29.25, 29.25]|[9.09375, 8.171875, 3.546875, 0.0]|[10, 9, 4, 0]|
|[980, 210]|[94.5, 8.0, 94.5, 94.5]|[87.5, 86.453125, 52.875, 0.0]|[87, 86, 53, 0]|
|[500, 35]|[43.25, 6.0, 43.25, 43.25]|[28.359375, 25.75, 14.890625, 0.0]|[27, 25, 14, 0]|

Parent current bloom800 nearest is(31,30,18); native nearest is(10,9,4). The separately reported native bilinear value(9.09375,8.171875,3.546875) must not be compared as if it were the nearest texel.

## Recovered native depth sampling contract

Captured DOF73253 binds VB128/memory129/offset79128/stride8. It draws six vertices: (-1,+1),(+1,+1),(+1,-1),(-1,+1),(+1,-1),(-1,-1). VS1838 copiesxy into clip(z0,w1), exportsUV=xy*(.5,-.5)+(.5,.5), and contains no halftexel offset. Viewport is(0,432,768,-432). PS1841 uses a normalizedUV NEAREST texture sample through sampler145, rather than integer texelFetch.

At idealhalf-pixel centers, the full-depth sampling point lands exactly on nearest-texel boundaries. Native interpolation/rasterization rounding is therefore material at leaf edges. The captured actualhalf-alpha contributors for800 are51,34,51,18, with weights1/16,3/16,3/16,9/16, producing29.25 before full effectU8 quantization to29.

Full native depth at even-coordinate candidates(798,148),(800,148),(798,150),(800,150) is u24=(16746596,16743341,16746599,16739520). Linear-depth values using captured inverse constants are(13966.465,12657.273,13967.918,11401.922); captured CoC equation gives U8(51,34,51,18). Across12contributors, even-depth candidates reproduce11actualalpha bytes exactly and the last within1LSB.

Forced-odd candidates(799,149),(801,149),(799,151),(801,151) predictU8(166,34,35,24) and bilinear36.8125, not captured29.25. This proves forcedinteger selection differs from the native point-sample contract. It does not establish an authored halftexel bias. It also cannot alone explain the parent currentalpha91: the custom neighboring depth field must be compared with native values. The complete rawdepths, formula, CoCs, neighboring candidates and sourcequad contract are saved in JSON.

Captured CoC: linear=1/(inv.x*D+inv.y); scaled=linear/524288; alpha=clamp((scaled−.01902448944747448)*26.213088989257812,0,.699999988079071). Native inverse=(-.03818615898489952,.03818806633353233). Raw posttransparent depth from already-dumped73214 is used; no additional depth replay was required.

## Bloom contract audit

Native73271 reads image173/view175, the scene after transparents, not DOFeffect image176. It overwrites half-image197.73280 extracts from197. Upsample draws73377/73386 useONE/ONE additive color+alpha withLOAD/STORE of previously blurred levels. Native sampler153 isLINEAR/LINEAR clamp. These match the current authoritative oa_native_bloom.c pass ordering/state.

Current live post.bin parameters exactly match captured values: exposure.8277000188827515, threshold.1738000065088272, inverseRange1.2103606462478638, finalbloomMerge.4306860566139221. Module blur weights.390625/.109375 and offsets.60000002384/2.14285719395 match the recovered native contract. No demonstrated bloom equation/state mismatch was found in this bounded check.

Because native bloom reads pre-DOF scene, the bloom difference is independent of whether the final DOF blend is applied later. A wide-neighborhood common-input comparison is needed before claiming a remaining bloom-shader defect or changing parameters. No visual tuning was performed.

Artifacts: analysis/native-dof-bloom-pixel-samples.json; analysis/previews/; analysis/dof-bloom-contact-sheet.png; native-depth-CoC-contributors.json; native-quad-contract.json; replay-result.json(inventory+hashes); replay.log.
