# Open Amalur: foliage and three-band scene review

Updated 2026-11-06. Current delivered build: **custom engine v0.36 R3**, Android package version0.36.0/code38. Windows and ARM64 builds passed. Installed APK SHA256: `4a38d2a722519258be04d1a377b3adae24d1efe35bd56d87df4be1ac5582b7e9`. This is an incremental visual-fidelity update, with a remaining native visibility/LOD blocker.

## Original-image review

The original is the existing 1536x864 native bridge capture, frame50994, replayed from its preserved capture. The Windows comparison uses its exact camera projection/view. Player model, HUD, moving NPCs and particle time differ, so whole-image pixel parity is not claimed.

| Band | Findings and corrections | Remaining limit |
|---|---|---|
| Top, rows0-287 | Native foliage attributes expanded from18 to175cells. Correct radial normals, colors, tangent frames and authored leaf texture mips. Missing regional trees recovered from real Region FabInstanceCollections. Godray texture, dimensions and soft-depth shader recovered. | Extra distant South-space leaf still covers part of a sky opening. Native scene admission/LOD criteria remain unrecovered; a simple cutoff incorrectly removes valid native draws. Particle emitter animation inputs remain a qualified candidate. |
| Middle, rows288-575 | Restored bridge-side lamp and overturned cart from source actors. Recovered emissive and Fresnel material paths; cart now uses its native reflection probe. Mossy water root uses the correct366-triangle source mesh, direct source placement and native normal-frame equation. | No claim of complete scene or actor/gameplay parity. Some body textures retain platform residency limits. |
| Bottom, rows576-863 | Foreground rock corrected from50-triangle distant mesh to190-triangle near mesh. Its false dark shadow was traced to visible tree leaf cards being used in place of the authored alpha-masked tree shadow proxy. The supported source proxy cohort now renders through a separate caster-only stream. | First proxy cohort covers34unit-scale placements of one proven source tree family.22nonunit placements and other families preserve the existing fallback. |

[Top comparison](top-final.png) · [Middle comparison](middle-final.png) · [Bottom comparison](bottom-final.png)

## Evidence-backed shadow and moss improvement

Native caster72203 uses FAB343974 assembly9, material1744210, VS292/PS293. Its28vertices/14triangles are different from the scene assembly5 leaf cards. The exact native shadow-alpha texture has transparent holes at all eight relevant shadow-map texels. Our old leaf cards passed the cutoff there and falsely shaded the foreground. The corrected source proxy restores the expected sunlight, without increasing material brightness.

The live Windows switch `debug.opem.shadowproxy` reproduces this difference. Native and corrected rock shadow visibility both equal1. The two sampled final rock colors changed from(60,33,14) and(56,31,11) to(190,117,60) and(163,99,42); native is(196,126,63) and(170,107,46). Moss-root pixel112,530 is now(67,76,30), versus native(65,72,28). These are selected diagnostic samples, not a whole-image score.

The source shadow classification comes from authored shadow groups and material identity. No reference-frame object whitelist or blanket removal of tree shadows was used. Exact ownership removes1325scene-card triangles only from shadow fallback; visible geometry stays intact. All other fallback vertex bytes and triangle order are retained. GPU readiness is checked before suppressing old casters, including cross-cell dependencies. Main-camera early depth continues to use visible leaf cards.

Native Region recovery matched all97previously missing captured part draws. Count terminology:51regional translation anchors include58full part transforms; legitimate part rotations are preserved. Across the tree inventory there are106translation anchors and113full transforms. The restored source subset contains129flora,21rocks and5skyline placements, retaining exclusive authored LOD ranges. Region distance scale0.5 is an observed matching preset, with its native derivation still pending.

## Waterfall exception preserved

The existing custom waterfall appearance is an intentional owner-approved difference. The waterfall fragment branch is byte-identical to v0.35 R4, as are all four waterfall material rows,13texture payloads and the water-parameter asset. Neither waterfall geometry nor its material/shader behavior was targeted. Global postprocessing and surrounding lighting can affect final animated pixels; no exact animated-pixel identity is claimed. See `waterfall-preference-preservation.json` on Windows.

## Android verification

Actual OPPO tablet99cc517a ran the new build, logging301material rows/42native profiles,175native leaf cells,200shadow registry cells,26Region replacement IDs,17readiness dependencies and real proxy GPU draws. Shaped soft native particles also rendered with a valid depth snapshot. A short joystick walk moved the target distance254m to248m. HOME/resume recreated the GLES surface, FX and proxy resources and rendered again in the same process. This is a short smoke test, not a long route or campaign test.

Short stationary samples at the same configured spawn/heading: full resolution2520x1680 produced32.0FPS, GPU27.76ms, thermal1; 50%linear resolution1260x840 produced47.3FPS, GPU13.68ms, thermal2. Startup and pause windows were excluded. These are different thermal windows and do not establish sustained performance or a strict improvement against the earlier build. A startup profiler GL0x502 message remains a diagnostic limitation; no new shader compilation/link failure or recurring steady rendering failure was observed.

Original save/settings SHA256 remain unchanged. Temporary position, heading, scaling, profiling and USB stay-awake settings were restored; app left stopped. Signing key was reused and never copied or replaced. The existing app was updated in place, never uninstalled. [Device receipt](android-validation/VALIDATION.json)

## Remaining blocker and exact next target

Pixel980,100 is occupied by current `l-3_-12.bin` triangle33, source leaf198, Space431642/FAB340232 assembly6, depth24=16762614. The native depth is clear. Its live alpha texture/mips match the capture; removing Region geometry leaves this mismatch unchanged. A proposed general range filter, even after exact geometry-alias unions and checking source bounds centers, preserves only31of33observed native Space leaf draws. It was withheld.

The next focused investigation must recover native scene/SPACE admission and exclusive LOD selection, then replace the cached selected-assembly assumption with the correct source producer. Absence of the raw pose from the current native draw inventory does not alone prove an active-Space cause. Six cached event/lifecycle bodies establish an exact manager handle-array seed at+0xb8/count+0xbc, but do not establish visibility or distance semantics. Do not repeat an arbitrary Euclidean cutoff or delete the offending tree by ID. A further bounded eight-function pass recovered a separate FabInstanceRender runtime-state propagation path, but no static collection selector. Its runtime flags and child handles cannot be evaluated for the33positive fixtures or source198 from the retained GPU capture. The next exact seed is loader00fec370 and registration00cd24e0/00cd2570, correlated to source198 and native-positive68811 through their identical static buffers and different poses. Continue toward the static admission consumer or a read-only CPU-state trace, rather than another actor virtual walk. [Focused native report](native-space-visibility/focused-render-selection/REPORT.md).

Other explicit limits:73unwitnessed scaled leaf transforms remain unchanged;22nonunit shadow poses remain withheld; source-classified shadow coverage is incremental; godray animation input/sign selection is not fully decoded. No whole-game or exact full-scene fidelity claim.

## Private recovery artifacts

Windows authoritative project remains `C:\Users\rwill\Documents\Opem Amalur`, outside Git. Signed build: `outputs/scene-v45-r3/open-amalur-v0.36-r3-arm64.apk`. Incremental recovery kit: `outputs/scene-v45-r3/restore-delta-v036-r3.zip`, SHA256a4407647dc83c54b9dcb496b73afab07a1cc5af4de8ea8fa502bf48f4bf2ea19, also verified on the Mac. It contains exact source/recipes, modified Android assets and ARM library, and requires the preserved v0.35 R4 baseline/dependencies. No signing key, credentials or original decompiler database is included. Build-time notes inside that immutable kit precede final device validation; this review and the device receipt supersede their status.

Relevant Windows evidence folders: `native-tree-shadow-proxies`, `image-band-audit/shadow-rock-audit`, `shadow-proxy-integration-review`, `instance-audit/tree-gap-producer`, `native-leaf-authored-ranges`, `native-space-visibility`, `final-band-review`. All experiments and rejected candidates remain preserved. A Windows text-encoding failure temporarily truncated the continuation ledger; its complete previous bytes were recovered from all four recorded successful writes, with encoding/newline simulation and a saved hash receipt. Source, assets, builds, saves and research results were unaffected.
