# Model419041 LOD/material audit: bounded result

2026-11-06. Model for_flora_twist01 only. Existing source/capture/decompilation reused. Exactly10native function bodies were inspected in this audit; their raw exported pseudocode is retained. No GPU/UI/game operations, database changes, installs or shared source/assets edits. Only missing419041.fab_bxml was extracted with the existing installed unpacker into this NEW audit directory. Existing stream input was copied.

## Concrete findings

The native right-tree pose is(4757.779296875,−86588.828125,5833.80712890625). The same captured draw69083 view block gives camera eye(8591.9326171875,−87036.03125,6493.06640625). Their Euclidean pose distance is3916.036914units, approximately39.16m, NOT13k units. XY distance3860.145375. The source cached part sphere-surface distances are2921.68..3235.95units. Every one of these simple distances lies below the authored first4000cut. Therefore this right tree provides no numeric contradiction requiring an invented FOV/pixelScale correction.

Original trunkasm1 has320triangles; branchasm2 has29. Cached source picks trunk5(114triangles),branch6(17),leaf8(60). That is a real near-versus-far prototype selection difference. Original leaf buffer matches assemblies0/7, which are byte-identical; assembly0 belongs to near group1 and7 to midgroup2. Trunk1 and branch2 resolve the actual combined prototype to near group1. A triangle-count-only rule cannot select among leaf0/7/8 because all have60triangles.

The foliage agent independently decoded authored groups and buffer identity. Its peer fixture is copied with provenance, not re-decoded here. Colour groups are1:[0,1,2],threshold4000;2:[3,4,7],threshold9000;3:[5,6,8],threshold15000;4:[5,6,8],threshold1e7. Group0 has no colour elements and a secondary list; groups5..8 are separate mode groups and must not be added to ordinary colour LODs merely because they contain assemblies. Secondary lists are not another visible canopy list.

## Material correction to the initial premise

The earlier proposed419060→359202 remap was a mistaken native draw association and must not be implemented. The cached instance leaf material is559590(for_flora_treeleafsaplinggreen); original draw69083 cb0 first32bytes are(.978120029,600,0,0;0,10,0,0), consistent with that sapling material. The FAB defaults use419060 for leaf elements0/7/8, while the space caches an explicit instance override559590. Changing LOD must preserve the per-instance override rather than replacing it with the FAB default.

The full texture descriptor correlation belongs to the foliage agent's ongoing work; matching shader controls alone is not proof of every texture binding. This audit does not claim a native semantic asset-ID remap from419060 to another global material.

Native material fixup FUN_00cae870 resolves element materialID through00a70b80 into a runtime material handle and selects rendering classification. The inspected body does not contain a hardcoded419060/359202/559590 substitution. FabInstanceRender vf6 also accesses per-instance group data before queueing its render command, but the complete serialized space-override consumer was not established within the10-function bound.

## Native distance evidence and limits

FabInstanceRender constructor/initialization00d35150 reads FAB runtime group thresholds at+8c/+ac/+cc/+ec, takes their maximum and writes its square to instance+1b8. FUN_00caec90 retrieves the current camera through019fdff0, reads an instance point through transform member+124 and a camera vector at+0xd8, then compares sum(deltaXYZ²) against instance+1b8. The corresponding x86 code is preserved, including helper-call arguments and the squared comparison. There is no explicit FOV/pixelScale or radius subtraction in this whole-instance distance gate.

This is a whole-instance far-distance gate, NOT a proven per-group4000/9000boundary consumer. The point/vector helper semantics and every mode/scale bias were not fully typed here. Do not present this as a complete portable native LOD selector. The actual right-tree distance calculation above is independently proven from captured camera and world matrices, and is sufficient to show why the near group is numerically plausible.

A tempting distance/FOV routine was rejected: FabMgrRender00cf4780 subtracts sphere radius, uses a projected factor and computes a logarithmic request, but ends in per-texture mip requests through00cd89a0. It is texture streaming, not model assembly LOD selection. Reusing it as the model LOD metric would be unsupported.

The10inspected functions are00d1b520,00d2d9e0,00cae870,00d0a9c0,00d3ce70,00cf4780,00d35150,00d32260,00ce2b00,00caec90. Several are lifecycle/wrapper candidates that did not answer the metric question; they are retained to make the bounded stopping point explicit.

## Minimal parser contract

1. Preserve authored visual groups/elements from nonstreamable FAB metadata alongside geometry assemblies. A cached space record's asm_index is the cached prototype, not a universal runtime LOD choice.
2. Preserve instance identity/pose/scale and per-part material overrides. For419041, cached5/6/8 correspond to trunk/branch/leaf; a near-group expansion should use1/2/0 while preserving bark343549,branch489469,leaf559590. Match overrides via a proven part/base-material association; do not substitute the FAB default leaf419060.
3. Retain the authored4000/9000/15000/1e7ranges and separate render modes. Do not infer LOD by triangle count or emit every group/secondary list.
4. For this exact reference fixture, assert the known native near prototype[0,1,2] at the measured pose. A general runtime distance selector still needs the remaining native group consumer; don't silently invent a pixelScale multiplier or label plain Euclidean selection universally native.

This is a prototype/metadata correction, not a complete canopy fix. The foliage agent's leaf0versus8 comparison finds i^1vertex permutation with bit-identical UVs and only about.429cm localY displacement; root's finest-detail diagnostic also did not fix canopy shape. Trunk/branch near detail is supported, but the thin-canopy discrepancy should remain open for material/coverage/instance evidence rather than being attributed entirely to leafLOD.

## Inputs and evidence

419041.fab_bxml4279bytes SHA7ad76685c67843ba222d43bac75d5f40a28133d490f6afe4402e5f92d408168d. OnlyDATA_0contains this FAB; initial/patch archive listings contain no419041entries. Stream56834bytes SHAd11714114b45dc477f9d4d8acd18125a6db1ef58f4165f99681f2746a8967072. Geometry parser consumes10assemblies and retains all bounds/triangle counts/raw assembly bytes in stream-assemblies.json.

right-tree-distance.json records captured eye/pose/material constants and cached sphere distances. peer-right-tree-prototype-contract.json is copied from the foliage agent's instance-audit evidence. native-functions.json and distance-gate-assembly.txt retain the bounded native code evidence. No shared parser implementation was changed.
