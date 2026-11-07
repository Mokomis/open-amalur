# First-room source environment probe

The Well of Souls first room SPACE1417252 has one authored environment reflection probe. It is not a no-point scene, so the creator's SimpleBlackCube is not its normal reflection resource.

Patch source1417252.space_bxml SHA118e4b67ecd5684957b3619dc10c64079ddd2e8eabe01fd0f891c783f82c643d stores the native probe pointer/count at payload+0xf0, which is raw file+0xf8 after the8-byte BXML fixup header. Count1, pointer0x8ae4. The20B record is XYZ(2007.81494140625,3784.437255859375,213.244384765625), reservedWORD0, texture1576506 at+16. Initial source record at0xd114 is byte-identical.

Existing native Space vf3 fdc910 passes payload+f0 to c8a9e0; vf4 ff04f0 publishes through d1ad60. The prior reviewed d1ad60->command28->RenderConfig+28 and c97e90 nearest3D query remain applicable. These positions are copied directly, without an extra Space origin transform.

## Staged runtime asset

1576506.oacube
SHA256 7bdbb9b9d8e506395b52c1ffe7c1051411c311ee8b16ca3108ee4623d65b719c
524208 bytes

The input installed initial_0.pak/1576506.dds SHA0460c72ee34d20cbc24827da20db88818be7479983d8c98b4863608be71ba280 is65558 bytes, KEEN format1 BC1 linear UNORM,128x128,6faces,6authored mips128/64/32/16/8/4. No patch asset of this name is present in the installed archive lists. source-extraction.json records exact archive precedence.

Runtime carrier is the existing OACUBE1 format: magic8 OACUBE1\0, u32width128,height128,levels6,GL_RGBA8(0x8058); each mip has u32totalRGBAbytes followed by6tightfaces in+X,-X,+Y,-Y,+Z,-Z order. Data is mip-major, source is face-major. Rows/channels are unchanged; no R/B swap, flip, rotation, resize, generated mip or gamma conversion. All source BC slices and decoded RGBA face hashes are pinned in cube-manifest.json.

The shared KEEN cube layout uses the already byte-proven source744821-to-native3423 all30face/mip correspondence from materials/evidence/eye-cube-source-to-native.json. This is not a direct captured1576506 resource join. Standard BC1 decoding follows the existing reviewed Pillow exporter; original GPU BC interpolation rounding is not claimed universally bit-identical.

stage_probe.py reproduces the carrier from the pinned source. The parser independently validates exact extents/payload hashes/no trailing bytes. A standalone existing ANGLE GLES3 fixture uploads all36faces/mips and samples every face/mip center against the exact carrier bytes:36/36 exact, GL0. test-output.txt names the RTX4080SUPER D3D11 ANGLE2.1.27600 renderer. It is an asset upload/sample test, not native game or scene parity.

## Registered collection scope

REGION1262814's ordinary one-hop source portal graph links first room1417252 to1751255. The neighbor has one additional point at(-6247.0185546875,2624.607666015625,422.5018615722656), texture1762548. The native query compares all registered collections, so calling1576506 the global sole probe would be incorrect. Choose1576506 when it is the nearest point at the actual query position; implement the existing generic nearest-point query across the actual loaded collections. No all-positions-inside-Space guarantee is inferred from the probe owner. This delivery stages requested1576506 only;1762548 is a separate asset not copied here.

scene-probe-collections.json inventories all Region-listed Space source probe fields, exact source paths/SHAs/points, and the first-room graph edge. The reviewed Region vf3/vf4 does not publish the Space EnvironmentProbeInstanceMgr path. Region payload+f0 is a different schema field and must not be parsed as a Space probe. Region ambient World/Character cubes are independent of these spatial reflection probes.

No sealed material files, live loader/pins/assets/core/UI or user state were changed. All new files are inside this first-room-probe staging folder.
