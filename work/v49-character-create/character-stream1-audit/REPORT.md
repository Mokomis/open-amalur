# Character stream1 COLOR: observed native shared white default

The active weighted56 HardLight declaration reads COLOR from stream1 UNORM8x4 offset0. In this existing native frame, stream1 is a shared131072B buffer1831 containing0xff in EVERY byte, not per-character color data. Actual bindings use dynamic stride12, offset0, input-rate VERTEX. Thus every fetched COLOR is exactly(1,1,1,1). It is not a zero-stride constant in the examined weighted pipeline.

This resolves the captured runtime default value. The specific four current Almain clothing VBs do not match this frame, and the native initializer/binding function address was not recovered. Their original execution/appearance is not claimed; integration must distinguish observed runtime-default reconstruction from authored source RGBA.

## Exact captured declaration and consumption

pipeline13260, VS375/PS376, pVertexInputState:
- stream0 position float3@0, boneindex SINT8x4@12, boneweight SNORM16x4@16, UV0 float2@24, N/T/B SNORM16x4@32/40/48.
- active COLOR location7, stream1 R8G8B8A8_UNORM@0.
- stream0/1 input rates both VERTEX.
- declared binding strides0 are DYNAMIC, not the actual draw strides.

Representative draw67427 (indexCount648, instanceCount1, firstIndex0, vertexOffset0, firstInstance0):
bind event67424 vkCmdBindVertexBuffers2 binds buffers[9200,1831,64,64], offsetsall0, strides[56,12,0,0].
VS375 lines27/29 declare inputCOLORlocation7/outputCOLORlocation1; lines345..346 load input%40 and store output%43 unchanged. No per-instance multiplier is applied at this VS color transfer.

For contrast pipeline13262, VS375/PS376, consumes COLOR from stream0 offset56 (60B primary stride), not stream1. Draw67421 bind67418 uses buffers[3392,1831,...], strides[60,8,...]. Retain authored source RGBA for60/type22.

Exact pipelines are native-pipelines13260-13262.json. Raw selected bind events, buffer creation/memory binding and destination-write audit are buffer1831-producer-and-write-audit.json. Full existing native VS375 is module-375.spvasm.

The original D3D declaration evidence under work/v49-character-create/vertex-contract-audit/evidence/recorded-input-layouts.json additionally includes inactive TEXCOORD1 in stream1. The actual active HardLight pipeline has no UV1 input; its stride12 is compatible with4B COLOR+8B inactive UV1. Do not synthesize valid UV1 by reinterpreting allFF: these8B would be NaNs if consumed.

## Buffer provenance and temporal proof

CreateBuffer index36: size131072, usage209. BindBufferMemory index7506: buffer1831 -> memory1832 offset0.

InitBuffer record14962 (meta65543), original gfxr payload file offset12855003,131072B uncompressed:
SHA256 b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260.
ALL131072 bytes255.

FillMemory record73641 (meta65538), original gfxr payload file offset537613305, memory1832 offset0/size131072, same exact hash and bytes. This is the final host memory state before QueueSubmit76331 executes commandBuffer46. No captured GPU copy/update/fill/image-copy destination writes target1831. It is not inferred only from initial data or from draw-recording time.

extract_stream1_buffer.py independently decompresses both source records without replay; buffer1831-content.json seals event offsets, allocation length, hash, byte histogram and stride8/12 samples. native-stream1-buffer1831.bin preserves the full actual resource. native-default-color.rgba and native_default_color.inc preserve its first4bytes as an explicitly RUNTIME-default constant.

## Reuse boundary and corrected counts

Filtering main Gbuffer draws by primary stride56/60 yields147, but75 are NONweighted layouts without active stream1 COLOR. They must not be counted as weighted proof.

The actual BONEINDEX-layout subset has72 weighted draws:
-58 weighted56 draws consume active COLOR1; ALL58 bind1831 at0 with stride12.
-14 weighted60 draws use authored COLOR0; buffer1831 at0/stride8 is secondary/inactive COLOR.
- HardLight VS375 specifically has30 weighted56 COLOR1 draws plus2 weighted60 COLOR0 draws.

summary.json groups actual vertex attributes, VS and strides. weighted56-60-gbuffer-bindings.json preserves complete snapshots plus explicit weighted-layout/COLOR1 classifications. These counts establish shared default reuse in this frame, not a whole-game assertion.

## Current source clothing join and integration

The four full source VB hashes were compared against ALL730 retained native main-Gbuffer buffers from work/v45-foliage-coverage/instance-audit/native-gbuffer-buffer-hashes.json. NONE match:
- part1 feet FAB660455/asm0 MID660429,1020vertices,56B/type17, sourceCOLORabsent.
- part2 pack FAB660458/asm0 MID660430,250vertices,60B/type22, sourceCOLORauthored.
- part3 legs FAB660458/asm1 MID660428,1206vertices,56B/type17, sourceCOLORabsent.
- part5 torso FAB660459/asm1 MID660426,712vertices,60B/type22, sourceCOLORauthored.

four-clothing-source-join.json seals source stream/FAB/assembly/MID/hash paths from the existing checked source-join-manifest. A missing fullVB match is a bounded negative result for this exact frame/inventory; no broad asset scan was attempted and no replacement source was extracted.

Reusable reconstruction candidate: for source56/type17 with the verified opaque weighted HardLight declaration, supply defaultCOLOR=(1,1,1,1), separately tagged native_shared_all_ff. This represents observed native fallback data, NOT source-authored vertex color or a directly captured starter-clothing draw. It can be represented by a constant disabled-array attribute or repeatedRGBAffffffff; skinning does not transform color and VS375passes it unchanged.

Keep source COLOR presencefalse in provenance. Do not set an authored-RGBA flag, replace60/type22 RGBA, infer unknown UV1, or apply this fallback to unreviewed formats/permutations. Both source feet/legs fit the observed131072B allocation at stride12, but this capacity check does not prove their runtime binding choice. integration-contract.json records these distinctions.

## Limits and preservation

Source default initializer/binding function address remains unresolved; no broad cached-native search was needed after the direct resource/binding evidence answered the value question. No new game launch/replay/GPU/UI, new native analysis session, database change, core/scene/source-cache edits or Mac mirror. Only new character-stream1-audit files were written.

Original recording work/v31-native-slice/captures/amalur_trim_trigger_20261105T113036.gfxr SHA25672c3524703435311542d555dc419771d820f6baf81c84676ef2c6dc28c367209; existing decoded work/v33-native-camera/dalentarth.jsonl. Runtime evidence here is an existing recorded frame, not a new live observation.
