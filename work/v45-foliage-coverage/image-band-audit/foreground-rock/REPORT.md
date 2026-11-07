# Foreground rock near-mesh candidate

Both requested native pixels (50,735) and (100,725) identify draw69783, VS923/PS924, pipeline12360, VB10440/IB10442. Source FAB424996 is for_rock_stone05. Exact native/source buffer hashes identify assembly0:119vertices/190triangles. Existing CPU picker triangle2/indices4,3,0 matches native attachment depth within1.6e-7 at both pixels. Pixel-identification.json preserves the existing depth data, orientation and sampling evidence.

Current c1_-14_0.bin row270 contains exact source assembly2:55vertices/50triangles. All55 worldpos/UV0/RGBA/N/T/B values match source exactly, and the50triangles match full76-byte corner records. Material identity is correct MID414763 for_rock_cliffblend, family4 vertexblendmodifiedmask; captured/source/profile spec(.924,67.12) and tiling(2,2,1,1) agree. This proves a source LOD difference. It does not attribute the entire brightness difference to geometry; texture/filter/fullshader parity was not re-audited.

Source record: PATCH431646.space_bxml rawslot0x160[470], also0x150[1324], rawfileoffset370216. Prior provenance ordinal672 is not a rawarray index. Complete84-byte record is in receipt.json. Source direct TRS, unit scale, matches native world matrix to3.92513e-8; transformed positions to9.69703e-6worldunits and native frames to6.62046e-8. Source UV/color raw bytes are covered by the exact captured VB hash. No centered-scale offset exists for this unit-scale instance.

candidate-cell/c1_-14_0.bin removes only these50triangles and appends190source near triangles/119vertices. All77609old vertex bytes and71578other triangles/order are preserved. Same29draws/material rows; drawrow270 and vertex nativeMID414763 remain unchanged. Before77609vertices/214884indices/71628triangles; after77728vertices/215304indices/71768triangles.

Input SHA:3ecc8fd97451db82cdf9409c93f5d353f06d9e6653e461ce90cfd9030371bf15.
Candidate SHA:203809d07d6416c1a4c9b671bc40558dc9b6592ce5b972324cf652388dd3b384.

Replacement AABB:(8325.276367,-86681.34375,6151.838379)..(8762.145508,-86217.578125,6345.098145). It fits both actual current OAWI cell666 AABB and nominalcell1,-14 XY; no request/frustum envelope expansion. Parent should patch only cell666 LOD0 trianglecount71628 to71768 against the live index, preserving other metadata. Receipt includes current index hash/bounds.

stage_rock_geometry.py regenerates with source/input hash guards and independent retained-byte/order checks. rock-only.oawe is a subset inspection fixture, not a fullcell replacement. removed-triangle-index-offsets.u32 lists the50old triangle offsets.

No promotion occurred. No existing/live code, assets, databases or waterfalls were edited; no game launch, replay or new native-function analysis. Parent owns image validation and promotion. This is one proven source near-mesh repair, not a general dynamicLOD or complete brightness-parity claim.
