# Final bounded tree-gap and placement coverage review

The captured tree identity inventory is resolved: all 189 catalogued native tree GBuffer part draws have exact source vertex/index-buffer hash witnesses and source transform matches. They represent 106 translation anchors and 113 distinct full world matrices. Image parity remains open: an exact current-only SPACE leaf hit has now been located at the reported sky opening, and a broad range-filter change fails the positive-capture guard.

## Captured placements and the omitted producer

The existing SPACE collections explain 92 draws, 55 transforms and 55 translation anchors. The omitted REGION collection explains 97 draws, 58 transforms and 51 translation anchors. Seven regional FAB393858 anchors have authored part rotation variants; the earlier shorthand “51 missing poses” counted translation anchors. These variants are not evidence for duplicate trees. The appendix and [full inventory](final-captured-tree-pose-inventory.json) list all 113 source transforms and their native draw IDs.

PATCH `431608.region_bxml` is the decisive missing source (SHA256 `5c867388c94039b14b4803bc7d2c738d17da38d2f2303025858f650aa04f9803`). Region vf4 `00fed630` initializes its Region+0x34 FabInstanceCollection via `00fec370`. The old builder emitted SPACE geometry while using REGION only for environment/lights. All 97 formerly unresolved draw transforms match source raw translation exactly and basis components within 5.919397949583072e-8. Identical geometry across authored aliases remains a candidate set, rather than a guessed unique LOD label. [Raw record layout and native route](REVIEW.md), [97-draw correspondence](region-native-tree-correspondence.json).

The regional stage contains 1,069 authored records at 155 FAB+rawT/Q/S identity keys: 129 flora placements, 21 rocks/cliffs and five skyline mountains. Those identity keys include authored part transforms and are not a count of independently visible tree silhouettes. The selection preserves complete source records intersecting the existing 203-cell reference selection: 198 auxiliary cells, including 65 outside the old base registry, 695,217 all-interval triangles and 61,196,828 serialized bytes. All source meshes were available. Shadow records and three river/waterfall records were excluded; the preferred waterfalls were unchanged. [Full stage manifest](region-aux-stage-full-manifest.json), [source provenance](region-aux-full-source-provenance.json).

The parent’s integration receipts report these source additions deployed, payload hashes checked and original material-bank prefixes preserved. Its existing pixel comparison shows the known missing-canopy pixel (500,35) improve from summed RGB error543 to52, and (800,150) from222 to16, relative to v035. Those sampled improvements do not constitute whole-frame parity. This subtask performed no live promotion, GPU launch or native replay.

## Distance ranges and duplicate safeguards

There are zero exact duplicated regional semantic records, zero exact source record matches against the four active SPACE collections, and zero FAB+rawT/Q/S overlaps between the 155 regional identity keys and 12,573 SPACE identity keys checked. The physical-identity comparison deliberately ignores material, assembly, range and flags. It does not claim that similar nearby silhouettes can never overlap. Different authored parts and intervals are preserved. [Overlap audit](region-space-physical-overlap-audit.json).

Auxiliary geometry retains original minSq/maxSq, raw flags, source identity and raw-origin anchor. Runtime range filtering is `minSq <= squaredDistance * scaleSquared < maxSq`; it does not draw every stored LOD together. Serialized draw index runs cover their index buffer once. This establishes the implemented exclusion rule, not complete semantics for every native group or source flag. Trunk/branch/leaf parts sharing an origin are not duplicates.

The REGION distanceScale0.5 remains an explicit provisional original-capture quality preset. It fits all97 captured regional draw candidate sets, versus36 with plain origin distance. Half sphere-center distance also fits97, so that fit does not uniquely recover native distance or quality settings. The bounded native trace reached registration but did not recover the factor’s consumer. Forward97/97 does not prove absence of extra active objects, or correctness at other cameras. Actor lamps use independently supported per-range scale1. [Metric candidates](region-native-lod-metric-candidates.json).

## SPACE leaf placement guard and the 73 withheld transforms

All590 existing source leaf records /51,831 triangles were correlated by old triangle ownership. The full direct-transform hypothesis changes78 records, but old positions fit all590 candidate source spheres; direct positions exceed those spheres on67 records and the prior1.25-radius-plus60cm guard on49. The approximately100.93m maximum correction has no native witness. This blocks broad generalization of the transform recipe.

Only source records457,458,467,468,484 have individually matching native matrices, each with a same-assembly leaf witness:68827,68909,68815,68897,68805. Their shifts are35.5293,12.7743,12.7744,117.2319,28.2932cm. All remain inside the candidate spheres. They affect331 triangles and582 existing vertices across six cells, with one tight bounds expansion. All other triangle vertex records remain byte-identical to the preserved input; headers/draws/indices, UV, color, source T/B, wind and material data are unchanged. The parent’s final placement receipt reports only these five deployed and material count300.

The other73 records /5,963 triangles remain withheld pending actual producer/binding semantics evidence. The full candidate and old pack remain preserved. There is no approval to promote the full candidate and no broad query loop is needed. [Placement guard review](../../native-leaf-direct-trs/REVIEW.md), [per-record bounds evidence](../../native-leaf-direct-trs/transform-bounds-guard.json), [proven-only manifest](../../native-leaf-direct-trs/proven-only-manifest.json).

## Reverse sky-opening audit and exact remaining current-only leaf

For rectangle x950..1020,y0..180, source projection finds nine active REGION records across seven translation anchors. All eight tree records have captured native part witnesses:68957,69041,68999,69298,69304,68935,68823,69029. The ninth, skyline mountain FAB1611848/assembly0/MID1611839, matches native draw68228 with exact VB12224/IB12226 hashes, raw translation and basis error1.777408238368139e-7. No unobserved regional tree/mountain placement is found in this bounded reverse check. Projected intersection alone does not prove final alpha/depth coverage. [Reverse coverage](sky-opening-reverse-coverage.json), [mountain witness](sky-opening-mountain-capture-correlation.json).

The mountain is ordinary Dot3Alpha, source Region group0/record2061/rawFlags7, alpha200/255 and cullNONE. Native VS310/PS311 depth passes43873/55036/66158 discard raw binding32 GREEN below0.7843137383461, using repeat/trilinear/aniso-disabled sampler149. Color68228 is VS591/PS592 with depth EQUAL. Current row297 uses raw t6 GREEN200/255 and cullNONE. Captured diffuse14019 and alpha14024 match every authored source/staged BC mip byte,1024²/nine mips. The bounded CPU point estimate predicts both regional leaf and mountain alpha GREEN0 at(980,100), consistent with native clear depth. No skyline exclusion or material tuning is justified. [Native bindings](mountain-2061-native-bindings.json), [mip identity](mountain-source-capture-mip-identity.json).

The parent then established that REGION-off has the same occupied current raw pixel. A live-pack CPU pick identifies the exact other geometry: `l-3_-12.bin`, triangle33/indexOffset99, material293/native359202. It predicts depth24=16762614, exactly the observed current value. UV=(0.7396466015,0.5843269953), alpha679 GREEN0.6588482561 passes100/255, estimated mipLOD7.35737. This is existing SPACE source198, space431642/out_dal_south_01, FAB340232/assembly6, rawT=(-19209.921875,-74337.1953125,6912.13134765625), unit scale. It is unrelated to the regional additions or withheld scaled transforms. [Exact live pick](current-live-opening-980-100-pick.json), [source ownership and bounds records](current-live-opening-source-provenance.json).

Actual current Windows t679 is capture-exact at every decoded authored mip: OATX SHA256 `d3048889108d36dee10a4dc557b371f40f1a0a722412ceb91bfb606547ea3efe`. Its nine RGBA mip hashes equal the captured alpha chain. This excludes generated alpha mips as the Windows explanation for this hit; Android encoding remains a separate parent-owned verification. [Live alpha identity](current-live-alpha679-native-identity.json).

Source198 has raw-origin distance30567.6162cm. Its selected assembly has source intervals12000..29200 plus blend29200..30000, with raw flags7/23. Exact geometry aliases4/6/12 union to0..30000. There is no same-origin matrix among the existing799 native GBuffer draws. Thus the current leaf auxiliary draws a part outside its stored range. This is a concrete current-only topology/coverage witness, but its absence cannot yet be attributed uniquely to distance: native SPACE activation/streaming or far/billboard routing are unresolved.

All55 previously matched SPACE anchors come from WEST431646(54) and transition431650(1), while the offender is SOUTH431642. This is an existing-inventory correlation, not a recovered native visibility rule.

## General leaf-range staging guard: blocked before geometry output

Exact full84B render-record joins recover authored ranges for all590 source records, with zero unknowns and zero disjoint unions. Adjacent blend intervals can be merged without drawing a triangle twice. However, strict selected-assembly ranges preserve only22/33 captured SPACE leaf positives. Exact fullVB+IB hash aliases, constrained to the same FAB/rawTQS/nativeMID, improve that to31/33. Changing from raw origin to stored bound center leaves both counts unchanged.

The two blockers are native68819/source451/FAB377118/assembly1 (observed origin distance30367.56cm, bound-center32855.91cm, authored max30000, no exact alias), and native69083/source478/FAB419041/assembly8 (observed3916.04cm, center3973.39cm, selected min9000; near0/7 are not exact VB hashes). Offender198 is excluded by both alias-origin and alias-center policies, but neither policy preserves all native positives. Therefore no ranged leaf cells were emitted and no per-instance exceptions or fitted distance offset were introduced. [Full590-source metadata](../../native-leaf-authored-ranges/authored-range-metadata.json), [33-positive/one-negative matrix](../../native-leaf-authored-ranges/alias-bound-center-check.json).

The remaining reusable fix requires actual distance/visibility/far-LOD semantics, or additional proven geometry alias handling. The current selected leaf geometry and all known native positives remain preserved while that policy is unresolved. Unknown far billboards were not added.

## Topology completeness limits

No unknown source VB/IB topology remains within the189 catalogued native tree GBuffer draws. This is identity completeness, not proof that the port selects the original authored part for every camera. The earlier SPACE audit found21/55 anchors with differing authored-group candidates; no broad body/LOD swap was promoted here. Sixteen bounded leaf assembly comparisons preserve triangle vertex sets, UV, RGBA and normals after permutation; fourteen have exact positions, two differ by at most0.429321289cm. This did not support a blanket leaf geometry swap as the original canopy-gap fix.

World-wide SPACE activation/PVS, the far billboard producer, exact distance metrics, complete dynamic wind/residency and final frame shading remain outside the resolved subset. The current-only leaf at(980,100) is specifically documented rather than hidden behind a parity claim.

## Captured transform inventory

The table lists all113 matched full source transforms; repeated translation rows can represent authored part rotation variants. Full raw T/Q/S, source candidates and draw IDs are retained in [the machine-readable inventory](final-captured-tree-pose-inventory.json). Translation is centimeters, rounded only in this table.

| Producer | FAB | Translation XYZ (cm) | Native draw IDs |
|---|---:|---|---|
| REGION | 340232 | -25105.7422, -44654.3984, 6283.1074 | 69045, 69049, 69370 |
| REGION | 340232 | -22075.7969, -37246.7148, 5476.2407 | 68965, 69252 |
| REGION | 340232 | -18242.2559, -42055.7930, 5708.9512 | 68831, 69384 |
| REGION | 340232 | -11421.5342, -74727.2031, 5292.3105 | 68209, 68801, 69017, 69308 |
| REGION | 340232 | -7458.0898, -73027.4297, 4942.3149 | 69021, 69025, 69332 |
| REGION | 340232 | -1385.5580, -86083.9375, 5731.2178 | 69033, 69037, 69362 |
| REGION | 340232 | -288.9050, -59399.8867, 5226.8574 | 68869 |
| REGION | 343974 | -35047.0234, -49781.6016, 6443.3633 | 68995, 69009, 69328 |
| REGION | 343974 | -2985.4805, -78683.6406, 5216.5552 | 68927, 68931, 69336 |
| REGION | 343974 | -880.2670, -76023.8594, 5371.8164 | 68983, 69284 |
| REGION | 353290 | -33505.9453, -50097.1484, 7215.1553 | 69013 |
| REGION | 353290 | -32445.9102, -59754.4766, 6769.2871 | 68921, 69388 |
| REGION | 353290 | -30657.1309, -55000.2070, 6868.0962 | 69316 |
| REGION | 353290 | -24597.0898, -53891.8164, 6961.7852 | 68975, 69392 |
| REGION | 353290 | -24237.7734, -37844.1680, 4917.2900 | 69256 |
| REGION | 353290 | -23771.6367, -53493.4805, 7575.7466 | 68951, 69258 |
| REGION | 353290 | -23106.8691, -45368.5859, 7766.8149 | 68797, 69374 |
| REGION | 353290 | -22786.8320, -40790.9414, 5887.4292 | 68839, 69390 |
| REGION | 353290 | -16678.1074, -45942.7031, 6603.3335 | 68789 |
| REGION | 353290 | -4181.1592, -60226.0859, 5571.9526 | 68923 |
| REGION | 363221 | -8695.0264, -83496.2891, 8754.3057 | 69029 |
| REGION | 363221 | -5275.7744, -78435.6172, 8594.7305 | 68823 |
| REGION | 363221 | -2230.3276, -76507.9609, 10701.8994 | 68987 |
| REGION | 377117 | -39024.4141, -59352.6758, 6513.0918 | 68947, 69378 |
| REGION | 377117 | -33871.4141, -65555.3438, 6678.9087 | 68935, 69380 |
| REGION | 377117 | -30665.3828, -43560.3047, 6892.7627 | 68917 |
| REGION | 377117 | -18827.0508, -92297.2031, 7715.2095 | 69005, 69344 |
| REGION | 377117 | -16394.3125, -77650.2500, 7925.8462 | 68957, 69304 |
| REGION | 377117 | -14594.6270, -42712.0352, 7864.4966 | 69358 |
| REGION | 377117 | -14321.2969, -71862.2891, 7807.1343 | 69003, 69302 |
| REGION | 377117 | -9037.8906, -56267.6250, 8363.7021 | 69324 |
| REGION | 377117 | -3162.7505, -65145.8867, 7309.1587 | 68955, 69366 |
| REGION | 377117 | 1978.9116, -68490.4688, 7859.7979 | 68883, 69272 |
| REGION | 377118 | -32949.6797, -45461.4297, 7326.4824 | 69248 |
| REGION | 377118 | -15780.9160, -80843.0547, 6206.6328 | 68939, 69320 |
| REGION | 377118 | -15470.8682, -74932.7188, 7133.0771 | 69041, 69298 |
| REGION | 377118 | -9670.5283, -47860.4141, 5489.2275 | 68971, 69354 |
| REGION | 377118 | -5362.4922, -45045.6797, 7042.6572 | 68961, 69352 |
| REGION | 377118 | -3614.1062, -57386.0586, 5476.9512 | 68793, 69296 |
| REGION | 377118 | -1436.8564, -70522.7266, 6995.4971 | 69266 |
| REGION | 377118 | -986.1416, -37880.3711, 8634.5742 | 68969 |
| REGION | 377118 | 2988.7268, -55636.3125, 6253.1797 | 68875, 69268 |
| REGION | 377118 | 11139.0674, -75575.7344, 6847.1338 | 69276 |
| REGION | 393858 | -10629.8438, -80787.1172, 4468.5137 | 68201, 69348 |
| REGION | 393858 | -10629.8438, -80787.1172, 4468.5137 | 68999 |
| REGION | 393858 | -6118.1279, -83065.6562, 4790.4819 | 68913 |
| REGION | 393858 | -6118.1279, -83065.6562, 4790.4819 | 68197, 69340 |
| REGION | 393858 | -2015.4528, -77358.0547, 4843.3169 | 68991 |
| REGION | 393858 | -2015.4528, -77358.0547, 4843.3169 | 68189, 69280 |
| REGION | 393858 | 744.6543, -51602.5898, 4849.2329 | 69312 |
| REGION | 393858 | 798.1328, -75889.0781, 5523.6851 | 68979 |
| REGION | 393858 | 798.1328, -75889.0781, 5523.6851 | 68213, 69288 |
| REGION | 393858 | 3773.2139, -89177.8750, 5278.0659 | 68205, 69262 |
| REGION | 393858 | 3773.2139, -89177.8750, 5278.0659 | 68859 |
| REGION | 393858 | 4005.0747, -67701.9688, 5219.1821 | 68145 |
| REGION | 393858 | 4005.0747, -67701.9688, 5219.1821 | 68943 |
| REGION | 393858 | 7018.1777, -56357.6875, 5003.7646 | 69292 |
| REGION | 393858 | 7018.1777, -56357.6875, 5003.7646 | 68851 |
| SPACE | 340232 | 506.4974, -79625.0703, 5574.7983 | 68185, 68811, 68843, 69192 |
| SPACE | 340232 | 4718.0508, -80144.2031, 5731.2178 | 68137, 68835, 68905, 69180 |
| SPACE | 343974 | 8675.9180, -80072.0156, 6627.0767 | 69208 |
| SPACE | 353290 | -12679.7627, -80024.9688, 4976.4893 | 68847, 69396 |
| SPACE | 353290 | -9410.8135, -67744.0703, 6098.1157 | 68879, 69244 |
| SPACE | 353290 | -2981.2253, -80275.4531, 5359.3872 | 68177, 68815, 69400 |
| SPACE | 353290 | -1699.3312, -85431.6641, 5808.5151 | 68827, 69170 |
| SPACE | 353290 | 2046.7274, -81828.6797, 5814.7144 | 68169, 68897, 69398 |
| SPACE | 353290 | 5555.3916, -88570.6406, 6180.4214 | 68909 |
| SPACE | 357911 | -11446.9502, -74552.3359, 4711.5845 | 68193 |
| SPACE | 357911 | -10009.7949, -79382.0781, 4784.5439 | 68181 |
| SPACE | 357911 | -8251.9766, -83716.6016, 5468.6504 | 68157 |
| SPACE | 357911 | -7402.0420, -82195.3672, 4795.6011 | 68173 |
| SPACE | 357911 | -6780.1597, -82097.8750, 4886.9102 | 68165 |
| SPACE | 357911 | -5265.1235, -83862.6641, 5570.1475 | 68155 |
| SPACE | 357911 | -978.1317, -85060.3125, 5724.1602 | 68153 |
| SPACE | 357911 | 326.3300, -76625.3750, 5641.4194 | 68149 |
| SPACE | 357911 | 1807.3839, -82173.6797, 5686.5801 | 68151 |
| SPACE | 357911 | 5108.3872, -82298.4922, 5678.6582 | 68141 |
| SPACE | 357911 | 6776.1733, -82788.6875, 5531.8491 | 68161 |
| SPACE | 359268 | 7439.8677, -81928.9609, 6441.9971 | 69212 |
| SPACE | 363221 | -10205.7773, -75747.1484, 8594.7305 | 68807 |
| SPACE | 363221 | -9882.9678, -80545.1562, 8594.7305 | 68805 |
| SPACE | 363221 | 912.7620, -80391.9141, 11161.3867 | 68889 |
| SPACE | 366251 | -12072.8057, -76843.3047, 4637.5474 | 69224 |
| SPACE | 366251 | -10603.8672, -79276.3438, 4801.0952 | 69216 |
| SPACE | 366251 | 5319.1714, -82234.5156, 6584.7808 | 69160 |
| SPACE | 366252 | 5475.3188, -81734.5938, 6268.7017 | 69204 |
| SPACE | 377117 | -19597.7559, -86501.6094, 7140.3335 | 68785, 69220 |
| SPACE | 377117 | -7851.2700, -90673.5625, 7395.8931 | 68893, 69240 |
| SPACE | 377117 | -3240.8376, -92541.6719, 8447.4424 | 69184 |
| SPACE | 377117 | -346.5975, -69243.8359, 8544.7354 | 68885, 69166 |
| SPACE | 377117 | 3591.8894, -76100.4141, 7620.9048 | 68901, 69200 |
| SPACE | 377117 | 9645.3193, -76272.1406, 8254.2520 | 69164 |
| SPACE | 377118 | -21611.5918, -89916.7344, 7772.5781 | 68819, 69188 |
| SPACE | 377118 | -15558.0732, -97237.5625, 8867.6309 | 68865 |
| SPACE | 377118 | -12061.1777, -91925.2266, 6079.2568 | 69236 |
| SPACE | 377118 | -6181.5156, -92102.9141, 7772.1357 | 68855, 69404 |
| SPACE | 377118 | 3502.7461, -67835.4297, 6617.3613 | 68863, 69196 |
| SPACE | 377118 | 13633.5459, -70554.7266, 6951.2207 | 68873 |
| SPACE | 377118 | 14390.7959, -76932.1016, 8218.9072 | 69176 |
| SPACE | 377118 | 15628.6260, -79126.8203, 8888.2871 | 69174 |
| SPACE | 418236 | -1822.5942, -85446.0391, 5561.6606 | 69228, 69232 |
| SPACE | 419041 | -10720.7031, -75746.2422, 5201.7871 | 69087, 69112 |
| SPACE | 419041 | -9434.6621, -74854.8438, 4706.1323 | 69129 |
| SPACE | 419041 | -1286.9548, -78463.1875, 5565.5903 | 69091, 69124 |
| SPACE | 419041 | 4757.7793, -86588.8281, 5833.8071 | 69083, 69104, 69155 |
| SPACE | 419058 | -6792.7061, -79493.5859, 4737.2197 | 69053, 69108, 69139 |
| SPACE | 419058 | -6304.6514, -85206.5859, 5444.5820 | 69067, 69137 |
| SPACE | 419058 | -856.0329, -84853.0469, 5594.5044 | 69055, 69116, 69143 |
| SPACE | 419058 | 1121.7335, -78846.0547, 5581.1470 | 69075, 69096, 69141 |
| SPACE | 419058 | 9629.9775, -84438.1562, 6087.0527 | 69071 |
| SPACE | 419059 | -10092.1074, -79254.9766, 4643.4116 | 69063, 69100, 69147 |
| SPACE | 419059 | -2188.8840, -82926.5859, 5393.3711 | 69079, 69120, 69133 |
| SPACE | 419059 | 6437.1094, -88330.5391, 6324.4038 | 69059, 69151 |

All analysis reuses preserved source files, captured SPIR-V/JSONL/memory and existing staged/live-pack bytes. No new native function bodies, replay, GPU launch, source edit or live asset modification was performed by this final review.

## Later source-authored shadow contract stage

A subsequent bounded caster audit found that the foreground rock's nearest current shadow blocker is visible SPACE leaf geometry, while native CSM uses a distinct source343974 assembly9 proxy/material1744210. Authored groups5..8 and source flags8/24 prove the shadow role. The approved UNIT34 caster-only stage preserves all other leaf casters and all visible geometry;22 nonunit proxy poses remain withheld. See [shadow staging review](../../native-tree-shadow-proxies/REVIEW.md) and [independent receipt](../../native-tree-shadow-proxies/independent-validation.json). This adds a concrete shadow-geometry explanation without changing the unresolved SPACE range/visibility conclusions above.
