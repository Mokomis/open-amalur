# Bridge tree provenance and capture residency audit

## Three-pixel cause classification

The follow-up now establishes two distinct problems. `canopy-3pixel-classification.json` links the witnesses below to full native/current ray reports. Native rays cover189 captured tree draws with exact source VB/IB hashes and captured per-draw world matrices; leaf deformation uses the captured palette. Coverage samples use the already proven captured-exact alpha chains, GREEN, and native cutoffs. Current rays use the finest-cutout diagnostic's normal opaque streaming LODs; a second pass uses existingLOD0 for all current geometry. No GPU or scene mutation was used.

| Pixel | Original native coverage | Current coverage | Classification |
|---|---|---|---|
|(500,35)|barkblend draw69284, FAB343974 assembly8, MID353286, distance14790.718cm; covered leaf draw68987 behind at15235cm|no covered world hit, including all-geometryLOD0|native-only coverage / unresolved native pose producer|
|(800,150)|leaf draw68811, FAB340232 assembly4, MID359202, raw GREEN0.446777, distance11818.04988cm|legacyMID0/family0, cell(-1,-13), GREEN/baked alpha0.423872, distance11818.05457cm|same leaf geometry and coverage, different shader attributes|
|(980,210)|leaf draw68805, FAB363221 assembly0, MID359202, GREEN0.618788|legacyMID0/family0, cell(-2,-13), alpha0.693311|both covered; legacy shader plus small source pivot placement difference|

At(800,150), UVs differ by less than0.000003 and world hits by0.00469cm. The legacy interpolated normal is `(-0.02594,-0.06936,0.99725)`; native main-leaf radial normal is `(-0.84764,-0.53057,0)`. This is direct pixel evidence for expanding source-proven native leaf attributes beyond the18 scoped cells. Both masks pass, so a missing leaf or alpha cutoff cannot explain this point's large visual difference.

At(980,210), the legacy interpolated normal is `(0.20036,-0.07053,-0.97718)` versus native radial `(0.94896,0.31540,0)`. Source scale is `(1.3640872,1.3640872,1)`. The current source producer scales around the serialized sphere center; its basis matches the native matrix within5.32e-8, but it adds translation `(-26.51579,9.87018,0)`cm relative to native. This accounts for the18.013cm ray-hit separation and small UV difference; preserve this as a separate placement correction from attribute propagation.

The missing coverage at(500,35) uses the native FAB343974 pose `(-880.26703,-76023.85938,5371.81641)`, not the offscreen343974 pose discussed below. Its first covered tree triangle hits world `(-668.18094,-76210.51402,10577.45673)`, with BACK culling and positive front-facing determinant. Native leaf cover68987 behind also passes GREEN alpha. The nearest cached tree origin of any FAB is1374.912cm away (FAB357911); no exact cached source-space translation was found. The all-current-geometryLOD0 ray remains uncovered, separating this gap from clustering policy.

Across all51 unmatched native translation poses, nearest cached tree origins of any FAB range from255.619cm to5729.095cm (median2264.122cm); none is within100cm. This rules out merely choosing the wrong FAB label at the same cached origin. It does not identify the missing producer/hierarchy. The single native-only ray supplies independent geometric evidence of a real reference-frame coverage gap.

The requested raw-translation follow-up is in `raw-render-translation-vs-native-audit.json`. All4489 raw84-byte records independently re-decode translation at+16, quaternion at+32 and scale at+48; rebuilt conjugate-quaternion/scale bases match the stored linear matrices within1e-10. Same FAB/proven geometry aliases, basis error<0.001 and raw translation distance<0.01cm match92/189 draws, with **zero new matches among the97 draws/51 unresolved poses**. The known sphere-pivot bug is real but does not explain this set. For the native500,35 tree, the nearest same-FAB raw origin is10453.895cm away and there is no compatible-basis candidate. For the980,210 leaf, raw origin matches exactly and the ported matrix shifts by28.293cm, confirming that the audit separates these cases.

To remove the tree/emitter filter as an explanation, `all-raw-render-record-nearest-translation-audit.json` searches all460887 raw84-byte render records in arrays0x150/0x160/0x170/0x180 across all170 cached `.space_bxml` files, with no FAB-name, material or emission filter. None of the51 native origins is within100cm of any raw record; the minimum remains255.619cm. Native500,35 has a nearest arbitrary raw record1045.987cm away. Cross-archive record copies are included, so this is a bounded cached-source search rather than a count of unique world instances. Parent/local hierarchy composition and other native producers remain unresolved.

Original non-tree occluders and final postprocessing are not replayed. Native tree cull/header state is used; isotropic bilinear/trilinear sampling approximates implicit derivatives. These are three bounded point witnesses, not complete pixel coverage or whole-zone duplication claims.

This audit does not establish duplicate foreground tree instances or missing authored leaf geometry as the cause of the canopy gap. Authored detail-group selection differs at matching physical tree poses, but all16 compared visible leaf assemblies are geometrically equivalent after vertex permutation. Four staged textures reproduce exact captured residency; root's subsequent decoded comparison shows that their alpha coverage is unchanged from matching old mip levels.

## Follow-up review: causes ruled out in the matched set

`detail-group-camera-coverage-inventory.json` projects all22 differing or mixed group cases through the actual reference VP, clipping triangle polygons to the frustum. The14 cases with visible leaf parts have identical original/custom conservative leaf triangle counts. `all-visible-leaf-authored-group-equivalence.json` then compares16 native/current leaf assemblies: every UV pair, normal and RGBA value matches bit-for-bit after vertex permutation; triangle vertex sets match exactly. Positions match exactly in14 comparisons. The two419041 comparisons differ only by the0.429cm shift detailed below. This rules out a large authored-leaf geometry deficit within this matched set. Body/trunk detail still differs.

The mixed343974 pose is entirely outside the actual frame: all13 assemblies have zero frustum triangles, and even native bark0 has maxNDCx=-1.0713. Native69208 was conservatively submitted, but this pose cannot explain a prominent canopy in this frame. `large-tree-343974-prototype-contract.json` preserves group1 materials/geometry and this explicit limit; do not select it as a visual canopy experiment.

Root's `work/v45-foliage-coverage/capture-leaf-texture-delta.json` compares the staged resident chains to equal-size levels of the old high-resolution maps. Sapling alpha680 and normal684 decode exactly equal to old mip2; alpha has zero coverage disagreement. Diffuse683 has small localized RGB differences (mean absolute about0.279/0.222/0.302, maxima33/21/25), and diffuse682 mean difference is about0.48. The stage remains an exact residency/memory correction, but it is not evidence for a large mask-density change.

`typed-reference-high-nibble-audit.json` covers all55 mapped poses:95 source parts have top nibble15,12 have4. Both tags occur among native-matching and differing assemblies. All four mixed343974 parts, including extra7, carry15. No nibble-only proxy exclusion is supported. Native IO function00a95c80 ORs plain asset IDs with0xf0000000 before streaming, while00cf6710/00cf68d0 mask resource-cache keys to28bits; this supports a resource-tag interpretation but does not recover the actual space render-channel consumer. Do not add a filter based on this audit.

## Ready stage

`capture-exact-leaf-stage-manifest.json` verifies all seven native leaf maps against the images actually bound in the original bridge capture. Every compressed source mip byte matches the captured image after removing only the recorded allocation padding. Decode checks use an independent scalar BC1/BC3 sampler; complete serialized OATX payloads are reparsed and compared.

| Texture | Original captured image | Exact authored source | Dimensions / mips | Stage |
|---|---:|---|---|---|
|678|4647|initial/1451347.dds|64² / 5|unchanged verified|
|679|13908|DATA/343436_1.dds|2048² / 9|unchanged verified|
|680|14150|DATA/477449_3.dds|512² / 8|same-ID replacement|
|681|13901|DATA/343437_1.dds|2048² / 9|unchanged verified|
|682|14145|DATA/457709_3.dds|512² / 8|same-ID replacement|
|683|5267|DATA/566740_0.dds, identical _4|256² / 7|same-ID replacement|
|684|14155|DATA/457710_3.dds|512² / 8|same-ID replacement|

The independently authored quality files are not byte-identical tails of `_1.dds`. The previous full-resolution stages preserved valid authored chains but did not reproduce the resident quality in this capture for the two sapling diffuse maps, shared sapling alpha, or shared sapling normal. No material-table, count, legacy global texture, gamma, resize, generated-mip, or channel-merge changes are required. Stage files remain private; root owns review, integration, and GPU comparison. Normal-view dynamic texture residency remains a separate policy.

All 82 original phase-97 leaf draws using VS877 were correlated through descriptor-set updates and bindings: 71 use main material controls and image13901, seven sapling controls/image14145, and four green-sapling controls/image5267. Color diffuse is binding33 and normal binding35. Matching native vertex-buffer plus exact object-world-matrix keys also correlate 132 submitted depth/shadow draws to alpha image13908 (main) or14150 (both saplings). Raw GREEN coverage and the existing100/255 or128/255 cutoffs remain unchanged. Native leaf sampler149 is repeat/trilinear/linear/bias0 with anisotropy disabled.

## Foreground right tree

Exact physical pose: `(4757.779296875, -86588.828125, 5833.80712890625)`, FAB419041 `for_flora_twist01`. Its native world matrix and the custom source pose agree. Native camera distance is about3916cm, just inside the first4000cm authored threshold.

| Part | Original captured geometry | Custom cached source | Material preserved |
|---|---|---|---:|
|leaves|assembly0 or identical7, draw69083,60tri|assembly8,60tri|559590|
|trunk|assembly1, draw69104,320tri|assembly5,114tri|343549|
|branches|assembly2, draw69155,29tri|assembly6,17tri|489469|

`right-tree-prototype-contract.json` includes complete original84-byte render-record hex, exact pose, source references620/621/622 and render indices7/680/691, selected source buffer hashes/paths, and native draw witnesses. A conservative geometry experiment may use assemblies0/1/2 with the current native materials and all established vertex/alpha/wind contracts.

The leaf equivalence check is essential: assembly8 vertex `i XOR1` corresponds to native assembly0 vertex `i`. All120 UV pairs, normal short4 values, and RGBA bytes match bit-for-bit. Tangent differs at two vertices and binormal at one, each by only one SNORM16 unit. Positions differ by about0.429cmY; X differs at two vertices by at most0.0000305cm, Z is exact. Per-card indices `[0,1,2;1,0,3]` become the same two triangles with their submission order exchanged; winding remains the same.54/120 wind phase indices differ because native phase uses local position. See `right-tree-leaf-all-attributes-comparison.json`.

An earlier association of this draw with main material359202 was incorrect and is explicitly withdrawn. Captured draw69083 binding0 at memory52+1199424 contains `(.97812003,600,0,0;0,10)`. More decisively, its bound diffuse image5267 matches every mip of source566740_0/_4, proving the green-sapling diffuse used by559590. Do not replace this instance material with FAB-default419060 or main359202.

## Authored group selection

`authored-fab-groups.json` decodes all27 cached tree FAB metadata files, including source SHA and byte offsets. Native deserialization is `BHG_FabRender__vf5@00d400d0` → element array `00d196c0` and nine group records `00cccc50`. Elements have runtime stride0x5c, material at+0x38 and distance limits at+0x18/+0x1c. Groups have runtime stride0x20: element count+0, byte-index list+4, second count+0xc/list+0x10, threshold+0x18, flag+0x1c. `00ccd0b0` inspects nonempty groups1..4 and marks their last group's elements; `00cae870` resolves element material through `00a70b80`. No runtime metric policy is inferred solely from these loaders.

For419041:

| Group | Elements | Threshold |
|---|---|---:|
|1|0,1,2|4000|
|2|3,4,7|9000|
|3|5,6,8|15000|
|4|5,6,8|10000000|

Element distance limits independently confirm0/1/2=(0,4000),3/4/7=(4000,9000),5/6/8=(9000,10000000). These are authored detail groups, not labels inferred from triangle counts. `outputs/{DATA,initial,patch}-archive-list.txt` places the four highlighted FAB metadata files only in DATA; no initial/patch metadata override was found. Stream geometry still follows existing patch-first lookup, recorded per assembly.

The responsible custom producer is `work/v20-char/build_zone.py`: it chooses the cached space record's material/assembly words directly at offsets64/68, then emits that full assembly. References0x1b0 pair to centers0x1a8 and render records0x160 by rounded sphere center; placed records0x148 pair to0x150, and the two extra groups are0x138/0x170 and0x140/0x180. There is no authored FAB group selection. `build_world_pack.py` subsequently adds global400/1600cm clustering; forcing its finest geometry cannot restore parts that `build_zone.py` selected from another authored group.

`captured-pose-group-mapping.json` contains55 matched physical poses spanning92 captured tree-part draws, using exact native VB/IB hashes and world-matrix agreement.21 have disjoint known native versus custom authored group candidates. Examples:340232 customgroup3 vs native1 or2;353290 custom3 vs native2 at four matched poses;419058 custom3/4 vs native2 at four poses. Ambiguous aliases remain explicit candidate sets, never forced labels.

There is also a mixed-group source case: FAB343974 at `(8675.91796875,-80072.015625,6627.07666015625)` emits assemblies3,5,7,12. Group3 is3,5,12 and group4 is6,7. Native matched draw69208 uses assembly0, supported only by group1. This is a possible source of an extra visible model part at one physical pose, not proof of an extra placed tree.

## Placement counts and limits

The source audit found5203 cached tree records:4489 admitted nonshadow parts and714 skipped shadow proxies. Of the emitted parts,690 sphere-frustum candidates represent335 physical FAB/pose groups;44 candidates have no triangle intersecting the conservative clip test. These are not occlusion-tested visible-tree counts.

The original GBuffer contains189 tree-part draws with exact cached tree-geometry hashes, spanning106 unique physical translation poses.55 poses match the source audit as above. The remaining97draws represent51 poses with no exact translation triplet in the cached `.space_bxml` sources searched. Their producer/hierarchy provenance is unresolved. The coverage of this source catalogue is bounded, and the two counts must not be subtracted to claim extra or missing world trees.

Three exact duplicate source assembly/pose groups all belong to one background FAB419059 tree at `(-20193.27734375,-59437.36328125,7286.44384765625)`, around38–39kcm from the camera. Its trunk80tri, branch28tri and leaf168tri records are each repeated twice. The rounded-center collisions choose byte-identical records; they do not collapse distinct near/mid/far records. No matching native pose witness was found for this tree, so this does not establish engine-side duplication or explain the prominent foreground canopy.

## Root evidence review

1. Keep the four capture-exact textures as the source-backed residency correction. Root's equal-size decode comparison rules out their alpha as the large canopy-density cause.
2. Treat the21 authored group mismatches as body/trunk detail corrections. All16 compared visible leaf assemblies are equivalent; do not promise canopy restoration from a leaf group swap. Preserve per-instance material overrides, UV, native TBN/leaf wind attributes, raw GREEN alpha, cutoffs and cull state.
3. Do not filter typed-reference nibbles without the actual native consumer. The mixed343974 instance is outside this camera.
4. Expand native leaf attributes through source joins for the visible legacy cells: the same-leaf(800,150) witness directly confirms the missing radial normal contract. Preserve existing geometry while correcting attributes.
5. Investigate the51 unmatched native pose producers, beginning with covered343974/69284 and leafcover68987 at(500,35). This native-only coverage persists with finest current geometry. Keep the small sphere-pivot placement mismatch separate. No global duplicate-instance, complete original model-LOD, or visual parity claim follows from this read-only audit.

All outputs were written only beneath this new instance-audit directory and its private Mac mirror. Existing source, packers, core renderer, live assets, original databases, previews, GPU and UI were untouched.
