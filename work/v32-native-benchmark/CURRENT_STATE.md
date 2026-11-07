# Open Amalur native rendering benchmark — 2026-11-05

## Verified milestone

A separate Android ARM64 NativeActivity app renders the real Dalentarth woodland-bridge capture and repeatedly redraws it without FEX, Wine or DroidDeck. Package org.openamalur.nativebenchmark, UID10308, versionCode5/versionName0.5-cached-layout. It uses Android's stock Adreno Vulkan driver, not the Linux Turnip driver in DroidDeck. The real engine has NOT been ported: this is a captured graphics workload, with no live simulation, animation or streaming.

The app was left visibly paused at frame1. Log confirms loading captured frame50994 and Paused at frame1. Evidence: evidence/tablet-native-visible.png and visible-scene.log. Tapping may resume/end the one-frame replay; use the show script to restore it. Launcher icon alone does not supply the private capture path.

## Final measurements

All timings offscreen at1536x864, no screenshots/readback during measurement,600plays with100warm-up and500measured. Repeating one fixed frame, cached resources mode:

| Run | Redraws/s | Mean ms | Median ms | p95 ms |
| --- | ---: | ---: | ---: | ---: |
| layout-cache-600-a |30.0115|33.3021|33.5041|39.9469|
| layout-cache-600-b |30.8838|32.3626|33.3727|39.4830|

Measured duration16.6603s/16.1897s; process CPU10.5076s/10.1055s. Each result has exactly500duration samples and frame_count500. JSON and replay logs preserved under evidence/RUN_NAME. Thermal status0 was observed before final measurements; no clocks, thermal policies or driver settings were changed. This is two short warmed runs, not sustained thermal testing.

Correctness: in separate30-loop screenshot run, frame1 and frame30 are RGB bit-identical to the unmodified/raw Android replay at1536x864. See oa-layout-cache-image-validation.json. Screenshot-inclusive runs are excluded from timings. This validates this particular captured frame, not arbitrary dynamic scenes. Compared with the original PC reference, earlier v31 replay had small differences; bit-identical here means against raw Android replay.

## Why raw replay was misleading

Raw replay measured7.903FPS/300samples. Profiling479CPU samples found40.16% in libc memcpy (flat CPU-cycle profile, not wall-time attribution). A bounds-validated capture parser found2700FillMemory commands/178,291,200bytes per frame, plus GPU snapshot restoration. Repeating the capture was copying whole recorded mapped regions and restoring frame-start data on every play; that is replay overhead rather than normal incremental engine updates.

Fixed-frame modes are explicit, defaultoff, and deliberately freeze captured inputs. Mode1 skips repeat host-memory uploads/buffer snapshots; mode2 also skips image-content restoration while retaining required image-layout/synchronization corrections. First play remains normal. Mode2 uses upstream cached layout barriers and allocates no unused buffer/image snapshots. For this capture skipped counters match2700calls and178,291,200bytes per repeated frame. This is NOT a valid generic dynamic-game optimization.

Earlier mode2 version4 runs varied20.2–31.5FPS. Version5 eliminates unused snapshots/per-frame layout map scanning; its two final runs were30.0–30.9. That narrow observed range is not a guarantee across scenes or long sessions.

## Source and build

Windows authoritative work: C:\Users\rwill\Documents\Opem Amalur\work\v32-native-benchmark
Mac scripts/results: /Users/rwillmore/Documents/Codex/2026-11-05/open-amalur-native-benchmark

GFXReconstruct dev commit9a673d202dc42a7cebadd9854c940f4209819279 (development1.0.5) was pinned because installed0.9.18 and current release lacked required experimental looping support. Dependencies are pinned in downloads/sources.json (Mac evidence/sources.json). Existing NDKr30/API29, CMake, Ninja, Java21, aapt2/zipalign/apksigner were reused. No global tool installation or agent/auth changes.

Source patches are additive in isolated v32 source. Originals preserved in upstream-before-timing-fix/, before-static-memory/, before-static-images/, before-layout-cache/. Patches copied into Mac evidence/:
- loop-measurement-counter.patch fixes the rewound loop frame counter: monotonically increasing timing frame IDs and actual completed-frame reporting.3plays/1warm-up yields exactly2samples; final runs500samples.
- static-memory-benchmark.patch adds explicit mode1 and repeat upload counters.
- static-image-benchmark.patch adds explicit mode2 and layout-only reset support.
- cached-layout-bookkeeping.patch avoids unused snapshots and uses upstream cached layout barriers in mode2. The earlier custom RestoreLayoutsOnly remains compiled but unused in mode2.

Build on Windows: run oa-build-loop-android.cmd, then Python312 oa-package-native-benchmark-v5.py in this folder. APK is apk-cached-layout/open-amalur-native-benchmark.apk; unstripped symbols remain build-arm64/libgfxrecon-replay.so. Each APK version retained. Separate benchmark debug key stays ONLY on Windows; original application signing key untouched.

IMPORTANT build identity: the APK was repackaged once after installation with identical native library but different ZIP metadata/hash. Installed v5 APK SHA2561ea9009719334a090d253b5b38771a5ef34fa0c97997cbc7d55c6c0bcc09049c (Mac /private/tmp/open-amalur-native-benchmark-v5.apk). Current Windows repack APK SHA256238c6fa010c9c8964a08c39871232d7dfe4b3709f8969389c87dc37e516984b7. Both native library SHA256bec8f546347b139e8306300e6b74909d3a5f23f3ab4240caa7aa360cab504975. evidence/v5-build-info.json describes Windows repack, not installed APK. No code differences; preserve both.

Capture unchanged from v31: amalur_trim_trigger_20261105T113036.gfxr,566260898bytes, SHA25672c3524703435311542d555dc419771d820f6baf81c84676ef2c6dc28c367209. Private app copy: /data/user/0/org.openamalur.nativebenchmark/files/dalentarth.gfxr. Windows original and original DroidDeck copy preserved. No game assets/APK/key uploaded.

## Repeat and view from Mac

Use existing externally-started ADB server5037; serial99cc517a. Do not kill/restart it unnecessarily. Always inspect screen before UI input; scripts wake the device/dismiss insecure keyguard and stop ONLY this benchmark app.

    python3 oa-run-android-replay.py --name NEW_UNIQUE_RUN --loops 600 --warmup 100 --static-resources

Results are private in /data/user/0/org.openamalur.nativebenchmark/files/NEW_UNIQUE_RUN/. Use oa-collect-benchmark.py RUN_A RUN_B to retrieve logs/JSON and summarize. Its latest-summary.json replaces only that summary; individual results remain.

    python3 oa-show-native-scene.py

This launches an on-screen one-frame replay with --pause-frame 1 (actual arguments separated properly by script), then leaves it paused. It is not interactive gameplay. To stop only benchmark app:

    /opt/homebrew/bin/adb -s 99cc517a shell am force-stop org.openamalur.nativebenchmark

Host launch scripts have correct commands. New benchmark app may be updated with adb install -r; NEVER uninstall original Open Amalur app or replace its key/save. No global device settings changed.

## Limits and next engineering gate

This establishes native rendering feasibility for one graphics workload. It does not estimate FEX overhead or predict full native-game FPS: game simulation, dynamic buffers, uploads, culling, input and streaming are absent. Android driver differs from DroidDeck; raw replay and cached mode are different workloads. Upstream also serializes loops with device-idle waits, and capture decode/driver overhead remains. CPU time vswall time is not GPU timing. Logs retain VK_NOT_READY query mismatches; repeated-image check passed. Visible swapchain returned VK_SUBOPTIMAL_KHR but rendered correctly.

Next useful gate: identify the captured frame's draw/resource inputs and connect a bounded recovered engine function to a native test that can change camera/draw inputs. Keep the exact capture as a visual reference. Do not spend further time tuning replayer FPS as if it were a native engine port or promise movement from this frozen frame. FEX attribution requires a separately matched measured workload; no percentage has been established.

Original Windows capture game was last known paused, not confirmed closed. No Windows gameplay/save changes in v32. Original Android app, only save, signing key, DroidDeck configuration and Ghidra databases untouched. Sol used; no Astra, local helper or subagents used for this pass.
