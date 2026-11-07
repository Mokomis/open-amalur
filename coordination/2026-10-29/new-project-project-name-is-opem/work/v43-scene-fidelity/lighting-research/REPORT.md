# Bridge-frame lighting contract investigation

Read-only source/capture analysis, 2026-11-05. Only new files under this directory were written. No original game launch/input/injection, database open/write, source edit, asset-pack edit, installation, or helper inference occurred. Canonical AGENTS.md and REA skill were read. Existing exported native evidence was reused.

## Outcome

The original bridge frame and current custom host use matching Noon sun, shadow and fog inputs. Do not tune their values from image appearance. Fog's exponential base is already correctly implemented in current GLSL. A real material-lighting mismatch exists: custom opaque materials omit the native specular-dependent ambient-cube reduction and sky-specular term, and replace the native material specular contract with a fixed Blinn exponent. Red-channel sampling is supported for the plain-dot3 family described in the follow-up below; other families use green. Native ambientDiffuseScale=5 is a sky-lobe exponent factor; multiplying the whole cube contribution by five is incorrect.

## Evidence identity and consumed constants

`inputs.json` hashes the capture prefix, Vulkan JSON and inspected current source files. `captured-global.json` gives every measured field offset/value. `evidence/g_globalbuffer.bin` preserves the exact 1376-byte block. It comes from existing `work/v33-native-camera/memory-52-prefix-v7.bin`, memory52 offset360896, buffer51. Shader `6ffd68426e1c6540.asm` supplies the shipped HLSL field layout.

`binding-proof.json` records the Vulkan consumption: capture JSON index43247 binds set13918. Sorted dynamic bindings0,64,65,68 have ranges256,256,1376,256 into buffer51 at offset0. Dynamic offsets360640,360640,360896,362304 therefore bind the global block at binding65. The trace contains 2848 bind calls including this offset. This proves use of the captured bytes, not merely a plausible float search. The JSON header has an invalid unescaped Windows path; only that non-record line was skipped while loading records.

Measured original values:

| HLSL field | Offset | Captured value |
| --- | ---: | --- |
| fogColor |0|(.419607878,.360784322,.223529428,1)|
| worldToFogConstants |16|(4.73102009e-5,-.155217022,0,1)|
| sunLightDirection |32|(-0,.365438223,.930835485)|
| sunLightColor |48|(.785888314,.785888314,.785888314)|
| skyLightColor |64|(.5,.5,.600000024,1)|
| shadowColor |80|(.200000018,.145098045,.109803930,1)|
| environmentTint |96|(1,1,1,1)|
| ambientDiffuseScale |1276|5|
| ambientSpecularScale |1280|.899999976|
| backlightScale |1284|.119999997|
| sunlightFogTintAmount/Power |1288/1292|.5 /10|
| waterFogDepthScale/OpacityScale/Enabled |1296/1300/1304|80 /.00999999978 /1|

## Current source and authored input verification

The Windows host's actual CMake target explicitly compiles `../v19-host/android_scene.c`, `room_lighting.c`, `oa_post.c`, `oa_sky.c`, and `oa_stream.c` (`work/v40-windows-host/CMakeLists.txt`). `android_scene.c` includes `town_live.inc` directly. At this inspection that include says **Dalentarth, Noon**, with1088 lights, fog density23.65510, start-.1552170, bloom_strength.6298, cutoff.43. No Erathell lighting include was active in this source path.

`room_lighting.c` includes `town_environment.inc`; its sun/shadow are used by `world_draw` at android_scene.c335-343. The generated values agree with the captured g_global block above within source literal precision. The build generator `work/v20-char/build_town.py`365-385 hardcodes Noon and resolves region431608 by default. `authored-noon.json` was decoded from the already-extracted patch region431608 without running extraction. Its Noon RGB*HDR*directionalIntensity equals captured sunRGB; negated authored direction equals captured direction. Thus Noon here is supported by captured constants, not guessed from daytime appearance. Matching constants do not uniquely identify the active runtime region because regions may share values.

`authored-input-comparison.json` verifies current cube bytes equal authored region431608 Noon ambient_cube_index2 and current LUT bytes equal already-extracted LUT1381912. This is byte identity of authored selections. The captured ambient image pixels were not extracted/matched, so runtime cube identity, native sampler face/channel convention, time/region blend selection remain unproven by this comparison.

## Fog: retain the current equation

Shipped VS `909a47556818e060.asm` computes `x=a*clipW+b`, then multiplies by-1.442695, D3D `exp` (base2), and min1. Since1.442695=log2(e), the native expression is `min(exp(-(a*clipW+b)),1)`. Current `oa_post.c:13` uses exactly that natural exponential and computes fog amount as1-keep. Current `world_draw` supplies density/500000 and fog_start. With matched native VP, clipW has the same source meaning.

Older `lighting_model.py` and lighting-provenance statements that simplify this to plain2^(-(a*z+b)) omit the log2(e) conversion and are stale/incomplete. Do not change GLSL `exp` to `exp2` without the conversion. Sun/fog source values are not a supported correction.

## Opaque ambient/specular equation: measured globals plus shipped shader

`evidence/1f82728c2c7f4270.asm` is a shipped three-target opaque G-buffer material shader with normal/detail maps. Its HLSL header names material SpecularValues; scalar x is strength and y is gloss/power. The exact ambient portion after evaluating that shader's detail-blended green-channel specular mask is:

```text
V = normalize(cameraPosition - worldPosition)
q = materialSpecularStrength * specularMask * ambientSpecularScale
ambientDiffuse = (1 - saturate(q)) * cube(N.xzy) * albedo
ambientSkySpecular = q * skyLightColor.rgb *
    pow(saturate(reflect(-V,N).z), skyLightColor.a * ambientDiffuseScale)
gbufferAmbient = saturate(ambientDiffuse + ambientSkySpecular)
```

In this bridge block ambientSpecularScale=.9, skyLightColor=(.5,.5,.6,1), ambientDiffuseScale=5. No factor5 multiplies cube diffuse. The constant's name is misleading if read without its instruction use. The shader multiplies raw albedo by vertex colour; detail-specific material sampling and per-instance tint remain material contracts, not global constants.

`183f1a1afcef9ca4.asm` confirms a related forward material's cube reduction/sky-lobe terms, but its final specular combination differs. Do not copy the entire forward equation into all opaque/terrain/foliage variants. The exact selected D3D shader hashes for every bridge draw were not mapped to Vulkan SPIR-V modules in this bounded pass. These are shipped material-family equations, not a proof that every restored prop uses the same one.

Current `oa_post.c:45-50` reads specularTexture.r (correct for the plain-dot3 candidate below, not universal across the earlier detail shader family), gives cube its full weight, omits skyLightColor and its lobe, computes fixed Blinn32 and multiplies the final spec_sum by.9. Its own comment labels specular an approximation. Current stream upload exposes cutoff and water[11], with no general SpecularValues material uniforms. Therefore a direct implementation should first carry the native material strength/power/channel contract for supported material families; do not invent a universal strength from appearance. The smallest useful scoped correction is the native ambient formula for identified regular opaque material families, driven by measured globals and recovered material scalars, with existing fallback explicitly retained for unsupported families. The sky ambient term is additive after albedo-weighted cube diffuse, rather than being multiplied by albedo again.

## Other known differences and limits

Native deferred combine `d2e799a101bdaddd.asm` applies shadow opacity through `1+shadowColor.w*(shadow-1)`, backlighting, light-buffer/specular terms, SSAO and the opaque G-buffer split. Current forward approximation combines those differently; current bridge shadow opacity1 makes ignoring the opacity scalar itself no numerical difference for this frame. Native shadow filtering is not the authored custom four-tap map.

Current river/waterfall use the ambient cube as a substitute for native reflection cubes (`oa_post.c:25-37`). Captured water-fog globals exist but current water shader does not consume them. Its water branches return before the generic world-fog mix. These gaps are factual; an exact replacement needs the native water material/reflection/depth-resource contract, not a global colour adjustment. Current sky documents host choices for dome mapping, horizon fade, absolute cloud scale and below-horizon colour in `oa_sky.c:9-16`; no native sky-vertex recovery was established here.

Post values in `authored-noon.json` are authored data, not exact measured active bridge merge constants: bloom_strength.6298, exposure.8277, min_luminance.1738, max_luminance1, post_bloom_scale.2958, cutoff.43, brightness1, contrast(1,0,0). `FUN_00cd6b70` scales exposure/min/max/strength through global weight and global scale fields, so authored equality alone does not prove final runtime output. Current custom bright/blur/AO and merge are authored simplifications (`oa_post.c:52-56,89-97`). An older Odarath/Midnight measured merge coefficient.5376 must not be transplanted into this Noon bridge frame. Post draw bindings were found, but their candidate buffers were outside the useful prefix or zero in this snapshot; no exact active bridge post coefficient was established. The shipped LUT final-pass shader `f412424ceb9dabb0.asm` and its48-byte field layout are preserved for the next focused read of the full captured memory fill.

Native readers reused here: `FUN_00cd6680` packs sunlight/shadow/fog/sky and packet0x40; `FUN_00c8a880` constructs fog constants with the global luminance-shift scales; `FUN_00cd6b70` constructs post packet0x42. Their exported bodies are saved in evidence with original source paths. Decompiled globals/temporaries remain untyped in places; captured constants take precedence over interpreting incomplete decompiler locals.

## Checklist

- Sun/shadow/fog bridge inputs: answered with bound captured bytes; retain current values.
- Fog exponential base: answered; current natural exp is correct.
- Ambient globals/equation: answered for the preserved shipped opaque family; material scalar and active per-draw family mapping remain required for exact implementation.
- Cube/LUT authored selection: byte-verified against Noon; captured runtime image identity not established.
- Exact bridge post, reflection cubes and native sky mapping: unresolved; no visual tuning proposed.


## Focused follow-up: the three restored-prop dot3 materials

`dot3-authored-materials.json` records materials301326,299790,1377236 from existing extracted files, retaining archive choice and hashes. Each material is128bytes; payload112 and fixup8. Root values at file+8 give paramPointer40 (a file offset), paramCount2, texturePointer88, textureCount4, shader8827. Symbol table maps8827 to `dot3`. Each24-byte parameter record is **float4 value, u32 type, u32 name-key**, so values precede their key. First record at file40/payload32 has key0x9ccd9a/type11; second at file64/payload56 has key0xb680d8/type11. The second value is(1,20,0,0) in all three. First value is(1,1,1,1) for301326/299790, and(1,.831372619,.576470613,1) for patched1377236. Thus this is real authored material data rather than a default invented from appearance.

`evidence/ba5e9f9d993a0e37.asm` is the **only** preserved shipped three-target pixel shader with exactly32-byte material layout `{ConstantColor(float4 at0),SpecularValues(float4 at16)}`, and samples normal/spec/diffuse maps. Its instructions differ materially from the detail family above:

```text
specRaw = specTexture.r * SpecularValues.x
GBufferGloss = specTexture.b * SpecularValues.y
q = specRaw * ambientSpecularScale
GBufferAlbedoSpec = saturate(float4(diffuse.rgb * vertexColor.rgb, specRaw))
GBufferAmbient = saturate((1-saturate(q))*cube(N.xzy)*albedo +
    q*skyLightColor.rgb*pow(saturate(reflect(-V,N).z),skyLightColor.a*ambientDiffuseScale))
```

Its vertex-colour input can already contain ConstantColor; the pixel shader does not directly read ConstantColor. The exact vertex-stage producer must be followed before applying this colour a second time.

Current red sampling is therefore **consistent with plain dot3**, and a blanket red-to-green replacement would break this candidate family. For these three materials, the authored scalar candidates are strength1 and glossScale20. Native deferred combine raises the specular reflected-light lobe to storedGloss*.25, not fixed Blinn32.

`material-buffer-candidates.json` proves169 original capture descriptor binds (binding0/64,256-byte allocated range) read memory52 slices whose first32bytes are white ConstantColor followed by(1,20,0,0); first example bind45100/set13889/offset651264. These corroborate the32-byte layout and material values, but they do not identify a specific candidate draw as material301326/299790/1377236. The exact key-to-HLSL-name mapping and shader8827 platform-variant-to-DXBC-hash association remain inferred from layout/family agreement, not directly traced end-to-end. The Vulkan JSON stores shader module pCode pointers, not SPIR-V byte payloads. No unsupported direct material/draw equivalence claim is made.

A narrowly-scoped sidecar can preserve the exact authored vectors and shaderID/key fields now. If implementation needs semantic names before that last mapping is completed, mark the two mappings as explicit inferences, retain unsupported-family fallback, and limit application to the identified dot3 materials/family. Strength1/gloss20 are not guesses for these three assets. Do not use the generator water helper's search-for-key-then-next-float approach for these records: the verified value precedes the key in the24-byte record.

SkyLightColor's source is answered: current decoder ENV record+0x480, four16-byte time keys; Noon is record+0x4A0, giving(.5,.5,.6,1), exactly matching captured g_global+64. `FUN_00cd6680` copies this float4 through environment snapshot+0x50 to packet+0x38..+0x44. Native shader uses its w as the multiplier of the5 exponent, not simply as an RGB intensity.
