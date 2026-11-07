# Current custom-engine work, 2026-11-06
Authoritative project remains this Windows folder. v47 performance milestone is COMPLETE; tablet remains signed v0.38/code40, not the new opening preview.
Read ../runtime-integration/INTEGRATION.txt, ../content-audit/README.md, ../material-audit/REPORT.md and ../lighting-selection-audit/REPORT.md for source evidence.

## Live Windows preview
Task OA_V48_FirstRoom runs start_preview.py. Own app/own user-data only.
DEFAULT RESTORED TO BASE per owner's feedback that blue looked worse. start_preview.py points to probe-preview (base), captures base-restored-first-room-auto.bmp.
Separate probe-preview-start preserves the authored blue start candidate. Do not silently re-enable it as default.
Static/native evidence now proves start lighting is a local contributor of weight1 at BOTH source spawn and current camera in ordinary mode. Native additional/hard override state and actual rendered-colour parity remain unknown. An unmatched web recording is not sufficient for quantitative colour validation.
Reference viewed: https://www.youtube.com/watch?v=NExi7gPfkEA&t=897s at14:57 and15:02, same opening room, different camera/unknown graphics settings.

## Implemented in live source, Windows verified
- Optional validated scene-profile reader: true first room SPACE1417252, REGION1262814; source spawn(4312,2806,-314), angle-180deg;113 source point lights, room cube/LUT/fog/sun, source post profile.
- Separate asset roots, main outdoor assets unchanged. This is a WINDOWS isolated preview, not yet a multi-scene Android/NewGame integration.
- Source-supported static subsets:31materials,106 authored portable textures,51.7e4 stored triangles. Source scaled placements and other shader families remain explicitly excluded.
- Distinct family11 GlassMetalProbe: real wall/trim, source non-Fresnel arithmetic, material+environment tint, independent authored cubes1259503/505647. Runtime logs prove both GPU probes loaded. Source cube0 stalagmite remains excluded; no inherited previous probe.
- Fixed world sampler setup so a scene without family9 still sets reflection cube to unit14. First attempted scene was blank; before-sampler-fix evidence preserved. Corrected scene visibly renders.
- Scene/profile and probe-registry unit tests pass; Windows+ARM64 compile.
- Real first-room walk test:296.1cm forward, remains grounded, no recovery; source Tutorial_Volume_Move contains start and excludes end. Original Lua event is NOT yet connected live.
- Current Windows stats:224 main draws,255146 submitted triangles,100 resident2D textures, queue0, estimated167MB stream GPU memory (not all graphics allocations). Windows offscreen rates are NOT tablet performance.
- Known Windows profiler first-use GL0x502 persists; rendering/probe loads visibly work. No Android instance of new scene yet.

## Next integration already staged, not live
1. Actual production amalur_runtime C wrapper around8 recovered source functions:51 checks, source hashes, budget/OOM/host-rejection rollback. under ../runtime-integration/.
2. Real minimal movement-volume/checkpoint host currently being staged by water worker under ../movement-host/, explicitly unavailable quest/sword/door services. Root will review and connect.
3. Creator data/state runtime under ../../v49-character-create/runtime-integration/:8types/40presets,1379 checks, source palette/skill/patron data. No creator UI or complete cosmetic rendering live;5 unresolved presets reject safely.
4. Pure native lighting-volume weights helper being staged by foliage worker. No auto-selection/colour math or source override-state guesses.

No original game UI/Steam/save/key/analysis database changed. Tablet test save/settings hashes were preserved and properties/stay-awake restored, app stopped, tablet sleeping. No Astra/model changes or new installations.
