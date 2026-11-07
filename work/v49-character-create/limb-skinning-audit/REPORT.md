# Almain male limb skinning audit

Private staging, no live/core/source/pack/save edits. Scope:12appearance parts/8144vertices; actual compiled existing oa_character_parse, oa_character_pose and oa_character_bones; one existing idle0 and walk8 pose.

## Actionable defect: wrong per-assembly palette

The builder's heuristic palettes() scan finds6tables for the4assemblies of FAB660459. The fallback max(tables,key=len) selects the FIRST12-entry skin table for BOTH near surfaces. Shirt part5/asm1/MID660426 therefore maps10of12slots to the wrong current rig joint. Its authored descriptor has its own12-entry table. This is not a weight problem or an eye-tint adjustment.

Current shirt slot rig joints:
[38,57,56,37,18,19,22,23,24,41,42,43].
Source-own table under EXISTING main-rig mapping/rest policy:
[2,38,57,17,18,19,19,19,22,23,41,42].

Actual current C pose/bones matrices + original vertices/weights:
| Pose | Shirt maximum displacement | Mean | Vertices above1mm |
|---|---|---|---|
| idle clip0/frame0 |28.725047cm |4.215466cm |605/712 |
| walk clip1/frame8 |29.116304cm |3.784271cm |646/712 |

The second exact association defect is hip pack part2/FAB660458/asm0/MID660430. Its own descriptor has1entry LFTHIP_ATTACH hash11187748 -> current rig15, while the heuristic uses the18-entry leg table and maps slot0 to PELVIS rig2. ALL positive-weight and ALL nonzero native-weight source indices are0. Correcting this entry changes tested positions only0.00000944cm idle /0.00003053cm walk, because the attachment follows pelvis in these poses. Do not claim a large visible hip defect from these two tests.

Hands24, feet4 and torso-skin12 mappings match their own exact source tables. No correction to their palettes is staged.

builder-heuristic-receipt.json executes ONLY the existing pure palettes() function in isolation and pins its source SHA. Exact scan counts:
hands3tables [24,24,1] vs2assemblies, feet4[4,4,1,1] vs2, legs8[1,1,1,18,1,18,1,1] vs4, torso6[12,12,12,12,1,1] vs4. Longest-table fallback explains the two demonstrated errors.

## Native weight proof: keep current policy

All31retained original weighted VS in outputs/scene-v19/shaders declare BONEWEIGHT only.xyz and execute:
mov r0.xyz,v2.xyzx; mov r0.w,1;
dp4 r0.x,(-1,-1,-1,1),r0.xyzw.
They index each bone palette entry as3float4rows, apply dp4 to P.xyz1 and combine with weights in order1,0,2,3. No stored fourth input or clamp is used. Exact file SHA and line numbers are in native-weight-contract.json; two complete original disassemblies are copied here. This does not assert which exact permutation the unrecorded candidate would select, but all retained variants agree on this arithmetic.

Source BONEWEIGHT is DXGI13 SNORM16x4. ALL8144raw fourth components are0; source four-component sum ranges down to0.794946, so blindly using the stored fourth would lose valid native influence. Native w3 is reconstructed1-sum(first3), not loaded from that zero field. Every raw weight is nonnegative/inrange.

The builder correctly reconstructs the fourth but clamps it to max(0,remainder).446vertices have tiny native negative remainder -1/32767 from quantization. Current packed weights agree with the builder policy to <=2.98e-8. Across both tested poses/all12parts, changing to the unclamped native arithmetic would move positions at most0.005565cm (=0.05565mm); limb-only max0.005403cm. This cannot account for the demonstrated29cm shirt error. No weight policy change is staged.

## Source bone mapping and rest algebra

Each assembly descriptor has fixed32B prefix, remapCountu32 at+28, then remapCount52B records. The raw remap layout is Tfloat3@0, Qfloat4@16, Sfloat3@32, flagsword44, boneIndexi32@48. The existing amalur_fab generic remap read_trs labels incorrectly call the first16B quaternion; this audit uses exact raw offsets and preserves all52B evidence. Descriptor boundaries/material/type association were already independently joined in the sealed vertex audit.

Each corrected slot joins source bone name HASH to current common-rig bone HASH, not geometry proximity or local bone ordinal. Hip joins directly. Ten shirt slots join directly. Source shirt slots6/7 hashes7969014/7976755 are absent current64rig: both ascend two source parents to SPINE2 hash7389006/current19. That is the EXISTING ancestor approximation, explicitly retained. Each slot influences3shirtvertices, maximum weights0.1735893/0.1758171. Thus6vertices still lack full native helper-bone behavior; no claim of complete native shirt rig parity.

The replacement keeps the builder's current inverse-common-rest convention:
iq=conjugate(commonBindWorldQ[j]);
it=-rotate(iq,commonBindWorldT[j]).
Runtime unchanged:
q=animatedWorldQ[j]*iq;
t=rotate(animatedWorldQ[j],it)+animatedWorldT[j];
apply facing/feet as existing; emit3x4rows.
Source hands/feet/torso-skin inverse-bind T agrees with this shared-rig inverse to <=0.000239cm; conjugated stored inverse-Q agrees <=9.46e-7/component, supporting the same convention on directly shared limb joints. The full native per-instance palette producer/motion tree is not reconstructed. Do not substitute source different-rig inverse-binds blindly or call this a new native bind-policy proof.

Cached native algebra references (no new native bodies requested):
native-00c9a9b0.c.txt loops source skeleton and applies parent transforms; native-00c44f20.c.txt reads source48B local records; native-00ac5770.c.txt is the retained parent/local quaternion+translation composition helper. Shader dp4 palette consumption is directly proven. End-to-end native producer/runtime mapping remains outside this bounded correction.

## Additive OACPL01 companion

almain-male-palette-corrections.oacpl:736B
SHA256 6ebc4821b5e2dcfbea1d5bf79fd27754820c57b3a7b73611a31acbbab242b24f.

Binds the UNMODIFIED15,030,356B Almain_Male character.bin:
ede399d687bcbbc9d1534a208e81a13b9b3785a6f2b52dc25b28f78f36a484a4.

All fields little-endian. Header64:
0 magic8 OACPL01 plus null;
8u32version1;12basePartCount17;16correctionCount2;
20recordBytes128;24paletteRecordBytes32;28reserved0;
32basePackSHA256raw32B.

Record128:
0u32partIndex;4FAB;8assembly;
12sourceCount;16currentCapacity;20vertexCount;24indexCount;28flags0;
32SHA256(FULL original current-capacity palette),32B;
64SHA256(replacement PREFIX payload),32B;
96SHA256(source FAB),32B.
Immediately followed by sourceCount*32B replacement records in existing <I7f> layout: u32rigJoint,float4inverseQ,float3inverseT.

Part2: record@64,payload@192,sourceCount1,currentCapacity18,payload32B.
Part5: record@224,payload@352,sourceCount12,currentCapacity12,payload384B.
Exact EOF736 required. Detailed hashes/maps/provenance in palette-correction-manifest.json.

Root integration: validate BOTH optional companions and ALL records against original preparse pack before ANY mutation. Validate counts, part capacity, all original palette/payload hashes and replacement finite/unitQ/joint bounds; require current positive-weight indices <sourceCount. Prepare both corrections; then copy ONLY sourceCount*32 bytes at the existing palette location. Preserve original capacity/header and unused hip records1..17. No resize, changed vertex bytes, weights, indices, animation, skin matrices or rig-policy changes. If any check fails, apply neither normals nor palettes. Existing52B files stay byte-identical.

## Validation and limitations

Independent stdlib verify_palette_corrections.py reconstructs source bone hashes/ancestor mapping/common-rig inverse-rest without importing exporter code. PASS36bad-size/hash/payload/header cases rejected. Private-memory test allows416prefixbytes, changes291bytes, keeps every other byte of the15MB pack identical; original capacities remain18/12.

skin_pose_probe.exe links the actual current oa_character.c; baseline and corrected calls both passed. Bone-world Q/T arrays are byte-identical between variants; all unaffected part palette rows and hip-unused rows1..17 are byte-identical. pose-displacement-receipt.json pins production source, pack and output hashes. Displacement analysis accumulates float64 over actual Cfloat32 matrices and original pack vertices/weights; it is a controlled current-code comparison, not native GPU replay or exact DXBC float rounding emulation.

Current source clips/binding and facial ancestor approximation remain preview policy. No general animation tuning, native motion-tree reconstruction, new clips, skin-weight changes, source edits or live promotions are included.
