# Approved UNIT34 caster-only stage

`candidate-shadow-world-unit` is the integration candidate. It contains 200 caster-only cells: all 175 original leaf fallback cells plus 25 proxy-anchor cells. The current visible `l*.bin` and base `c*.bin` are unchanged. Source343974 shadow proxies are placed whole at their rawT anchor cells, once each: 34 unit-scale poses /476 triangles. The other22 nonunit proxy poses remain withheld.

The fallback retains50,506 existing triangles and all7,359,004 original vertex bytes. Exactly1,325 source-owned triangles from18 SPACE leaf records at nine eligible unit poses are removed from the caster fallback. No other source leaf is removed or moved. Source tangent/binormal, color, UV, wind and material bytes remain exact for all fallback vertices; surviving index triangles preserve their original ordering. The combined caster-only stream has50,982 triangles,97,781 vertices and at most20 ranges per cell, occupying8,109,356 bytes including its index/maps.

Family10 /material300 /materialCount301 /alpha703 is the parent-approved proxy contract. Proxy N.xyz stores full float worldLinear*normalize(sourceSNORMN), without world renormalization or half packing. UV2=(float phase0..9,0); T/B are zero; UV0/RGBA are source-exact; nativeMID1744210 and unused flags0 are retained. NativeSpec.y10 applies the captured12-scalar palette in the caster-only vertex path. Proxy source ranges merge authored adjacent bands to0..30000, SPACE distanceScale1 and REGION0.5 provisional preset. All fallback ranges are explicitly unbounded0..FLT_MAX with scale1, preserving the known positive native leaf activity instead of applying the unsafe31/33 range policy.

`shadow-index.bin` uses OARGIDX1 with materialCount301 and defaultScale1; `sCX_CY.bin` uses OARGEO1 indexed76-byte vertices/48-byte ranges. `shadow-cell-deps.bin` is OASHD01\0 +u32 count +sorted16-byte(fallbackCx,Cy,proxyAnchorCx,Cy). Seventeen rows cover16 fallback cells, including legitimate self-anchor dependencies. The parent must check anchor GPU/texture readiness directly rather than recurse on fallback readiness.

REGION color/early-depth geometry stays unchanged. Only26 source-owned family6 IDs at three of the six eligible regional proxy anchors are flagged for conditional CSM replacement, across66 ranges in nine existing region cells. Six IDs use different authored visible-part rotations; each passes the approved sameFAB/rawT/scale join, visible group1..4 membership, and exactly-one-proxy-fullTQS test across all source records. All other31 flag bits and every region geometry byte are exact. `shadow-replacements.bin` is OASHR01\0 +u32 count +sorted12-byte(originalRegionSourceID,proxyAnchorCx,proxyAnchorCy). A flagged range is skipped only when its mapped proxy anchor and textures are GPU-ready.

Header-only patches change existing leaf-index u32@16 and region-index u32@12 from300 to301; every other byte is exact. The intentional zero-triangle region metadata row(1,-14) is preserved without an r-file. Global index textureCount704 and all current rock metadata remain parent-owned and were not changed here.

`independent-validation.json` independently verifies all cell headers/ranges/indices, exact fallback payload/ownership, proxy fields, flag-only region diffs, header count patches and sorted dependency/replacement maps. It lists every staged SHA and byte count. Total candidate directory size including existing r-file flag-copy overrides is18,255,276 bytes. This is staging evidence, not GPU validation or live promotion. The water/shader agent separately supplies exact alpha703 and hash-guarded301-row material banks.

# Source-authored tree shadow proxy inventory

The investigated tree FAB343974 has an explicit shadow-only leaf assembly9, distinct from visible assemblies1/2/4/5/10/11/12. Its material1744210 is `for_flora_shadowlod2`. Authored FAB shadow groups5=[9,0],6=[9,3],7/8=[9,7] pair that proxy with distance-appropriate opaque bark. Assembly9 never appears in visible groups1..4.

The known27-FAB metadata inventory contains seven models with explicit shadowlod material elements; all such elements occur only in groups5..8. This does not authorize suppressing every scene leaf caster: lowtree377117/377118 and leafcover363221 have no dedicated shadowlod element in this inventory.

| FAB | Proxy assembly |
|---:|---:|
|340232|13|
|343974|9|
|353290|10|
|393858|11|
|419041|9|
|419058|9|
|419059|9|

All cached authoritative Dalentarth SPACE files and the PATCH REGION source contain112 explicit343974 proxy records:56 opaque shadow flags8 and56 adjacent blend flags24. Full FAB/material/assembly/rawT/Q/S dedup yields56 proxy poses,48SPACE+8REGION, with no cross-producer identity overlap. Source ranges union0..30000cm; the FAB element’s separate default maximum25000 is preserved as metadata and does not overwrite collection bounds. This inventory selects explicit proxy source records, not captured-pose exclusions or fabricated placements.

The mesh is28 vertices/14 triangles, source stride48. Full56-pose staging would contain784 triangles, partitioned into89 centroid cells, approximately131KB before cell-split overhead. Direct geometry bounds are(-54880.08,-94512.66,2621.89)..(72653.14,82500.55,23800.59).

There are34 unit-scale poses (28SPACE+6REGION), and22 nonunit poses. The direct transform of nonunit proxy records reaches a maximum1.55289 ratio against its candidate source sphere; broad transform semantics remain unobserved. The retained native CSM inventory witnesses two343974 proxy anchors, both unit scale. A unit-scale cohort is therefore available separately from a preserved full source candidate, with nonunit promotion withheld unless additional producer/binding evidence establishes it. The inventory is not a claim that34 runtime matrices were observed.

Native source witness: offender WEST431646 atT(8675.91796875,-80072.015625,6627.07666015625),q(0,0,-.2321552038192749,.9726788401603699),scale1. Native CSM101 draw72203 has exact assembly9 VB/IB. The current rock-shadow blocker instead comes from the visible assembly5 leaf mesh. The water/shader agent independently found the proxy’s sampled alpha is zero at all eight investigated shadow texels, while the visible cards pass alpha there.

The proxy material uses a separate source alpha1741969/native image14030, not the visible-leaf alpha679. Its exact authored9-mip2048² chain is staged by the water/shader agent. Native VS292 uses local normalized sourceN for palette displacement, movement10, with the existing source-position phase hash and12 captured leaf palette scalars. World wind direction must retain source rotation and scale. PS293 discards rawGREEN below100/255; source cullNONE, repeat/trilinear/anisotropy disabled. Material controls are spherical normals1,CenterZ600, movement10; other disable controls defaultzero. This is a shadow-only material and does not replace any visible profile.

`inventory.json` retains every source file SHA, reference/bounds/render byte record and offset, dedup/interval provenance, and the general known-FAB classifier. `geometry-estimate.json` retains every candidate pose extent/cell assignment. The inventory pass wrote no geometry. The later approved UNIT34 caster-only stage is documented above; source files and live assets remain untouched.
