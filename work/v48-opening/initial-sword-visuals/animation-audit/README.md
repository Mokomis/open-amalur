# Source container clip1789841 — native offline decode

Existing tool reused: work/v20-char/clip-bake.exe, SHAaa597dd00fcf06dcdaf1cb5755fdc5a7383b71f1ff684d9e4ddf976cd4b33d58.
Reviewed source copied as clip_bake-reviewed.cpp (SHA4d96e2f42ff74b3f10bfcb84f38314d9fbdd8611285480b01aadb57785c18e68).
It privately maps original koa.exe sections at0x400000 and invokes only Edge decoder0111bf10. No PE entrypoint/import resolution/game launch/UI/device access.
Exact invocation, all input hashes, stdout/exit0 and output SHA are in decode-command.json. Existing files unchanged.

## Decoded output

1789841-native-local-trs.bin:261804bytes, header(u32joints54,u32frames101,f32fps29.999998092651367), then101*54 records of12float32 Qxyzw,Txyzw,Sxyzw.
Frame-major, source skeleton bone-index order,48B perbone. No bone-name reorder, quaternion conjugation/normalization or generated poses.
All S.xyz values are bit-exact1 across every bone and frame.
decoded-rig-contract.json seals byte offsets, ordering, parent/namehash mapping and quaternion convention.

Source clip payload10128bytes plus8B container and1 trailing byte, tag50AE; outerword3333; float+4=3.3329999446868896 (duration candidate), fps+8=29.999998092651367.
54 declared clip joints;101 frames;3 frame-table entries. Data sets(0,52),(53,46); final(100,0) is zero-byte endpoint sentinel. Existing helper's final sample uses data set1,idx46,alpha1.
No new native duration consumer or actual elapsed-playback timing was proved; frame100/fps=3.3333335453 differs slightly from source float+4.

## Track/bone proof

FAB1789717 footer references motion-set1789863; that source references animation1789841 atfile40/1060.
Source skeleton has54bones. Native0111bf10 reads explicit channel-index lists and passes them to scatter decoders:
-25 dynamic rotation tracks;
-10 dynamic translation tracks;
-2 static translation tracks(bones11,19);
-53 static scale tracks(all bones except48);
-no static rotation/dynamic scale/user channels.
The exact lists/offsets are in track-mapping-source.json and animation-manifest.json.
01112400/01112990 scatter quaternion to out[boneIndex*48];011141e0/011142a0 scatter vectors to matching component offset.
All indices are valid0..53, without duplicate indices within each list.
Every unanimated component is byte-identical to the same source bind slot across all101frames; static tracks are constant across allframes. All output floats finite.

## Samples and rest deltas

sample-frame-000.json, sample-frame-050.json, sample-frame-100.json contain all54 localQ/T/S records plus derived global matrices; bone-rest-deltas.json has allbone rest differences; frame-summary.csv covers all101samples.
Frame0 is NOT the FAB rest pose: static T11/19 differ by~78.46/99.63 source units (cm in current scene conventions), while largest normalized angular delta is only.007878degrees (native compression/quantization).
End frame100 local maximum translation delta362.82373 atbone49, angular delta124.30245degrees atbone38.
Sword rigid bone51 starts with its rest local T but later reaches165.318cm translation delta; woodplank bone53 reaches~95.005degree rotation delta byend.
These are decoded sample facts, not a choice of initial actor pose.

Quaternion/math: output remains rawEdge/sourceQ.00adcd40 copies that Q into runtimeTQS;00ac4b10 constructs R(conjugate(rawQ)). A standard Hamilton consumer conjugates xyz exactly once, then uses parent*local hierarchy. Native rawQ composition00ac5770 is childRaw*parentRaw. See decoded-rig-contract.json and previous native-rigid-audit.

## Remaining boundaries

No default/initial motion-set state selected. No claim the starting closed door should use rest, frame0 or CloseIdle. Source state-selection remains separate.
No active animation blending, rootmotion policy, IK, custom-bone callbacks, inverse-bind palette or skin renderer was added.
Raw native quaternions have norm drift up to~.000242; output floats retained unchanged, angular statistics normalize only for comparisons.
Container stride60 attribute labels still inherit the prior character reader; actual container format22 input-layout certificate is pending, explicitly marked in decoded-rig-contract.json. Raw vertex fields remain preserved.
Only this new animation-audit folder was written. No older candidate, core, default, source asset, database or Mac mirror changed.

## Input-layout receipt received

Actual standalone sword draw67406/pipeline13252 VS351/PS352 certifies stride48: float3@0,float2@12,SNORM16x4@20/28/36,UNORM8x4@44. Source receipt: work/v49-character-create/character-gloss-audit/pipeline-13252.json (lighting agent). Container60 remains unproved by that draw.
T.w/S.w vary0..1 in decoded samples; preserve raw words but do not reinterpret them as runtimeTQS flags. Native00adcd40 derives flags and consumes scale.xyz.
