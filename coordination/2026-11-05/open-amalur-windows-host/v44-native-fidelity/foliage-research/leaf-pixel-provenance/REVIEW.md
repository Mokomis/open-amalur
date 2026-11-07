# Final-r2 dark-card pixel provenance

The large dark cards are not caused by retained legacy leaf materials0/6/8 at the inspected pixels. The raycast found a distinct source-backed material-state bug: native branch material489469, port row274, was rendered opaque instead of alpha-tested.

## Exact candidates

The offline raycast uses the recorded final-r2 camera VP,1536x864 pixel coordinates, current cell geometry and reference leaf wind palette. Expected fully loaded stream selection is LOD0 for these nearby candidates.

| Pixel | Candidate | Cell / LOD | UV | Relevant coverage |
|---|---|---|---|---|
|1155,236|274, native489469 treebranch|0,-14 /0|.947884,.110959|Raw alpha667.GREEN≈.01359; must discard at100/255|
|1280,325|274, native489469 treebranch|0,-14 /0|.914006,.664669|Raw alpha667.GREEN=0; must discard|
|1300,270|295, native559590 green leaf|0,-14 /0|.393491,.445034|Raw alpha680.GREEN≈.704; passes128/255|
|1260,290|Legacy opaque trunk1 after leaf holes|-1,-14 /0|.175041,5.593187|Opaque; front-facing under GL_CW|

At both large-card samples, applying native branch coverage reveals family6 green leaves behind the rejected card. Nearby1258,288 and1262,292 already hit family6 row295. The full depth-sorted hit lists retain material IDs, native IDs, triangle/index offsets, vertices, UVs, gradients, alpha samples and facing information in `pixel-raycast-report.json`. The branch correction prediction is in `branch-alpha-pixel-prediction.json`.

## Native branch coverage proof

Source489469 is `for_flora_treebranch`, shader8860/trunkdot3. Its header has AlphaTest1, CullMode0 and cutoff byte100. Its alpha asset489465 is already bound as native texture667 on unit6. The initial inspected port row274 had flags32768, meaning opaque and cutoff128, so coverage was never tested.

The original captured card vertex buffers12307/10164 appear in depth draws66571/66592/66596 with pipeline12323, VS310/PS311. PS311 samples textureGREEN and discards below cb0[0].x. Captured cutoff is0.392156869 (100/255). The bound alpha image14135/view14139 is256x512 BC1_UNORM with7mips. Its top block hash exactly matches source489465 authored mip2:

`c6a49b1d97e5534af74afa49e4b66628eafacf378b5ced3f23bea588740ef8b8`

The same buffers use color pipeline13167, VS883/PS884, with depth EQUAL. Both branch depth/color pipelines have cullNONE. Their sampler149 disables anisotropy and uses repeat/trilinear sampling. Use anisotropy1 for branch alpha667 as well as the previously corrected leaf maps.

Recommended semantic correction: row274 is cutout with100/255 and independent native unit6.GREEN coverage, in both depth and color. Root's proposed0x20000000 material flag cleanly identifies this coverage source. Preserve diffuse textures and geometry. Root staged row274's corrected0x20006402 flags during the audit; the later material-state snapshot therefore already contains this first correction.

## Culling proof and limit

Native opaque trunk pipeline8238 uses the same VS883/PS884 with BACK culling and CLOCKWISE front face. Native branch-card pipeline13167 uses NONE. A family-wide trunk cull rule would therefore be wrong. The sampled274 cards are back-facing under GL_CW, but native intentionally renders them; alpha testing is the correct semantic fix. The legacy trunk hit at1260,290 is front-facing, so enabling backface culling cannot remove it.

All new rows263–295 were audited separately in `../material-state-audit/native-material-state-audit.json`:28 source materials require BACK, while274/275/293/294/295 require NONE. Row275 is the opaque two-sided `pln_sparrow` material577592.

No core, assets, preview or GPU state was changed by this audit. Texture sampling is an offline isotropic trilinear approximation; legacy anisotropy4 is not simulated. Geometry intersections and UV provenance are exact for the current cells; active LOD is inferred from the recorded fully loaded camera and stream thresholds rather than instrumented. This identifies the large-card bug without asserting that all remaining tree darkness is resolved.
