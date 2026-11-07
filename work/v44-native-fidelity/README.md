# Open Amalur v0.35 — native fidelity pass

The custom engine is active in `work/v19-host`, with its Windows host in `work/v40-windows-host`. The original-engine/FEX work remains paused and preserved. This pass uses the existing game capture and native exports; it did not launch the original game or modify original saves, keys or analysis databases.

The final Android build is `outputs/scene-v44-r4/open-amalur-v0.35-r4-arm64.apk`, version 0.35.0 / code 37, package `org.opemamalur.scene`. It is installed on tablet 99cc517a with the existing signer. Installed APK SHA256: `a07cdf8bcae3d68c79f43609c7854e2584a61422ad081cdc6a7991f417613e2d`.

## Rendering changes and evidence

- Water: eight captured river draws, original geometry/UV/tangent frames/material parameters, reflection probes, depth/refraction equations and authored mip chains. All 6,494 corresponding legacy water triangles were removed across the three LODs. The native camera and ordinary walking camera now select the correct face winding.
- Foliage: recovered grass geometry, vertex colors, wind palette, leaf deformation and independent GREEN alpha masks. Seven native leaf texture chains retain authored mip levels. Thirty-six coarse cells carry source-owned native attributes. Branch material 274 was incorrectly opaque: native PS311 and draw bindings prove unit6.GREEN cutoff100/255, fixing the large dark branch cards in both color and depth/AO passes.
- Materials: source header audit for 33 native rows supplies 28 BACK and five NONE culling states. Original material rows0–262 and shared textures0/17/18/22 are preserved. Nineteen native-only static maps now use authored mips; eight have exact capture residency identity. Captured samplers use anisotropy1. The pack contains296 materials and685 texture slots.
- Lighting: recovered ambient cube channel order, terrain blend/specular data, half-float material/light boundaries, native point-light aggregation, sunlight/AO/shadow terms and per-pixel fog. Lighting is saturated to native scene UNORM before fog. Native AO, three shadow cascades, sky, bloom, distance DOF, quantized LUT nodes and final edge filtering are integrated. Posed actors contribute to depth and shadow passes.
- Render scaling: each surface initialization resets to physical defaults before applying the percentage, preventing room-to-town scale compounding.

Native arithmetic was checked independently against the captured SPIR-V streams. Read `lighting-research/combine-audit/REPORT.md`, `lighting-research/native-dof/`, `foliage-research/material-state-audit/REVIEW.md`, `foliage-research/leaf-pixel-provenance/REVIEW.md`, and `water-research/static-authored-mips/REPORT.md`. Root reviewed these findings and integrated the shared source; worker reports alone were not treated as runtime proof.

## Runtime validation

Windows final matched-camera capture: `bridge-native-v035-final.png` and its runtime log. Original frame: `work/v31-native-slice/render-20261105/windows-replay.png`. Native paths actually ran; fully streamed reference draws1749 / triangles644734,140 native-material and32 native-terrain draws. Large dark branch cards and the earlier terrain holes are gone. An isolated ordinary-camera walk also rendered water/culling correctly and moved the player down the stairs. The Windows pbuffer/readback host is not a performance benchmark.

Android R4 ran the same recovered renderer on Adreno829. The log confirms native water, AO/shadow/sky and DOF execution. Earlier integrated R2 touch walking moved the player down the steps; final R4 was checked stationary at all three render scales. Save and settings hashes remained unchanged before installation, after walking and after the final scale tests. R4 touch movement was not repeated at lower resolution, so lower-resolution input mapping is not certified by these stationary tests.

| Linear scale | Render size | Mean FPS | GPU ms | Submission/driver ms | Thermal status |
|---|---|---:|---:|---:|---|
|100%|2520×1680|35.73|26.37|21.96|0→0|
|75%|1890×1260|46.57|17.79|19.67|2→2|
|50%|1260×840|53.02|13.89|18.03|2→2|

These are short stationary samples with the same pose, native features255, shadows on, 2,173 draws and705,034 triangles. Live wind/actors and thermal state varied. Each mean uses three steady240-frame windows. CPU submission and GPU times overlap; they must not be added. The75% collector attached to an already-started process after a PID-startup race, so its collection-duration field is not a game startup measurement. Logs, screenshots and individual windows are in `android-validation/scaling/`.

Scaling helps substantially, then exposes drawing/driver overhead. Next performance work should cache material/uniform bindings, simplify depth/shadow pass state, batch or instance repeated geometry and avoid redundant static shadow work. Simulation threading has little leverage in this sample (~0.1ms measured updates). Full-resolution60FPS needs a much larger GPU reduction than the scaled case. No sustained60FPS claim is made.

## Current limits

Validation is scoped to the captured Gorhart bridge at Noon. Other time/region settings, original engine LOD selection, unsupported legacy material families and full actor lighting remain broader parity work. Eleven static texture replacements have authored-source identity but no captured residency identity; two sapling diffuse chains likewise lack active capture identity. Collapsing the original UNORM store into shader rounding retains a possible one-LSB tie-conversion difference. Point-light grid selection remains capped at eight per tile and does not guarantee original additive draw order. Foliage/paint recovery covers18 near-scene cells, not all Dalentarth.

One initialization GL0x502 remains logged on Windows and Android, also seen in the earlier baseline. No recurring error or shader failure was observed in the checked steady runs. Its origin is not resolved by this pass. Whole-game or exact pixel identity is not certified.

## Build, preservation and next use

Windows: run `work/v40-windows-host/build.cmd`. Android: build existing `work/v19-host/build-android-arm64` target `opem_amalur_scene`. The original installed tools were reused; no new system installation or agent configuration change was needed.

`final-renderer-build.json` pins the shared source and both binary hashes. `integrated-world-manifest-final.json` pins127 overlay files. The final APK contains the coherent base content plus all earlier and v44 overlays. A plain Git clone still lacks required private assets. Use the preserved base/release backup and final APK; APK assets can restore the prepared pack. Do not rerun desktop preparation from the old base without reapplying the overlays and actor-index correction.

`outputs/scene-v44-r4/source-checkpoint-v035-r4.zip` preserves169 source/build/instruction files, with a separate per-file receipt. `package_android_v035_r4.py` reuses unchanged compressed R3 ZIP records, verifies the resulting archive and signs with the existing key. Packaging took11.77seconds; preserve its unsigned R3 parent if reusing this exact script. Use a fresh revision/output name for another build.

Tablet test spawn, heading, profiling, shadow override and scale have been restored; render scale is100. Native feature mask255 remains enabled for this upgrade. App stopped. Windows preview closed and scheduled task restored to normal town mode. Original app settings/save, signing key and v0.34 rollback artifacts are intact. No GitHub upload was performed.
