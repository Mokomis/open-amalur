# First real ARM64 scene frame — 2026-11-05

## Confirmed result

A complete captured Dalentarth game frame was successfully rendered on the
OPPO Pad Mini's Adreno 829 using the native ARM64 Linux GFXReconstruct 0.9.18
replayer. Exit code 0; screenshot generated and visually inspected. Terrain,
character, foliage, textures, lighting and HUD are present and closely match
Windows replay of the identical captured frame.

The executable is ELF64, little-endian, machine 183 (AArch64). Its native Linux
loader and Vulkan driver run directly under Android's kernel in a private chroot
mount namespace. This invocation uses no FEX, Wine or proot. This is a native
captured-frame graphics replay, not the recovered engine/game loop or a standalone
Android APK. It does not yet support movement or gameplay.

## Capture and proof

Windows capture layer: our separately built x86 GFXReconstruct 0.9.18, verified
loaded in actual koa.exe alongside our own d3d11.dll. Scene: Dalentarth (Tutorial
Complete), level-1 Moko, outdoor woodland bridge. This is not yesterday's tablet
cave view. One F10 trigger captured frame 50994.

File: captures/amalur_trim_trigger_20261105T113036.gfxr under the Windows v31 root.
Length 566,260,898 bytes; SHA256 on Windows, Mac and tablet:
72c3524703435311542d555dc419771d820f6baf81c84676ef2c6dc28c367209.
GFXReconstruct info: 1 trimmed frame, Vulkan 1.3.0, LZ4, 3,731 allocations,
134 graphics pipelines and 5 compute pipelines (the capture also includes the
loaded Steam Vulkan overlay). Largest allocation 41,943,040 bytes.

Windows standalone replay exited 0 and wrote a 1536x864 BMP. ARM64 headless replay
also exited 0 and produced the same-sized view. Evidence is in
`evidence/render-20261105/`, including PNGs, logs, result JSON, image comparison,
capture info and hashes. The capture itself stays private on Windows/tablet;
Mac staging copy is /private/tmp/oa-dalentarth-20261105.gfxr.

Image comparison of the identical GPU workload, RGB channels only:
- Mean absolute channel error: 1.37247 on a 0..255 scale.
- 2.9761% of pixels have any RGB channel difference above 8.
- Images are close by eye, not pixel-identical. No claim of universal rendering
  equivalence is made from one scene.

## Native invocation

Tablet capture:
/data/user/0/com.droiddeck.launcher/files/linuxfs/root/oa-native-tools/captures/dalentarth-20261105.gfxr

Successful result folder, relative to guest /root/oa-native-tools/results/:
dalentarth-20261105-1793900741962400035/

Invoke through root ADB, with the existing private namespace launcher:

```sh
timeout 60 /system/bin/sh /data/local/tmp/oa-native-guest.sh /usr/bin/python3 /root/oa-native-tools/oa-replay-capture.py /root/oa-native-tools/captures/dalentarth-20261105.gfxr --wsi headless --timeout 50
```

Replayer arguments include --remove-unsupported, --memory-translation rebind,
--opcd, --screenshot-all. These remove Windows-only extensions and adapt allocation
requirements from NVIDIA to Adreno. Installed drivers were not changed. The
isolated existing-driver copy driver.so/driver.json needed ownership/read access
for DroidDeck UID 10307; an initial run failed to find the driver until that was
corrected. Its failed result/log are preserved separately.

The native process completed, and no private mounts remain in the host namespace.
The original Android game/app, saves and signing key were not modified.

## Timing: do not call this gameplay performance

Native total Python wrapper time ~2.27 s. Replayer reported 1.965 s loading and
0.180 s for one frame. Windows reported 2.993 s loading and 0.046 s for one frame.
Those frame intervals include screenshot/readback and first-use work. The tool's
printed 5.54 FPS (ARM64) and 21.57 FPS (Windows) are NOT steady rendering rates,
not game FPS, and cannot establish FEX overhead or native-engine performance.

Next measured task: repeat the same graphics workload after warm-up, excluding
loading, shader/pipeline setup and screenshot readback; measure CPU submission
and GPU time separately. The current 0.9.18 CLI has no frame-loop option. Prefer
a validated loop in the replayer or a bounded multi-frame capture; do not equate
relaunching one-frame captures with a steady-state benchmark. Engine simulation,
script, animation, scene loading and D3D-to-Vulkan translation remain outside
this replay and require separate implementation/profiling.

## Operational notes

- Initial 0-byte capture file was temporary while the recorder gathered state;
  it completed without retrying capture. Do not infer deadlock from that first
  metadata sample. LLDB attempt produced no usable output; no attachment was
  confirmed or needed. No game binary was patched during this capture.
- All 19 Windows save/metadata files matched the pre-test backup after capture.
  Result is captures/save-check.json. Original test game is left paused on Windows;
  the SSH CloseMainWindow call did not close it across the desktop session.
- Capture/replay scheduled tasks: OA_native_capture_20261105 and
  OA_native_replay_20261105. They completed launch actions; no persistent service
  or global Vulkan registration was installed. Do not rerun them blindly.
- Mac ADB started inside this app could see USB descriptors but repeatedly failed
  with usb_osx interface plug-in error e00002be. A temporary LIBUSB server on 5038
  also saw no device and was stopped. User restarted the usual 5037 server from
  ordinary Mac Terminal; USB immediately worked. Keep that working server alive.
  No tablet settings or authorization keys were reset.
- tablet.py now uses the existing absolute /opt/homebrew/bin/adb path so a minimal
  host shell PATH does not prevent invoking the helper.
- Source/notes/tool changes are saved in the Windows v31 root and this Mac folder.
  No game payload, decompile, key, or capture was uploaded to GitHub.
