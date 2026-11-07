# Native static assembly distance and frustum contract

This report resolves the actual renderer metric from cached native code. It does not infer thresholds from pixel appearance or force source-instance exceptions. Only NEW research files were written.

## Exact predicate

The main static four-group descriptor path is:

`BHG_RsSceneRenderController::vf4@00d32b10 →00d28a80 →00ce93e0 →00cd5490/00cd5550 →00c98fe0 (scalar) /00c43e90 (SIMD)`.

Each descriptor is72B: ownerTag0,SpaceID4, four16B groups8..71. Each group supplies count and source80B bounds pointer. Both scalar/SIMD predicates implement the same distance formula:

```
if ((bounds.flags & passMask) != 0) reject;
q = DAT_019661f6 ? DAT_019662d8 : 1.0f;
d = bounds.distanceAnchorXYZ - actualCullCameraXYZ;
metricSquared = (d.x*d.x + d.y*d.y + d.z*d.z) / q;
if (!(bounds.minSquared <= metricSquared && metricSquared < bounds.maxSquared)) reject;
for each plane (n,offset):
    if (dot(n,OBBcenter)+offset
        +abs(dot(n,OBBaxis0))+abs(dot(n,OBBaxis1))+abs(dot(n,OBBaxis2)) < 0) reject;
accept;
```

Source80B offsets are exact:

| offset | field |
| --- | --- |
|0|OBB center XYZ|
|12,24,36|three world OBB half-axis vectors|
|48/0x30|distance anchor XYZ|
|60|separate word, not used in this predicate|
|64/0x40|minimum squared distance, inclusive|
|68/0x44|maximum squared distance, exclusive|
|72/0x48|pass flags|
|76|source/rank word, not used here|

Source-distance-anchors.json proves distanceAnchor equals raw authored placement translation, bit-for-bit, for source198,451,478. The render84 bounding sphere center is NOT the distance anchor. Neither view depth, XY-only distance, radius subtraction nor projected size appears in this predicate. OBB support is a separate conservative plane test.

The main d32b10 call passes mask0x308 into d28a80. Both source flag7 and23 pass that mask. Quality scale is a divisor of squared distance, not a linear divisor: q4 means effectiveDistance=rawEuclideanDistance*.5.

## Quality provenance

The shipped v30 native PE initialized byte VA019661f6 to1 and float VA019662d8 to4.0. Constant VA013be4a0 is1.0. These are raw binary values, not a fitted quality assumption. quality-binary-xrefs.json preserves section mapping and all exact-VA immediate references: flag has3 reads, scale has2 reads; no direct write or pointer-table address reference was found. Packed/base-relative writes are not excluded by that search alone.

Parent subsequently reported read-only RPM against the already-running paused bridge scene confirming flag1 and scale4. This corroborates binary defaults; the raw RPM file path should be linked alongside this report when preserved by the parent. Preferred-image VA addresses must be relocated by `actualModuleBase-0x400000` (parent reported actual base0x7b0000).

Per-element PVS candidate lists are used by00cd5550 ONLY when DAT019fdfd9!=0 AND DAT019661f6==0. With the confirmed flag1, that function falls back to00cd5490 and evaluates all bounds in an admitted descriptor. Whole SPACE admission still precedes this predicate and remains essential.

## Space admission and camera context

00ce93e0 calls00c3e3e0(renderContext,descriptor.SpaceID,&visibilityEntry). NULL rejects the whole descriptor. Visibility/current entry uses actual context.SpaceID, not inferred source geometry. Foliage agent owns the full registration/stream and portal-context reconstruction.

00c97d40 builds context:

- context+4 and+8 = selected native render camera.
- context+0xc = camera+0x360 current SpaceID.
- context+0x10 = plane count from camera+0x31c.
- context+0x14 = copied planes from camera+0x1cc.
- actual cull XYZ comes from camera+4,+8,+0xc, copied into00ce93e0 local vector.
- current visibility entry is context0; admitted neighbor entries begin context+0x168,stride0x15c,count+0x1728.

Native backend root was ABI-verified by foliage agent as `*[preferredVA019fdfb4]`. Main config is selected from backend+0x3f8 using the low16 bits of handle backend+0xa90. **This config is not the RsSceneRenderController object**. Do not add0x5e2d68 to config. For the actual controller object C (vtable preferredVA0173df30), its current renderContext is C+0x5e2d68, and C+4 is backend. Parent is resolving the live controller separately; selected camera pointers can independently be read from backend's camera registry+0x5f0.

## Source/native validation and limits

Using exact host reference eye with float32 arithmetic, q4 does not magically fix a lost assembly selector: only15/33 source-selected fixed assemblies are interval-active. Expanding ONLY exact fullVB/fullIB aliases gives31/33. Failures are native69083/source478 (current far8 vs native near0) and69091/source474; those indicate upstream source assembly/alias-selection gaps, not permission to change the native distance equation.

Source451 raw distance30367.56 now passes its0..30000 authored interval under q4. Source198 raw30567.62 also passes under q4, so distance cannot distinguish them. Canonical six-plane GLVP OBB tests also pass198,451,478. Root's live RPM then reported main config descriptors only0,431646,431650, excluding source198's SPACE431642 entirely. Thus the extra south canopy belongs to registration/stream admission, not a corrected-distance threshold trick. Native portal clip planes can differ from the canonical six-plane diagnostic; source-OBB-six-frustum-plane-check.json labels that limit.

The native metric, anchor, range inclusivity, pass-mask and OBB equation are resolved. Active-space streaming and exact source assembly selection are separate requirements being handled by the parent/foliage investigation. No whole-game visibility parity is claimed.


## Preserved runtime corroboration

Raw runtime evidence is work/v46-canopy/runtime/registered-collections.json with read_registered_collections.py and the raw render-config.bin,descriptor00..02,spacegroup00/01,camera00/01 dumps. Parent reports native EXE SHA16a400f6..., camera0 Space431646 and exact captured eye(8591.932617,-87036.03125,6493.066406). No native input or position changed. This preserves the distinction between checked static defaults and the actual paused reference runtime.
