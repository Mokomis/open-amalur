# Source Close Idle container candidate — staging only

This is the ordinary-default source pose, replacing no prior files. The frozen native-rest candidate remains at ../placed-container-rigid-candidate.

## Ready for review

world/ contains:
-OAWI index.bin (one empty basecell; no c-file);
-OARGIDX1 region-index.bin (one row,4materials,defaultdistanceScale1);
-OARGEO1 r-1_0.bin (76B indexedvertices,48B authoredranges);
-materials.bin (4exact supportedrows) and native-materials.bin;
-14 portable OATX RGBA8 authored<=512mip-tail maps, byte-identical to earlier reviewed bank.

17rigid parts /1370triangles. Three remapped parts18/19/20(318tri) and HardLight part0(610tri) remain withheld, with no fallback.
Family11 still requires separate original cube505647 +current sourceEnvironmentTint; there is no outdoor/neutral fabricated light pack.

## Why frame0

../initial-state-consumer-audit/close-idle-variant/REPORT.md proves:
-MotionTree351502 source defaultCloseIdle4514355;
-one RandomMotionChooser variant withweight1;
-MotionSet1789863 slot3 refersclip1789841;
-native00c63d80 evaluates start0+signedDelta0, so thismotion holds sampletime0;
-staged localQ/T/S are exact output from nativeEdge decoder,54bones,allscale.xyz1.

Death branch Object+10c bit7 and optional MotionSetoverride+1B4 remain separate conditions. This candidate does not claim a currently paused originalactor/save state or execute any later script/timer.

## Transform and attributes

stage_closed_idle.py reuses only reviewed helper function definitions viaAST (never oldmain/builders).
Raw nativeEdgeQ is passed to matrix() once, which builds R(conjugateQ). Parent*local54bone hierarchy, then descriptor rigidbone, then exact sourceGOR TQS. No inverse bind in the rigid branch; no bone remapping/weights invented; no quaternion normalization.
frame0-global-bone-matrices.json gives all54matrices and actorTQS matrix.

Native source type22/stride60 attribute correspondence is backed by work/v49-character-create/vertex-contract-audit/REPORT.md and retained actual native declarations:
P0,jointsUINT8x4@12,weightsSNORM16x4@16,UV0float2@24,N/T/B SNORM16x4@32/40/48,RGBA8@56.
This is type/stride correspondence, not a captured rendering pipeline for this exact container.
No old normal-length scorer is used. N/T/B raw components decode max(-1,short/32767), then derived rigidrotation transforms. Full raw source fourth components/joints/weights remain preserved in ../raw-meshes.
Authored UV1stream1 is unavailable; compatibleOAWE UV1 duplicatesUV0 explicitly. Selectedfamilies1/11 useUV0; duplicate is not called authoredUV1.

## Validation and differences

All triangle index occurrence order,UV0/RGBA/nativeMID/flags,material andtexture bytes remain identical to the frozenrest candidate.
Only derivedP/N/T/B anddraw/registrybounds change.
Ranges retain source0..25000 interval,rawGOR Tanchor,sourceindex/material/flags,actor distanceScale1. Conservative radius andAABBs recomputed from all retained vertices.
Reader OARGEO reparse and pertriangle76B identity checks pass.
New world bounds:
min(-1709.3052978515625,2728.520263671875,33.19043731689453)
max(-1576.5396728515625,3011.66748046875,398.12225341796875).

Largest vertex shifts fromrest:
-assembly16/bone19:99.63167 sourceunits;
-assembly15/bone11:78.44393;
-others atmost.03270 in this supportedsubset.
These are the decodedclip's statictranslation differences, not manuallyfitted limbs.

manifest.json preserves allsourcehashes andperpartjoin/bounds; evidence-manifest.json seals thisnewfolder.
No core/default/live assets,earlier receipts,candidates,sourceinputs,DB,game/UI/save orMac mirror changed. Root remaps the isolatedbank and reviews before any merge.
