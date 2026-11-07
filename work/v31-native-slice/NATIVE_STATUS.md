**Latest (2026-11-05): real Dalentarth frame rendered successfully on tablet ARM64.**
Read `RENDER_RESULT_2026-11-05.md` first. This is a native graphics replay; gameplay
and steady-state performance remain unfinished. Earlier checkpoints below are historical.

# Native ARM64 slice checkpoint — 2026-11-04

**Newer checkpoint:** Read `FOCUSED_PASS.md` first. The material-constant helper
0x00c34c90 is now ported with 29 passing native ARM64 contract checks. The tablet
capture-layer experiment failed at launch and was reverted; no native scene has
rendered. Next bounded step is a complete capture on Windows, not another tablet
driver/capture retry. The following text preserves the earlier checkpoint.

Goal: build a native ARM64 slice of the original recovered rendering code and
ultimately render a self-contained real captured game frame without FEX.

Completed:
- `native-render/oa_recovered.c/.h`: portable kind-0 geometry submission boundary
  inside original engine function 0x00c961e0, quad expansion ordering from its
  immediate drawing path, and texture subresource arithmetic from 0x010596c0.
- Input capture addresses/resource tokens are explicitly uint32_t; captured game
  pointers are never cast to native pointers. Geometry submission uses a native
  callback interface rather than original COM/vtable addresses.
- `probe.c` tests indexed/non-indexed call contracts, unsafe/truncated address
  rejection, quad ordering/capacity/overlap and subresource arithmetic.
- Built with installed Windows Android NDK r30 (30.0.16248370), API 26, ARM64.
- Actual tablet execution succeeded: 17 checks, 64-bit host pointers. ELF machine
  AArch64 and Android `/system/bin/linker64`. This executable runs without FEX.
- Fixtures are SYNTHETIC contract tests, not a captured real scene. Full material,
  state, constant-buffer setup and complete engine function are NOT ported.

Files on Windows: C:\Users\rwill\Documents\Opem Amalur\work\v31-native-slice.
Mac source/results: this folder's native-render/.
Tablet probe: /data/local/tmp/oa-native-probe.
Probe SHA256: 48db135e1f48180dd885d6cc869184cd2c41a068937b89a217d1961adadbd7ae.

Open problem:
Existing v30 recordings store call sequences/counts and shaders, not the full
geometry/texture contents and complete state needed for self-contained replay.
No native game frame has been rendered and no native full-game FPS is known.

Capture experiment prepared, not configured/enabled:
- Downloaded/extracted Debian's ARM64 GFXReconstruct 0.9.18 package into
  capture-tools/. No system package installation or library replacement.
- Isolated tools copied to DroidDeck guest /root/oa-native-tools.
- ARM64 gfxrecon-replay --version works through a native chroot; this is a Linux
  ARM64 tool under Android's kernel, NOT a standalone native Android APK and NOT
  the original engine port.
- Native X display connectivity test blocked and its owned test was terminated.
- DroidDeck's agent bridge stopped servicing requests after a game restart.
  Its Steam proot supervisor PID 32424 was originally stopped; a temporary
  SIGCONT to that supervisor and agent PID 32611 did not restore bridge operation.
  Check current state before using/restoring them; never blindly signal reused PIDs.
- Two OWN pending read-only bridge requests may remain:
  oa-feedbb0295764db688fdd480c0fa1c16 and oa-c03f63ce914b47078897a18fa44e2df6.
- No GFX capture layer, capture environment variables or driver changes have
  been enabled. DroidDeck game-environment.json schema was inspected only:
  version=1; per-game entries under games[app_id]. Preserve existing shared keys.
- Cross-platform replay and graphics-only replay cannot establish native engine
  performance. Do not present a GPU replay or generic scene viewer as a whole
  original-engine native build.

Existing game remains on prior highest-mip diagnostic renderer, toggle OFF,
from the earlier stopped texture investigation. Original renderer rollback:
/sdcard/Download/oa/rollback-20261104-lod0/d3d11.dll.
Do not uninstall the original Open Amalur app, modify its save/signing key, or
edit frozen custom-engine sources to disguise missing original-engine recovery.
