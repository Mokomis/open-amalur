# Generation4 coarse native attributes

Deploy only the 36 `world/c*.bin` files and patch per-cell/LOD triangle counts using `index-triangle-counts.json`. Materials, texture resources, terrain profiles, grass files, index header and grass metadata must remain the current integrated versions. No index.bin is supplied.

All cells were rebuilt from SHA-verified original before-world backups where present, otherwise verified unchanged baseline cells. Generation3 exact water removal index subsets were retained. Frozen coarse source-owned overlays replace the corresponding disjoint original triangle indices; all native 76-byte records, including packed leaf wind and radial-length bits, are checked byte-for-byte after serialized reread. Original retained vertex positions/UV0 and baseline-expanded 76-byte records are unchanged.

The 36 cells carry 28,450 LOD1 plus 5,461 LOD2 native source-owned triangles. They retain original coarse positions and UV0; shader attributes are propagated from their exact original source ancestors. This is the port global-cluster geometry, not a claim to original-game authored LOD meshes.

All 6,494 native-water legacy triangle removals across every LOD remain exact when these 36 files are combined with untouched generation3 cells. Prior generation files, live assets, core sources and original inputs were not modified.
