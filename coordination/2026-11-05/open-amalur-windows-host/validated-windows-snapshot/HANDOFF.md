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
