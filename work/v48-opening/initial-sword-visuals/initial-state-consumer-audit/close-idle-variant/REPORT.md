# Close Idle selected variant and first pose — resolved

For ordinary fresh-container initialization, source MotionSet1789863 slot3 Close Idle4514355 deterministically selects variant0 of1 and holds source clip1789841 at sampletime0. Therefore its geometric pose is the already-decoded clipframe0, not FABrest.

## Provider / boundaries

Native factory registration00a1aac0 identifies typeID013e8f54 as RandomMotionChooser. Provider vtable017228d0 has vf4=00c8ff30; PE sixpointer sequence is preserved in native-provider-PE.json.
Vf3=00a1b1d0 calls00a1b0c0, reading integer weightcount and count*4 bytes. All5source slots contain onevariant, chooser weight[1];00d1d5d0 invokes chooser with excludedprevious=-1. Output initializesindex0; nootherindex exists, so no randompose ambiguity.

The5 chooser offsets are565,1036,1359,1709,1907. Typed chooser tails make nextslot offsets28,577,1048,1371,1721 and consume filethrough1919; lastbyte0 is nativeMotionSet+1c.
CloseIdle slot begins1371, variant1375, clipasset1789841@1383. Earlier aligned-only scans missed this unaligned reference; do not reuse their 'two references' count as acomplete animation catalogue.

## Typed fields and actual time formula

00d42ad0 loads sourceprefix arrays. Prefix child loaders00d34ab0/00ce0570 read count+8B segmentpairs;00d3cc20/00a5d7b0 read childarrays12B/44B through00a5d4c0/00a5d5d0, allowing exact nextfield offsets. Event/othermiddledata is preservedopaque, not guessed.

Runtime start array: count+24 / pointer+28.
Runtime signed-delta array: count+30 / pointer+34.
Source CloseIdle:
-clip1789841, segment pair(0,3333);
-start count@1535=1, value@1539=0;
-delta count@1543=1, signedvalue@1547=0.

Crosscheck source motions:
Open: start0,delta3333.
Close: start3333,delta-3333.
OpenIdle: start3333,delta0.
CloseIdle: start0,delta0.

This is not just value-pattern inference:00c63d80 explicitly computes
sampleTime = start[clip] + trunc(signedDelta[clip] * (clampedElapsed-segmentStart) / segmentLength).
00c8f810/00ce6b70 call it during leafmotion updates;00cb3700/00d0ea90 place resulting times in nativeEdge command data.
For CloseIdle, start0+delta0 forces sampleTime0 for every phase. The source segment length3333 is nonzero.
DAT014c61a8 has PEdefault0; its runtimeinitializer/value was not audited, so no fittedtimebase is assumed. The zero-time result does not depend on a positive runtime timebase's particular value.

## Concrete staged pose

close-idle-native-local-trs.bin:
u32joints54,u32frames1,f32fps29.999998092651367, then54records of12float32 Qxyzw,Txyzw,Sxyzw.
Its2592B posepayload is byte-exact to native decoded clipframe0. No interpolation, normalization, retargeting or newweights.
Source rawEdgeQ is unchanged; renderer applies R(conjugateQ) exactlyonce. Scale.xyz are all1.
Previous audit showed this pose differs from FABrest at static translations11/19 (max99.63 sourceunits), so FABrest is not an equivalent substitute.

## Conditions retained

The previous source/native initializer proves ordinarydefault requests CloseIdle; deathbranch Object+10c bit7 and optional MotionSetoverride+1B4 remain separate. Freshconstructor overrides0; later scripts/statechanges were not executed or audited here.
This is a source-backed ordinary-default pose candidate, not proof of any currently paused originalactor/save state.
No existingreceipt,geometry,sourceasset,core/default,game/UI/save/database orMac mirror changed.
