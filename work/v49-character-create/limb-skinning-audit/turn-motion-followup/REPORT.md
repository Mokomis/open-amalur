# Turn motion: bounded source/math check

The current comment that a turn clip "carries no net rotation" is too broad. It is exact for static_root/joint0, not BIP01/joint1 or pelvis/joint2.

Measured staged clip endpoints, with current local quaternion normalization/FK and facing0:
| Clip | BIP01 net world yaw | Pelvis net world yaw | BIP01/pelvis translation |
|---|---:|---:|---|
|17 Left90 EnterRun |-18.6121deg |-18.1965deg |XY0,Z-12.710403cm |
|18 Right90 EnterRun |-16.0356deg |-15.6312deg |XY0,Z-12.710403cm |
|19 Right180 EnterRun |-17.2390deg |-16.8345deg |XY0,Z-12.710915cm |

World yaw here means yaw about global Z of Qframe_world * inverse(Qstart_world), not an assumed mesh forward-axis projection. static_root stays exactly identical in all frames. No accumulated90/180degree rotation is present there.

Pelvis transient yaw ranges relative to clip start:
17: -25.9226..+32.8120deg;
18: -56.6618..+4.0973deg;
19: -102.7139..0deg.
These are real skeletal turns/posture changes, not zero-motion clips.

The existing loop_entry whole-joint quaternion score chooses run clip2/frame0 after all3turns. Relative to that RUN endpoint convention, pelvis endpoint yaw differs only -1.36355deg/+1.20328deg/approximately0deg; endpoint translation differs Z0.000511cm/0.000511cm/0cm. Thus most start-to-end change reflects entering a different run posture. No distinct parser/endpoint fault was found.

## Builder/baker

Every frame and joint of all3staged clips exactly equals conjugate(bakedQ) plus copied bakedXYZ translation. The builder does not explicitly strip root rotation/translation. The retained baker initializes the bind output, invokes the Edge decoder, then writes joint48B records. It does not persist its separate user-output buffer. Therefore these findings establish staged skeletal clip motion, not complete original native root trajectory/motion-tree behavior. No new native execution/body requests were made.

## Facing and double-turn assessment

oa_character_turn_step only returns an authored change to facing; android_scene applies it once to character.facing. oa_character_pose evaluates skeletal clip/FK without facing. oa_character_bones applies the facing Z rotation once to the resulting palette.

There is no duplicate application of the SAME facing rotation in those functions, nor a full90/180degree root trajectory in the staged clips that is automatically doubled. However, clip BIP01/pelvis transient rotation and authored facing rotation DO compose. The delay20%/rate40% timing is host policy, not recovered native motion-tree timing. Large transient posture parity therefore remains unresolved; the comment must not imply native proof or an exactly in-place pelvis. This report proposes no blend/timing patch.

## Slope/lean

Still explicitly unproven. oa_character_parse computes a quaternion midpoint between authored up/down or left/right clip samples, then builds a delta from that midpoint. oa_character_pose scales/applies the derived quaternion. The original reference pose/additive convention has not been recovered, exactly as the existing code comment says. Do not relabel this midpoint as native or invent a replacement blend from this check.

Evidence: turn-motion-receipt.json (source/baked/pack SHA, all endpoints and exact conversion checks), turn-to-run-endpoint-check.json (run-entry score/relative endpoints), audit_turn_motion.py and turn-motion.log. Source/core/clip/pack files remain unchanged.
