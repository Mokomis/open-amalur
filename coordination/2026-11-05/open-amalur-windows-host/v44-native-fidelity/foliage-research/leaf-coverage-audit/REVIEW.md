# Leaf coverage evidence review

Recommendation: integrate the source-backed family6 coverage correction already staged by root. Both the depth-only pass and cutout color pass must test `texture(t2, UV).g` for family6. Keep the existing100/255 and128/255 cutoffs.

The inspected shader tested combined diffuse `t0.a` in both places (`oa_post.c` lines29 and56 at the initial review). Native depth PS325, exported DXBC `0846c6c833c4aba3.asm`, samples the independent alpha map GREEN channel. Root already binds raw alpha343436 as texture679 for row293, and477449 as texture680 for rows294/295, on unit2. No new asset or binding is required for this correction.

## Direct evidence for dark undercards

At1024 mip0, the combined diffuse alpha and raw native alpha differ substantially at the exact native cutoffs. False positives are pixels currently passing coverage that the independent alpha map rejects. Near-black means maximum RGB component below32/255.

| Diffuse texture / profile | Cutoff byte | Coverage disagreement | False positives | Near-black false positives | Mean false-positive RGB, bytes |
|---|---:|---:|---:|---:|---|
|0 / main leaf|100|6.175%|4.868%|3.707%|21.47,21.53,6.10|
|17 / sapling|128|3.821%|1.783%|1.729%|2.88,1.77,1.25|
|22 / green sapling|128|3.843%|1.793%|1.736%|2.45,2.89,0.97|

The falsely covered sapling pixels are almost black before lighting. This is a concrete explanation for dark card interiors and edges; changing illumination is unnecessary to explain those pixels. Statistics for all current mips are retained in `leaf-current-coverage-diagnosis.json`.

## Normal, backface and color-space comparison

The family6 normal path matches captured VS877/PS878: raw source tangent/binormal, normal-map XY=`(R*A,G)*2-1`, positive reconstructed Z, normalized mapped normal, then `mapped+(radial-mapped)*NormalDisable` without a final material-normal normalization. Main profile NormalDisable1 preserves radial normals. Native color PS does not use front-facing input or flip the normal on backfaces; root likewise does not flip it. Root disables culling for family6, matching native cullNONE. Texture wrapping and trilinear/linear filters are consistent with native repeat sampling.

The cutoff uniforms are correct: main100/255; sapling/green128/255. Native depth also compares noise.BLUE at leafUV with instance dissolve; all captured main leaf instances have dissolve1, so that test admits every noise value and cannot explain these reference black patches.

Native main diffuse image13901 is `VK_FORMAT_BC1_RGBA_UNORM_BLOCK`, with source343437 BC1 top-mip hash recorded in the binding report. Root textures use `GL_RGBA8`, also UNORM. Both sample the stored RGB directly. An sRGB conversion or gamma adjustment would change the native contract.

## Diffuse content correlation and limits

Current diffuse RGB is close in average brightness to the decoded authored1024 mip: main visible RGB means107.33/110.38/31.85 versus native108.22/111.33/32.14; green sapling87.16/104.71/24.26 versus87.71/105.58/24.68. It is not byte-identical. Current generated smaller mips differ more: at512, main green104.49 versus110.01; green sapling95.86 versus105.44. Detailed native-visible RGB comparisons are retained in the two RGB correlation reports. This is a texture mip-content difference, not evidence for a shader color-space change.

This audit changes no core or asset files and launches no GPU work. Root staged the coverage correction during review; retained source snapshots may therefore already contain that correction. The corrected image has not been validated here. Remaining shape/coarseness can still reflect the port's400/1600cm global-cluster LOD policy and original geometry differences. The captured main leaf movement is zero; native sapling movement is separately recovered. No brightness, cutoff, normal or backface tuning is recommended by this evidence.

Raw native SPIR-V, corresponding DXBC assembly, current material bindings and source snapshots are included alongside this report for review.
