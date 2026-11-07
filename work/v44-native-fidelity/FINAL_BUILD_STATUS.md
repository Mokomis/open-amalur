# Current continuation: v44 / Android v0.35 R4, 2026-11-05

Custom native engine remains active in work/v19-host, Windows host work/v40-windows-host. Read work/v44-native-fidelity/README.md, PERFORMANCE.md and CODEX_EVIDENCE_REVIEW.json first. Older notes below are preserved history.

Installed: outputs/scene-v44-r4/open-amalur-v0.35-r4-arm64.apk, version0.35.0/code37, existing package/key. Installed APK SHA a07cdf8bcae3d68c79f43609c7854e2584a61422ad081cdc6a7991f417613e2d. Native water, foliage attributes/wind/independent alpha, source material culling, AO/3cascades/sky/bloom/DOF/LUT/filter and point/fog equations are integrated. Large dark tree-branch cards were source-alpha metadata bugs and are fixed. Windows matched original-camera and ordinary walking-camera images reviewed. Complete source/build checkpoint and receipts are in outputs/scene-v44-r4.

Tablet same-scene stationary samples, nativefeatures255 and shadows:100%2520x1680=35.73FPS;75%1890x1260=46.57FPS;50%1260x840=53.02FPS. Thermal0 at100%,2 at75/50; short samples, not sustained benchmarks. Scaling now resets physical buffer defaults across room transitions. At50% GPU13.89ms, submission/driver18.03ms: prioritize drawing/state/depth/shadow overhead before simulation threading. Full-resolution GPU26.37ms remains costly.

Save/settings hashes unchanged. Test spawn/heading/profile/shadow/scale restored; native255 retained, defaultscale100. App stopped. Windows preview closed and task restored to normal town mode. Keys, original saves/databases and all previous artifacts preserved; no GitHub push. Original-engine/FEX work remains paused. Do not run old prepare.py without reapplying overlays. Validation is captured Gorhart bridge Noon; unsupported legacy materials, other time/regions, originalLODs and full actor lighting remain broader parity work. Whole-game/exact pixel parity is not certified.

---

