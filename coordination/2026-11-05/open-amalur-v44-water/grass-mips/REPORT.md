# Native grass authored-mip audit

The current integrated grass textures already retain every authored native mip. No replacement or new texture IDs are required. Staged `world/t655.bin`, `t656.bin`, `t657.bin`, and `t677.bin` are independently regenerated from original/captured BC payloads and are byte-identical to current integrated files.

Maps655/656/657 are 1024x1024 with nine levels ending4x4. Noise677 is16x16 with three levels ending4x4. Every one of the30 original BC mip payloads SHA-matches the native recording. There is no resize, generated mip, or discarded authored level. `grass-mip-validation.json` records every payload and output hash.

655 contains diffuse343428 RGB and raw344837 GREEN copied into ALPHA independently at every authored level.657 contains that raw alpha/specular atlas unchanged;656 contains native packed normal3520. Native depth SPV327 samples344837 GREEN and noise1816 GREEN. Current grass shader samples655 ALPHA, which is byte-for-byte equivalent at every mip. All material2D samplers have matching native trilinear/linear, repeat, zeroLOD-bias state, so the merged channel is valid. Direct657.GREEN is available if desired without an additional texture.

The one state correction is generic texture anisotropy: active oa_stream.c:137 forces4, whereas captured grass depth/color samplers have anisotropy disabled. Override anisotropy1 forIDs655,656,657,677 for native parity. The loader already sets MAX_LEVEL8 for the maps and2 for the noise.

SPV327 and894 assembly and all34 relevant depth/color descriptor snapshots are included. Color grass also binds ambient cubes7496/7499,8x8x6 RGBA8 with onelevel; raw blobs and metadata were preserved on Mac and supplied to the lighting owner. This audit does not replace the shared room-lighting cube.

Only new private grass-mips files were written. Original assets, databases, prior research outputs and live integrated assets remain untouched.
