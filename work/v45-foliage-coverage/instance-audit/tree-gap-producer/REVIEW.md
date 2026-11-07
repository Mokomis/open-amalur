# Missing tree producer recovered

All51 previously unresolved native tree poses come from the Dalentarth **region** FabInstanceCollection. The custom builder emitted only space collections. This is a source omission, not evidence for fabricated positions, random density tuning, or a global duplicate-tree policy.

The exact source is `work/v20-inputs/patch_0.pak/431608.region_bxml`, SHA256 `5c867388c94039b14b4803bc7d2c738d17da38d2f2303025858f650aa04f9803`. DATA also contains these poses; patch precedence is preserved. The earlier search across170 `.space_bxml` files included all84-byte arrays0x150/0x160/0x170/0x180, including both blended groups. Its zero matches were correct within that space-only scope; it did not search the region collection.

## Native/source route

`BHG_Region__vf4@00fed630` calls the same collection initializer `00fec370` used by spaces. Region construction places `BHG::FabInstanceCollection` at Region+0x34. The collection initializer processes four reference/render groups, resolves material at render+0x40 and assembly at+0x44, and registers the resulting scene data through00cd24e0/00cd2570. The current `build_zone.py` uses the region file only for environment/light information after emitting its space geometry.

The Region table is0x18 bytes later than Space's equivalent table. Pointers stored in these BXML table entries are file offsets:

| Group | Reference table / stride | Bounds table / stride | Render table / stride | Count |
|---|---|---|---|---:|
|0|0x140 /16|0x160 /80|0x168 /84|2138|
|1|0x148 /16|0x170 /80|0x178 /84|773|
|2|0x150 /16|0x180 /80|0x188 /84|3|
|3|0x158 /16|0x190 /80|0x198 /84|0|

Reference+8 holds the FAB ID. Render+16 holds raw world translation float3; +32 quaternion float4; +48 scale float3; +64 native material ID; +68 assembly index. Bounds+64 and+68 hold the authored squared-distance interval; +72 raw flags and+76 collection-local ordinal. All16/80/84 source bytes and their offsets are preserved. Unrecovered bounds/flag semantics are retained rather than repurposed. `read_region_collection.py` provides an independent source reader.

## Direct native witness

Native draw69284 uses FAB343974 `for_flora_treelarge01`, assembly8 and material353286 at `(-880.2670288085938,-76023.859375,5371.81640625)`. This is Region group0 record666. Its authored squared-distance interval is16000000..144000000 (4000..12000), raw flags7. The referenced source VB and IB match the captured geometry hashes.

`region-native-tree-correspondence.json` resolves every97 previously unmatched tree-part draws across all51 poses, matching FAB/proven geometry alias, assembly, raw translation and transform basis. Translation error is exactly0; maximum basis error is5.919397949583072e-8. Identical authored geometry appearing in several LOD records remains an explicit candidate set; it is not an unambiguous LOD label.

This resolves the previously proven native-only coverage at(500,35). It is a different pose from the offscreen343974 tree at(8675.918,-80072.016,6627.077).

## Candidate output ready for root

Use `candidate-world-full`, described by `region-aux-stage-full-manifest.json`. The earlier133-cell `candidate-world` remains intact for comparison.

- 1069 authored records, representing155 physical FAB+rawT/Q/S placements.
- 198 indexed auxiliary cells, including65 cells absent from the base1271-cell registry.
- 695217 total triangles across all authored distance intervals; these are not simultaneous active triangles.
- 693680 indexed vertices,2522 draw ranges, maximum77 ranges in one cell.
- 61196828 bytes, approximately58.36MiB; registry SHA256 `696eb5c640fc2135a01a87b4ba56dd0daffcca1ac646cc591150cb08ffc4e006`.

Selection includes all authored nonshadow/nonwater regional records with a triangle centroid in the203 reference-visible cells, then preserves each selected record's complete original geometry. The full candidate includes the627 skyline triangles omitted by the earlier base-cell-only candidate.144 shadow records and three river/waterfall records remain excluded; the preferred existing waterfalls are untouched.

Exact semantic record identity includes native FAB, material, assembly, bitwise rawT/Q/S, min/max range and raw flags. There are zero duplicate regional records and zero exact matches against all four active space collections. A second check ignores material, assembly, distance and flags: the155 regional physical placements have zero FAB+T/Q/S overlap with12573 space placements. Different LOD parts are preserved. See `region-space-physical-overlap-audit.json`.

World positions use direct native T/Q/S, without the older per-assembly sphere-center scaling recipe. Source UV and RGBA are bit-exact. Body frames use the established inverse-transpose frame decoder; leaf vertices preserve native radial normals, raw-origin pivot, source T/B, color, wind direction/phase and radial length. Original source mesh, VB, IB, reference/bounds/render bytes and hashes are retained in `region-aux-full-source-provenance.json`.

## Auxiliary binary contract

`rCX_CY.bin`: magic8 `OARGEO1\0`, uint32 vertexCount,indexCount,drawCount,vertexStride76,rangeStride48. Header28 bytes. Each48-byte range is `<4I6fIf>`: materialRow,firstIndex,indexCount,rawFlags; raw-origin XYZ and source bound radius; minSq,maxSq; stable sourceIndex; per-range distanceScale. Scale0 inherits the registry. The original source group/rank remains in JSON. Then OAWE76 indexed vertex data and uint32 indices follow.

`region-index.bin`: magic8 `OARGIDX1`, uint32 cellCount,materialCount, float distanceScale, uint32 reserved0. Header24 bytes. Each40-byte cell record is `<iiII6f>`: cx,cy,triangleCount,drawCount,actual vertex minXYZ,maxXYZ. Material count299; registry distanceScale0.5.

Root's optional reader owns region-only cells and runtime distance filtering. No base `c*.bin`, leaf `l*.bin`, renderer or live pack files were changed by this work.

## Distance policy: explicit remaining inference

Plain origin distance satisfies36/97 captured draw candidate sets; sphere center35/97, sphere surface45/97, and origin-minus-radius49/97. Half origin distance satisfies97/97; half sphere-center distance also97/97. Scale0.4 satisfies94/97,0.6 only67/97. This strongly supports a regional quality/distance scale, but the exact native consumer/configuration was not recovered. The bounded trace reached registration helpers; it did not establish the factor's provenance.

Therefore0.5 is explicitly a **provisional original-capture quality preset**, accepted by root, not a universal engine constant. The record intervals and raw origins remain authored. Actor lamps independently require scale1 and use their own per-range override; do not apply0.5 globally to actors. `region-native-lod-metric-candidates.json` retains every candidate and calculation.

## Materials

`candidate-materials` contains independent28-byte MATS and84-byte native row patches for296/297, plus exact authored OATX textures685..691. `region-material-stage-manifest.json` records source and per-mip hashes, scalar BC1/BC3 decoder checks and full serialized payload verification. Normal4002 exactly matches existing texture668, so668 is reused and reserved692 is unused.

| Native material | Row | Native contract | Alpha / cull | Triangles |
|---|---:|---|---|---:|
|353286 treebarkblend|266|existing family3|existing profile|504944|
|343630 treebarkbonus|296|Dot3Alpha, family1|GREEN150/255, BACK|104501|
|414763 cliffblend|270|existing family4|existing profile|42428|
|359202 treeleaf|293|existing family6|GREEN100/255, NONE|42324|
|1611839 skyline|297|Dot3Alpha, family1|GREEN200/255, NONE|1020|

New rows use ConstantColor(1,1,1,1), SpecularValues(1,20,0,0), source shader419915 `dot3alpha`. The source-backed base contract is existing Dot3 plus independent raw GREEN alpha. Texture685..688 samplers are captured sampler149 at draw68145: repeat, trilinear, linear min/mag, bias0, anisotropy disabled. No specific skyline sampler witness was found in the97-tree subset; anisotropy1 there remains the documented default consistent with the native material samplers observed elsewhere.

The material candidate is a patch, not a replacement for live banks. Root merges rows296/297 and actor row298 while preserving current original rows. Alpha-map selection does not imply cullNONE:343630 explicitly remains BACK. Root separately corrected that renderer coupling.

All output stays inside this private `tree-gap-producer` directory and its Mac mirror. Source files, databases, native game, GPU, running previews, and deployed assets were untouched.
