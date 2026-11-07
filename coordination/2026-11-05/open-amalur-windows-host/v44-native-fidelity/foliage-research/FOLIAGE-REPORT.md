# Native foliage reference reconstruction

All outputs are private overlays; existing renderer, packers, and active assets were preserved.

## Grass ready for integration

`pack-overlay/g*.bin` contains 18 OAWF40 cells: 25,224 deterministic authored instances, 307,269 vertices, 177,266 triangles, original material254. The index overlay changes only selected grass counts; merge those counts with other index work.

OAWF40 vertices retain position@0, packed wind@12, UV@16, float normal@24, RGBA8@36. The parser recovers authored geometry/UVs, native tile ownership, MT19937 seed table, lattice/LCG placement, density acceptance, scale/yaw, terrain normals, shade colors, and packed wind.

`validate_native_foliage.py` independently verifies all 25,417 vertices in six captured original-game foliage buffers. UVs, packed wind, and RGBA are byte exact. Maximum position difference is0.008735 native centimetres (0.0874mm); maximum normal component difference is below5e-6. An independent MT19937 implementation agrees for all1024 seed values. These checks establish geometry correspondence, not visual parity of a renderer.

The previous grass was synthetic crossed cards with estimated atlas rectangles. Its alpha merge also copied packed atlas RED into coverage; captured depth shader uses GREEN. Native atlas channels are RED specular level, GREEN coverage, BLUE specular power. Corrected assets preserve authored mip chains:

- `native-grass-diffuse-alpha-343428-344837.oatx` → reserved texture655.
- `native-grass-normal-3520.oatx` →656.
- `native-grass-alpha-specular-344837.oatx` →657.
- `native-dissolve-noise-1816.oatx` →677;16x16, three native mips, repeat/trilinear.

Texture source top-mip BC blocks exactly match the saved capture. Source grass material344843 uses cutoff128/255. `native_foliage_contract.glsl` describes active VS893/PS894 and depthPS327, including TBN reconstruction, native diffuse/specular/ambient outputs, signed-byte dissolve jitter, noise.GREEN, and5000cm far distance with1500cm fade range.

## Tree leaves ready for integration

`cell-overlays/*.oawt` and `*.remove.u32` contain4,872 exact source joins across all18LOD0 cells. Every output position/UV0 equals its original selected cell indices, with zero ambiguous joins. Removals are disjoint from the static-material overlay. Native materials359202/419060/559590 map to rows293/294/295, family6. `native-leaf-material-profiles.json` contains exact authored controls, textures, cutoff bytes, defaults, and provenance.

Tree VS877/PS878 (DXBC dcec41082e980adc/5f69b61f58517ed1) use per-instance radial normals, raw source tangent/binormal and source vertex colors. Main leaves use cylindrical radial normals, disable normal mapping/specular, and have zero movement. Saplings use spherical radial normals with600cm center offset and movement scale10. `native_tree_leaf_contract.glsl` covers both paths.

OAWT76 family6 spare UV1@56 stores float-bitcast half pairs `[worldWindDirection.xy]`, `[worldWindDirection.z,paletteIndex]`. Direction includes authored instance scale/rotation. The former flags field@72 stores float radialLength bits; expose this as FLOAT attribute8. Preserve both fields verbatim during OAWE merging. The shader updates position and radial normal. Worst measured final displacement error from compact direction quantization is0.00244140625cm (0.0244mm). Source48-byte meshes have no authored second UV to lose.

Material keys are independently recovered through native hash/reflection, not inferred from values. Native00c58d40 zeroes missing material slots;00c8dbe0 overlays authored parameters and injects AlphaCutoff from material data byte+0x1c (source file0x24), divided by255. Main leaf cutoff100/255 matches the captured depth pass. Tree depth tests noise.BLUE at leafUV against instance dissolve and coverage.GREEN against cutoff. Captured main leaf dissolve is1.

## Native dynamic producers

`native_foliage_wind.h` implements native grass initialization00d079e0, simulation step00c5f6d0/00c5f770, and palette00c8a680. World update00ff0c33 supplies unsigned millisecond delta. The eight rates0.4 through0.75rad/sec match both saved original-game uniform snapshots over their8ms interval, maximum phase discrepancy4.2e-7rad.

It also implements native tree scalar palette00ca00e0→00a76770→00a75030. Five paired periods are3*(.71,.89,1.01,1.13,1.31), with integer millisecond modulo. An independently compiled C harness reproduces all12 captured components bit-for-bit at native clock305493984ms. Saved `native-captured-global-uniforms-360896.bin` retains all1376 reference bytes, and `native-captured-wind-palette-360896.bin` retains64vec4 grass offsets. Freeze these only for reference comparison; regular mode should advance native clocks.

## Remaining limits

Renderer integration and visual comparison belong to the parent task. Tree sidecars cover LOD0; native LOD1/2 cluster attribute ownership remains unresolved. Cross-platform floating arithmetic is not a claimed original-x87 bitmatch. Captured absolute clock origin is reference-specific; the native dynamic equations and timing units are recovered. Whole-zone foliage generation should follow validation of the18-cell reference scope.
