# LOD1/2 native attribute propagation

Frozen independent inputs for a later pack merge. Existing core, active pack and static overlay were preserved.

All113,658 source-correlated full-resolution triangles were mapped to their exact `zone_pos.npy`/`zone_uv.npy` ancestors:108,786 static and4,872 leaf. There are zero missing or ambiguous ancestors. The native material ID lookup preserves aliases of legacy rows19/20 instead of choosing one by texture signature.

The existing port uses global vertex clustering with400cm and1600cm grids. Its cell ownership remains based on the original full-resolution centroids. Triangle order within each material stays stable; clustering removes triangles whose corner cluster IDs coincide. Reproducing that exact policy gives an original global ancestor for every surviving supported triangle, without spatial approximation.

| Detail level | Cells | Surviving source triangles | Exact cell joins | Unmatched |
|---|---:|---:|---:|---:|
| LOD1 /400cm |18|28,450|28,450|0|
| LOD2 /1600cm |18|5,461|5,461|0|

`cell-overlays/cX_Y_LOD.oawt` uses the existing OAWT76 schema. Its positions and UV0 equal the actual selected coarse cell vertices byte-for-byte. Normal/tangent/binormal, native material ID, RGBA8, UV1 and final field are copied from the corresponding source triangle corners. For family6 this preserves the packed wind half pairs in UV1 and radialLength float bits@72. No new material profiles or shader families are introduced; the same33 native profiles already allocated by generation3 apply.

Each matching `.remove.u32` contains offsets into the current cell's index array; each offset identifies one three-index triangle. The manifest records source cell hashes, native material counts, output hashes and every ancestor global triangle index. Use the actual cell snapshot named by the manifest for merging.

`recover_lod_attributes.py` is the retained reproducible producer. `summary.json` is the compact result; `lod-attribute-manifest.json` contains the full evidence. `lod-cache/` retains source ancestry and reconstructed cluster results. Production checks are integrated into the producer; no app build or new test suite was added.

This propagates recovered shader attributes over the current port's coarse geometry. It does not claim to recover original-game LOD geometry, change the clustering policy, average normals, or invent attributes for unsupported families.
