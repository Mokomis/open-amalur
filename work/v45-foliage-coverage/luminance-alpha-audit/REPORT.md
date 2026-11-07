# G2 alpha / luminanceShiftId active-use audit

## Conclusion

G2 alpha is **not globally unused**: the active deferred combine uses its strict `alpha >0.5` predicate to enable wrapped diffuse. It does **not** apply a fractional-ID luminance shift, colour tint, exposure factor, LUT selection or shadow-map class.

For the measured final bridge frame, every one of799 phase97 bound values is below0.5:701draws0.1875,68draws0.0625,30draws0.4375. These are exactly representable in HALF. Thus leaf0.1875,cart0.4375 and ordinary0.0625 take the same alpha-dependent branch. The current forward combine's ordinary nonwrapped path agrees with these captured values; omitting the fractional IDs cannot explain the reported20percent darker reference surfaces.

This conclusion concerns this active shader and capture, not every dormant shader variant or future world/material.

## Exact active shader citations

Active pipeline7543,PS1895,phase106 draw72932. Native G2 is image161, read through view163, formatR16G16B16A16_SFLOAT, identity component swizzle, sampled binding34.

In retained `module-1895.spvasm`:

- lines102..103 define0.5 and constantvector%266.
- lines339..343: binding34 image%37 is loaded, sampled at%264 and stored in register%50.
- lines344..346: %268 extracts sampleW, and `%269=OpFOrdLessThan %266 %268` is exactly **0.5 < alpha**.
- lines347..364 turn that boolean into offset bitpattern0x3f0624dd (0.5239999890327454) and select multiplier0.6561679840087891 versus1.
- lines368..388 add the offset to NdotSun, clamp0..1 and multiply the selected factor: `lambert=saturate(d+(wrap?.523999989:0))*(wrap?.656167984:1)`.
- lines390..413 apply the shared shadow cap. The resulting front factor affects direct diffuse, shadow-colour ambient complement and sun-specular weighting. It is not a separate shadow cascade/class selector.
- lines527..530 are the only other load from G2 register%50; shuffle%443 selects RGB only.
- lines565..567 overwrite outputalpha with1. The original fractional G2 alpha is not forwarded into scenealpha.

The shipped DXBC `outputs/scene-v19/shaders/d2e799a101bdaddd.asm` independently agrees: sampleG2 at144,strict `lt0.5,r4.w` at145,offset/multiplier at146..150,shadow cap at153,RGB-only ambient use at166,outputalpha1 at170. The copy in this directory preserves these line numbers.

## Producer and later-pass coverage

Existing `work/v44-native-fidelity/lighting-research/dynamic-instance-lighting/REPORT.md` and `dynamic-shader-tail-reads.json` inspect all29 active phase97 VS/PS pairs: the dynamic tail's only consumed field is offset252/CB4[15].w, packed to G2alpha. No active pair reads globalTintColor, luminanceFactors or luminanceTint RGB for a hidden material colour shift. PS878 leaf output directly clamps this field with no+.5 operation; TranslucencyDisableW is not read by that active shader. Phase98 writes only RGB, preserving alpha.

Examples from existing exact bound fields: leafdraw68811 and69083 are0.1875; cartdraw68274 and lampdraw68589 are0.4375. `alpha-statistics-and-scope.json` retains the counts/examples and HALF check. A bilinear mixture of these alpha values also remains at most0.4375, so filtering cannot activate the wrap predicate.

A fresh full-recording descriptor/resource inventory finds image161 sampled **only** by PS1895: one draw in phases14,60,106 (the repeated frames). There are no G2 image copy/blit/resolve operations. No compute dispatch, indirect draw or secondary-command execution occurs. Every descriptor bind is a complete firstSet0,count1 bind, so retained-set ambiguity does not apply. The full draw inventory is in `g2-resource-consumers.json`.

Consequently the active later fog,DOF,bloom,LUT and finalfilter/AA stages do not sample G2. Scenealpha is reset to1 by the combine; the later luma-alpha AA producer derives its own value from final RGB rather than recovering luminanceShiftId.

## Practical boundary

Do not add a brightness multiplier or instance tint based on the field's name. Preserve a future wrap flag when a source producer actually emits alpha>0.5, but no wrap correction is supported for the799 final-frame producers measured here. This audit does not diagnose the remaining colour mismatch.

Read-only source/capture inspection and new research outputs only; no implementation changes,Ghidra,replay or GPU actions.
