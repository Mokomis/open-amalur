# Gorhart bridge image thirds and three local mismatches

The comparison uses the same1536x864 Gorhart bridge camera. Original is `work/v31-native-slice/render-20261105/windows-replay.png`; current is `work/v45-foliage-coverage/bridge-native-leaves-expanded.png`. Input hashes and crop coordinates are retained in `images-and-crops.json`. All paired crops have original left/current right and identical coordinates.

## Vertical thirds: observations

- **Top, y0..287:** canopy gaps and silhouettes differ visibly, including open sky above the left-centre trees. This is a coverage observation; the separate foliage investigation owns the missing regional trees and LOD selection. The HUD also differs, so this is not a valid whole-band pixel-error score.
- **Middle, y288..575:** two solid objects are absent in ours: the wooden structure immediately left of the bridge and the lit post immediately right. The far-left root is present in both, but its position/mesh and moss pattern differ. These are the three focused source traces below.
- **Bottom, y576..863:** the original player and action HUD occlude a large area exposed in ours. Visible flowers/path also differ in colour, with global brightness being investigated separately. No missing-object claim is made for pixels hidden by the original player/HUD.

**Waterfalls are an owner-preferred intentional difference.** Their visibly different curtain/flow shapes are documented and excluded from correction; no waterfall files were changed.

## 1. Far-left mossy root: proven geometry and placement mismatch

At pixel112,530, native draw69212 uses VS903/PS904, VB10212/IB10214. Both source buffer hashes match FAB359268 `for_flora_treeroot01`, assembly0,253vertices/366triangles. Native translation is (7439.8676758,-81928.9609375,6441.9970703). Cached space431646 `out_dal_west_01` render0x160[211] carries the same pose, material353286 `for_flora_treebarkblend`, but cached assembly1.

The actual current `work/v40-windows-host/assets/world/c1_-13_0.bin` is **OAWE76**, not a retained28-byte OAWC cell. Its SHA256 is `b5a893a08a53443a98383c644b60e0bad008f2c375ea674a3c4adaf58ba1987c`. The target root is rendered through material row266, native family3; it is165triangles/121vertices from assembly1. Its positions match the legacy centred-scale transform exactly after float32 serialization.

That centred-scale transform adds **(108.456249,186.370272,113.165810)** world units to the direct authored translation, length243.522354 (about2.44m). Source-only direct TRS `qconjugate(position*scale)+translation` reproduces the captured native world matrix within **5.23904e-8**. No captured save-specific placement is needed to generate this fixture.

Seam-aware matching is essential: several source vertices share position/UV but have different tangent frames. After matching all attributes, current assembly1's positions, UV0/UV1, RGBA, N/T/B are **all bit exact** to its source. Thus lost vertex colour, lost blend alpha or missing tangent data is not supported for this root. Earlier nearest-position-only large TBN errors were seam ambiguity, corrected before delivery.

The native near mesh and the current cached mesh are different: assembly0=366tri/253v, assembly1=165tri/121v, assembly2=79tri/68v. Geometry/UV/vertex-paint interpolation at a screen pixel can therefore differ even though each selected mesh's attributes are preserved. This investigation does not claim the geometry correction alone resolves the full green/brightness difference.

### Material and texture contract

Current row266 has family3, colour(1,1,1,1), specular(1,20,0,0), tiling(1.2,1.2,1,1), texture indices[2,3,4,11,12,13,658,658]. Source map roles are d1=353287,n1=353288,s1=353289,d2=343429,n2=343430,s2=343431. Blend weight is **vertex alpha**, and interpolated vertex RGB multiplies the blended diffuse.

Captured active resource roles are binding33/image15029 d1,35/image15053 d2,37/image15046 n1,38/image15039 s1,39/image13896 n2,40/image15062 s2; cube32/image7496. Diffuse/spec images are BC1_UNORM, normal images BC3_UNORM. Current corresponding textures are RGBA8 linear. Native six maps are2048square with9 authored levels; current six are1024square with11levels. Direct comparison of native authored1024 mip1 against current top mip is not byte-identical: diffuse d1/d2 mean errors3.36/2.44 byte values, maximum64/43. This is a separate texture fidelity limitation, not proof of a wrong source-map assignment or the cause of moss colour loss.

A separate family3 arithmetic mismatch is proven: native PS904 has one normal normalization **after** combining interpolated N/T/B. Current oa_post.c calls oaNativeVertexBlend with `N,normalize(TW),normalize(BW)` while N was already normalize(N0). For family3, the exact inputs are raw `N0,TW,BW`; the helper already normalizes the final mapped normal. No source edit was made.

### Isolated staging for parent review

`root-staging/c1_-13_0.bin` replaces only this target root's165 triangles with source-authored direct-TRS assembly0's366 triangles. It preserves all old vertex bytes and all52815 retained triangles in original order; adds253 vertices; material row266 is unchanged. Input and output hashes are in `receipt.json` and independently checked in `independent-cell-validation.json`.

`root-only.oawe` and `root-native.oawt` contain only the corrected root for inspection/merging. They are **not** full world-cell replacements. `build_root_staging.py` regenerates the staged full cell from unchanged source files. Three native/source vertex comparisons and native frame errors (maximum6.4e-8) are retained in the receipt. No deployment or visual validation was performed. General dynamic LOD policy is not established by this one fixture.

## 2. Missing right-hand bridge lamp: exact source identity

The lamp visible around1103,484 in the original is absent in ours; the post body is absent as well as its light. Native draw68088 VS571 uses the metal-body geometry and draw68589 VS837 the luminous part. Vertex and index hashes identify FAB540961 `vil_lamp_ns_stand` assemblies9 and12 exactly, respectively208 and64triangles. Both use world translation(5173.41015625,-86035.984375,5857.6357421875). The CPU-projected lamp body bounds are x1097..1116,y448..504; luminous-part bounds x1095.7..1116.1,y470.8..493.0.

No matching translation within1world unit occurs in the audited Dal cached84-byte render arrays0x150/0x160/0x170/0x180 or existing v41 placement/global-record catalogues. This is a bounded placement-source gap; no particular omitted producer is claimed. Because solid post geometry is also missing, emissive brightness alone cannot explain the observation.

## 3. Missing wooden structure left of bridge: native draw established, source model unresolved

The original structure occupies roughly x777..918,y464..542. Native draw68274 VS650, VB8611/IB8613, covers sampled pixel850,489 at clipW3213.6. Its world translation is(5717.9614258,-85493.5546875,5865.5439453). Both draw arguments are noninstanced with zero firstIndex/baseVertex/firstInstance.

No exact vertex-buffer hash matches any of1270 cached stream files searched with patch>initial>DATA precedence; all parsed successfully. This bounds the negative search and does not identify its FAB, material or source-placement producer. The separate capture/static-prop investigation is following geometry signatures and bound textures. No guessed bulletin-board or quest-object substitution was produced.

## Evidence and limits

`native-three-point-hits.json` records CPU triangle coverage/depth candidates using captured matrices and exact resource bytes. It is geometric coverage, not a new GPU observation: alpha/culling/stencil and local leaf wind are not simulated. The selected root/booth/lamp families were individually checked to apply binding68 rows8..11 directly to position; they are rigid opaque geometry. Exact full-buffer hashes and source assembly joins support object identity independently of apparent image shape.

No core files, original assets, live renderer state, databases or waterfall files were modified. This is a bounded camera/image audit and staged root fixture, not a claim of whole-game parity.

### Final corner-level check

`root-staging/triangle-corner-attribute-validation.json` compares all165 current target-root triangles against source assembly1 including every corner position, both UVs, RGBA and all N/T/B float bytes. The triangle multisets are exactly equal, with zero differing keys. This closes the seam ambiguity at triangle-corner level, not merely by finding matching individual vertices.

## Subsequent source resolution for both missing bridge objects

The independent static-prop investigator resolved the left structure as FAB638222 for_cart_overturned, exact vertex/index buffers and actor0x98[0] in PATCH431646.space_bxml. Reproducible proof is in left-bridge-structure/REPORT.md and source-and-placement-contract.json. Its source pose plus FAB local-Z candidate reproduces native translation; node ownership remains explicitly scoped there.

The right lamp is source actor0x98[17] in the same space, FAB540961, with source TRS reproducing its capture directly. The new lamp-source-audit/REPORT.md and staged pack cover32 authored lamp actors/14 intersecting requested cells, all source LOD groups and exact active emissive contract. The original bounded negative84-byte-array search remains valid but was incomplete: these objects are in the separate80-byte actor collection.
