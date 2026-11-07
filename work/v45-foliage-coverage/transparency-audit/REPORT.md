# Native phase111 transparent particle audit

The missing green addition is localized to authored Ambient-Godray_Medium_03 particles, rather than a shared sunlight/fog error or static web blend state. No core, live asset, water or owner-preferred waterfall file was edited. This investigation used the existing capture/source only, with no GPU/replay/Ghidra.

## Exact source/capture/current join

Source cluster4878 `Ambient-Godray_Medium_03` contains emitter task2131 and particle task2132 `Ambient-Godray_Medium_03_Ray_particle_task`. Material4093 `par_glow_godray_03_add` explicitly selects source shader363355 `particlefogadditivesoft`. It binds250070 `par_color_white_d` and236125 `par_glow_godray_03_a`.

Captured soft-additive draws73063 and73194 use VS1041/PS1042, diffuse image12707 and alpha image3804. **All ten authored compressed mip levels are byte-identical to those source assets**, independently of their names (texture-native-source-proof.json). White is32x32/4 levels; alpha is128x128/6 levels. Both BC1_UNORM, no sRGB conversion. Captured alpha uses GREEN. Exact samplers: sceneDepth NEAREST/CLAMP_EDGE; diffuse/alpha TRILINEAR/REPEAT, anisotropy OFF.

Actual current `work/v40-windows-host/assets/fx/fx.bin` is byte-identical to cached v25 Dal FX pack:35textures,72types,1359placements,53floats/type. Type27 matches this source particle/material, texture5, add=1. Type6 also shares texture5/material4093 but is a different warm particle task2130, `Ambient_Godray_Medium_02_Ray_particle_task`; do not apply type27 shape settings to6.

Current texture5 is **exactly** source white32 RGB plus source alpha128 GREEN resized to32 by Pillow's default resize. The current packed alpha range0..198 versus native source0..207 confirms the reduction; runtime generates replacement mips. Green-channel selection and additive SRC_ALPHA,ONE are already correct. A blanket phase6 additive switch would change unrelated static web MATS113–117 and is unsupported.

## Reviewable texture/shader correction

Private staged `stage/fx/t5.bin` is OATX_RGBA8,128x128,6 authored levels,87,404bytes. Every level has constant white RGB255 and alpha copied from the exact source/native level's GREEN. This is mathematically the native pair's sampled product because white is constant. It affects current types6 and27, both of which already use the same source texture pair. Load this optional override by FX texture index5, set MAX_LEVEL5, and omit glGenerateMipmap for the override. No texture IDs or live assets were changed.

`native_particle.frag` is an independently compiled GLES3 translation of PS1040/1042. It provides source-driven additive/soft-additive classification with explicit tint/luminance handling. Native soft PS1042:

- c=vec4(diffuse.rgb,alpha.g)*VC; VC is native RGBA8 UNORM. In VS, VC.a additionally multiplies global cb1[7].x, captured1.
- sceneZ=1/(inverseDepth.x*sceneDepth+inverseDepth.y).
- particleZ is **native clip.z**, exported by VS1041, not clip.w. With GL VP, export `.5*(gl_Position.z+gl_Position.w)` before interpolation to recover the native clipZ convention. sceneDepth remains hardware depth0..1.
- x=(sceneZ-particleZ)*.0199999996; soft=min(x*x,1); **if soft<=0 select1**, preserving the unusual native zero branch.
- c.a*=soft; c*=globalTint; lum=dot(c.rgb,luminanceFactors.rgb); c.rgb+=luminanceFactors.w*(lum*luminanceTint-c.rgb).
- outputRGB=c.rgb, outputA=c.a*interpolatedFogTransmission. No fog RGB addition. VS fogTransmission=min(exp(-(fogA*clipW+fogB)),1), perspective interpolated.
- Both RGB and alpha blend SRC_ALPHA,ONE, ADD into RGBA8; LEQUAL, depth write OFF. Current moving fog to RGB is equivalent only for additive RGB without other differences; native output-alpha semantics are explicit here.

Captured dynamic tint=(1,1,1,1), luminanceFactors=(.211764723,.713725507,.070588239,0); therefore luminance adjustment is inactive for the decisive beam draws. No arbitrary RGB tint is required.

PS1040 is the same additive family without sceneDepth/softness. Its draw73048 mask image3539 matches source texture236156 `par_moths_01_a` by exact compressed mip0 hash, with material4080 `par_moths_01_add`, source shader210906 `particlefogadditive`. Thus source shaderID, not the substring '_add', is the generic family classification. Other native alpha families are preserved separately in phase111-pipelines.json; no universal phase change is justified.

Proposed FX metadata bits are new implementation labels, not claimed native bit values: ADDITIVE, ALPHA_GREEN, SOFT_DEPTH, FOG_IN_ALPHA, LUMINANCE_SHIFT. Source shader210906 gets additive/green/fog-alpha/luminance;363355 adds soft-depth. Current material/type indexing can remain unchanged.

## Pixel coverage and effect size

All6 native quads in draws73063/73194 have full dimensions1100x5000 (maximum observed length error .00065), unlike current square550..750 geometry. All3 draw73194 quads cover980210; they also cover800150 and50035. Draw73063 additionally covers50035. Their projected winding is clockwise and survives captured pipeline13398's CLOCKWISE/BACK state. Raw dynamic VB128/memory129 is preserved, not used as a production fixture.

With exact mip0 mask bilinear samples, packed VC, perspective-interpolated native VS fog and soft fade1/no occlusion, the predicted additive RGB8 is:

| pixel | shader sum, before RGBA8 rounding/depth | reported native after-minus-before |
| --- | --- | --- |
|980,210|5.84,11.26,9.09|6,11,8|
|800,150|2.62,4.83,3.86|3,5,4|
|500,35|6.89,13.17,10.61|7,13,10|

This is strong causal localization. It is explicitly a coverage/contribution bound until native depth and exact per-draw target rounding are included; see additive-point-upper-bounds.json. No capture particles are baked into staged assets. Actual current transparents probe is AFTER oa_fx_draw (android_scene.c482/485), so the observed deficit is not a checkpoint excluding FX.

## Portable shape evidence and unresolved producer rules

The existing source cluster placements are already portable: nearest type27 source T=(7060.395996,-86044.3828125,7572.934082), Q=(-.396317780,-.286554039,.700241864,.520077229), PATCH431646 space0xd0 row15 (same DATA row). This exact pose is already in current fx.bin. All source raw fields/placements and tasks are preserved. There are33 cache occurrences including duplicate archives, versus17 selected current type27 placements; preserve patch-over-base precedence and do not duplicate them.

Task2132 explicitly contains width keys (time0,550,tangent0),(time1,750,tangent0) at bytes176..196 and height keys (time0,2500,tangent0),(time1,2500,tangent0) at300..320. Current size_curve() stops after the first width pair and completely discards the second dimension. Source values550/2500 correspond to measured native **half extents**. But width lifetime-lerp is NOT established: all6 sampled native widths are1100 despite different colour/alpha ages. Keep the whole source curve and its mode fields; do not assert current linear life interpolation is native.

The native quad basis is a cylindrical billboard around source emitter-local -X, not worldZ. Let A=rotate(conjugate(sourceQ),(-1,0,0)), B=normalize(cross(cameraForward,A)). Measured basis U=B*cos(5deg)+A*sin(5deg), V=A*cos(5deg)-B*sin(5deg) agrees with the captured unit directions within4e-7, modulo a simultaneous sign flip. The middle particle has both U and V negated while UV ordering remains0,0/1,0/1,1, so an unresolved180-degree orientation branch exists. Current unconstrained camera-facing random0..360 rotation is demonstrably different; fixed5deg without this sign branch is also incomplete.

Emitter2131 has two currently discarded integer channels0x1234094 and0x1261f62, both5 (class0x132c1a2), candidates for the measured angle. Particle2132 also has channel0x30a626/class0xc263f8 float10. Their semantic names and producer policy are not proven; **do not claim10/2 is an authored conversion**. The exact source/capture bounds are recorded in source-type27-shape-candidate.json. The proposed worldZ-up flag is contradicted for this family; reserve a distinct emitter-local-X cylindrical flag if implementing the measured family. Fixed-angle/sign/curve selection need further native producer evidence, not image tuning.

The staged texture and shader contract are ready independently. No shape binary is labelled promotion-ready while these producer choices remain unresolved. This report makes no claim of complete particle-system parity.


## Native follow-up superseding the float10 angle candidate

See NATIVE_PRODUCER_REPORT.md. Exact cached class identity proves particle float10 is BHG_TaskletFlatness, not rotation. Named native MinMaxAngle writes the source second5 angle channel. Dimensions uses authored property inputs/caller fallback plus persistent per-instance offsets, not automatic life interpolation. Eight-function cap reached; sign and caller-domain remain explicitly unresolved.
