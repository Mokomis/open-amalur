# Open Amalur native camera — verified 2026-11-05

## Current result

The separate native Android app now opens the real captured Dalentarth scene from its launcher and allows camera rotation/translation. It runs directly as ARM64 using Android Vulkan, without FEX, Wine or DroidDeck. This is a captured-scene viewer with a recovered engine matrix kernel; the live game engine, animation, collision and streaming are not ported.

Tablet: OPD2515, serial99cc517a. Package org.openamalur.nativebenchmark, UID10308, versionCode8 / versionName0.8-camera-launcher, app label Open Amalur Camera Test. Uses the original benchmark app's private key in Windows v32; original Open Amalur application's signing key/save untouched. Source authoritative on Windows in C:\Users\rwill\Documents\Opem Amalur\work\v33-native-camera. v32 source/build/artifacts preserved separately.

Controls: one-finger drag looks; tap resets camera; two-finger drag is implemented for translation but not yet gesture-tested. Keyboard arrows or WASD translate; R resets. Up-arrow movement20 game units and R reset were exercised through Android input and confirmed in the log and screen. v6 touch drag and tap reset were observed; v8 retains that path with native projection rebuilding. Current viewer left at reset view (verify device before interaction). To restore it, launch the app icon or run oa-launch-camera.py without a loop limit.

## Native code recovery with original-code comparison

Recovered function: koa.exe build cs:15032 VA0x00abc070 (RVA0x006bc070),1618bytes, returns left*right with row-vector matrix layout. Original destination ECX, right/left on stack, ret8. SHA256be9a7a669ee2309ca456abdd93a5175f7f3623a8da9e9bd5e663d9a11bfd8b49. Original executable SHA25616a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314.

The native SSE assembly uses cvtps2pd, mulsd/addsd, then cvtpd2ps: double intermediates followed by float storage. Ghidra pseudocode conceals that distinction. Portable oa_recovered_matrix.h preserves it and disables fused multiply-add. Windows32bit probe executed a private copy of the exact original instructions in an RX page; no game executable bytes changed. Assembly checked for no calls/branches/global memory operands. ARM64 probe executed directly on the tablet.

Validation:4221 input pairs,0 differences for original x86 vs reconstructed x86 and original x86 vs native ARM64. Includes1024 finite randomized matrices,1598 captured matrices with identity, a cancellation case and1598 actual model/camera producer pairs. Original and reconstructed code reproduce ALL1598 captured object projection matrices byte-for-byte.1596 use the absolute shared VP;2 packed-instance records use rotation-only VP (matrix offsets3328,642944). See matrix-validation.json, projection-producer-correlation.json and matrix-proof-*.bin.

Engine producer0x00c92150 writes model, normal and projection blocks at offsets0x00,0x40,0x80 and calls0x00abc070. Original native code evidence stays on Windows in native-projection-producer.txt, abc070-assembly.txt, matrix-native-identity.json. Existing Ghidra exports reused, original databases untouched. REA6.8.0 reports no active binary; no redundant whole-game reimport performed.

The Android renderer now rebuilds1598 projections from captured model matrices and camera VP through this kernel on every camera change, rather than simply modifying old output matrices. An exact memory-prefix fingerprint admits only this capture. Six shared camera records also have VP, position and forward updated. This is a real bounded native engine function integrated into the viewer, not evidence of a complete engine port.

## Captured camera evidence

Source capture unchanged from v31: amalur_trim_trigger_20261105T113036.gfxr,566260898bytes, SHA25672c3524703435311542d555dc419771d820f6baf81c84676ef2c6dc28c367209. Captured frame50994. Private app file /data/user/0/org.openamalur.nativebenchmark/files/dalentarth.gfxr.

Existing GFXReconstruct0.9.18 converter produced dalentarth.jsonl (~19.6MB). Only header line is invalid JSON due to unescaped Windows backslashes; all other lines parse. Capture block indices zero-based. Live frame begins62468; pre-state includes older command buffers. Live2753draws. Main depth pass93 has987 draws and geometry pass97 has799. Every draw in both uses a CB4 projection at vectors8..11 (+0x80). Our translator maps vertex slots to64+slot; shaders312,789,791 confirm binding68 reads.1598unique perspective matrices cover these plus other world passes. Orthographic shadows excluded by z/w basis test. capture-index.json and camera-manifest.json preserve identities.

Six144byte shared CB2 records at memory52 offsets639296,1482688,1622016,1704000,1764224,1764672. Camera VP rows0..3, positionrow4, forwardrow5, projection/depth valuesrows6..7 and pixel sizesrow8. Basis/forward/position-to-VP numeric agreement and shader accesses support the recovered fields. Native0x00c66520 is a generic144byte update candidate; its link to the camera record is NOT yet proven. Do not call it a confirmed camera producer.

Measured projection fx1.311106091287448, fy2.330855274807898, q1.00004996337216, near term-26.1875. World camera position8591.9326,-87036.03125,6493.0664. Per-object model matrices and absolute VP regenerate captured projections exactly, including translation. Remaining special effects/camera-dependent uniforms are not exhaustively traced.

## Runtime checks

v6: zero30 loops first/last/raw RGB identical. Yaw0.08 and right80/forward80 visibly alter geometry with stable first/last. Touch drag produced yaw-0.0686,pitch0.02058; tap reset restored allzero.
v8: camera-v8-zero-30 first/last/raw RGB bit-identical at1536x864 after native projection rebuild and all6 shared record updates. camera-v8-motion-30 (yaw0.06,pitch0.02,right20,forward20) first/last RGB identical with visibly changed world and fixed HUD. Logs confirm1598 matrices/6 shared records applied. Default launcher with no arguments loaded the scene. Up-arrow produced forward20; R reset verified. These screenshot tests are correctness checks, not performance numbers. The previous30.0–30.9 redraws/s belongs to v32 static benchmarking; dynamic v8 camera performance is not measured.

## Build and repeat

Pinned upstream GFXReconstruct dev9a673d202dc42a7cebadd9854c940f4209819279. Existing NDKr30, API29, CMake/Ninja, Java21 and Android build tools reused. Copied v32 source into isolated v33; dependencies reused from v32. Initial219 build steps passed; later edits built in small batches. No tools/auth/databases reset, no agents/Astra used.

Windows build: oa-build-native-camera.cmd, then Python312 oa-package-camera-launcher.py. Latest APK apk-camera-launcher/open-amalur-native-benchmark.apk SHA256064ac125ff4e4de4b2d08273be24e59d6841e5183f54b49ff0c4bc5dbcdd4409. Native library SHA2561a5f354f7870d89fb069954c6f61ded6c1da9d01f0b155447828b697ad42ab9f. v5,v6,v7,v8 APKs retained; v7 was packaged but not installed. All own benchmark updates used adb install -r. Original applications never uninstalled.

From this Mac directory:

    python3 oa-launch-camera.py
    python3 oa-launch-camera.py --name UNIQUE_TEST --loops 30 --screenshots 1,30 --offscreen --yaw 0.06 --pitch 0.02 --right 20 --forward 20
    python3 oa-camera-readback.py UNIQUE_TEST
    /opt/homebrew/bin/adb -s 99cc517a shell am force-stop org.openamalur.nativebenchmark

Launcher intent also works directly, no args:

    /opt/homebrew/bin/adb -s 99cc517a shell am start -a android.intent.action.MAIN -c android.intent.category.LAUNCHER -n org.openamalur.nativebenchmark/android.app.NativeActivity

No loop limit means continuous redraw until app stopped/backgrounded. Screen stays awake while active (upstream app behavior), no global timeout/thermal/clock setting changed. NativeActivity taps now reset instead of upstream pause only in explicit camera/default-viewer mode. Explicit benchmark args preserve old paths. Camera file private in app files: camera.txt four floats yaw,pitch,right,forward; only changed lines override touch state. Default app launch resets it tozero. Limits yaw0.2rad,pitch0.13rad,right/forward300 units.

Before UI input, inspect current screen. ADB externally-started server5037 works; do not restart it unnecessarily. SSH alias open-rune-windows, hostRobMachineX. /private/tmp/oa-win.py avoids occasional FileProvider stalls. Keep capture/APKs/game binaries/original pseudocode and all keys private. Original Windows game remains paused in v31 run-capture PID15992 (verify before tracing). No Windows gameplay/save changes during v33.

## Current boundary / next work

The visible view is still a fixed captured scene. Camera controls cannot recover culled/unrecorded objects, animation, collision or live gameplay. Camera movement can expose missing geometry and frozen effects. No full native-game FPS or FEX overhead percentage established. Do not tune replay FPS as if it were game simulation.

Continuing in v34-native-packets: capture one original engine draw packet and its actual native D3D submissions, then feed its32bit object snapshot into existing portable geometry decoder on ARM64. GPU-only capture lacks those original object roots. Windows game still running/paused in same scene; existing Frida17.23.2 Node bindings located at tools/rea-frida, Node26.13.0. No new install. Node local-device probe is in progress/check result before attaching. Keep instrumentation bounded, remove hooks/detach, preserve game saves. Read applicable AGENTS before further work.
