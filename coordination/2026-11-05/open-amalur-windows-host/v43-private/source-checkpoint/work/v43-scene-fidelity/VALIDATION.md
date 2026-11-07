# v43 integrated validation

## Build/package

Both final builds returned0: Windows MSVC x64 host and NDKr30 arm64 shared library. final-renderer-build.json pins the five changed source hashes and Android library60622b309b2a5713722b06a15f0407312867bf3b24a26ba2e0a817add401d12f. The Android compiler reports the existing unused collision variable and long combined GLSL-string warning; no compile/link error remains.

Signed v0.34 APK:858235805bytes, SHA256 ecae89e850c37a7819b719f261e8a8580b5a280b165b5eab42cbf57a4f9b9c4a. 6677 original ZIP entries preserved. Every overlay entry was hash checked after signing; duplicate names and CRC corruption rejected; signature and16KiB alignment verified. Scene identity020c6df9316e33fded0280605deb1bd60f6217a4adb4b5465689422e50e05475 matches the compiled marker and cache. Actual previously installed APK v2 certificate SHA256c47ba7823090afa66297683d7be45c2df8d7c37e1443bcece168f5b915e9344f matches the new signer.

## Windows visible checks

- Controller same-start v42 comparison: old body passes target plane (x6596.516), new stops x6377.729 with positive68.786remaining. Grounded/valid1, contacts464; probe PASS. See v42/collision-land-approach-results.json.
- Live Windows app: crate approach blocked x6379.953, reverse x6078.612, valid1 and zero recoveries. Blocked corner grounded0 caveat; after reverse grounded1. v43/collision-completed.json and collision-walk-*.png/json.
- Original bridge fixed VP/player-hidden: native127 and post-off63 metadata matrices identical. Runtime confirms features127, native material34draws, terrain32draws, atlas4097/R8UI4096uploaded80MB and actual native post constants. Comparison bridge-post-comparison.json is only a change detector, not a ground-truth parity score because actors/water animate.
- Shop exterior: native material44draws, terrain19draws, actual features127. shop-native127.png.
- Enter and exit shop: metadata world0then1, grounded1, valid scene images and resource recreation. shop-interior-regression and shop-return-regression PNG/JSON. World load caused a recorded~4.9second desktop hitch; no instant-loading claim.
- One known initial profiler GL_INVALID_OPERATION0x502 remains. No subsequent recurring GL error or shader compile failure appears in the final Windows run.
- Desktop audio_xruns4294967295 is unsupported-adapter output, not a measured underrun count.

## Tablet checks

Device99cc517a, OPD2515, Android16, Adreno829. adb install-r succeeded to v0.34.0/versionCode36. No uninstall, app data clear, signing key replacement or save modification.

Save88B SHA25613734501b6cdbd25fbe8fa8202226ea084382755d2522ee46d0b985045e85f11 and settings184B SHA25627665629f70cf1902ed4e5bec8daadcd6cdb5dfef857dfd3a0430ab475af0c55 remained identical after update and after all tests. Private pre-update APK and tar backup retained on the Mac.

Fresh GPU view shows native terrain roads and recovered props; runtime native_terrain_draws19/native_material_draws42/features127. Captured post values consumed: exposure.8277000, minLum.1738000, inverseRange1.2103606, bloomMerge.4306861.

Touch walk moved from(1575.060,-62759.434,5145.830) to(1575.060,-62558.645,5137.924), grounded1, zero recoveries. Real restored crate fixture stopped at(6376.775,-85831.508,5862.581), then backed out to(6129.411,-85831.508,5863.030), grounded/valid1 at both ends and zero recoveries. See tablet-prop-full.log and before/blocked/back images.

Touch prompt enters/exits shop. Injected keyboard E did not activate it on Android; no general keyboard compatibility claim. Home/resume kept the same PID22838 and successfully recreated surface/paint atlas/post resources. One early return screenshot caught asynchronous cells still streaming; settled/resumed capture has complete nearby ground/buildings. No loading-screen feature was added.

Bounded stationary shop performance: eight retained240-frame interval samples, initial two logcat backfill samples excluded. Mean17.67875ms =56.565FPS, sample means17.64..17.76ms, largest reported frame27.2ms. Mean CPU submit12.201ms, swap5.206ms. Asynchronous GPU queries18.33ms must not be added to CPU/swap. Resolution2520x1680, thermal status0. PSS snapshot~680MB. No sustained thermal, original-game-equivalent workload, full campaign or worst-case performance claim. See tablet-steady-summary/window JSON and raw log.

After tests: app force-stopped, temporary spawn cleared, heading0/profile0 restored, live127 deliberately retained. Save/settings still byte-identical. Display sleep requested. The final package is Dalentarth, replacing the former Erathell test assets; old APK remains privately backed up. Source-save format unchanged.

All native findings have qualified provenance in CODEX_EVIDENCE_REVIEW.json and the three research reports. Full scene/material/lighting parity remains incomplete.
