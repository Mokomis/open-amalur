# Current continuation: v44 / Android v0.35 R4, 2026-11-05

Custom native engine remains active in work/v19-host, Windows host work/v40-windows-host. Read work/v44-native-fidelity/README.md, PERFORMANCE.md and CODEX_EVIDENCE_REVIEW.json first. Older notes below are preserved history.

Installed: outputs/scene-v44-r4/open-amalur-v0.35-r4-arm64.apk, version0.35.0/code37, existing package/key. Installed APK SHA a07cdf8bcae3d68c79f43609c7854e2584a61422ad081cdc6a7991f417613e2d. Native water, foliage attributes/wind/independent alpha, source material culling, AO/3cascades/sky/bloom/DOF/LUT/filter and point/fog equations are integrated. Large dark tree-branch cards were source-alpha metadata bugs and are fixed. Windows matched original-camera and ordinary walking-camera images reviewed. Complete source/build checkpoint and receipts are in outputs/scene-v44-r4.

Tablet same-scene stationary samples, nativefeatures255 and shadows:100%2520x1680=35.73FPS;75%1890x1260=46.57FPS;50%1260x840=53.02FPS. Thermal0 at100%,2 at75/50; short samples, not sustained benchmarks. Scaling now resets physical buffer defaults across room transitions. At50% GPU13.89ms, submission/driver18.03ms: prioritize drawing/state/depth/shadow overhead before simulation threading. Full-resolution GPU26.37ms remains costly.

Save/settings hashes unchanged. Test spawn/heading/profile/shadow/scale restored; native255 retained, defaultscale100. App stopped. Windows preview closed and task restored to normal town mode. Keys, original saves/databases and all previous artifacts preserved; no GitHub push. Original-engine/FEX work remains paused. Do not run old prepare.py without reapplying overlays. Validation is captured Gorhart bridge Noon; unsupported legacy materials, other time/regions, originalLODs and full actor lighting remain broader parity work. Whole-game/exact pixel parity is not certified.

---

# Latest update: v43 / Android v0.34

Read ../v43-scene-fidelity/README.md and VALIDATION.md. Windows prepared pack now contains267 additional static visuals, derived collision, native paint in18cells and recovered lighting/post. Tablet v0.34 was updated and verified; older statements that no tablet changed are historical. The scheduled task is reset to normal town mode; no preview currently runs.

# Windows custom-engine preview

Active development host for the existing custom Android engine (v0.33 baseline), added 2026-11-05. This executes our shared gameplay/render modules, not koa.exe or an original-engine port. Develop and compare primarily on Windows; use the tablet at meaningful milestones.

Authoritative root: `C:\Users\rwill\Documents\Opem Amalur`. Keep this working folder separate from Git clones. It contains required private outputs.

## Run on the Windows desktop

- `run-town.cmd`: playable Gorhart preview. WASD walking; E interaction enters the shop near the initial position. Mouse/window input follows the existing custom engine.
- `run-title.cmd`: title/menu entry.
- `python start.py --scene reference`: fixed original bridge camera, player hidden. Reference mode intentionally cannot supply a normal walking view.
- `python control.py capture --out evidence/my-new-view.png`: fresh GPU image plus camera metadata. Existing evidence files are never overwritten.
- `python control.py tap W --ms 1000`: bounded input to this host only.
- `python control.py close`: clean shutdown.
- `python control.py status`: current host log.

For reference sessions, add `--user-data reference-data` to control commands. Run launchers in the logged-in Windows desktop session. From SSH use the existing owned scheduled task `OA_CustomEngine_Windows_v40`, now configured for normal town mode. It launches `start.py`, which refuses another preview instance. It does not control the original game. Avoid simultaneous control writers.

## Build / dependencies

Run `build.cmd` from this folder. Existing VS18 Build Tools, CMake 4.4.4, Ninja, NDK headers and locally installed ANGLE are reused. No system installations/configuration replacements were needed. `prepare.py` prepares private dependency/asset copies; `transcode_desktop.py` derives desktop textures using the existing astcenc decoder. Do not run preparation casually over a prepared evidence set.

The source links the actual work/v19-host scene, Lua bootstrap, collision, actor, AI, animation, audio, UI and streaming modules. NativeActivity/assets/input/audio have narrow Windows adapters. The logical input inventory is virtual. Scripts intentionally retain the Android-target service profile for compatibility; this is not a real Android JVM or physical Android device inventory.

ANGLE came from the existing local Daggerfall Online installation. It uses D3D11 on RTX 4080 SUPER. The default is a GLES pbuffer with GPU readback and GDI display. Native-window presentation stalled in this session. The readback path is useful for correctness work but is NOT a desktop or Android performance benchmark. `--window-surface` is experimental/unvalidated.

## Preservation / private data

Assets come from a preserved coherent Dalentarth APK, rather than the current Erathell Android test selection. Desktop assets and user saves are private and separate from Android. 627 ASTC textures were converted with all original mips to RGBA8/sRGB8_ALPHA8 for desktop ANGLE; original packages were not changed. Index texture t344.bin was already absent from the source package and live pack; no replacement was invented. Desktop decoded texture memory must not be extrapolated to Android.

`before/` preserves replaced source/library files. `assets/`, dependencies, saves, captures, native evidence, generated data and binaries are excluded from source commits. Do not upload decompilation, game data, APKs, signing keys or credentials. No tablet update/uninstall was performed. Never remove the installed custom app or replace its signing key.

See VALIDATION.md and REFERENCE_VALIDATION.md.
