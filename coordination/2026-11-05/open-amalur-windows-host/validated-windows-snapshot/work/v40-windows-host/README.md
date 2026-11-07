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
