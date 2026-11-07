# Native static authored mip replacements

Stage only; original/live assets are unchanged. Merge only `world/t658.bin` through `world/t676.bin`. Texture IDs, texture count, material profiles and index metadata stay unchanged.

|ID|Source asset|Staged base|Levels|Provenance|
|---|---|---|---|---|
|658|250070|32x32|4|Captured image 12707|
|659|299244|128x128|6|Captured image 4827|
|660|510546|4096x4096|9|Captured image 13729|
|661|758816|1024x1024|9|Authored source; residency unverified|
|662|604240|1024x1024|9|Authored source; residency unverified|
|663|758813|1024x1024|9|Authored source; residency unverified|
|664|758815|1024x1024|9|Authored source; residency unverified|
|665|758814|1024x1024|9|Authored source; residency unverified|
|666|489466|256x512|7|Captured image 14126|
|667|489465|256x512|7|Captured image 14135|
|668|4002|64x64|5|Captured image 4762|
|669|572520|4096x4096|9|Captured image 13496|
|670|1412166|1024x1024|9|Authored source; residency unverified|
|671|1412168|1024x1024|9|Authored source; residency unverified|
|672|1412167|1024x1024|9|Authored source; residency unverified|
|673|1412172|1024x1024|9|Authored source; residency unverified|
|674|1412174|1024x1024|9|Authored source; residency unverified|
|675|1412173|1024x1024|9|Authored source; residency unverified|
|676|3030|256x256|1|Captured image 3418|

Eight images have actual fragment-shader sampling in the native recording. All48 mip payloads match original BC source bytes by SHA. Image/view IDs, draw indexes, pipeline IDs, descriptor bindings, view mip ranges, native image dimensions, original-file offsets, per-level BC/RGBA hashes and output hashes are retained in the JSON evidence. SPIR-V resource loads were inspected so unused descriptor bindings were excluded.

For the other11 maps, no active captured image with matching content was found. The staged version keeps each current1024x1024 base dimension and uses the complete original authored nine-level chain beginning at that dimension. These maps are explicitly source-only and do not claim verified native GPU residency.

The native branch maps666/667 are256x512 with7levels, from full-size source mip2 (DDSpart3). The original authored mask resources660/669 are4096x4096 with9levels ending16x16, rather than the previous1024 cap. Native3030 has only one256x256 mip; no synthetic levels are appended. Every level is decoded independently from original BC1/BC3 into portable RGBA8; no resize or generated mips are used.

The existing loader already uploads every supplied level and sets MAX_LEVEL=levelCount−1, which is required for intentionally partial authored chains. Anisotropy/filter choices are separate renderer state and are not changed by these files.

Total staged bytes: 242,248,264; previous19 files: 84,264,064; delta: 157,984,200 bytes (150.67MiB).

Validation re-read all staged files, checked every framing/hash, and re-hashed every chosen original source file unchanged. No original source, archive, database, prior generation or active renderer file was edited.
