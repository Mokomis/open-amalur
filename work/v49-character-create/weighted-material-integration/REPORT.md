# Staged weighted CharacterHardLight adapter: four Almain clothing parts

Complete as a bounded opt-in module, staging ONLY. No live v19/core/UI/preview/config/database/assets were edited or deployed.

Files oa_weighted_hardlight.c/.h plus clothing_source_tables.inc use the existing root oa_post caller-vertex factory, oa_character_hardlight_upload, actual production character repair/pose/bones APIs, original OACAT RAW VBs,12source portable D/N/S chains and exact opening CharacterAmbientMap. No generic cosmetic/skin fallback or guessed race compatibility is added.

## Supported scope and admission

Approved source parts only:
| Part | FAB/assembly | MID | Source format | COLOR provenance |
| --- | --- | --- | --- | --- |
| 1 feet | 660455/0 | 660429 | 56B/type17 | native_shared_all_ff |
| 2 hip pack | 660458/0 | 660430 | 60B/type22 | authoredRGBA |
| 3 legs | 660458/1 | 660428 | 56B/type17 | native_shared_all_ff |
| 5 shirt | 660459/1 | 660426 | 60B/type22 | authoredRGBA |

Ready mask46=0x2e. The caller explicitly allow-lists parts; unsupported bits do not admit a part. Whole original pack SHA must match the known Almain pack AFTER both production repairs:40b7c1ba7147a1b0d35e754362d7313603f748a7733b75210098a4de7ce40026. Original pack ede399d... and original OACAT ab02a4a4... remain untouched. Production oa_character_repairs_apply actually produced this exact heap SHA (2781normal corrections,2palette prefixes). No repaired pack file is written by the adapter.

The pinned original OACAT is fully hashed and bounded parsed. The adapter uploads each retained RAW56/60 source VB, not the old52B float-normal/float-weight vertex conversion. Source UV0, N/T/B SNORM and first3SNORM weights are thus preserved. All4 source joint indices are range checked, including zero-weight entries because nativeVS loads all4. Nonfinite P/UV and zero source basis vectors reject the part.

Source56 has no authored COLOR. Its source presence flag stays absent; runtime color1 is explicitly native_shared_all_ff, supported by the separate captured stream1 audit. Source60 retains its actualRGBA bytes. UV1 is not read or synthesized. Shared shader interface UV2 is an unused zero padding varying, not an asserted source attribute; family12 never samples it.

These source clothing assets were NOT matched to executed draws in the existing native reference frame. Source identity/layout/material proof and generic native shader/default-color proof are separate; original clothing-instance capture equality is not claimed.

## Proven weighted basis implementation

The new vertex stage reconstructs w3=1-w0-w1-w2 without clamping or weight renormalization, accumulates joint1,0,2,3 and uses three affine rows per joint. Binding-style palette capacity is78entries/234float4s. Positions use dot4; N/T use dot3.

Actual production oa_character_bones rows already include entity facing and feet. Therefore:
- P and N/T skin DIRECTLY to world, with no second entity rotation.
- N/T normalize independently AFTER world skinning.
- B does NOT joint-skin. It receives only c->facing around worldZ, then normalizes.
- The source frame is not orthogonalized and B is not cross-derived.
- Fragment stage is the existing verified family12 source math/CharacterAmbientMap and shared forward emulation, including independent HALF Gbuffer-term emulation.

This follows captured VS375's deliberate P/N/T-versus-B asymmetry under the current rotation/translation-only entity producer. Arbitrary entity scale or a changed bone-row coordinate convention is not inferred/supported here.

## API and host integration

Open signature returns admitted PART bits:
oa_weighted_hardlight_open(g,c,originalOACAT,size,characterCubeBGRA,1536,
 read_malloc,user,texturePrefix,allowMask,lightCapacity,error,errorCapacity).

Prerequisites: production repairs applied to heap BEFORE oa_character_parse; caller's oa_character stays alive/immutable in bytes while adapter exists. Open copies GPU geometry and textures, does not retain OACAT/cube buffers and never mutates c. Callback returns malloc-owned whole file; adapter frees it. Prefix is concatenated with exact generated source OATX filename.

Per frame:
1. program=oa_weighted_hardlight_begin(g,actualWorldEye). Finite actual eye is REQUIRED because rim is view-dependent even with direct lights off. No draw is admitted after open alone.
2. Host uploads real shared sun/shadow/AO/fog/points and resources to this returned program as needed. begin establishes safe cube-only defaults, typed no-light grid/fullAO/depth resources, features128|16|4, but does NOT establish source room lighting or native point113 behavior by itself.
3. oa_weighted_hardlight_draw_part(g,c,part,worldVP) returns1submitted,0unsupported/hidden/invalid/native-bit-off,or-1GLerror.
4. Skip the old renderer for that part ONLY after successful submission. Leave all other parts on its existing path. Changing c or data invalidates this bounded adapter; close/reopen with reviewed data.
5. close before freeing c or reopening. Adapter owns its program, VAOs/VBOs/IBOs,12maps,cube and tiny typed dummy resources. It never owns/changes caller character heap.

begin MUST happen before host environment upload, not afterward (it resets those defaults). program() exposes the shared program; ready_mask() exposes admission. Root owns actual mixed old/new per-part draw routing; no live routing was added here.

Draw mutates program/VAO and texture units0,1,2,8 plus material/bone uniforms. begin also binds typed dummy resources at9/10/11. Host can override sampler assignments/resources after begin for native AO/shadow/light-grid. Native CharacterCube remains owned at8. Rebind/invalidate caller-owned texture-slot caches before returning to renderers whose cached bindings this code changed; existing global uniform-cache reset on close does not reset external texture-slot arrays. FBO,viewport,depth,blend,cull are caller-owned and unchanged by draw. This is standard explicit render sequencing, not an isolated state-preserving UI widget.

Raster fixture disables culling so it tests all source geometry; native back-cull/CW and current host projection policy remain the host's render-state integration responsibility. No unsupported opaque/transparent state fallback is hidden inside the material adapter.

## Resources and provenance

Borrowed source stage (unchanged): work/v49-character-create/material-integration/native-clothing-stage.
12portable OATX files are looked up through generated tables with exact per-file byte sizes/SHA. Internal format is linearRGBA8; all authored <=512-tail levels upload individually; no sRGB transform, mip generation or guessed normal/spec maps. Native source slot mapping is0D,3N,2S to GL0/1/2. White source slot1 is not consumed by HardLight.

Opening character cube input: character-ambient-audit/opening-base-character-ambient.bgra; Start's separate table yields identical bytes. Authored BGRA SHA a09e463bd738571bf4d19dfb19173ee4ef58972283ddf046ef59f0645ac41836. Loader swaps R/B once into nativeRGBA8 six8x8faces; one level, no generated mips, linear filtering. It will reject Gorhart or worldcube payloads. This pins BASE/Start inputs, not arbitrary world environments.

Source material params are generated from the checked source manifest, not manually tuned. ConstantColor is preserved/uploaded but source HardLight ignores it. RawGloss20 reaches source G0 semantics unchanged; shared exponent is5. Native cube/HardLight and shader-proof reports remain in their earlier audit folders.

## Actual build, GPU results and fail-closed tests

Existing Windows MSVC compiled the final adapter and actual root oa_character/attributes/material/post/cache/nativepost dependencies with no warnings/errors. No stubs replaced the production pose or shader factory. Only logging/unused desktop probe hook are local fixture stubs. Private import tables use existing EGL/GLES DLLs; project libraries were not changed.

Renderer:
ANGLE2.1.27600 gitf39c3524d091, OpenGL ES3.0/GLSL ES3.00,
NVIDIA GeForce RTX4080SUPER, D3D11 driver32.0.16.1692, EGL1.5.
256x256pbuffer, no native window/game/device actions.

Tests ran actual production repair/parse/pose/bones then actual adapter draws for16part-cases:
idle clip0/frame0 and walk clip1/frame8, each with facing0/feet0 plus facing.7/feet(35,-15,10) or1.4/feet(-50,25,10). All16part images contain geometry (175..4246covered pixels); all4combined images contain clothing. production-pose-contact-sheet.png visually shows ONLY the selected clothing (head/skin/hair deliberately remain outside this module).

Transform feedback captures the ACTUAL adapter vertex stage at every source vertex. Independent sourceVS375 equations use actual C bone matrices, raw source weights/TBN/UV/color and a separately derived production half-angle entity quaternion for B:
12752vertices /229536float components compared.
Maximum position component error0.000030517578125cm.
Maximum N/T/B component error1.7881393432617188e-7.
SourceUV0 and COLOR match EXACTLY, every vertex.
Incorrectly skinning B would differ by up to.709302187 per component, so this fixture detects that failure.
feedback-validation.json contains all errors, feedback/raster hashes and world bounds; manifest.json seals all bone-file hashes. No original capture pixel equality is claimed.

Fallback tests passed:
- Missing feet diffuse: returned mask44 (0x2c), all other parts admitted; old feet path stays available.
- Corrupt OACAT and wrong character cube: mask0/no program.
- Unsupported part0, hidden feet, and native bit128OFF: draw returns0.
- Before valid begin(actualEye): draw returns0.
No silent map/cube/default-color substitution occurred.

Existing NDKr30 additionally compiled final oa_weighted_hardlight.c as Android26 ARM64 C99 with -Wall -Wextra -Werror. This is object-compilation proof only, not Android GPU/device execution. The first cross-compile identified a header-order issue in this new module; moving the existing SHA header after string.h resolved it without changing core files. Final Windows+ANGLE and CPU feedback checks were rerun after that change. No shared quantizer experiment/change was made.

## Reproduction and limits

Run generate_source_tables.py only to regenerate owned static tables from pinned source manifests. build_and_run.cmd produces the isolated EGL fixture; existing Python312 validate_feedback.py checks its feedback. compile_arm64.cmd produces only a local staged object. These do not deploy/run the game. Resource filenames/prefix in fixture point to existing Windows staging data; Android host must supply an asset reader/deployment mapping if root admits this module.

No full creator, all-race/female compatibility, skin/head/hair material, source animation timing equivalence, actual sun/point113/shadow/fog/AO lighting test, full-room original comparison or FPS claim. The shader compiled with113light capacity but fixture leaves illuminating sources off. Source texture-tail/BC-decoder rounding and old main-rig/facial ancestor policies retain their prior qualifications.

All9reviewed core source/header hashes before/after match. Original pack,OACAT,OACPL,cube and all12portablemaps match their existing hashes (preservation-receipt.json). No live/core/UI/preview/config/database/default/user-data files changed. Module remains opt-in staging only; parent owns any admission/merge. Work stops at this tested module and notes.
