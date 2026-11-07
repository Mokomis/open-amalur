# Initial opening-container motion consumer

Result: the source-backed ordinary initialization requests MotionTree351502 Door_Std's default motion **Close Idle4514355**. This is a real native selector, separate from TypeAnimation scalar0.
It does NOT yet prove that the original initial geometry is FABrest or sampled clipframe0. No pose was promoted.

## Exact source/native link

FAB1789717 footer file6333 contains MotionSet1789863; file6369 contains MotionTree351502.
Exact original Door_Std source was extracted into source-inputs only. Its last8bytes at1694/1698 are u32 4514355 and float.30000001192092896.

MotionTree serializer00d40390 reads its final4B into+D8 and next4B into+DC. Thus the source default field+D8 is exactlyCloseIdle, not a name-based inference.
00cb45f0 binds the MotionTree and copies tree+D8 into MotionTreeInstance+B0.
00f34e10 (normal PartAnimation activation) verifies motiongroups/tree then calls00d3fff0.
00d3fff0 reads FabInstance+F4 defaultkey and requests it through00d3ec40.
00ce71d0 /00c8af20 resolve the requested key in active MotionSets. The supplied source MotionSet's dictionary=[open577232,close998527,open idle3475629,Close Idle4514355,Loot651734]; default finds slot3 of5.
00c8af20 checks optional instance override MotionSet+1B4 first. The fresh constructor sets it0; later override writes were not audited.

The adjacent source+D C float.3 is preserved without calling it a fade/time or fitting any pose.

## Conditions and scalar0

00f594a0 PartAnimation::vf8 uses normal initialization unless Object+10c bit7 is set. That special branch checks catalog death motions Death_Idle_Loop12559562,death_idle5067038,death idle4609133. Its runtime flag was not observed for this new actor; source Type flags must not be substituted blindly for Object flags.
The logical-default proof is therefore the ordinary fresh-object path; no unconditional active-state claim.

Compiled Type1789987 PartAnimation kind4 is at actualfile64; scalar+4/file68 is0.
00ef69a0 copies it toPartAnimation+24. No read of that field occurs in the traced activation/defaultkey path; its general semantic name is still unassigned. Integer0 is not evidence of clipframe0.

## Exact remaining blocker

MotionSet1789863 slot3's selected variant/segment has not been decoded. Native00d47350 reads slotvariant arrays via00d42ad0 and constructs a polymorphic MotionVariantChooser.00d1d5d0 calls chooser virtual+10 when explicit indices=-1.
The source slot3's variable-length record boundary, variant/clip range and startup time are the next smallest inputs. Without them, the correct decoded sample of1789841 cannot be selected. Shared animation-ID byte matches at40/1060 are insufficient to assign idle state pose.

The inspected path now pins the loader and consumer, rather than leaving the entire initial selector unknown. Rest, frame0 and CloseIdle remain distinct: CloseIdle is a logicalmotion request; rest/frame0 are geometric samples.
Native offline clip bank remains available under ../animation-audit; that audit proved frame0 differs from FABrest in bones11/19.

## Scope

Cached native export/source bytes only. No original game launch, UI/input/save/RPM activity, live/core/default edits or database modifications.
Exact bodies, source tree and JSON offsets/hashes preserved here. Some cached thiscall pseudocode omitsECX/hidden outputs, so no new machine-code ABI certificate is claimed.
All earlier geometry/clip candidates remain unchanged and quarantined.
