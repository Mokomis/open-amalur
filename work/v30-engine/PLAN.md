> Status 2026-11-05: original-engine port PAUSED; custom engine resumed, Windows-first development. See ../v39-custom-resume/PLAN.md. Preserve all work below as reference.

# Real-engine port plan (started 2026-11-01)

Goal, in the user's words: "using the same engine or version of it that can run on the tablet and other hardware using vulkan."
work/v19-host (custom GLES3 engine) is frozen: salvage and fallback only. Keep all decompiled code and APKs private.

## Measured: koa.exe (build cs:15032, sha256 starts 16a400f6e8fc10db)
Run work/v30-engine/pe32_size.py. Outputs: imports.json, rtti.json in the same folder. (pe_size.py assumed 64-bit and its output is wrong.)
- 32-bit x86 PE, image base 0x400000, ASLR and large-address-aware on. Compiled with SSE (heavy addps/mulps), almost no x87.
- .text 16.12 MB. Ghidra 12.1.4 default analysis (7 min, project in work/v30-engine/ghidra, list in functions.tsv): 45,842 functions, 161 thunks, 44,852 unnamed. They cover 11.44 MB; the other 4.68 MB is not yet attributed (data, jump tables or undiscovered code). Sizes: 35,239 at 256 bytes or less, 147 over 4 KB, 10 over 16 KB. RTTI classes not yet applied to the functions.
- No .pdb and no exports. 2,305 RTTI class names (1,841 in BHG), 13 source-like paths including koa.pdb build path.
- 349 imports from 19 DLLs. Graphics: only D3D11CreateDevice plus D3DReflect. Input: XInput, DirectInput8, raw input. Audio: XAudio2 through keen::SoundSystem. Video: binkw32. Platform: steam_api (10 functions).
- WS2_32, WLDAP32, CRYPT32, Normaliz, OpenSSL DLLs: networking, likely not needed for single player. Unverified.
- Middleware seen: Bullet 2.88 (open source), Lua 5.1 variant (open source), OC3Ent (FaceFX, closed), keen sound system (closed), Bink 1.3 (closed).
- No Havok, Scaleform, PhysX runtime classes, FMOD or Wwise strings found. "PhysX-PC" strings exist; meaning not checked.
- Sections are ordinary, no packer section seen.

## Measured: tablet (OPD2515, SM8845P, Android 16)
- arm64-v8a only, no 32-bit ARM. 11.7 GB RAM, 400 GB free. 4 KB pages. Driver has SVE2, atomics, lrcpc.
- Qualcomm Vulkan driver has BC textures, geometry and tessellation shaders, transform feedback, robustness2, custom border colour, dual source blend, depth clamp. VK_EXT_memory_budget absent.

## Decision 2026-11-01: work on Windows first
The user asked to do this on the Windows PC. All engine work (hooks, decompile, Vulkan) is developed and checked there, where the real game runs on the RTX 4080. The tablet is parked until the PC build is worth porting.
Tablet result so far: koa.exe runs under DroidDeck and reaches gameplay, but lighting flashes badly. Tested and not fixed: two Turnip builds, TU_DEBUG=sysmem, TU_DEBUG=sysmem,nolrz,noubwc,flushall,syncdraw. Change scores (8 frames, standing still, not a controlled comparison): all safeguards 4.4, none 6.2. Not tested: WineD3D, native d3dcompiler, FEX settings. Launch options on the tablet are now empty.
PC test done 2026-11-01: koa.exe through DXVK 3.1.1 on the RTX 4080, modules confirmed from run-dxvk, about 119 fps at 4K. Odarath spot, 8 frames standing still: wall brightness range 0.0 on PC native and PC DXVK, 0.7 on the tablet with and without driver safeguards. So DXVK alone does not flash at this spot. Remaining suspects on the tablet: Turnip beyond the options tried, FEX, Wine's D3DReflect, or Proton's DXVK build. One spot only. DXVK logged a SetPredication stub error.

Run setup: work/v30-engine/run-dxvk.cmd starts a copy of the game from work/v30-engine/run-dxvk (copied exe and DLLs, DXVK DLLs, junctions to data, steam_appid.txt) with Steam running, so the Steam install stays unmodified. Writing to the Steam folder from the SSH session fails. Use this layout for the proxy DLL. work/v30-engine/desk.ps1 does launch, shot, key and click on the desktop. Check loaded modules with 32-bit PowerShell before trusting a run.
Steam Cloud: the tablet's 12:21 session had not uploaded. "Play anyway" was chosen on the PC, so a conflict prompt may appear later. Keep the PC copy; backup in save-backup-20261101.

## Recording 2026-11-01 (work/v30-engine/proxy, run-rec, render_backend.tsv)
d3d11.dll proxy built with VS 2026 Build Tools (proxy/build.cmd), recording through DXVK. Vtable thunks on Microsoft's d3d11 showed no draw calls at all, cause unconfirmed, so record through DXVK (OA_REAL_D3D11 in run-rec.cmd). One standing spot in Odarath plus title, menu and loading:
- Feature level 11_0, Shader Model 4.0 only, 117 VS and 388 PS seen. Trace shows no compute, geometry or tessellation calls, no MSAA, no ExecuteCommandList. One deferred context created.
- About 25,300 calls and 1,432 draws a frame. Pass 0: 501 occlusion queries. A later pass: 501 predicated draws. DXVK stubs SetPredication, so these draw unconditionally.
- 32,768 occlusion predicates created. Targets: RGBA16F and RGBA8 at screen size, 1024x1024 format 53 (typeless R16, presumably shadow maps, x4), blur chain, D24S8.
- 83 engine functions call D3D here. FUN_00c961e0 issues nearly all main draws and all predication. Creation code around 0x0106xxxx: 01060270 device, 01061ed0 shaders, 0106b170 and 0106ab50 textures. Other scenes will add more.
Decompile: work/v30-engine/decomp, 45,957 functions, 0 failed, 2,471 files, 53 MB. Raw pseudocode, does not compile. names.tsv: 13,684 applied names from RTTI (vfN = vtable slot, xtor = stores the vtable), classes.tsv: 2,247 classes.

## Replacing engine functions (work/v30-engine/proxy/oa_engine.c, rec_run.ps1)
Method: entry bytes checked, 5-byte jump to our C in the proxy, call counter, callers.txt confirms the original no longer calls D3D, OA_NO_REPLACE=1 turns it off. Check each candidate's calling convention in the disassembly first (some functions take hidden register arguments, such as ESI in 01059640).
Done, verified in the running game at one Odarath spot through DXVK: 010596c0 texture unmap (217,028 calls), 00c5b2a0 material texture binding (21.1 M calls in about 3 min, 120 fps, wall unchanged).

Also done: 00c5b390 (8.2 M calls), 00c726d0 (1.06 M), 00c961e0 main draw list, kind 0 packets only (20.2 M packets rewritten, 812 K, about 3.9%, sent to the original through a trampoline). Same spot, about 3 min, 120 fps, no crash. Per-frame counts against the run without the draw rewrite: draws, predication, Begin/End, Map/Unmap, constant buffers identical. PSSetShader, VSSetShader and IASetInputLayout 133 vs 113, blend 71 vs 67, depth 95 vs 93, textures and samplers +2: expected from re-binding after each fallback, gone once kinds 1 and 2 are rewritten. Not verified: other scenes, combat, outdoors; kinds 1 and 2.
Test notes: frame call order varies between identical runs (commonest frame 25,326 vs 25,341 calls), cause unconfirmed, so compare counts with trace_counts.py, not sequences. Patches must skip bytes holding absolute addresses (ASLR), see reloc_from/reloc_to. The wall brightness score only covers one dark area and is a weak check.

00c961e0 now fully rewritten, all kinds, no fallback. Three runs at the same Odarath spot, 3 min each, 120 fps, no crash events, saves unchanged. The original makes no D3D calls. Last run: kind0 20.2 M, kind1 748 K, kind2 64 K.
Coverage from counters: every kind 2 packet was quads, ring wraps 273. NEVER RUN: kind 2 split path (over 64 KB), kind 2 non-quad topologies, skip paths, Map failure paths. Those are transcribed from the disassembly but untested.
Control (OA_NO_REPLACE=1, 28 frames) and the four-function run (28): DrawIndexed always 1313. Draw 118-123. PSSetShader 113-121, blend 67 or 71, depth 93 or 95 depending on the run, so those shift with no rewrite. Rewrite runs (86 frames): DrawIndexed 1313 except one frame of 1311 in each of 2 runs (blend and depth 3 lower in the same runs); Draw reached 124 in 2 of 3 runs. Not explained: 2 frames in 86 vs 0 in 56 is too few to call either way. Sampled frames from separate runs cannot settle it; needs the same frame compared, or a longer sample.

Settled 2026-11-01 with every frame logged (frames.csv, frame_compare.py), about 30,700 steady frames per mode, same spot, 116.7 fps both, 0 crashes. Original code vs rewrite: DrawIndexed 1235 x14, 1311 x76 in BOTH, then 1313 (30,617 vs 30,625). The 90 odd frames are consecutive and are the first 90 steady frames after loading, in both modes. SetPredication and Begin distributions match. Draw 124 appears in both (83 vs 87 frames). So neither the 1311 nor the 124 is caused by the rewrite; 1-in-600 sampling only sometimes landed on them. Blend, depth and PSSetShader levels vary by run: 67/93/113 here on the original, 71/95/116 on the original in the earlier control.
Limits: this compares counts of calls, not their arguments or the pixels. Kind 2 split and non-quad paths still never ran (split=0, all 119,508 kind 2 packets were quads). One scene.

Other scenes, 2026-11-01 (scene_run.ps1, scene_compare.py, img_diff.py): saves "Dalentarth" (outdoor), "The Gardens of Ysa", "Haxhi Dam", loaded from the menu, standing still. Two rewrite runs and one true original run each, 0 crashes, saves unchanged. Over the last 6000 frames: DrawIndexed Dalentarth 2508 in all; Ysa 1446, 1446, 1455 (same range, NPCs walk through); Haxhi 1434, 1432, 1432. Draw, SetPredication, Begin, OMSetRenderTargets match. 5 fewer D3D callers on the rewrite, as expected. Images: differences between rewrite and original are the same size as between two rewrite runs, mainly idle and NPC motion; one frame per run at 320 px with a 16-level threshold, so a weak test. Non-quad kind 2 ran in Dalentarth (about 3,000) and Ysa (about 4,200). Split path still never ran (split=0 everywhere). New D3D callers outside the Odarath list: 00d00f70, 00c7b890.
Script bug found: PowerShell variables ignore case, $c overwrote $C, so the first "original" runs were rewrite runs; those are kept as oa_rec-*-rewrite2. Always confirm the mode from resources.txt.
Save list warning: every row in the Load menu has a red delete X at the right. Click only the name column (x=768 at 4K) and load with Enter. Rows: y=1163 Dalentarth, 1372 Ysa, 1581 Haxhi Dam. First click on the title goes to the main menu; Load Game at 480,547.

Not tested: moving, combat, menus in play, cutscenes, split path. Next: remaining backend functions in render_backend_ka.tsv.

Job size from the call graph (direct calls only; 4.68 MB of .text is unattributed): 45,950 functions, 11.2 MB. Unnamed 31,532 (9.3 MB), BHG 7,405, templates 3,386, Bullet 1,386 (471 KB, open source), FaceFX 445, keen sound 249, Kore 540. Leaf functions with no calls: 11,027 (2 MB). 35,232 functions are 256 bytes or less but only 2.6 MB of code. Render backend seen so far: 83 functions, 93 KB.

## Our Vulkan layer, 2026-11-01 (work/v30-engine/vk: oa_vk.c, oa_dxbc.c, build.cmd, vk_run.ps1; game runs from run-vk)
Own d3d11.dll on Vulkan 1.3: COM objects for device, context, DXGI chain; shader translator SM4 to SPIR-V; no DXVK, no Microsoft d3d11. All 510 recorded shaders pass spirv-val. Stage results on the PC, by eye: title, main menu, load list, loading screen, Odarath, outdoor Dalentarth, running, swinging, casting, inventory not retried. 120 fps at 1536x864 with vsync on the 120 Hz display. No crash in those runs after the alignment fix. Saves unchanged.
Known gaps: predication ignored, so predicated draws always run (the occlusion culling is lost); occlusion queries are stubs; Direct3D image copies to CPU not implemented; every image kept in GENERAL layout with full barriers (bad for tile GPUs); one Vulkan allocation per resource (limit risk, leak-free only through the parked delete list); blocking texture uploads; depth-with-stencil clears only clear the aspects asked; SwapChain GetContainingOutput stubbed; no Vulkan validation layers run yet (SDK not installed); render size is the 1536x864 the game asked for because of the display scale.
Mapped memory must be 16-byte aligned. PowerShell variable names ignore case: never reuse a letter of $E, $R etc. Enter does not always load from the Load list; double click the name. Check the screen before sending game input.
Crash dialog from the game offers to upload a diagnostic file: never press Yes; kill the process.

Tablet result 2026-11-01: our layer runs under DroidDeck 0.6.0 (FEX, Proton, WN-Turnip-1.19-b_Axxx) on Adreno 829. Title, main menu and Odarath drawn. About 90 fps at 1350x900 in Odarath, thermal 0 early on. Standing still, 8 frames about 1 s apart: 1.8% of pixels changed, brightness range 0.4. Earlier under Proton's DXVK at the same spot: 6.2% and 3.7, and the user saw heavy flashing. The flashing appears gone by capture, not yet confirmed by the user's eye. One spot only. So the flashing was not FEX alone; the difference is the graphics path, exact cause unknown.
Tablet route: push to /sdcard/Download/oa/d3d11.dll. Launch option: cp /storage/emulated/0/Download/oa/d3d11.dll /root/.local/share/Steam/steamapps/common/Kingdoms*/;ls -la ... >/storage/emulated/0/Download/oa/ls.txt 2>&1;WINEDLLOVERRIDES=d3d11=n,b %command%. Log at /sdcard/Download/oa/oa_vk.log. To undo: clear the launch option and delete d3d11.dll from the game folder, or verify files in Steam. Steam tap points (landscape, 2520x1680): hide gamepad 88,1587; game tile 504,1134; gear 2392,800; Properties 1050,965; keyboard close 2407,1618; Back 2380,1627; Play 252,800.

User play test 2026-11-01: flashing gone (user confirmed). Feels slow, some textures missing.
Slow, measured on the tablet: GPU wait about 0.03-0.06 ms a frame, so CPU limited, not GPU. Push descriptors replaced with cached descriptor sets and dynamic offsets (backup of the old file: oa_vk.push.c.bak on the Mac). Draw call cost 5.7 to 3.55 us per draw, different views, so approximate. Latest: 25.6 fps at 2,821 draws, thermal 2, with 10 ms draws, 2.9 ms map, 3.2 ms unmap, 0.65 ms submit. So about 16 ms of 39 ms is our layer; the other 23 ms is unattributed (game code under FEX, wine, thermal throttling). Same area was 55 fps at 2,490 draws at thermal 1 before the change, so FPS has NOT been shown to improve. Not cooled and re-measured.
Query draws: 1,082 a frame all kept, none skippable (they write depth or colour). Predicated draws always run. Real occlusion culling is the biggest available cut.
Textures: cave rocks detailed on PC, flat on tablet, through the same layer. Ruled out: formats (no unsupported flags), game log differences (identical render targets), texture dimension mismatch, BC mutable views (rocks still flat after fix). Unbound t5 on one pixel shader occurs on both. Still unknown. Next idea: compare what that rock draw binds, shader output differences on Turnip, sampler LOD.
Tablet control: with the Kishi attached there is no touch overlay and USB adb is gone (wireless adb works, port from mdns). Without it: + at 92,1596 opens gamepad; long-press Steam at 1184,1550 (input swipe, 200 ms); - at 88,1590; Exit game 730,1300; confirm 870,890; Play 252,800; title tap 1260,1200; Continue 400,345 needs tapping twice.

Occlusion culling built (vk/oa_vk.c: pred_skips, query_begin, read_queries; results read back from a finished frame; live off switch is a file named nocull in the run folder or /sdcard/Download/oa). Lazy constant buffer copies added. Timers now sample every 8th frame. First real PC run at the Odarath load spot: 1,257 draws/f, 174 hidden skipped/f, 212 tests/f, 288 tests saved/f, no errors. On/off at that one spot on the PC, standing still: draws 1,256 on, 1,431 off, 0.64 vs 0.74 ms/f in draw calls. Image difference on vs off was 3.5-3.7%, on vs on again 4.4%, so no difference above noise (one frame, 320 px). NOT yet: walking, popping check, any tablet run. The user stopped the walking run before it started. The tablet still has the earlier build without culling.
Working rule after user feedback: check the screen before each input, confirm from the log that a feature ran before quoting numbers, label guesses as guesses. PC menu flow: click 3000,1500 on the title, wait 25 s, look, then Enter on Continue.

Next: finish culling on/off on PC, then tablet, then the flat textures; layouts and allocator after.

## Stages
1. Size the job: done above except a real function count (run Ghidra headless, tools/ghidra_12.1.4_PUBLIC).
2. Real engine on the tablet through translation: DroidDeck 0.6.0 (com.droiddeck.launcher), which runs the real Steam client with ARM64 Proton, FEX and DXVK. The user installs the game through it. Winlator was dropped.
   Unknowns: 32-bit koa.exe under FEX on this arm64-only device; which Vulkan driver works on A829; frame rate; whether the dinput8 proxy loads under Proton.
   PC saves backed up 2026-11-01 to work/v30-engine/save-backup-20261101 (18 files, hashes match). Steam Cloud shares them with the tablet.
3. Staged decompile on the PC: dinput8 proxy DLL (the method the VR mod in references/ uses) replacing functions one at a time, tested against the real game. Order: platform layer, then D3D11 calls, then the rest.
4. Vulkan: decide between DXVK as the renderer backend and a direct Vulkan backend behind the engine's PlatformShaderMgr and device layer. D3D11 surface must be measured first.
5. Native ARM64: compile finished systems natively. Bullet and Lua can come from source. FaceFX, keen sound, Bink need replacing or decompiling.

Other hardware follows from stage 4 and 5: nothing should stay Android-only except the host layer.

## Salvage
- src/, tests/, outputs/reconstruction-v04: Lua 5.1 format 0x08 parser and reconstruction. Game logic is partly in Lua, so this is direct knowledge of the engine's scripting.
- work/v20-inputs/symbols.json: names from symbol_table_*.bin (abilities and more), useful for naming decompiled code.
- work/v19-capture, tools/rea-frida: live capture of the real game via Frida, with the launch method in CURRENT_STATE.txt. Note koa.exe rewrites the save at exit and Steam Cloud uploads it.
- work/v20-char/clip_bake.cpp: runs the game's own animation decompressor. FORMATS notes in CURRENT_STATE.txt line 96 on.
- tools/ghidra_12.1.4_PUBLIC, tools/rea, NDK r30, adb and test scripts.
- references/: mark-mon VR mod (hooks the game's renderer), KoaModFramework, coop mod, depak, AmalurBxmlConverter.
- Custom engine: fallback only. Its effect, terrain and clip meanings are inferred, so treat them as hints and confirm them in the decompile.
