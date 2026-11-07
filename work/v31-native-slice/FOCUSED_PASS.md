# Native original-engine pass — 2026-11-04

## Result and model handoff

Switch back to Sol High for the next implementation task. Do not repeat tablet
capture setup or driver investigations. No native scene has been rendered.

One additional original-engine helper is now portable and runs directly on
Android ARM64: material-constant filling at cs:15032 **0x00c34c90**. It is not yet
connected to a complete native draw-list implementation. The existing geometry
slice is preserved and extended. All 29 synthetic contract checks pass on the
tablet; the host test also passes with AddressSanitizer and UndefinedBehaviorSanitizer.
These establish bounded helper behavior, not real-scene equivalence or speed.

Windows build: installed NDK r30, API 26, `aarch64-linux-android26-clang.cmd`,
`-std=c11 -O2 -Wall -Wextra -Werror oa_recovered.c probe.c -o oa-native-probe-constants`.
Binary SHA256: `3bdbebdf82cda019e122325c9c90c51999329dfa3bb93632a00b0be7be4459dc`.
Tablet invocation: `adb -s 99cc517a shell /data/local/tmp/oa-native-probe-constants`.
This uses Android's linker directly, with no Wine, proot, or FEX.

## Native evidence and remaining engine boundary

`evidence/00c34c90-native-evidence.txt` contains the executable hash, existing
Ghidra export, and a fresh LLVM disassembly of 0x00c34c90..0x00c34ce2 from Windows.
This reuses the established reverse-engineering project; no database was changed.

The function takes `(destination, source, material, layout)`:

- `layout+0`: unsigned 16-bit entry count.
- `material+0`: 32-bit pointer to 8-byte records.
- Record `+4`: unsigned 16-bit byte count; `+6`: unsigned 16-bit destination offset.
- `layout+8`: 32-bit pointer to unsigned 16-bit source offsets, one per entry.
- Copies run in table order; later copies overwrite earlier destination overlaps.
- Zero entries return without reading the other arguments. This is byte copying,
  not matrix computation or float conversion.

The portable helper resolves captured 32-bit addresses explicitly and keeps host
pointers separate. It rejects malformed input before any output changes, and
rejects destination aliasing with immutable snapshot storage. Those checks are
our capture-boundary policy, not behavior claimed for invalid original pointers.

The complete 0x00c961e0 draw-list port still needs material/shader/state setup,
three texture-binding functions, constant-buffer map/commit, packet kinds 1/2,
predicates, and a native rendering backend. The old C rewrite still references
32-bit game state, COM vtables, global flags, topology tables and original logging.
Our new constants helper has NOT replaced the `ABS(0x00c34c90)` call in that old
Windows rewrite. Do not compile that rewrite as 64-bit and assume its layouts work.

Next engine implementation: define explicit pass inputs for globals and resource
IDs, recover the full packet/material snapshot closure, and compare resulting
ordered commands and constant bytes against the same original captured input.
Call-count equality alone is insufficient.

## Rendering decision

Use a self-contained original-game Vulkan frame as the first native rendering
test. Existing v30 recordings lack complete resource payloads/state. Do not use
an old custom-engine mesh, generic triangle, or synthetic fixture as proof that
the original scene renders natively.

A replay can validate resources, shaders, passes, and native graphics submission.
It cannot predict full native-engine FPS: simulation, animation, culling, scripts,
material assembly and the D3D-to-Vulkan layer are absent from Vulkan replay.
Initialization/pipeline-compilation time is also not steady frame time.

Chosen next capture host: **Windows**, through the existing own Vulkan layer in
the isolated run-vk game copy. First verify a recorder with 32-bit Windows Vulkan
support and a compatible ARM64 replay version. No Windows recorder was installed
or verified in this pass. Keep capture local/private. Cross-platform replay is a
testable hypothesis, not guaranteed support. Try one capture and validate payloads,
then replay on the same Adreno driver; stop on a concrete incompatibility rather
than entering a driver/settings loop. Existing saves and game assets are preserved.

## Tablet capture experiment: failed, reverted

The previously staged GFXReconstruct 0.9.18 ARM64 Linux tools run directly under
Android's kernel. A new private mount-namespace launcher provides /dev, /proc,
/sys and hides DroidDeck's process-injection preload only within that namespace.
It uses an isolated byte-copy of the existing WN_Linux_Turnip_0.1.2-b driver;
the installed driver and its settings were not replaced.

Verified:

- Native ARM64 Vulkan enumerates Adreno 829; VK_EXT_headless_surface is advertised.
- GFXReconstruct loads in that native test and records/replays an initialization-only
  trace. It contains **zero frames**, so this is not a graphics-rendering success.
- Native X11 connection works when using DroidDeck's UID 10307; root alone is refused.
- Game-specific configuration is read at game launch, but DroidDeck regenerates it
  when starting a new Steam session. Initial capture settings were therefore erased.
- After re-arming inside the existing Steam session, recorder initialization was
  logged, but the game stalled at Steam's launch spinner. The renderer log reached
  GPU enumeration, not a rendered frame. No capture file was produced.
- One initialization also warned about unsupported Vulkan structure 1000272000
  (VK_EXT_map_memory_placed features). This demonstrates a version gap, but **does
  not establish the cause of the stall**. No further unchanged attempts were made.

Original `game-environment.json` was restored byte-for-byte, SHA256
`8cb756d2556d5c0f0d27995a786b3ba820249dc32c9dd1cae3e93925e95cdb79`.
The stalled test game process was terminated after identity verification, before
loading a scene. No game process remains. No capture trigger key was sent.
Capture configuration is OFF. No persistent mounts remain from the native runner.
The existing highest-mip diagnostic game DLL remains as before, its toggle OFF.
No saves, signing keys, game data, installed drivers, or original app were edited or deleted by the tooling. Save-file hashes were not compared after this pass.

Preserved tooling under `capture-tools/`:

- `capture_control.py status|arm|restore`: checked per-game config with backups.
  **Do not re-arm this known-failed tablet experiment without a changed hypothesis.**
- `native_guest.sh`: temporary private-mount native Linux ARM64 runner, no FEX/proot.
- `native_vulkan_probe.py`: device/layer compatibility check, no drawing.
- `trigger_capture.py`: one held F10, unused; inspect screen first if ever used.
- `replay_capture.py`: bounded headless/xlib replay with screenshots/log/result files.
  The real-frame replay path remains unvalidated. Default timeout is 60 seconds;
  it reports total launch time, never labels that FPS.

## Saved locations

Mac root: `/Users/rwillmore/Documents/Codex/2026-11-04/open-amalur-native-slice`.
Windows root: `C:\Users\rwill\Documents\Opem Amalur\work\v31-native-slice`.
New Windows code/binary: `material-constants\`; original root probe remains intact.
Old Mac source preserved under `native-render/before-constants/`.
Evidence is in `evidence/`; new tablet result is `native-render/android-result-constants.json`.
Nothing was pushed to GitHub.

References checked: GFXReconstruct v0.9.18 capture manager/settings source and
[Android capture/replay guidance](https://github.com/LunarG/gfxreconstruct/blob/dev/USAGE_android.md),
plus the [Khronos structure definitions](https://docs.vulkan.org/refpages/latest/refpages/source/VkStructureType.html).
