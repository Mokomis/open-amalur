# v43 scene fidelity / Android v0.34

This closes the five-milestone pass authorized on 2026-11-05. The active product is the custom C/GLES3 native engine, shared between the Windows development host and arm64 Android. The original-engine/FEX port remains paused and untouched. This is a scene/gameplay prototype, not a completed game or an engine decompilation.

## Delivered scope

1. **Solid restored props.** Visual-mesh collision is deployed for the 251 recovered static props plus the 16 new barrel02 instances. Original collision is backed up. Independent same-start controller comparison proves the previous controller passes through the crate and the new geometry blocks it. Windows app can stop and back out without recovery. At one detailed Windows corner the grounded flag went false; it could still back out. The tablet stopped grounded and backed out grounded, with zero recoveries. This is static triangle collision, not the original rigid-body/destruction system.
2. **Evidence-driven shared lighting/material/post pass.** Captured global buffer binding proves the existing Noon sun/fog values were already correct. Retained natural-exp fog; did not brighten the whole cube by five. Added measured sky/ambient inputs, native ambient/specular terms for three supported dot3 materials, and active captured bloom extraction/merge constants. Exposure is applied only to bloom. A fixed original-camera GPU A/B confirms the new path ran. The original multiscale blur, deferred AO/shadow combination, sky/water reflections, and adaptive time/region settings are still incomplete. This is a scoped fidelity milestone, not exact whole-scene lighting parity.
3. **Native terrain paint.** Recovered descriptor-indexed paint maps, native palette selection, per-triangle set selectors, alpha height blending, normals and UV scales. All 1344 paint descriptors decoded, shared atlas edges agree. Integrated five sets across 18 shop/bridge cells, all three LODs. Original vertex/index geometry is unchanged. Real roads now render on Windows and Android. Unmapped/unsupported selectors preserve legacy ground. The separately discovered missing early height chunks and foliage/grass geometry are not rebuilt here.
4. **Non-identity local bind recovery.** Original reviewed pure native kernels plus raw assembly confirm the +15-degree local barrel02 pose in our convention. Sixteen type360769 placements added across ten cells; total added static visuals is now267. This proves the serialized-to-instance pose contract for one no-remap/unit-scale case, not every FAB or an observed original draw.
5. **Integrated Android delivery.** v0.34.0/versionCode36 installed over v0.33 without uninstalling. Same signer independently matched the previously installed APK. Save and settings hashes remained identical before the update, after it, and after all tests. Touch walking, crate blocking/reverse, shop enter/exit and Home/resume passed. New paint maps/post resources recreated after surface loss. Device screenshots and measured short stationary performance are saved in android-validation/.

## Where things are

- Shared implementation: work/v19-host/{android_scene.c,oa_stream.c/.h,oa_post.c/.h}.
- Windows development host and prepared private pack: work/v40-windows-host/.
- Generated combined overlay: integrated-world/, integrated-world-manifest.json.
- Independent source research: lighting-research/, terrain-research/, placement-research/.
- Codex review: CODEX_EVIDENCE_REVIEW.json; see qualifications in the reports.
- Native post sidecar: lighting-overlay/post.bin, post-deployment.json.
- Final source/library build hashes: final-renderer-build.json.
- Android package recipe: package_android_v034.py, package-v034.log.
- Signed APK: outputs/scene-v43/open-amalur-v0.34-arm64.apk.
- Signed payload/build receipt: outputs/scene-v43/android-apk-manifest.json.
- Tablet validation and evidence: android-validation/ANDROID_VALIDATION.json and evidence/.
- Original source/asset/project-note backups: before/, before-integrated-world/, before-project-notes/; earlier v40/v42 backups are retained.

## Build and use

On the logged-in Windows desktop, from work/v40-windows-host:

    build.cmd
    python start.py --scene town
    python control.py capture --out NEW.png
    python control.py close

For a fixed original bridge camera:

    python start.py --scene reference
    python control.py capture --user-data reference-data --out NEW.png
    python control.py close --user-data reference-data

The existing scheduled task OA_CustomEngine_Windows_v40 starts the normal town preview when invoked over SSH. Only one preview/control writer should run. Windows saves and test user-data folders are separate from Android.

The shared Android library is built with the existing work/v19-host/build-android-arm64 CMake/NDK r30 target. The v0.34 package script validates source and library hashes against final-renderer-build.json and refuses to overwrite an existing signed v0.34 APK. Give future releases a new output/version. It starts from the coherent Dalentarth v0.33 APK and overlays only changed files, preserving original ASTC textures. Desktop RGBA texture expansion must not be copied wholesale into Android.

Do not casually rerun v40 prepare.py over this prepared asset set. Regenerating from the old APK needs v41 actor corrections, v42 static visuals/collision and the v43 merged overlay reapplied in order. The v43 merged overlay includes overlapping terrain/barrel cells; copying the two research overlays over each other loses content. post.bin was deployed separately and has its own hash receipt.

Device update from the Mac uses the existing adb:

    /opt/homebrew/bin/adb install -r /absolute/path/open-amalur-v0.34-arm64.apk
    /opt/homebrew/bin/adb shell am start -n org.opemamalur.scene/android.app.NativeActivity

Keep package org.opemamalur.scene and the existing Windows-only signing key. Do not uninstall. The original installed APK and all app files are privately backed up on the Mac; direct version downgrade can be rejected by Android, so do not uninstall to work around it. A future rollback package would need an accepted version code and the same key.

## Renderer switches

Debug feature bitmask debug.opem.live defaults to127. Existing base bits1..8 retain their old meanings;16 enables scoped native dot3,32 enables native terrain paint,64 enables recovered post. Thus15 is the legacy comparison,63 omits new post,127 enables the combined result. In profiling mode the live mask refreshes every500ms; logs confirm actual applied values. The Windows INI lives in the active user-data folder. Android uses adb shell setprop. Profiling is off on the tablet after testing; live127 remains enabled. Temporary debug spawn/heading were cleared/restored. The app is stopped and the display was put back to sleep.

## Evidence boundaries / next work

See VALIDATION.md. The reference camera matches the original PC view/projection; Android captures are normal third-person views, not an exact original-camera pixel comparison. Windows uses an ANGLE pbuffer/readback/GDI path and its FPS cannot predict Android performance. Tablet stationary shop sample at2520x1680 averaged17.679ms (~56.6FPS), thermal status0. It is not a sustained gameplay/campaign result.

Remaining visible gaps: foliage geometry/density/lighting; water depth/reflections/fog; native multiscale bloom and proper deferred AO/shadow behavior; terrain height coverage outside the existing pack; broader material families/local binds. The next broad product step after the scene fidelity work is still one real quest with dialogue, objective, reward and persistent reload. Do not resume broad original-engine decompilation or FEX diagnosis unless directed.

Keep APKs, extracted game data, recordings, native decompilation and signing keys private. Nothing was uploaded to GitHub in this pass. Existing original game installs/saves/databases and worker configuration were not changed. The optional Qwen helper was not started. No exact credit meter is available; final Windows/Android builds were batched, and no Astra escalation occurred.
