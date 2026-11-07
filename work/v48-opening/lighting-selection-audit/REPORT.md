# First-room lighting selection — bounded static audit

Direct source linkage exists: SPACE1417252 root+0xc0 contains2 environment records, each0x570 bytes; record0 matches the shipped Lighting_DGN_WellofSouls_Start XML on every mapped float32 time-key field. Root+0xc8 contains2 source60B lighting volumes. Volume0 references settings index0, not a guessed name-based activation.

Volume0 source T=(4104.502441,2541.979004,12.481781), Q=identity, S=(9.918001,8.458000,5.296000), fade2000. Native00db2820 uses half extents=float32(S*1000)*0.5. PE doubles at014c61a8=1000 and013be500=0.5 are preserved in geometry-constants.json. The two exact C0 records and two exact C8 records are saved as .bin files, with source offsets/SHA in lighting-selection-evidence.json.

At BOTH authored player spawn(4312,2806,-314) and recorded custom camera eye(4547.21387,2805.99219,-116.858307), volume0 box distance=0 and raw weight=1. Volume1 is more than24,000cm away, fade1000, weight0. Native finalizer00e170b0 adds the region BASE only with max(0,1-sumLocalWeights), then divides by total weight. For these two local volumes at either query point, normalized start weight=1, base weight=0.

Native path: SPACEvf3 00fdc910 invokes00dd0580 with source+b8;00dd0580/00ce21d0 import C0 settings and C8 volumes.00ce21d0 builds cache entries stride0x314 pointing at source environments stride0x570.00df6150 iterates source volumes stride0x3c, computes weight using00db2820, accumulates settings and total at+0x2c4.00ad2000 assembly confirms full3-axis outside-box Euclidean distance; its decompilation omits SIMD X/Y arithmetic, so the saved ASM is authoritative for that kernel.

Query point: SpaceRenderEventHandler00fcce20 takes event+0x1c into00fc6800.00fb0bb0 copies queryObject+4/+8/+0xc XYZ into the volume-distance call. This is a render-event query position, not a direct player-coordinate lookup. The producer of that payload was not resolved in this bounded pass, so camera identity is not claimed solely from its matching offset. Checking BOTH supplied points removes that ambiguity for these two volume weights.

Important mode condition:00fc6800 branches on00dccd00. Result0 uses ordinary local/base evaluation. Result1 also evaluates ordinary local/base, then calls00fb8990 for an additional override. Result2 calls00fb8870 and bypasses normal local volumes. Actual original opening override mode and payload/temporal state were not observed; final rendered colour cannot be established without correlated native runtime evidence. Portal-neighbor contributions are not fully evaluated here.

The direct authored Start contributor is proven; equivalence of the port's blue rendering is not. Keep the owner's BASE default and the Start candidate separate. No automatic profile activation, colour interpolation, tint adjustment, game launch/input, DB mutation or core/asset change was made. No Mac mirror was created.


## Portable C99 helper and tests

native_light_volume_weights.h/.c implement only source T/Q/S outside-box distance, native fade weight, residual BASE and normalization. The quaternion kernel follows db2820→ac11b0→ac1720; q products use native float-product/double-sum order. Quaternion inputs are approximately-unit, never silently normalized. Source scales are admitted when finite/nonnegative. No source profile, color interpolation, current Space selection or unknown override input is invented.

API: oa_light_volume_distance; oa_light_volume_fade_weight; oa_light_volume_weights. The convenience weights call applies one caller-supplied Space weight to its group of local volumes. For multi-Space aggregation, collect raw fade weights with each Space's own supplied weight and normalize once across the combined contribution set; the helper does not infer portal weights.

Mode NORMAL(0) computes ordinary weights. ADDITIONAL(1) computes that ordinary component but returns ADDITIONAL_INPUT_REQUIRED: it is NOT a final overridden result. HARD(2) returns HARD_INPUT_REQUIRED without touching the caller's output buffers. Parent must retain its existing owner-preferred BASE default; these are calculation primitives, not an automatic activation change.

| Test | Ordinary local weight(s) | BASE |
|---|---|---|
| Authored spawn, two real records | 1,0 | 0 |
| Recorded camera eye, two real records | 1,0 | 0 |
| Volume0 center / exact box face | 1 | 0 |
| 1000cm beyond box, fade2000 | 0.5 | 0.5 |
| 2000cm fade endpoint / farther | 0 | 1 |
| Two overlapping identical volumes | 0.5,0.5 normalized from raw1,1 | 0 |
| Current local Space weight0.25 inside | 0.25 | 0.75 |
| Zero fade | inside1, outside0 | complementary |
| Rotated90-degree nonuniform box,250cm outside/fade1000 | 0.75 | 0.25 |
| No local volumes | none | 1 |

Existing Windows MSVC compiled the C99-compatible source with /TC /std:c11 /W4 /WX /fp:strict. The standalone test executable passed47 checks; helper-validation.json, helper-build.log, helper-compiler.log and helper-test-output.txt retain results. build_helper_tests.cmd reproduces the test only in this audit directory. A first attempt hit a log file sharing error; separate setup/compiler logs resolved it, without tool reconfiguration.

Both original Start profile's four time keys are identical for every decoded field, so time-of-day interpolation does not alter these local Start settings. This does not resolve cinematic override mode, neighbor contributions, exposure adaptation or the original render-event query payload identity. No further native expansion or runtime action was performed.
