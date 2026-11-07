# Open Amalur v45 foliage and scene-fidelity work

Current build is v0.36 R3. See [final visual review](FINAL_VISUAL_REVIEW.md) for the three-band original comparison, corrected roots/bridge props/tree shadows, actual Android validation and the remaining distant-canopy visibility/LOD blocker.

All prior evidence, experiments and source assets remain preserved. The authoritative live working folder is on Windows; this Mac folder mirrors evidence and the private incremental recovery kit. Waterfall styling is an intentional preserved difference.

[Android validation](android-validation/VALIDATION.json) · [Top](top-final.png) · [Middle](middle-final.png) · [Bottom](bottom-final.png)

---

# v45 background foliage correction (working state, 2026-11-06)

The custom engine is active. Android remains v0.35 R4/code37; current Windows source is newer and both Windows and ARM64 compilation pass. Do not interpret v44 source hashes as the current working source. See renderer-build.json for current source/executable/library hashes. Existing v035 source/exe/library and reference properties are preserved in before/; original native-only textures are in before-world/.

## Confirmed and implemented

Native recovered leaf attributes previously covered only18shop/bridge cells. Existing distant leaf triangles used legacy surface normals and masks. At pixel(800,150), original and current triangles coincide within0.00469cm, but the legacy normal is nearly vertical while the native radial normal is horizontal. This is a demonstrated shading fault, independent of missing trees.

A new optional leaf-only stream covers175visible cells and51,831existing leaf triangles (7,989,460bytes). It uses source position/UV matched attributes;48,013new joins had0unmatched/0ambiguous matches. No new tree instances or positions were invented. The sidecars replace matching leaf materials in color, depth, AO and shadow passes while preserving ordinary body/terrain LODs. No full-fine geometry promotion was deployed. The four native leaf texture residency replacements are also deployed, but decoded mip differences were small and are not claimed to explain the major canopy gap.

Current Windows reference capture: bridge-native-leaves-expanded.png, runtime native-leaves-expanded-runtime.log. Fully loaded203cells,1,751draws,666,237triangles,175native_leaf_cells,0forced_leaf_cells,queue0. At(800,150), sum of absolute RGB-channel differences from original fell222->82; at(980,210),75->49. These are two selected pixel checks, not whole-image parity scores. Visual canopy shading improved but still differs.

## Remaining differences and ruled-out leads

At(500,35), original bark draw69284/FAB343974 is absent even from our all-fine scene geometry. Native object translation(-880.2670,-76023.8594,5371.8164) and captured matrix were verified independently. A scan of460,887raw84-byte render records across170cached spaces did not recover51unmatched native tree poses. The producer remains unknown. Do not insert captured one-camera trees as if the general source were recovered.

Forcing finest cutouts added geometry but did not fix the prominent discrepancy. Native leaf assembly swaps are mostly identical (all16 tested UV/normal/RGBA/index sets equivalent; two have a0.429cmposition delta). Trunk/branch authored LOD mismatches are real but not demonstrated to explain canopy coverage. Raw authored transform vs centered-scale recipe also has a separate28cmoffset on one known leaf; keep this separate from missing-instance recovery.

Residual leaf brightness needs stage-by-stage reference data. A new isolated GFXReconstruct1.0.5attachment-dump replayer built and passed version/help checks. One existing original capture replay selects15stage checkpoints with200MiBbudget; no original game/Steam launch is required. Read replay-dump-capability/REPORT.md and later execution receipts before quoting results. Point-light sphere audit sample-point-light-coverage.json found no authored light sphere overlaps at any of the three sampled native world positions, ruling out extra authored point lights for those specific samples only.

## Next validation

Inspect actual native Gbuffers/AO/combine/fog/LUT output before additional shading changes. Then package one batched Android update and verify optional-stream loading, walking/context lifecycle and resource cost. No new tablet FPS is measured yet. Preserve saves/settings/key. Do not rerun old desktop asset preparation over this overlay. Original-engine/FEX path remains paused.

## Owner visual direction, 2026-11-06

Continue foliage brightness, then missing-tree producer, then compare top/middle/bottom thirds of matched original imagery. Explicit examples: missing bridge-side objects and pronounced moss on roots left of tree enteringwater. Waterfalls differ from original and OWNER PREFERS CURRENT WATERFALLS: intentional difference, document only; no waterfall visual/material/geometry changes. No questions/checkpoint stops while owner asleep.
