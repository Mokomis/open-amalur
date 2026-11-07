# Custom engine resumed — 2026-11-05

Owner direction: reopen the shelved custom engine. Do major development, scene comparisons and correctness checks on Windows; use the tablet when Android-specific validation is needed. The native-original-engine port and FEX/texture investigation are paused. Preserve their work as reference. Continue from v0.33 without restarting completed recovery work.

## Active baseline
Windows authoritative root: C:\Users\rwill\Documents\Opem Amalur (not a Git checkout).
Runtime: work/v19-host, ARM64 C99/GLES3, org.opemamalur.scene v0.33 versionCode35. Content tooling: work/v20-char and related folders. The last custom tablet build was reported as the Erathell content test. Verify actual tablet package and save before changing it. Preserve signing key and app data. Do not uninstall.

## Immediate next step: Windows preview
The current Windows targets are portable logic tests and inspectors. The renderer/app target exists only under if(ANDROID) in android_scene.cmake; there is no existing complete Windows custom-engine preview target in this tree. android_scene.c mixes NativeActivity/EGL lifecycle and Android input/assets with game and graphics integration.

Add a Windows host for the SAME custom runtime/rendering modules, with a small platform boundary for window/input/assets/logging/audio. Prefer reusing the GLES rendering path through a suitable Windows implementation rather than writing a second renderer. Keep Android building. Use separate desktop user-data paths, leaving the installed Android save untouched. Confirm the current Erathell-vs-Dalentarth content selection before comparing scenes; restore the intended Gorhart content through explicit desktop build inputs without overwriting the preserved zone assets.

First visible result: the custom engine renders the shop and Gorhart on Windows, with walking/collision, animated player, and a reproducible fixed camera matching an original-game reference. Compare geometry, materials, skinning and broad lighting at matched camera/scene settings. Do not turn this into an indefinite exact-lighting project or require a save for every room. Use native evidence and scene records to resolve shared problems.

## Next gameplay milestone
One original Gorhart quest end to end: NPC conversation, accepted objective, required action, reward, save/reload preserving the result. Select a short quest from actual recovered records/scripts and trace its missing host services before implementation. Do not substitute an invented quest and call it recovered.

Implement the minimum reusable dialogue/quest state, event and persistent world/object services. Version and migrate the existing limited save. Unknown required services should fail visibly rather than silently succeed.

## Validation strategy
Batch existing Windows checks once at resume; save fresh logs here, leaving old receipts intact. Develop and compare mainly on Windows. Build/install on tablet only for meaningful milestones or Android-specific graphics/input/lifecycle/performance questions. No routine rebuild/install after every small edit. No need to launch original game or alter Steam saves until a concrete matched-view comparison is ready.

Current AI, combat stats, item powers, animation selection and some rendering choices are authored approximations. Label separately from recovered behavior. Historical v0.33 performance is encouraging, not a fresh full-game measurement. Full campaign compatibility and timing remain unknown.

## Resume session
Windows SSH verified on ROBMACHINEX; canonical AGENTS instructions read. Mac ADB currently sees no USB device or wireless mDNS services. No tablet changes performed. Optional Qwen helper not started. Source/config/save/key/analysis files preserved; previous direction notes backed up in before/.
