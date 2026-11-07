# Windows capture checkpoint — 2026-11-04

Goal: render one real recorded Amalur frame using native ARM64 Vulkan on the
connected tablet. This is a graphics test, not playable native engine code.

Completed in this continuation:
- Read canonical project instructions and FOCUSED_PASS.md.
- Verified ROBMACHINEX SSH access and existing CMake/Visual Studio tools.
- Official GFXReconstruct v0.9.18 Windows downloadable release is x64 only.
- Downloaded official v0.9.18 source and its exact Vulkan-Headers submodule
  2bb0a23104ceffd9a28d5b7401f2cee7dae35bb8. Built x86 capture layer and generated
  its matching JSON manifest with existing Visual Studio 2026, CMake and Ninja.
- Build succeeded (50 compile/link steps), PE machine 0x14c (32-bit x86).
  DLL SHA256: 088421f076c0389dd3b533a50ac6480cd551830c8b29214119aace232c21ca97.
  Header version 1.3.239, capture version 0.9.18 matching tablet Linux ARM64 tools.
  ZSTD unavailable; bundled LZ4 and zlib found and linked.
- Prepared separate v31-native-slice/run-capture with copied game executable,
  our existing culling d3d11.dll and needed support DLLs/controller files, plus
  junctions to original Steam data directories. Original run-vk was not changed.
- capture-tools/capture-windows.cmd uses process-local Vulkan/capture variables,
  F10 trigger, one captured frame, unassisted mapped-memory tracking. No machine
  Vulkan registration or Steam launch options were modified.

Windows root: C:\Users\rwill\Documents\Opem Amalur\work\v31-native-slice.
Layer: capture-tools/build-x86/layer/VkLayer_gfxreconstruct.dll and .json.
Source: capture-tools/source/gfxreconstruct-0.9.18.
Matching official x64 replay/info tools: capture-tools/windows-x64/gfxreconstruct-v0.9.18.

BLOCKER: desktop screenshot shows Steam Refresh sign in, stating the account
logged in on another computer. No game was launched. User was asked to sign in
on the Windows PC and leave Steam open. Do not request or inspect passwords.

Next:
1. Verify current screen after user signs in; do not click saved-game delete Xs.
2. Launch capture-windows.cmd on the logged-in desktop (existing scheduled-task
   pattern). Check capture log and loaded layer in actual game before claiming use.
3. Load cave-entrance save; record screenshot. Trigger F10 once for one frame.
4. Inspect resulting .gfxr with matching x64 gfxrecon-info. Validate resource
   payload and Vulkan draw content, not just file existence.
5. Replay on Windows first to establish the capture; then use tablet ARM64
   native_guest.sh / replay_capture.py. Cross-platform replay remains unproven.
6. Capture/replay is not an engine port and cannot predict full native-engine FPS.

Actual build verified; capture layer runtime and real-frame replay NOT yet verified.
No tablet changes in this continuation; no game process started. No GitHub upload.
The Windows desk.ps1 wrapper requires invocation with powershell.exe -ExecutionPolicy
Bypass -File (process-only); direct invocation from windows_probe.py was rejected
by the existing script policy. The screenshot completed through the existing
interactive scheduled-task pattern. Its wrapper can take roughly a minute.

Official source/release: https://github.com/LunarG/gfxreconstruct/releases/tag/v0.9.18
