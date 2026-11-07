# Intro corpse-limb audit

Finding: the foreground long orange limbs in the owner's retained frame belong to an original static corpse-pile mesh. No current scale multiplier, skin palette, remapped joint or animated limb deformation was found for those limbs. Do not resize them on this evidence.

## Actual visible source

Retained frame: work/v50-character-complete/ui-integration/live-before-v50-preview-promotion.png,1536x864. Camera and matrix are frozen in corpse-pixel-hits.json (camera JSON SHA c1f4d08ac0e8b968ec874f80c97be6bc779d7d91681dceaf72161ea17ce3e34d).

CPU picks at (1450,375),(1395,353),(1330,345),(1480,400) all identify FAB1302074 wos_corpsepile01, assembly0, native MID442846 for_corpse, source84 record79, current r0_0.bin range36. Distances from the retained camera are 9.78–11.85m. This is opaque corpse geometry. The companion assembly1/MID1302073 is a separate source-authored pile surface at the same pose, not a second animated character.

Placed source T=(3870.76708984375,3977.60107421875,-313.3776550292969), Q=(0,0,-0.5220944285392761,0.8528876900672913), S=(1,1,1). Assembly0 has6957 IB-referenced vertices/5651 triangles. Its source stream SHA80ed7529ddcedc0147663de76ca676fed7f3b73c736b375424ce55be3c976dad.

Left-side picks(170,285)/(100,285) identify assembly1 of the same FAB at separate source poses1315/1325. Pixel280,280 instead hits the authored room rock shell; not every apparently corpse-adjacent pixel is a body.

## Mesh, bind and palette

The foreground FAB has four source bones, each raw Q=(0,0,0,1),T.xyz=(0,0,0),S.xyz=(1,1,1). Assembly0 references bone1; assembly1 bone2. Both have zero remaps. All source parents are root/children of root, so the global bind matrices are also identity. This result is algebraic and does not depend on the old importer's speculative nonidentity matrix convention.

Both VBs are stride48 rigid P0/UV12/N20/T28/B36/RGBA44. They do not carry weighted joints or skin weights. Their piled/contorted anatomy is already present in the source vertex positions. Neither the new creator skinning palettes nor the54-bone source initial-door/container animation produces these foreground limbs.

The static scene producer applies exactly conjugated source rotation and source unit scale, then source translation. The current foreground indexed vertex sequence matches that operation with 0.0cm float32 position error. UV and RGBA are bit-exact. Thus the port has not elongated this mesh relative to its shipped source vertices.

For context only: source standalone corpse variants447783/447791 have longest bounds207.16cm/201.56cm; their unit system is not globally inflated. The selected wos_corpsepile01 is a multi-body, whole-pile mesh with1064.73x876.89x368.21cm bounds. Whole-pile bounds are not individual arm/anatomical measurements.

## Broader retained corpse audit

Seven corpse-named FABs were checked:447783,447784,447791,1302074,1302251,1520492,1558823. Across all stored source intervals,227 render ranges/42 distinct full TQS poses/662560 submitted range triangles retain exact source-derived positions, UV and RGBA. These totals include mutually exclusive ranges and remote cinematic props; they are not a simultaneous visible corpse count.

Every checked source bone is identity, every remap list empty, and every retained placement unit-scale. Model/assembly bounds, exact source SHA, per-range provenance and current-file hashes are in source-current-validation.json. The three current world files were rehashed after the audit and remain unchanged.

## Limits and recommendation

The limbs do read visually long in this frame. Source identity rules out a newly introduced length/skin-weight/bone-scale defect for the sampled foreground pile. It does not prove that current camera perspective, materials, lighting, culling or source-part admission visually matches the original opening frame.

No cached original opening-room screenshot or matching original GPU pose capture was identified in the bounded existing v48/v49 evidence inventory. The retained native draw captures used elsewhere are outdoor creator/bridge evidence, not an opening-room comparison. No original launch/input/capture was performed.

Keep the authored mesh and scale. If the owner still finds the silhouette wrong after the new creator renderer lands, the next useful check is a matched original opening-room camera/visible-part comparison, not a global corpse resize. The initial animated door/container remains a separate source-posed object and cannot establish native corpse-pile visual parity.

Evidence scripts only; no live/default/source assets or databases changed.
