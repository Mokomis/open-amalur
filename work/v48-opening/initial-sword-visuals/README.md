# Initial sword and container visuals â€” staging only

Authoritative directory: C:\Users\rwill\Documents\Opem Amalur\work\v48-opening\initial-sword-visuals.
No live/default/frozen preview files edited; no game/input/GPU/database actions or Mac mirror.

## Outputs

- placed-container-rigid-candidate/world/: current-reader OAWI index, OARGIDX1 registry, indexed OARGEO1 r-1_0.bin, four-row MATS/OANM001 bank and14 local portable OATX textures.17 supported rigid parts /1370 triangles. QUARANTINED rest-pose candidate, not validated active pose.
- source-local/fab-1789717.bin: all21 container parts /2298tri, component-local positions. source-local/fab-1880465.bin: all604 sword triangles, unplaced. These preserve original triangle occurrence order but are not assembled/material-complete world packs.
- source-bind-candidate/:18 rigid container parts /1980tri, including unsupported sword material, plus sole604tri sword node. Same explicit candidate transform assumptions below.
- raw-meshes/{FAB}/assembly-*.vb48 or vb60 / *.u16: byte-exact original vertices/indices, including all bone/weight/SNORM fourth components.
- material-contracts.json: all5 exact source materials, shader IDs, typed/hash parameters, alpha/cull headers, source texture slots and bytes.
- texture-stage-manifest.json:18 source2D maps with full nativeBC chains and explicit <=512 authored-tail RGBA preview profile; one separate cube carrier.19,574,948 nativeBC bytes;15,734,244 portable bytes. No resizing/generated mips or original residency claim.
- textures-native-bc/, textures-portable-512/, textures-cube-native/asset-505647.keen: asset-named outputs, independent of existing world IDs.
- family11-external-integration/: existing source-backed glassmetalprobe contract/GLSL/probe pack copied intact. Bind source505647 for this object; pack also contains other opening probes.
- *-fab-metadata.json, *-groups.json: source parent indices/TRS/descriptor/remap bytes and bounds/groups. Existing generic reader's standard-Hamilton candidate matrices are not used.
- *-conjugate-bind-candidate.json: matrices actually used here, candidate only.
- animation-source-manifest.json: raw motion-set1789863 and one aligned animation identity1789841. Zero animation clips decoded/applied.
- visual-stage-manifest.json, validation.json, evidence-manifest.json: complete per-part provenance, omissions, bounds, receipts.
- stage_visual_geometry.py / stage_visual_textures.py: reproducible scripts restricted to this folder.

## Source placement

Container FAB1789717 wos_start_door01 is PartRendering+0x14 of Type1789987 / GOR1790948 MQ01_Start_Door_01, instance1789992 in SPACE1417252.
T=(-1666.24658203125,2861.4287109375,40.57246398925781), Q=(0,0,.718055784702301,.6959856152534485), S=(1,1,1), GOR flags30.
GOR flags30 are provenance, not reinterpreted as scene-bounds/pass flags.
Source GOR/native Type/acquisition evidence is in ../initial-sword-audit/initial-sword-source-contract.json.

Sword Type1360571 references FAB1880465 at rendering+18/+1c/+20; direct-world+14=0. No loose-world sword position, socket or equipment scale role is invented.

Container stream SHA7a87a8ff5c353cbdb7b01b8c3e84fe36cdcd0459f66145f5b6135408766eea85.
Sword stream SHA4958407eb71e4cd9ac830acf3a9ce26d00aba287f412a2ed061b9babf1a0a598.

## Bones, bounds and withheld parts

Container:54bones,21parts,2161vertices,2298tri,stride60.
Sword:4bones,1part,424vertices,604tri,stride48.
Only authored group1 is populated: container0..20 threshold25000, sword0 threshold5000; other8 groups empty.

Container source component-local bounds min(-152.21331787109375,-41.64279556274414,-157.4730224609375), max(174.86019897460938,160.1680450439453,358.3076477050781).
Sword source-local min(-11.07607650756836,-4.826735973358154,-107.94999694824219), max(15.082925796508789,5.825641632080078,60.95643615722656).
Per-part all/IB-used bounds and source descriptor center/radius remain separate.

Container0..17 have descriptor bone>=0, no remaps, all used vertex indices=(0,0,0,0), weights=(32767,0,0,0). This proves source single-node classification, not active pose.
18/19/20 have bone=-1, remap counts6/4/4, genuine blended weights;70/128/120tri withheld.
Genuine decoder gap: remap52B rows are not in the skeleton reader's Q/T vector order. First vectors such as(-103.73,16.66,-2.01) produce invalid quaternion norms. Raw bytes/boneIDs retained; no corrected order/inverse bind/skinning guessed.

Candidate recipe:
L_b=T(sourceT)*R(conjugate(sourceQ))*S(sourceS);
W_b=W_parent*L_b;
P_candidate=GOR_TQS*W_descriptorBone*P_source.
All source scales here are1. NO inverse-bind matrix is applied.
This hierarchy/descriptor single-node interpretation still needs native animation/palette confirmation before claiming original pose. Earlier conjugate actor quaternion evidence does not certify complete animated palette semantics.
Candidate N/T/B use that same unit-scale linear transform. UV0/RGBA remain byte-identical; UV1 duplicates UV0 under existing single-UV static convention. Raw .w and skin words remain in full raw VBs.

## Materials

| Native MID | Source shader | Current family | Container triangles |
| --- | --- | --- | --- |
|459142|dot3|1|woodbase24|
|464123|dot3|1|woodplanks80|
|464114|glassmetalprobe|11|metaltrim220|
|737050|dot3alpha|1|skeleton1364 total,1046 rigid retained|
|1880463|characterhardlight545212|unsupported here|container sword610; also all604 standalone sword|

No selected parts use families3/4.
Skeleton independent alpha737046 GREEN, cutoff128/255, source cull2 BACK. No alpha bake or tuned fallback.
Exact supported mappings use local IDs independent of old world. Family11 requires current authored EnvironmentTint and exact cube505647; no outdoor constants/lighting.bin provided.
Parent's separate initial-sword-material-audit owns characterhardlight; this stage does not substitute dot3.

## Animation seed and next smallest contract

Footer references motion-set1789863 WOS_Start_Door01.
First5 aligned catalog keys: open577232, close998527, open-idle3475629, Close-Idle4514355, Loot651734.
Aligned fields40/1060 both reference animation1789841 WOS_Start_Door01_anim, exact10137B source staged.
These are source references, not decoded state/clip counts. Earlier *-animation-reference-audit.json raw scans include incidental numeric matches; animation-source-manifest.json supersedes them as the bounded reference ledger.

Next smallest animated-render blocker: exact descriptor-remap/bind-palette equation (including52B vector order/inverse role), then sample1789841 and select native initial motion-set state. That supplies3 blended parts and source-backed active pose for rigid parts.
Existing group-reader anchors00d400d0/00d196c0/00cccc50/00ccd0b0 are inherited evidence, not a new animation semantics proof.

## Validation / integration

CPU PASS22assemblies /2902source triangles: complete stream consumption, assembly counts agree full referenced IB/VB, all indices valid, raw payload hashes preserved, source-local P/UV/RGBA bytes unchanged, triangle occurrence order unchanged, OARGEO reparse identity, candidate UV/RGBA identity.
1370 supported+928 withheld=2298container triangles.
BCpayload hashes and scalar-vs-Pillow RGBA sample receipts retained per mip; exact OATX lengths reparse.

Reader-compatible candidate has no original collision, animation, active-pose validation, new material fallback or environment globals. Root must review quarantined hierarchy/probe dependencies and remap IDs before integration; existing assets remain unchanged.

## Subsequent native certificate

See native-rigid-audit/REPORT.md and INITIAL_STATE_LIMIT.md. The native rest hierarchy and rigid bone selector are now recovered; the52B remap vector order is narrowed to runtime TQS48+boneID. This supersedes the earlier field-order blocker above, but active initial pose/animation sampling remain unresolved. Existing candidate bytes are unchanged and remain explicitly native-rest previews.
