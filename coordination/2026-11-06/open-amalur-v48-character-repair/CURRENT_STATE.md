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
- Real first-room walk test:296.1cm forward, remains grounded, no recovery; source Tutorial_Volume_Move contains start and excludes end. This earlier controller-only test is superseded by the live Lua/checkpoint integration below.
- Current Windows stats:224 main draws,255146 submitted triangles,100 resident2D textures, queue0, estimated167MB stream GPU memory (not all graphics allocations). Windows offscreen rates are NOT tablet performance.
- Known Windows profiler first-use GL0x502 persists; rendering/probe loads visibly work. No Android instance of new scene yet.

## Additional staged systems
3. Creator data/state runtime under ../../v49-character-create/runtime-integration/:8types/40presets,1379 checks, source palette/skill/patron data. No creator UI or complete cosmetic rendering live;5 unresolved presets reject safely.
4. Pure native lighting-volume weights helper staged and tested (47 checks). No auto-selection/colour math or source override-state guesses.

No original game UI/Steam/save/key/analysis database changed. Tablet test save/settings hashes were preserved and properties/stay-awake restored, app stopped, tablet sleeping. No Astra/model changes or new installations.

## Live first-room script/checkpoint integration, 2026-11-06
The live v19 core now links oa_opening_runtime, oa_opening_movement and oa_opening_session against the existing production amalur_runtime/Lua5.1.5. Sixteen exact SHA-pinned source/bootstrap assets live under opening-runtime/ in each isolated preview root. Existing source files/backups remain intact.

Actual controller feet feed exact source convex planes. Dev preview explicitly sets debug.opem.skipintro=1; this is a skip, not recovered cinematic/creator playback. Start containment mask3 -> mask1 triggers original WoS_Start_Room movement callback. Final live 700ms walk ~296.5cm, grounded,0recoveries, two real registry kill counters1,1 and real source autosave. Typed Lua moved bit is present in independently decoded checkpoint. Standalone production runtime51, movement184 and existing menu115 checks pass.

Dedicated wellofsouls.opening-checkpoint-v1.bin uses source/profile hashes, exact pose, typed Lua state and registry; no old save/settings overwrite. Live menu Load restored the exact saved pose, grounded, without repeating tutorial effects; current-collision world+temporary controller validate before Lua/physical commit. Live menu Save and final source autosave both succeed. Menu labels explicitly say Save/Load Checkpoint. Availability is cached, not opened from disk each frame. Events latch and pause on failure without repeated Lua/file attempts.

Source-room startup bypasses unrelated shop/workbench boot. New Game restarts this room/session and preserves the existing checkpoint until an explicit save/autosave. Outdoor demo inventory/attack is disabled for the isolated opening prototype. No generic initial sword grant, fake quest stage or unspawned door success.

Final build receipts: final-renderer-build.json. Live evidence: movement-live-validation/VALIDATION.json, independent-live-checkpoint-decode.json, captures/logs and checkpoint copies.
The Windows and Android ARM64 renderer targets compile. No new APK packaged/installed and no new Android scene runtime proof.

## Owner UI requirement
EVERY interface must extend the project's existing new oa_ui/oa_menu styling and touch/controller input: character creation, tutorial prompts, inventory, pause/options and future screens. Source original-game choices/logic can drive this UI; do not introduce another or reproduce the original game's menu framework.

## Immediate next object work
Exact initial sword container GOR1790948 in source room is audited. initial-sword-visuals/ preserves raw models and a quarantined17-part rigid-bind candidate (1370tri);3 remapped container parts, active animation1789841 and source characterhardlight545212 remain contract work. No candidate object added live. Original source volumes/checkpoint are working independently.

## Character limbs/posture follow-through, 2026-11-06
Root integrated optional oa_character_attributes.c/.h, applying SHA-bound normal+palette companions to a temporary heap copy BEFORE oa_character_parse, then committing together. Original character.bin files stay byte-identical (ede399d687bcbbc9d1534a208e81a13b9b3785a6f2b52dc25b28f78f36a484a4). No weights, animation clip bytes, bind convention or user saves changed.

Normal defect: old heuristic importer chose TANGENT as NORMAL for2781/8144 appearance vertices. Recorded native input declarations + source stride/type correspondence provide correct N. All8144 corrected normals independently match source SNORM decoding; all bytes outside allowed normal fields/two palette prefixes remain identical.

Posture defect: shirt part5 used another assembly's palette; hip-pack part2 used the leg palette. Source-own palette prefixes now applied. Native31 weightedVS prove XYZ+reconstructed fourth; existing tiny negative-clamp difference is negligible in sampled limbs, so weight policy preserved. Actual productionC matrices show shirt changes up to28.725cm idle,29.116cm walk,25.642cm run,38.089cm turn. Hip association corrected but displacement negligible. Two absent shirt helper bones still follow existing SPINE2 ancestor policy, affecting6vertices at<=17.6%weight; full native auxiliary dynamics unproven.

Standalone actual repair C:22 checks pass, including failure atomicity. Independent full-byte/source decoder passes. Windows+ARM64 builds pass (final-renderer-build.json). Exact-camera/feet/MVP frozen-pose A/B for idle/walk/run/turn visibly reduces shirt distortion. Subsequent continuous forward run and side turn stayed grounded with0controller recoveries and no source-script failure. Source movement callback/checkpoint still ran successfully. See character-repair-validation/FINAL_STATUS.json and turn-before-after.png.

Capture aid debug.opem.charpose/charposems freezes a single authored clip ONLY when profiler enabled; default -1/disabled. Source repair default1, startup debug.opem.charrepair=0 restores prior heap data for comparison. All temporary comparison properties were restored byte-exactly; live preview uses normal motion and corrected source data. This is not proof of native motion-tree equivalence. The old code comment claiming turn clips have 'no net rotation' is too strong: current bounded source audit finds static_root no net turn, but BIP01/pelvis endpoint offsets and substantial transient rotations. No guessed blend change was made; follow-up evidence under v49 limb-skinning-audit.

## Additional native evidence sealed
- Initial sword authored parallel scalar1 is integer quantity ONE, not chance/weight. Native blueprint+0x0c/10 -> Inventory+98/9c ->00f8e400/00f8e0c0. Direct contents initialize via00f916f0; create_loot_objects processes a DIFFERENT pending queue. See initial-sword-audit/inventory-quantity-native/REPORT.md.
- Source-rest container transforms and remap T@0,Q@16,S@32,bone48 confirmed; active initial animation selector still unknown. Rest geometry remains quarantined; no generic native door success.
- Missing CharacterHardLight shader permutations recovered from previously skipped aPLib prefix flags; exact named platformID-to-bytecode registration remains qualified. See initial-sword-material-audit/.
- Native capture/source byte comparison proves separate CharacterAmbientMap. Opening BASE/Start char cube both BGRA a09e463bd738571bf4d19dfb19173ee4ef58972283ddf046ef59f0645ac41836; world cube both ec33749a7ff2170480dabcac78bb702c386b0174429451ef2d28e70820a91985 (already current). BASE and Start own separate Region/Space tables but payloads happen identical. No world-cube composition bug found. Source character cubes staged under v49-character-create/character-ambient-audit/, not integrated into current generic diffuse character lighting. BASE remains the default per owner; final native override/colour parity unproven.
- Creator state/catalogue1379 checks remain staged only, no usable creator screen yet. Every eventual screen must extend the EXISTING NEW oa_ui/oa_menu and input controls.
