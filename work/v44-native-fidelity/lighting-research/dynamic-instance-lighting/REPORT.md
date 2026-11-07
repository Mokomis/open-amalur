# Active per-instance tint/luminance and leaf wrap audit

Static capture/source audit, 2026-11-05. Original recording and shader disassembly read; new research files only. No shared edits, renderer/UI/game actions or database mutation.

## Conclusion

There is no missing dynamic global tint or per-instance luminance operation in the active phase97/98 shader families. Do not multiply serialized instanceTint into already source-correlated native vertex colours based only on the struct field name.

All29 phase97 active VS/PS pairs were inspected. Their dynamic buffer tail only reads cb4[15].w (offset252 luminanceShiftId). No active shader reads cb4/68[13] globalTintColor, [14] luminanceFactors, or [15].rgb luminanceTint. Every pixel variant directly packs the clamped shiftId into G2.a; the vertex shaders do not use these tail colour fields. dynamic-shader-tail-reads.json records every active tail access with SPIR-V result ID and binding.

## Bound value statistics

Phase97 has799 draws. Of these667 bind white globalTint=(1,1,1,1). The other132 are terrain/instance variants(791/79294draws,785/78632draws,893/8946draws) whose unused dynamic tail contains world-coordinate/VP aliases: globalTint-like bytes(-102425,-102425,0,1), luminanceFactors-like bytes VP row0 and luminanceTint-like bytes VP row1. Applying these as tint would corrupt rendering; only consumed fields have semantic meaning.

For667 ordinary colour layouts, luminanceFactors are637draws(.211764723,.713725507,.070588239,0),30draws(1,1,1,0). LuminanceTint is569draws(.215686291,.309803933,.631372571),98draws white. The shift amount is0 in both actual luminanceFactors layouts, and these values are not consumed by the active material shaders anyway.

G2 shift IDs are .1875(701draws),.0625(68),.4375(30). All below .5, so no wrapped-diffuse flag in this reference's phase97.

Phase98's four748/749 draws bind a VS dynamic block at68 but NO pixel dynamic block4. VS748 only reads rows0..11. Their tail has white tint with stale VP aliases in the other colour slots, all unused. Phase98 blends only RGB into G1image158/G2image161 (both colorWriteMask7), preserving preexisting G2.a. It does not add an instance colour operation or change the wrapped-sun flag.

## Tree-leaf active PS878

82draws. All write `G2.a=saturate(cb4[15].w)` with shift .1875. The decisive operations are access%392, load%390, shuffleW%393, clamp%394, output%396. There is no+.5 operation.

The material0[0] vector is read at%181/%179 only to shuffle componentZ at%183 (NormalDisable). ComponentW TranslucencyDisable is not read by this active shader. Do not synthesize a wrap bit from that material field.

71leaf draws have mat0=(0,0,1,1),mat1=(1,0,0,0). Eleven have mat0=(1or.978120029,600,0,0),mat1=(0,10,0,0). Even those11 with TranslucencyDisable0 still output shift .1875 and no wrap bit. This is a measured active-family result, not a claim about every dormant native leaf shader variant.

All bound per-draw fields/offsets/modules/pipelines are retained in instance-draws.json; complete field histograms are in instance-dynamic-statistics.json. Raw leaf and phase98 active shaders are included. No colour tuning or new instance multiplier is proposed.
