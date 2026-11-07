# v47 performance and portable worker sizing
v0.38.0 / code40 installed in place on OPD2515, preserving signing identity and all save/settings bytes.

## Result
The cache removes repeated world-program uniform lookups, redundant texture binds and setup of programs unused in a pass. No shader, mesh, material, canopy, waterfall or texture bytes were changed. Runtime comparison: debug.opem.rendercache=0 uses the previous path;1 is default.
Windows A/B/A: twelve depth samples and six opaque-color samples exactly match. Final images include moving particles/actors and are not pixel-identical; full-image A/B mean difference2.90levels versus A/A3.03, so no full-image parity claim.
Windows steady world lookups20144->0; texture binds15529->10683; program setups42->23.

## Tablet measurements
Same view/process and live cache toggle, two full240-frame intervals per mode after discarding transition interval. All tablet cases use automatic3background readers.
-2520x1680: cacheA34.89FPS, legacy34.20, cacheB33.42. GPU25.7->27.1ms changed over run; no proven full-resolution FPS increase. Submission cache20.7-21.5ms vs legacy23.2ms.
-1260x840 (50% linear/25% pixels): cache59.97FPS vs legacy52.34; submission15.85ms vs18.63ms, GPU9.48ms vs9.51ms. Short sequential samples, not sustained thermal/campaign proof.
This gain is attributable to the render-cache comparison, NOT isolated proof of benefit from additional loading workers.

## Worker scaling
Counts CPUs available to the process using affinity APIs, then conservatively chooses half the spare CPUs after reserving two, minimum1 maximum4 background readers. Examples:1/2/4CPUs->1worker;6->2;8->3;12+->4.
No hardcoded big/little arrangement, no affinity pinning. Best-effort background priority; OS handles heterogeneous placement.
Independent asset reads can run concurrently; collision builds remain single-flight; GLES uploads/draws stay on renderer.
debug.opem.workers=1..4 overrides at scene opening; empty/0 selects auto. Counts are selected at scene opening; no live thermal resizing or general animation/visibility job scheduler is claimed.
Windows real process-affinity tests pass with1/2/4CPUs. Windows forced1reader and auto4readers settle to identical1910draws/764902triangles/404textures/queue0. Tablet detects8availableCPUs and starts3readers.

## Verification and preservation
Windows and ARM64 builds pass; cache tests cover context reset/ID reuse, missing uniforms, table saturation and binding-state equivalence.
APK signer SHA256 c47ba7823090afa66297683d7be45c2df8d7c37e1443bcece168f5b915e9344f.
APK SHA256 11bc6c0c44900e28a7a8267416d58a377553f8df7f7a8938d1a564f7c5713b7b.
88-byte save SHA13734501b6cdbd25fbe8fa8202226ea084382755d2522ee46d0b985045e85f11 unchanged.
184-byte settings SHA27665629f70cf1902ed4e5bec8daadcd6cdb5dfef857dfd3a0430ab475af0c55 unchanged.
Test properties restored, stay-awake restored0, own app stopped and tablet put to sleep.
Original game/saves/DB/key not changed; prior v0.37 artifacts remain.
Source snapshot and build receipts retain exactly this tested batch before opening-room changes.
