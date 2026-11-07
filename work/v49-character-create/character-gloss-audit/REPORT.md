# One exact character material: source gloss20 uploads as20

The captured RustySword material1880463 (CharacterHardLight545212) uploads source SpecularValues.y=20.0 unchanged. Captured PS352 writes that20 directly to G0.a. G0 is RGBA16F, so20 survives storage exactly. Native shared deferred lighting later uses storedGloss*.25, yielding exponent5.0. Do NOT divide the source value by255, clamp it to0..1, or multiply by.25 before G0 storage.

This closes the requested ONE-character-material upload question. It is not an observed skin/head/hair material setter audit, and does not establish all future shader families by analogy. Existing MATERIAL_SUPPORT.md was not edited; it can cite this scoped result.

## Exact source-to-captured material join

Phase97 draw67406, commandBuffer46, pipeline13252, VS351/PS352. IndexCount1812 (604 triangles), firstIndex0, vertexOffset0, instanceCount1.

Both raw meshes match original source FAB1880465 assembly0 byte for byte:
- Source424*48B VB / native buffer3343:20352B, SHA256 e233102852916da55d655feb6683ee9da46c4887febf094318704affaecc8145.
- Source1812*u16 IB / native buffer3345:3624B, SHA256 182a00979767a1a4d09d8f5a8f3a390a355778a37470679501be9367f3adefd5.

Source files: work/v48-opening/initial-sword-visuals/raw-meshes/1880465/assembly-00.vb48 and assembly-00.u16. Native hash provenance: work/v45-foliage-coverage/instance-audit/native-gbuffer-buffer-hashes.json. FAB/source material association is preserved by that source stage; this audit independently confirms all actual bound textures and params:

| Captured binding/image | Source material1880463 slot/asset | Native format | Comparison |
| --- | --- | --- | --- |
| 32/image13839 | slot0 diffuse1880460 | BC1_RGBA_UNORM | All7 authored mips exact |
| 33/image13844 | slot3 normal1880461 | BC3_UNORM | All7 authored mips exact |
| 34/image13875 | slot2 specular1880462 | BC1_RGBA_UNORM | All7 authored mips exact |

No image decompression-to-RGBA or color conversion is involved in this texture proof: compare original BC blocks at each original source offset to each capture InitImage mip's tight bytes, skipping allocation-tail padding. Dimensions256x1024, seven mips. Source slot1 white250070 is not read by this PS. sword-texture-byte-join.json records all21 mip SHA/offset matches, and join_sword_texture_bytes.py reproduces them. Source textures/manifest remain under initial-sword-visuals; only3 capture InitImage blobs are staged here.

## Source CB and temporal upload

Original mat_bxml is copied here as1880463-source-material.mat_bxml; its source path/SHA and four parameter value offsets are in material-runtime-gloss-proof.json. The complete source64B of four float4 values equals captured CB0 ALL64bytes:

ConstantColor=(1,1,1,1)
SpecularValues=(1,20,0,0)
CharacterExtraTerms2=(.15000000596046448,1,1,0)
FresnelValues2=(1.399999976158142,2.4000000953674316,0,0)

At bind event67404, set13889 has dynamic UBOs in binding order0,2,4,68, each buffer51/baseoffset0. Dynamic offsets are651264,639296,651520,651520. Thus fragment material binding0 resolves memory52@651264; world VS binding68 resolves memory52@651520. Full raw bind args and current descriptor writes are in draw-67406-bindings.json.

Important capture timing: draw67406 records commands BEFORE the host memory write. FillMemory event73631 supplies memory52 offset0 length33554432 before QueueSubmit76331 executes commandBuffer46. reconstruct_sword_uniforms.py replays the relevant intersection through this actual SUBMISSION boundary, not the draw-recording event. The reconstructed512B equals the prior prefix snapshot exactly; no stale-uniform assumption is needed. Full32MB uncompressed FillMemory SHA256 a9433c481e510e8777abfaa9105019d735e66551125b7fb083deac6ea9e3befd.

uniform-temporal-proof.json preserves event/file offsets, compression, hashes and all16 source/runtime floats. draw67406-cb0.bin is64B; draw67406-world-cb68.bin is256B. No new game execution or replay occurred.

## Shader consumption and target

module-352.spvasm is the previously extracted active native shader, copied read-only here:
- lines14..15 material CB binding0; the block is four float4s.
- lines48..50 output locations0/1/2.
- lines241..246 load CB0[1].yyyy and put it directly in output0.w.
- no multiply/divide/clamp is applied to output0.w, and there are no later stores to output0.
- phase97 target0 view221/image155 is R16G16B16A16_SFLOAT, not UNORM. phase97-gbuffer-formats.json seals all3 targets.
- binary16(20) is0x4d00 (little-endian004d); source/runtime20 is exactly representable.

The existing reviewed native combine evidence at work/v44-native-fidelity/lighting-research/combine-audit/REPORT.md uses active PS1895 and native pointPS1870/1871: exponent=sampledG0.a*.25, no other gloss normalization. This audit does not rerun that established arithmetic work.

For forward emulation of GBuffer terms, keep runtimeGloss=sourceSpecularValues.y; emulate half storage if other material terms do; evaluate reflected-light lobes using runtimeGloss*.25 once, in the shared lighting stage. This is compatible with eventual MRT or the parent's current quantized-term forward path.

## Same draw's actual standalone vertex contract

pipeline-13252.json retains the complete native pipeline. vkCmdBindVertexBuffers2 event67403 supplies effective stride48 for binding0/buffer3343 at offset0; the declaration's stride0 is overridden dynamically.

| Location | Byte offset | Native input format | Consumed semantic |
| --- | --- | --- | --- |
| 0 | 0 | R32G32B32_SFLOAT | Position |
| 1 | 12 | R32G32_SFLOAT | UV0 |
| 2 | 20 | R16G16B16A16_SNORM | Normal XYZ |
| 3 | 28 | R16G16B16A16_SNORM | Tangent XYZ |
| 4 | 36 | R16G16B16A16_SNORM | Bitangent XYZ |
| 5 | 44 | R8G8B8A8_UNORM | Vertex color |

VS351 binding68 uses source P.x*row0.xyz+P.y*row1.xyz+P.z*row2.xyz+row3.xyz for world position; rows8..11 similarly produce captured clip position directly. N/T/B are EACH transformed by rows4..6 then normalized in the VERTEX shader before smooth interpolation. It does not orthogonalize the three vectors. Fragment PS352 combines interpolated raw T/B/N with decoded mapXYZ and normalizes that sum. Thus vertex normalization and fragment normalization are distinct steps; do not normalize each basis again per fragment.

VS351 inputlocation5 VC passes to outputlocation1 unchanged; inputUV0 passes outputlocation2.xy. Normal/Tangent/Bitangent map to outputlocations5/6/7. Full module-351.spvasm is retained here. standalone-hardlight-vertex.glsl expresses only this VS math; it is not a complete skinning implementation or a runtime replacement.

Captured world matrix rows0..3 (row-vector convention) are preserved in uniform-temporal-proof.json:
( .6354823112, .5893834829, .4987879097,0)
( .5933947563,-.7861242294, .1728924513,0)
( .4940091074, .1861079931,-.8493051529,0)
(8479.7978516,-86891.59375,6402.4038086,1)

This draw proves the standalone48B layout ONLY. Container1789717 stride60 semantics/bone binding/animated pose remain separate and are not promoted from source heuristics.

## Scope and preservation

Capture: work/v31-native-slice/captures/amalur_trim_trigger_20261105T113036.gfxr, SHA256 72c3524703435311542d555dc419771d820f6baf81c84676ef2c6dc28c367209. All new files only in work/v49-character-create/character-gloss-audit. Source mesh hashes, all21 original texture-mip comparisons, complete64B parameter match, reconstructed pre-submission memory and direct native PS output agree.

No core/UI/live preview assets, legacy save/settings, original database, or original game UI changed. No GPU/game launch, broad material scan, new Ghidra session or Mac mirror. This is one exact source/captured CharacterHardLight material; full skinned character, skin/head/hair cosmetic application and final lighting parity remain outside the result.
