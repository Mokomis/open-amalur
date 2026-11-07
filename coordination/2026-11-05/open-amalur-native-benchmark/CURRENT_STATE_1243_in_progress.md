# Native benchmark continuation — 2026-11-05, in progress

Read canonical project AGENTS.md and v31 RENDER_RESULT_2026-11-05.md first.
Windows authoritative new work: C:\Users\rwill\Documents\Opem Amalur\work\v32-native-benchmark.
Sol is active; no Astra or sub-agent delegation used. Internet use is authorized
by owner; platform may enforce network permission at turn boundaries.

Built Android ARM64 replay from upstream GFXReconstruct dev commit
9a673d202dc42a7cebadd9854c940f4209819279 with existing Windows NDK r30, API29,
CMake and Ninja. Source/dependency archive versions+hashes in downloads/sources.json.
219-step initial build succeeded. NativeActivity APK packaged by our own small
script, separate package org.openamalur.nativebenchmark, UID10308. Installed on
OPD2515 99cc517a. Its own debug signing key is private in v32; ORIGINAL game key
was not touched. Original game/app and DroidDeck configs remain untouched.

New app capture in /data/user/0/org.openamalur.nativebenchmark/files/dalentarth.gfxr
(copy of v31 capture; original in DroidDeck and Windows remains). Root-owned copy
was chowned UID10308 and restorecon applied only to new app files.

Loop support is experimental upstream. It rendered frame1/frame3 pixel-identically
at1536x864 with Android stock Adreno driver (vulkan.adreno.so), no FEX/Wine/Proot.
This differs from the earlier Linux ARM64 replay's Turnip driver; comparisons
cannot attribute differences solely to FEX.

Found/fixed upstream timing bug: the loop restores the file position, so its
measurement reporting counted only1 frame and rejected warm-up range. Local
loop-measurement-counter.patch fixes Application::Run timing indices and
FpsInfo::GetLastCompletedFrame; replay_main_common uses actual completed plays.
Validation:3plays,1warm-up produces frame_count2 and2duration samples correctly.
Version2 APK hash ff8e04524df26c40eb522cae4a3a135d65fd0ed243e61715da44a4cc79f4f52a.
Old APK and upstream files preserved. V2 native library stripped for packaging;
unstripped build artifact still available for symbols. See apk-timing-fix/.

Raw replay measurement (no screenshots, offscreen, warm-up excluded):
- baseline-360-a:360plays,60warm-up,300measured.37.9604s,7.90297FPS.
  300duration samples; mean126.508ms, median127.779ms, p95136.071ms.
  Process CPU24.3779s. Thermal status0 before run; raw thermal sensors appear
  implausible and are not used to claim throttling.
- profile-120:120plays,20warm-up,100measured.8.18291FPS.
- profile-120b: same run with simpleperf recorded8seconds at99Hz cpu-cycles.
  /data/local/tmp/oa-native-profile-120b.data,1.89MB.479samples.
 40.16% of sampled CPU cycles in libc __memcpy_aarch64_nt; vendor driver also
 significant. Flat profile only, not a wall-time attribution or callgraph.
 Android simpleperf has NO --stdio option; omit it. Report is at
 /data/local/tmp/oa-native-profile-report.txt.

These raw replay FPS values DO NOT establish native-game performance. Source
capture parser (public v0.9.18 format, file bounds/EOF validated) found per-frame
2,700 FillMemory commands totaling178,291,200bytes; ~170MiB reuploaded every loop.
Snapshot setup is524MB; captured frame body41MB compressed. This is significant
capture/replay overhead compared with real incremental engine writes.

CURRENT WORK: build a benchmark-only optional frozen-buffer mode. Script
OA-add-static-memory-mode.py is patched into isolated source and currently building
through existing SSH exec session87713 (check completion/log before more builds).
Adds intent extra oa_static_memory=1; defaultfalse. In repetitions skips host
FillMemory commands and buffer-content restoration; first play and all image,
fence,event,semaphore fixups retained. This is specifically a fixed-input rendering
experiment, NOT a general valid dynamic-game optimization. MUST compare new frame1
and late loop screenshots to raw baseline before using performance figures.
Stats log records skipped bytes/calls. Expected per skipped frame2700calls and
178291200bytes if all are Vulkan FillMemory.
Patch: static-memory-benchmark.patch. Before-edit files in before-static-memory/.
Timing patch original files in upstream-before-timing-fix/.

Next: finish build; packagev3 using separate apk-static-memory/ folder/versionCode3,
matching own benchmark key; keep v1/v2. Update only benchmark app (adb install-r),
never original apps. Extend host runner --static-memory to add --es oa_static_memory1.
Validate3or30loops+first/lastscreenshots; compareRGBto pre-change raw image. Then
run360plays/60warm-up without screenshots in raw/frozen modes as justified.
Measure and clearly label static rendering replay, not engine/game FPS.
Put a visible scene in app window after offscreen timing passes as promised.

Host helper in this folder starts ONLY new benchmark app, uses private result
folders and force-stops only that app. It wakes/dismisses insecure keyguard before
run to avoid paused initial loading; never changes global screen timeout. Always
inspect current screen before input. App automatically exits after requested loops.
Capture/root result reads via tablet.py root; fixed absolute ADB path. Working
ADB5037 server was started by user outside this app; preserve it. USB works.

Initial install waited on ColorOS Install button while deviceasleep; wake+look
showed authorized installer screen, Install tapped, succeeded. Updates of same
new app signature completed without further UI. No original game uninstall.
Private result paths: /data/user/0/org.openamalur.nativebenchmark/files/RUN_NAME/.
Raw/log scripts and results copied into this Mac folder. APKs,capture,private
signing key should stay private and never be pushed to GitHub.
