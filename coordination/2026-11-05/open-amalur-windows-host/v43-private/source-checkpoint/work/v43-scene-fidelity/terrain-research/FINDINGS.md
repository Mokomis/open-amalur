# Terrain paint and palette contract — static evidence, 2026-11-05

Recovered the actual 431658 tile-to-paint-map linkage, palette selection, and shader blend math. No slope/proximity assignment is necessary. No engine/build/pack edits, game launches, Ghidra sessions or database writes occurred. Source assets were read; the existing unpacker extracted only 325525.palettetmp_bxml to this new research directory.

## Reusable outputs

- decode_terrain_paint.py: bounded standard-library parser, reads existing terrain assets; writes evidence only under selected research output. Currently pinned to native 431658 example, one-segment zlib entries and the observed MultiEntryFile format.
- linkage-evidence.json: source hashes, exact file offsets, complete door example.
- paint-manifest.json: all 1344 spatial paint descriptors, stream offsets and decoded SHA256s.
- palette-evidence.json: all nine material rows and five palette sets.
- height-coverage-audit.json: exhaustive descriptor-referenced height record audit.
- native-evidence.c: 27 copied native export functions with original source paths/addresses.
- 1bc6cb4d0dcff9cf.asm, 7691e37f0a97b1de.asm, 8bf24b8dc30a668c.asm: copied original disassembled shaders.
- door-paint-129x129.u32: 66564 raw RGBA8 bytes, no header; little-endian u32 records.

Run on existing Windows Python312:
`python decode_terrain_paint.py --root "C:\Users\rwill\Documents\Opem Amalur"`

## Native file linkage

Native TerrainObject reader 0x00d46f60 reads the main header, bitsets, nested mesh block, MultiEntryFile format, and two LOD descriptor arrays. Their runtime locations are terrain+0x36c (height) and terrain+0x378 (paint). File offsets below apply to SHA256 f8eb745fde7d7a1a0193c91755f725077176a8d84786a748cfbfd29cb61b7415, 1081220 bytes.

- Nine bitsets begin +104; native ca9e70/a7edc0 imply u32 bits, u32 occupied count, ceil(bits/8) bytes.
- Serialized TerrainMeshRenderMgr begins +11235 (d46dd0, d45f10, d3ccb0, d3a810, d0e2e0).
- Its 4225-element sparse pointer array begins +14712. Native ce03b0 is badly decompiled; raw instructions ce03e5..ce04b9 prove alternating runs: u32 initial occupied flag, then u32 run length; occupied runs carry one u32 key per item. Empty runs carry no item payload. Initial flag is zero here. Ends +22916.
- Second MultiEntryFile descriptor begins +22916: six u32 [version1, offsetBits21, offsetAlignment64, lengthBits8, lengthAlignment32768, segmentIndexBits3]. Native a8db50 builds masks, a876d0 returns `(key & 0x1fffff)*64`, a876f0 decodes segment index. a92d10 derives rounded read length. Thus values around 0x200000 are packed descriptors, not small paint ordinals.
- Height array count at +22940: nine levels, counts [66049,16641,4225,1089,289,81,25,9,4], exactly (4096/(16<<lod)+1)^2. Their item offsets are in linkage-evidence.json.
- Paint array count at +376628: four levels with counts [1,64,256,1024]. Data starts respectively +376636,+376644,+376904,+377932. Levels1..3 describe 8x8,16x16,32x32 maps, tile spans512,256,128 map units. There is no +1 border in this spatial tile array; each paint image has its own +1 border pixel.
- Native ring request d21bb0 calculates x/y quadrant origin and indexes `terrain+0x378[level].data[(y/tileHeight)*gridWidth+x/tileWidth]`, then b03200 with callback d15990. The latter cc6800 decodes u32 count plus count u32 texels; cd8380 copies these bytes into `rings_blend_texture`. cd81c0 creates the blend texture/staging surface.

All 1344 paint entries were independently decoded by their packed descriptor: every one produced 66568 bytes, u32 count16641 then129x129 pixels. All1344 entry offsets are unique. No correlation was used.

## Exact door example

World (1575.1,-62759.2) maps using source origin(-102425,-102425), scale50 to (2080.002,793.316).

- Finest paint level3 cell(16,6), tile map bounds[2048,2176]x[768,896]. Main file+378764 contains key0x481445. It points to stream+33886528, zlib+33886552. Decoded SHA256355d6058e9463a07cb90dbae0535bde3c19e142d081f2530045347d2cd70bf1f.
- Local pixel floor(32,25), decoded record+13032: bytes00 ff00 ff, RGBA=(0,1,0,1).
- Height LOD0 spatial entry(130,49), main file+73840, key0x20dc18, stream+3606016, zlib+3606040. Decoded chunk23052 bytes contains16 grids. Reader d15490 gives exact grid rectangles, avoiding inferred partial-chunk placement.
- Door grid is record6, decoded chunk+8670..10099, map bounds[2080,2096]x[784,800]. Material-set array is [1]. Heights begin decoded chunk+8843.

## Palette binding

Main header word20 is asset325525 (`out_for_prototype`), NOT the old4720 palette suggestion. The extracted initial_0.pak member325525.palettetmp_bxml is464 bytes, compiled carrier with428-byte body. Native TerrainPaletteSet vf4 d153e0 resolves first two fields of28-byte material rows. d15250 constructs material sets from their row-index lists, cd7d40 binds the rows in list order to the four diffuse/normal slots. cbb4c0 selects set per terrain grid from runtime chunk+0x48 array and copies its row indices to draw+0x59..0x5c.

Palette325525 has9 material rows and5 sets. Door set1 at palette file+292 references [7,4,1,0], binding:

1. t1 road: diffuse641635 for_terrain_road01_d, normal641638.
2. t2 stone: diffuse343449 for_terrain_stone01_d, normal343450.
3. t3 grass2: diffuse343442 for_terrain_grass02_d, normal343443.
4. t4 grass1: diffuse343440 for_terrain_grass01_d, normal343441.

Row+0xc is UV scale. cbb4c0 multiplies it by terrainScale/100 (double at VA014c95b8 is100.0), so here per-material multipliers [.1,.125,.125,.125] in map-coordinate UV space. Rows+0x14,+0x18 feed native material parameter arrays; their names/complete roles remain qualified in evidence.

The source grid parser d15490 reads exact grid bounds8+8 bytes, transform48 bytes, two counted bitset arrays, one flagbyte, optional counted u32 material-set array when !(flags&2), u16 height array, byte mask array, occupancy bitset; finest grids additionally carry occupancy/auxiliary fields. The decoder implements this and consumed all examined chunk bytes exactly.

## Shader semantics

Authoritative retained shader disassembly: outputs/scene-v19/shaders/1bc6cb4d0dcff9cf.asm (normal-mapped terrain),7691e37f0a97b1de.asm (simpler terrain),8bf24b8dc30a668c.asm (terrainVS). Both PS variants agree on the following operations.

Blend sample t9 is `g_blend_sampler_F_ANIS_U_WRAP_V_WRAP_S_GLBL_E_TerrainBlendMap_texture`. It returns RGBA; channels are not four independent weights, and alpha is not the fourth weight. Byte order is also established: cd81c0 sets staging format0x27;0106ab50 calls0105ade0(0x27,0), which returns DXGI_FORMAT28, R8G8B8A8_UNORM. No sRGB decode applies to this blend map.

For sampled blend `b=(R,G,B,A)`:

```
t = 1 - R;
w0 = R;
w1 = G*t;
w2 = B*(1-G*t)*t;
w3 = 1 - saturate(w0+w1+w2);
```

This is a literal transcription of the shader's mad/mul swizzles; do not replace it with an assumed conventional splat formula. Next, sample four diffuse textures (including their alpha h0..h3):

```
a_i = w_i * h_i;
cut = max(a0,a1,a2,a3) - terrainHeightBlendFactor;
q_i = max(a_i-cut,0);
color = A * sum(q_i * diffuse_i.rgb) / sum(q_i);
```

The height blend factor is g_globalbuffer byte1308/cb1[81].w. The normal variant blends normal maps with the same q. Source shader has no zero-sum guard. Preserve source diffuse alpha as height data. The simple shader subsequently applies lighting/tint; that is separate from this contract.

Door blend(0,1,0,1) yields w=[0,1,0,0], selecting slot2 stone before material-height blending. This is a static numeric example; no original-game runtime or visual-parity claim.

VS computes common UV from world/map XY using terrainTexcoordMad, then blendUV=commonUV*terrainBlendTexcoordTransform.xy+terrainBlendTexcoordTransform.zw. The native ring atlas uses wrap+border129 pixels; a reconstruction may use direct per-tile texture sampling with local map coordinate/128 and texel-center/border handling, but exact filtering/atlas seams need review.

## Height coverage correction

The 16MB prefix is NOT globally ignorable. Across all native height LOD descriptors there are5724 unique keys:2545 empty4-byte records and3179 nonempty chunks. Of the nonempty chunks1919 are before16MB and1260 after16MB. All3179 decompressed and parsed successfully, yielding47093 exact grid rectangles, zero duplicate rectangle keys. See height-coverage-audit.json. Empty default records were counted, not incorrectly decompressed.

This audit does not establish which current builder's terrain cache is in use. The old terrain-index.pkl currently has959 entries and its (2048,768) key points to a different coarser LOD; do not use that spatial key alone as exact identity. Existing terrain-grids.pkl has12493 grids and terrain-abs.pkl12409 positions, with no exact(2080,784,16) position. These are older v20 caches, not proof about the current zone-dal outputs. No rebake was attempted. Parent should choose active inputs deliberately; using native LOD arrays and exact per-grid bounds avoids same-origin LOD overwrites.

## Minimal implementation and limits

Use native descriptor arrays to locate a world XY's finest available height grid and paint tile; retain each grid's material-set index. Bind the four palette rows in stored order, preserve diffuse alpha and linear RGBA8 paint, and implement the shader math above. A direct per-tile GPU blend texture is sufficient to replace slope selection if border/filtering/UV conventions are reviewed. Do not interpolate palette indices between unrelated grid draws; each draw has its own set.

Outstanding: live visual parity, atlas seam/filter sampling, terrainHeightBlendFactor's selected region runtime value, full heightfield/collision integration, unusual flagged grids beyond the statically parsed records, diffuse/normal color-space/resource details, and normal/tangent conventions. Native height scale/offset use was not newly traced in this bounded task. All conclusions are static native/source-asset evidence; no runtime claim.

## Implementation handoff supplement (same bounded task)

The initial limitation about multi-set ownership is now resolved statically. Native ceae80 constructs actual indexed terrain triangles using the first per-part bitset array: bit `(localQuadY*16+localQuadX)*2+triangle`. The second per-part64-bit array selects skirts. Stored per-grid material-set array entries correspond to these part-mask array entries.

The source quad corners are0=v00,1=v10,2=v11,3=v01. VA0173e014 contains `[0,1,2,0,2,3]` (primary diagonal v00→v11). VA0173dffc contains `[3,0,1,3,1,2]` (alternate v01→v10). Native chooses primary only if the two diagonal vertex-state bits at19*(qy+1)+(qx+1) and19*(qy+2)+(qx+2) are both set; otherwise alternate. These vertex-state bits are the first post-height/mask occupancy block read by d15490, runtime grid+0xac data pointer.

The generated selector stores first triangle's set ID in bits0..2, second in bits3..5, alternate diagonal in bit6. ID7 denotes no native owner. For fractions f within source50-world-unit quad:

- Primary: first triangle if f.y<=f.x, second otherwise. Examples(.8,.2)→first,(.2,.8)→second.
- Alternate: first triangle if f.x+f.y<=1, second otherwise. Examples(.2,.2)→first,(.8,.8)→second.

The global4096x4096 selector covers all35039 finest native grids. It retains376555 unowned native triangles asID7 and7,807,232 quads outside finest native source as255. All source bitset occupied-counts and triangle-owner disjointness assertions passed. The door byte73 has both triangle owners set1 and alternate diagonal. The reference256x256 selector region has131072/131072 triangles with exactly one owner and zero overlaps.

`build_terrain_proposal.py` builds the paint atlas and reference sidecars. `build_full_selector.py` builds the global selector. Shared129-pixel map boundaries were compared exhaustively: zero horizontal or vertical mismatching pixels. The assembled atlas4097x4097 includes the final outer border. Atlas RGBA SHA256172571324d4a46f08ed2b321ec776bae6e1c8c5726cb872b0ed0696053fc98eb. Blend UV is `(mapXY+.5)/4097`, mapXY=(worldXY+102425)/50. Sampling requires linear UNORM, no implicit row flip.

`build_pack_overlay.py` emits an isolated overlay for both shop9cells(-1..1,-11..-9) and bridge9cells(0..2,-15..-13), all3LODs. Original vertex/index bytes and object draw records are preserved. Legacy terrain draws stay as fallbacks; native draws repeat only material sets present in each ground draw's conservative source-selector window. New flags0x40000001, materials258..262; OATP sidecar56-byte rows store materialIndex,nativeSetID,4diffuseTextureIndices,4normalTextureIndices,4mapUVScales. Draw-count capacity128 is asserted, never truncated.

Overlay files: materials.bin,water.bin,index.bin,terrain_materials.bin,terrain_paint.bin,terrain_selector.bin,newtextures t637.bin..t654.bin,and changed cell draw-record files. `terrain_paint.bin` has OATX `<4s4I>` header('OATX',0x8058,4097,4097,1), u32 bytecount67141636, pixels at+24. `terrain_selector.bin` is raw4096x4096 R8UI without header. Index cell count,bounds,triangle counts remain source values; texture count is655; water material count263 with appended zero entries.

Parent renderer contract: featurebit32 enables this layer. Native draw rejects fragments unless feature32 and selected native set equals expected draw set. Legacy terrain rejects fragments only if feature32 and selected set<5; ID7,255 and out-of-map coverage retain legacy. This avoids adding unsupported ground or removing existing ground where native coverage has holes. Native draws must always reject when feature32 is off.

The18 new terrain textures are decoded from actual DATA_0.pak KEEN source `_1` carriers, selecting at most1024 source dimensions; full box-generated RGBA8 mips reach1x1. Original diffuse alpha is retained (grass01_d28..79,stone01_d20..152), never forced255. Existing Pillow decodes standard BC1/BC3 payloads through an in-memory DDS header. GPU BC rounding, generated-vs-native mip differences, normal mip renormalization and diffuse texture color-space parity remain unverified. This is explicit and separate from the exact paint/palette contract.

No overlay was deployed by this worker. Parent owns renderer integration and feature testing. See pack-overlay-report.json and proposal/*.json for complete exact output contract and checks.
