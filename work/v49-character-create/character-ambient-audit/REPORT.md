# Character ambient identity and opening-source payloads

CharacterAmbientMap is a separate cube from world ambient, proved by active capture bindings and all1536 source bytes. Opening BASE and local Start independently select their own charactercube1; those two payloads happen to be byte-identical. Their worldcube0 payloads also match exactly. The parent's supplied existing preview world SHA is therefore correct for both, not evidence of a Start composition defect.

## Captured identity

Original recording work/v31-native-slice/captures/amalur_trim_trigger_20261105T113036.gfxr SHA256 72c3524703435311542d555dc419771d820f6baf81c84676ef2c6dc28c367209. Existing work/v33-native-camera/dalentarth.jsonl SHA256 1fb27de5dcfca8b5795e92292ee27de0dc2ef6fe7beb79e932b075c53c40c25e. No replay/new capture.

| phase97 draw/PS | Cube binding | Image/view | Sampler binding/object |
| --- | --- | --- | --- |
| 67406 /352 | 36 (D3D t4) | 7502/7504 | 20 (s4)/336 |
| 67421 /376 | 36 (D3D t4) | 7502/7504 | 20 (s4)/336 |
| 66910 /792 terrain | 32 (D3D t0) | 7496/7498 | 16 (s0)/336 |
| 68785 /878 foliage | 32 (D3D t0) | 7496/7498 | 16 (s0)/336 |

All8x8x6, one mip, R8G8B8A8_UNORM; CUBE views layers0..5, identity swizzles. Sampler336: linear min/mag/mip, clamp U/V, repeat W, no anisotropy/comparison, LOD0..1000 (only mip0 exists). capture-binding-summary.json seals exact definitions; selected-character-world-bindings.json retains full snapshots; active-cube-draws.json retains all826 cube-bearing draw snapshots; active-cube-binding-counts.json groups by phase/PS/binding/image.

Captured PS352 lines294..300 shuffle normal xyz to xzy and sample cube36 with sampler20. Lines302..308 multiply cube RGB by interpolated vertex alpha;412..419 multiply by material base and clamp G2. See captured-character-ps352-excerpt.txt. Exact RustySword material-to-embedded-hash registration retains the separate initial-sword-material-audit qualification; current resource proof does not depend on it.

## Captured Gorhart source-byte join

extract_ambient_images.py decompresses three existing InitImage records with pure Python LZ4. Each3072B allocation contains six tight256B faces first (1536B) and1536B allocation-tail padding, NOT per-face stride. Independently reviewed world7496 hashes are reproduced.

Authored patch Region431608 SHA256 5c867388c94039b14b4803bc7d2c738d17da38d2f2303025858f650aa04f9803 explicitly selects Noon world2 at payload21396 and character3 at21412. Comparing EVERY authored cube, with ONLY R/B swap per texel:

- cube2 uniquely equals captured world7496/7499, RGBA SHA256 df71f39a8cfa77673155c7ec5d5de4b3d36583c05c712ac9022e920c96fcef1c.
- cube3 uniquely equals captured character7502, RGBA SHA256 693bcf48abd29a8a7171f482e67cadae493b23199254fa07a51a5cea63cd2348.
- World and character differ; no face permutation, row flip, rotation, sRGB decode or extra tint was needed. Faces: +X,-X,+Y,-Y,+Z,-Z.

Exact source face offsets and raw comparison hashes: authored-character-cube-join.json, ambient-image-extraction.json. Gorhart cubes are reference evidence, NOT opening inputs.

## Opening BASE and Start

Offsets below are PAYLOAD offsets; add8 for file offsets. Each role has its own cube table namespace.

| Source | Environment | Cube table | World fields, all4 times | Character fields, all4 times |
| --- | --- | --- | --- | --- |
| Region1262814 BASE | F0 record0 at6816 | E8 | index0:8176/8180/8184/8188 | index1:8192/8196/8200/8204 |
| Space1417252 Start | C0 record0 at23840 | B8 | index0:25200/25204/25208/25212 | index1:25216/25220/25224/25228 |

Region SHA256 c65e0a23a4edf3d0deaf5444d3785534351bee82e1c2d59e23bfa0b291b8ba2d.
Space SHA256 118e4b67ecd5684957b3619dc10c64079ddd2e8eabe01fd0f891c783f82c643d.
Start C0record0 SHA256 d7bf3d7e330a2b58cf2df480a39a6d68365ae41bb97a69e950600ff569756153.

The existing work/v48-opening/lighting-selection-audit proves C0record0 matches shipped Lighting_DGN_WellofSouls_Start mapped fields. Space vf3 passes source+B8 to dd0580/ce21d0: the importer copies that group's cube pointer/count, then builds C0 setting-cache entries. Preserve that owning table provenance. C0record1 instead selects world2/character3 all4times; do not substitute it for Start0.

Both BASE and Start charactercube1:
- Source BGRA SHA256 a09e463bd738571bf4d19dfb19173ee4ef58972283ddf046ef59f0645ac41836; first108,110,108,255.
- Converted RGBA SHA256 e344c034255e814943cbf052374993a7dc6e938693517412e4ef2546a81ad0bd.
- BASE face payload offsets5280,5536,5792,6048,6304,6560.
- Start face payload offsets19232,19488,19744,20000,20256,20512.

Both BASE and Start worldcube0:
- Source BGRA SHA256 ec33749a7ff2170480dabcac78bb702c386b0174429451ef2d28e70820a91985; first33,24,20,255.
- Converted RGBA SHA256 d030bafd48e63d4558d5592d7814db6503da0dac0cded1f6841c4efb345d30c9.
- This equals the parent's supplied hash for BOTH current preview world cubes. This subagent compared the supplied hash, not those preview files. Retaining it in Start is source-correct.

## Integration and staged paths

All files reside ONLY under work/v49-character-create/character-ambient-audit:

- opening-base-character-ambient.bgra, .rgba, -bgra.inc
- opening-start-character-ambient.bgra, .rgba, -bgra.inc
- opening-base-world-ambient.bgra, .rgba, -bgra.inc
- opening-start-world-ambient.bgra, .rgba, -bgra.inc
- opening-character-cubes.json and opening-world-cubes.json: complete hashes/offsets/explicit time fields/source paths.
- seal_opening_character_cubes.py and seal_opening_world_cubes.py: reproducible recipes.
- source-payload-validation.json: all four1536B payloads passed SHA, exact R/B conversion and C-include roundtrip; BASE/Start equality passed.

Existing preview/room_lighting.c storage convention: use .bgra unchanged and the existing R/B upload swap. Direct GL_RGBA8/GL_RGBA upload: use .rgba and DO NOT swap again. Six consecutive8x8 faces, one level; do not generate mips or sRGB-decode. Sample with normal.xzy; each shader family's vertex-alpha/ambient arithmetic remains its own contract.

Generic selection is explicit active environment character_ambient_cube_index at env+560, resolved within owning lighting group's cube array. World uses env+550. Never derive world+1, use slot ordinal alone, or inject Gorhart data. Normal/additional/hard overrides and blend selection remain parent's existing logic. No runtime handle number is invented; source table and captured resource identity prove the payload independently.

Opening source fields/bytes and shared carrier conversion are proven; no correlated original-opening resource capture exists here. Exact opening override mode/portal blending and rendered appearance remain unobserved. Generic diffuse character preview does not imply skin/cosmetic parity or pointlight113 coverage. Owner-preferred BASE is unchanged. No live core/menu/preview files, DB, save or original game UI were modified. No Mac mirror.
