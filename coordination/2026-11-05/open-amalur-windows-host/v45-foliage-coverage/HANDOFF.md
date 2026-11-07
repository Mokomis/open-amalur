# Current verified state: Open Amalur v0.36 R3 (2026-11-06)

The custom GLES3 replacement engine is the active Android approach. The separate real-engine/FEX work is preserved and paused. Windows and ARM64 builds pass. Native Android v0.36 R3 is installed on tablet99cc517a (package0.36.0/code38), with APK SHA2564a38d2a722519258be04d1a377b3adae24d1efe35bd56d87df4be1ac5582b7e9. The existing signing key was reused on Windows and never copied or replaced; the app was updated in place.

The current update restores source Region trees and bridge-side lamp/cart actors, the correct mossy root and near-detail foreground rock, native foliage attributes, DOF sampling and soft godrays. A separate authored tree-shadow proxy now replaces the proven false leaf-card shadows. Windows live A/B matches native sunlight at both sampled foreground rock pixels. The first supported proxy cohort is34unit-scale FAB343974 placements;22nonunit placements and other families retain the old fallback. Read work/v45-foliage-coverage/FINAL_VISUAL_REVIEW.md for the top/middle/bottom original-image comparison and qualifications.

Actual tablet logs confirm301material rows/42native profiles,175leaf cells,200shadow cells,26Region replacement IDs,17readiness dependencies, proxy GPU draws and shaped soft particles. A short joystick walk advanced6metres; HOME/resume recreated the GLES surface and rendered successfully. Short stationary samples were32.0FPS at2520x1680/thermal1 and47.3FPS at50%linear resolution1260x840/thermal2. They are not a strict baseline or sustained benchmark. A startup profiler GL0x502 message remains documented.

The original save and settings hashes remain unchanged. Temporary position, heading, resolution, profiling and USB stay-awake settings were restored. The app is stopped and tablet asleep. The Windows preview is closed, reference properties restored and OA_CustomEngine_Windows_v40 task returned to its normal --scene town action. The temporary localhost-only ADB/SSH tunnel is closed. Other tools, credentials, databases and helper/model services were not reconfigured.

The remaining clear visual blocker is excess distant canopy at native pixel980,100. Current source198 from South SPACE431642 occupies a native clear-depth pixel. Simple source/alias/bounds-centre cutoff rules reject2of33valid native leaf draws and were withheld. A focused eight-function native pass recovered a separate runtime actor-state propagation path, not the static collection admission/SPACE/LOD selector. The GPU capture lacks the corresponding CPU flags and handles for these fixtures. Continue from exact static registration00fec370 ->00cd24e0/00cd2570, correlating source198 and positive68811; trace the actual static admission consumer or capture its CPU state. Avoid another actor virtual walk, fitted cutoff or reference-frame visibility whitelist. See native-space-visibility/focused-render-selection/REPORT.md.

Other limits remain explicit:73unwitnessed scaled leaf transforms are unchanged, shadow-proxy support is incremental, and godray animation input/sign selection is a qualified candidate. The waterfalls retain the owner-preferred custom style. Their shader branch, four material rows,13texture payloads and water parameters remain identical to R4. No full-scene pixel or whole-game parity is claimed.

Private recovery kit: outputs/scene-v45-r3/restore-delta-v036-r3.zip (58,050,346bytes), SHA256a4407647dc83c54b9dcb496b73afab07a1cc5af4de8ea8fa502bf48f4bf2ea19, verified on the Mac. It requires the preserved R4 baseline and dependencies. It contains actual source, changed assets and ARM library, without the signing key or analysis database. source-build-receipt.json pins the delivered code. The authoritative Windows folder is not a Git checkout; keep clones separate.

For future builds, read OPERATOR_BUILD_GUIDE.md and use build_renderer_batch.py once after a batch of source edits. Existing one-time integration scripts preserve their original input guards and are not the normal build entry point. The previous notes remain below; they are historical where this checkpoint differs. A notes-encoding failure was fully recovered byte-for-byte, with the original file and recovery receipt retained. Use explicit UTF-8 and atomic note writes.

---

# Current continuation: v45 background foliage, 2026-11-06 (in progress)

Read work/v45-foliage-coverage/README.md and renderer-build.json before older notes. Windows source/live reference assets include the new native leaf stream:175cells/51,831existing triangles, no new instances; both Windows and ARM64 compilation pass. Windows shading improved at two confirmed pixels. A separate native-only tree geometry gap and residual brightness remain unresolved. Current source hashes differ from v44R4 by design; baseline files preserved in v45/before. Android is STILL v0.35R4/code37 with its save/settings untouched in this pass; no v45APK or tablet performance result yet. Original-engine/FEX work stays paused. Stage attachment reference replay is underway; inspect actual receipts before claiming it succeeded. The Windows scheduled task is temporarily in reference-camera mode; restore town mode when integrated testing finishes. Preserve all prior notes below.

---

# Current continuation: v44 / Android v0.35 R4, 2026-11-05

Custom native engine remains active in work/v19-host, Windows host work/v40-windows-host. Read work/v44-native-fidelity/README.md, PERFORMANCE.md and CODEX_EVIDENCE_REVIEW.json first. Older notes below are preserved history.

Installed: outputs/scene-v44-r4/open-amalur-v0.35-r4-arm64.apk, version0.35.0/code37, existing package/key. Installed APK SHA a07cdf8bcae3d68c79f43609c7854e2584a61422ad081cdc6a7991f417613e2d. Native water, foliage attributes/wind/independent alpha, source material culling, AO/3cascades/sky/bloom/DOF/LUT/filter and point/fog equations are integrated. Large dark tree-branch cards were source-alpha metadata bugs and are fixed. Windows matched original-camera and ordinary walking-camera images reviewed. Complete source/build checkpoint and receipts are in outputs/scene-v44-r4.

Tablet same-scene stationary samples, nativefeatures255 and shadows:100%2520x1680=35.73FPS;75%1890x1260=46.57FPS;50%1260x840=53.02FPS. Thermal0 at100%,2 at75/50; short samples, not sustained benchmarks. Scaling now resets physical buffer defaults across room transitions. At50% GPU13.89ms, submission/driver18.03ms: prioritize drawing/state/depth/shadow overhead before simulation threading. Full-resolution GPU26.37ms remains costly.

Save/settings hashes unchanged. Test spawn/heading/profile/shadow/scale restored; native255 retained, defaultscale100. App stopped. Windows preview closed and task restored to normal town mode. Keys, original saves/databases and all previous artifacts preserved; no GitHub push. Original-engine/FEX work remains paused. Do not run old prepare.py without reapplying overlays. Validation is captured Gorhart bridge Noon; unsupported legacy materials, other time/regions, originalLODs and full actor lighting remain broader parity work. Whole-game/exact pixel parity is not certified.

---

# Current continuation: v43 / Android v0.34, 2026-11-05

The owner-authorized five-milestone custom-engine pass is complete within documented scope. Read work/v43-scene-fidelity/README.md, VALIDATION.md, CODEX_EVIDENCE_REVIEW.json and android-validation/ANDROID_VALIDATION.json first. The older notes below are preserved history and are superseded where contradictory.

Active shared source remains work/v19-host; Windows host work/v40-windows-host. New:267 restored static visuals total, deployed visual-mesh collision, native terrain paint in18shop/bridge cells, scoped native dot3 ambient/specular, measured reference bloom extraction/merge. Windows and Android final builds passed. v0.34.0/versionCode36 is installed on tablet99cc517a under existing package/key. Real touch walking/crate blocking/reverse/shop transitions/Home-resume verified. Original app save/settings hashes unchanged throughout. APK outputs/scene-v43/open-amalur-v0.34-arm64.apk. Tablet stationary shop sample~56.6FPS at2520x1680, thermal0; not a sustained gameplay benchmark.

User-data/key/original game saves/databases retained. Tablet test spawn/profile/heading restored; live127 retained. App stopped/display returned to sleep. Windows preview closed. No GitHub push in this pass. Original engine/FEX work stays paused. Do not rerun prepared desktop assets from old base without reapplying corrections/overlays. Native blur/deferred AO/water/sky/foliage and broader material/placement support remain incomplete; exact lighting parity is NOT achieved. Next: address the obvious foliage/water/material fidelity gaps using original captures, then one original quest with dialogue/objective/reward/persistent reload. Use Windows first and batch Android checks.

---

# Active direction â€” 2026-11-05

The owner resumed the custom native engine from v0.33. Develop and compare scenes mainly on Windows, with tablet checks at substantial milestones. work/v19-host is ACTIVE again. Original-engine native-port and FEX/texture work is PAUSED and preserved as reference. Read work/v39-custom-resume/PLAN.md and its fresh baseline results.

Windows host is now working in work/v40-windows-host: shared custom runtime, textured Gorhart/shop, walking, interaction, isolated desktop saves and fixed original-camera comparisons. Read its README.md, VALIDATION.md and REFERENCE_VALIDATION.md. Windows executable and Android shared library build successfully; no tablet installation was changed.

Latest visible progress: work/v42-object-visuals now restores 251 native-record crates, barrels and urns in the Windows scene (nine FABs / three materials). Fresh matched-camera capture static-props-reference.png shows missing bridge-side piles back in place. Existing geometry is byte-identical. Deployment/rollback are hash checked; read v42 README.md. This is static visual recovery, not destruction/loot/physics. Derived collision is prepared but NOT deployed: integrated blocking comparison remains unverified. Non-identity local binds remain omitted; follow-up anchors are in NATIVE_BIND_NOTES.md. No Android installation changed.

Use original-game footage/captures as the reference for placement, terrain, materials, lighting and movement. A bridge matched-camera comparison is saved; still frames expose missing props and approximate ground paint, foliage, fog, water and lighting. Paired movement clips remain to be captured. Do not claim exact parity or infer Android FPS from the desktop readback host.

Native placement parser and evidence: work/v41-world-objects. Corrected GOR quaternion offset and native heading convention; 65 placed actor headings repaired, with before copies and byte-integrity evidence. Full gameplay behavior is still authored in several areas. Next content work: missing visual instances/terrain paint mapping, followed by one original Gorhart quest with dialogue, objective, reward and persistent save/reload. Preserve the installed app, saves, signing key and analysis databases.

The earlier frozen-engine instructions below are superseded historical context.

---

## Historical handoff (preserved)

# Open Amalur handoff (2026-11-01)

## Goal
Run the real Kingdoms of Amalur: Re-Reckoning engine, not a substitute, on the Android tablet and other hardware through Vulkan. In the owner's words: "using the same engine or version of it that can run on the tablet and other hardware using vulkan."

The custom C99/GLES3 engine (`work/v19-host` and related, app version v0.33) is frozen. Use it for salvage only.

## Where things are
| Item | Location |
| --- | --- |
| Repo (private) | https://github.com/Mokomis/open-amalur |
| This work | branch `sync/real-engine-2026-11-01`, based on `sync/v0.23-source`. `main` has not been updated |
| Live working tree | Windows PC, `C:\Users\rwill\Documents\Opem Amalur`. It is not a git checkout, so clone the repo separately to commit |
| Detailed notes | `work/v30-engine/PLAN.md`, then `work/CURRENT_STATE.txt` |
| Vulkan layer source | `work/v30-engine/vk` (`oa_vk.c`, `oa_dxbc.c`, `build.cmd`, `vk_run.ps1`) |
| Function replacement and recording proxy | `work/v30-engine/proxy` |

### On the Windows PC only, never push
All under `C:\Users\rwill\Documents\Opem Amalur\work\v30-engine\` unless noted:
- `decomp\`: Ghidra pseudocode, 45,957 functions, 2,471 files, 53 MB. It does not compile. Read one function with `python show_fn.py decomp koa.exe <hex address>`
- `ghidra\`: Ghidra project. Rebuild the export with `run_export.cmd`
- `koa.exe`: copy of the game executable (build cs:15032)
- `names.tsv`, `classes.tsv`, `functions.tsv`, `render_backend*.tsv`, `rtti.json`, `imports.json`: name and call data
- `oa_rec-*\`: Direct3D recordings and dumped shaders
- `pc\`: screenshots
- `run-vk\`, `run-rec\`, `run-dxvk\`: runnable copies of the game. Their junctions point at the Steam install
- `save-backup-20261101\`: backup of all 18 PC saves
- `..\v20-inputs\`, `..\v2*\` data folders, `outputs\`: extracted game data and APKs
- `tools\android\opem-scene-debug.keystore`: signing key. Do not copy, replace or delete it

Tools on the PC: Visual Studio 2026 Build Tools (x86), Ghidra in `tools\ghidra_12.1.4_PUBLIC`, JDK in `tools\jdk-21.0.13+9`, NDK r30.

## Current state
Working:
- `koa.exe` runs on our own `d3d11.dll` on Vulkan 1.3, with no DXVK and no Microsoft Direct3D doing the drawing. The layer includes a Shader Model 4 to SPIR-V translator, and all 510 recorded shaders pass `spirv-val`.
- PC: title, menus, Odarath and outdoor Dalentarth drew correctly by eye, with running, swinging and casting, at 120 fps at 1536x864.
- Tablet (OPD2515, SM8845P, Adreno 829, DroidDeck 0.6.0, FEX, Proton, driver `WN-Turnip-1.19-b_Axxx`): the real game runs on this layer. The heavy lighting flashing seen under Proton's DXVK is gone, confirmed by the owner playing it.

Proven earlier, on the original engine with DXVK:
- Five engine functions replaced with C inside the running game, including all of the main draw list `00c961e0` (`proxy/oa_engine.c`). Call counts matched the original in three areas, standing still.

Newest work:
- Occlusion culling and lazy constant buffer copies are in `vk/oa_vk.c`.
- On the PC at one spot, standing still: 1,431 draws become 1,256, with no image difference above noise.

The engine is still 32-bit x86, under FEX translation on the tablet. A native ARM engine is a much longer job: 5 of 45,957 functions have been rewritten.

## Current blockers
1. **Slow on the tablet.** The limit is the CPU, not the GPU: GPU wait is about 0.03 to 0.06 ms a frame. Last reading at the cave entrance in Odarath was 25.6 fps at 2,821 draws at thermal status 2, on the build before culling. The same area read about 55 fps at 2,490 draws at thermal 1 on the build before that, so no frame rate gain has been shown yet. About 16 ms of the 39 ms frame is in our layer. The other 23 ms is unattributed, possibly game code under FEX and thermal throttling, which is not measured.
2. **Flat textures, tablet only.** Cave rocks are detailed on the PC through the same layer and smooth on the tablet. The owner also reported a few textures missing. Ruled out: unsupported formats, game log differences, texture dimension mismatch, and BC view format flags. Cause unknown. Next idea: compare what one rock draw binds on each device, then sampler LOD and shader behaviour on Turnip.
3. **Culling is unfinished.** It has not been tested while walking, has not been checked for popping, and has not been run on the tablet. Results come from a finished frame, so objects may appear a frame or two late.

Other known gaps: images stay in GENERAL layout with full barriers, which suits tile GPUs poorly; one Vulkan allocation per resource; blocking texture uploads; no CPU readback copies; no Vulkan validation layers run, since the SDK is not installed. Not tested on our layer: real combat, cutscenes and videos, long sessions, sound.

## Next steps
1. Push the culling build to the tablet and compare on and off at the same spot. A file named `nocull` in `/sdcard/Download/oa` turns culling off live.
2. Break down the unattributed 23 ms per thread, with the tablet cooled.
3. Investigate the flat textures.
4. Then image layouts, memory allocation and uploads.

## Machines and how to drive them
- **PC:** from the Mac, SSH alias `open-rune-windows`, HostName `192.168.68.59`. Run the game with `run-vk.cmd` with Steam open. Input and capture go through `desk.ps1`, which uses a scheduled task on the desktop session.
- **PC menu flow:** click 3000,1500 on the title, wait 25 s, look, then Enter on Continue. Use the Load Game list only by clicking the name column (x=768 at 4K).
- **Tablet DLL:** push to `/sdcard/Download/oa/d3d11.dll`. The Steam launch option copies it into the game folder on each launch and sets `WINEDLLOVERRIDES=d3d11=n,b`. Log: `/sdcard/Download/oa/oa_vk.log`. Game log copy: `game.log` in the same folder.
- **To undo on the tablet:** clear the launch option and verify the game files in Steam.
- **Tablet controls without the Kishi:** + at 92,1596 opens the gamepad; long-press Steam at 1184,1550; - at 88,1590; Exit game 730,1300; confirm 870,890; Play 252,800; title tap 1260,1200; Continue 400,345, which may need tapping twice.
- **With the Kishi attached:** no touch overlay and no USB adb. Wireless adb works; find the port with `adb mdns services`. The game has to be exited by hand.

## Rules from the owner
- Do not stop to ask when you can solve it yourself. Give evidence-backed findings and concrete blockers, and never present guessed values as native-equivalent.
- Set goals as something visible on screen. Avoid verification work that shows no visible progress.
- Preserve the working folder, saves, signing key and tablet install. Do not upload private keys. Keep the decompile, APKs and game data private.

## Traps that have already cost time
- Look at the screen before every input. Blind input chains have repeatedly gone wrong.
- Confirm from the log that a feature actually ran before quoting numbers. Check the loaded mode or modules too: one "original code" run was actually the rewrite.
- PowerShell variable names ignore case, so `$c` overwrites `$C`.
- Writing into the Steam game folder over SSH fails silently from a script's point of view. Use the run folders.
- Every Load Game row has a red X that deletes the save.
- The game's crash dialog offers to upload a diagnostic file: answer No and kill the process.
- Steam Cloud syncs saves between PC and tablet, and quitting can rewrite a save. Check against `save-backup-20261101` after runs. If Steam asks about a conflict, keep the PC copy unless the owner says otherwise.
- The tablet's Open Amalur app holds the Erathell test build and the only copy of that app's save. Do not uninstall it.
