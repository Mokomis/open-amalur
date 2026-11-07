# Character vertex contract: Almain male candidate

Private staging only; no core, preview, existing pack, source cache, original asset, settings or save edits.

## Concrete finding
The current OACHAR01 builder chooses a normal offset by scoring vector lengths. It selects source TANGENT instead of NORMAL for 2,781 of 8,144 weighted vertices:
- Part0 hands FAB514034/asm0, MID513702:1086 vertices.
- Part1 feet FAB660455/asm0, MID660429:1020.
- Part4 torso skin FAB660459/asm0, MID513702:466.
- Part8 eyes FAB1465831/asm4, MID790131:209.

All four old normals match source byte40, while NORMAL is byte32; maximum component errors1.41–1.77. Other eight parts match source N to float quantization tolerance. Head1347 source UV1 pairs all differ from UV0. Four color-bearing parts have authored RGBAffffffff; the other eight carry no COLOR in source stream0. Missing fields remain explicitly absent.

## Native evidence and limits
evidence/recorded-input-layouts.json retains exact original D3D CreateInputLayout log lines, line numbers and SHA256 from work/v30-engine/oa_rec-dal-original/resources.txt and oa_rec-standstill/resources.txt. Both retain the same four weighted declarations. All offsets are APPEND_ALIGNED_ELEMENT; compute offsets independently per input slot.

DXGI formats:6 float3;32 UINT8x4;13 SNORM16x4;16 float2;28 UNORM8x4.
Common stream0: P@0, BONEINDEX@12, BONEWEIGHT@16, UV0@24.
- Stride56, source type17: N32,T40,B48; COLOR and UV1 stream1.
- Stride60, type22: N32,T40,B48,COLOR56; UV1 stream1.
- Stride64, type25: UV1@32,N40,T48,B56; COLOR stream1.

Missing native stream1 contents and the candidate's executed shader/layout identity are NOT joined. Native declaration-to-candidate correspondence is backed by exact serialized stride and matching FAB-descriptor/assembly vertex types; it is not a capture of these exact male parts drawing. No68-byte candidate layout is exported.

Actual representatives: head1465831/asm0 stride64; body514034/asm0 stride56; hair1302979/asm0 stride56; clothing660459/asm1 stride60. source-join-manifest.json contains all paths/SHA/byte offsets/VB hashes/raw descriptor tails.

MID and shaderID are first two u32 fields at the exact structured FAB mesh-descriptor tail25 boundary, checked against mat_bxml header shaderID. Existing amalur_fab's layout originates in the external-format profile and still has native_layout_confirmed=false; this audit does not relabel it native proof. The exact byte associations replace the old symbol-ID scan and match all12 surfaces. materials/ retains10 whole mat_bxml bytes plus JSON source slots and raw parameter values/types/keys. Mat header @8/12 params pointer/count, @16/20 texture pointer/count,@24 shaderID, all bounds checked. Texture semantic slot is not a GL unit or an active runtime per-instance binding. Runtime substitution/samplers/cosmetics remain separate.

## Additive OACAT01 sidecar
All integers LE, source shorts/raw floats exact. Existing character.bin stays byte-identical. Bind sidecar to full original pack SHA BEFORE any runtime correction. Reject malformed/wrong-pack/unsupported/integrity failure atomically, without partial changes.

Header64B:
0 magic8 OACAT01 plus null;
8 u32 version1;
12 u32 basePartCount17;
16 u32 coveredPartCount12;
20 u32 partRecordBytes128;
24 u32 attributeStride64;
28 u32 reserved0;
32 SHA256(base character.bin),32raw bytes.

Each sequential entry has fixed128B record:
0 u32 originalPartIndex;
4 u32 FAB;
8 u32 assembly;
12 u32 nativeMID;
16 u32 nativeSourceStride;
20 u32 vertexCount;
24 u32 indexCount;
28 u32 presenceFlags;
32 SHA256(existing52B part vertices),32B;
64 SHA256(raw source VB payload),32B;
96 SHA256(existing u32 indices),32B.
Then vertexCount*64B attributes, then vertexCount*sourceStride raw source VB bytes. Next record follows immediately; exact EOF required. Manifest gives each payload's absolute file offset.

Attribute64B:
0 NORMAL SNORM16x4 (8raw bytes);
8 TANGENT SNORM16x4;
16 BINORMAL SNORM16x4;
24 UV0 float2;
32 UV1 float2 only if flag16;
40 COLOR RGBA8 only if flag32;
44 u32 flags;
48 u32 source vertex index;
52 source P float3 (join key; existing52B P remains authoritative).
Flags1=N,2=T,4=B,8=UV0,16=authoredUV1,32=authoredRGBA.
Absent field zero placeholders MUST NOT be consumed as authored values; no white or duplicated UV is invented. Raw fourth components are retained. Native component decode max(-1,signed16/32767), no source-vector normalization. GL can use4xGL_SHORT normalized and authored RGBA4xGL_UNSIGNED_BYTE normalized.

Base:
work/v49-character-create/packs/Almain_Male/character.bin
15,030,356B SHA256 ede399d687bcbbc9d1534a208e81a13b9b3785a6f2b52dc25b28f78f36a484a4.
Sidecar:
almain-male-attributes.oacat
998,556B SHA256 ab02a4a4c87996f5ac5584987455e812f6286c87a563b2bbfbca4b635c7635bf.

## Narrow normal-only integration
After validating/hash-pinning ALL records, prepare all normal corrections from attribute NORMAL.xyz; update ONLY in-memory52B normal float3@12 using native SNORM decode. Preserve source pack file, P@0, UV0@24, joint bytes@32, weights@36, palettes, animations, indices/order and matrices. Do not renormalize component values during this conversion.

oa_character_parse may clear otherwise-unused out-of-range zero-weight joint bytes, so hash ORIGINAL preparse pack/vertex bytes rather than a parser-mutated buffer. On any optional-sidecar failure leave the character unchanged. Validate before committing any correction.

Later full material integration can use TBN/UV1/RGBA plus MID per part; this stage does not prove or change native skinning/matrix policy. Raw interpolated TBN material math is covered separately by analysis/MATERIAL_SUPPORT.md. Missing runtime stream1, per-instance cosmetic bindings, eye/mouth omitted surfaces, active material variants and facial-bone fallback remain unresolved.

Parts12..16 existing rigid weapons are deliberately outside this weighted appearance audit. Eye_shadow and mouth_black source surfaces omitted by old builder are not silently restored. No UI scope.

## Validation
Run python export_character_attributes.py then python verify_character_attributes.py here. Exporter imports existing readers read-only with bytecode writes disabled; no extraction or old-builder execution.

Independent verifier does not import exporter. It checks source unchanged hashes, exact descriptor MID/shader, every P/UV0/joint/index join, packed TBN/UV1/RGBA, payload hashes and EOF. PASS12parts/8144vertices/32712indices;46 negative corruption/truncation/wrong-base cases rejected. validation-receipt.json and verification.log record results. Structural/source verification only, no new GPU/animation test.
