# Latest live scope, 2026-11-06 21:17 UTC

The editor remains DRAFT only. It now includes rotatable default male Almain/Varani BASE MODEL previews, using the existing character renderer and an explicitly neutral inspection light. The two SHA-pinned corrected packs are staged under creator-preview/. Selected skin/hair/eye/makeup colours are NOT applied. Unsupported meshes/female/elf selections hide the preview; no mismatched fixed body is shown. See live-varani-base-preview-fixed.png, live-almain-base-preview-fixed.png, live-almain-base-preview-rotated.png and live-unsupported-female-preview-hidden.png. Source Varani normal/palette audit is sealed separately.

The ROOM player now uses recovered CharacterHardLight for four approved Almain clothing parts1/2/3/5, exact D/N/S maps, native weighted P/N/T and entity-only B, and the separate source CharacterAmbientMap1. It uses current113-point light grid/sun/AO/fog. Skin/head/hair stay on the previous path. Depth/shadow geometry uses the same native source P as the new colour path, so the slightly different old fourth-weight conversion cannot self-occlude. Actual live A/B: rendered mask46, no HardLight draw failures, exact feet/camera/MVP/frozen idle pose. Source clothing-instance pixel equivalence and full native lighting parity are NOT claimed. debug.opem.charhardlight=0 selects the previous path (profile mode polls it); default1 enables this source-supported subset. New module assets are isolated, source files untouched.

Shared room shader sampler cube/LUT/shadow units are now initialized at creation even in neutral mode; this fixes the initially blank model preview. The separate existing first-frame profiler GL0x502 still occurs, so no global GL-error resolution is claimed. A separate explicit character asset manager fixes the profile path: its unrelated FX manager is intentionally unset when shop/outdoor bootstrap is bypassed.

Character playback now uses accepted horizontal displacement rather than requested stick speed when collision blocks movement. Facing still follows the request. This is an AUTHORED HOST improvement, not native MotionTree timing. debug.opem.motioninput=1 STARTUP restores the prior requested-input comparison policy. At the same blocked bridge edge, held-W old/new endpoints differed0.8695cm; both grounded,0recoveries. New policy logged requested1/accepted0 and stood idle instead of running in place. Tests ran in two fresh isolated user-data directories. Original movement checkpoint/draft/settings/inventory/properties were hash-preserved; launcher restored exactly.

All temporary pose/renderer properties are restored. Ordinary live preview uses BASE lighting, source clothing subset enabled and normal motion. Existing saved draft remains Varani/Male/Stigandr DRAFT, transaction0; it does NOT change the in-world fixed Almain or grant skills/buffs/startMQ01. No new APK/tablet changes.

Latest both-target build: integration/build-receipts/20261106T211151.104110Z, Windows0 and ARM640, stable inputs. Other staged gameplay host is NOT live (1388CPU checks+45typed corruptions); it still requires actual object/UI/weapon/door admission. Skin palette producer audit is ongoing separately. Earlier notes below describe prior staging milestones and are retained for history.

# Live creator draft UI, 2026-11-06

Authoritative files remain on Windows. This uses the existing Veil oa_ui/oa_menu widgets, fonts, colours and touch/controller/keyboard routing; there is no legacy original-game WINDOW UI framework.

## Live scope
In the isolated first-room preview, pause/title now offer Character Draft. Identity, Features, Colours, Details and Review pages operate the source-backed creation catalogue. Race/body/preset/patron/name, six cosmetic asset slots, eight palette indices and four opacity values can be edited. Invalid source presets are skipped rather than clamped. The existing name screen offers an on-screen keyboard for touch/controller and physical ASCII typing/backspace on Windows. The source state accepts UTF-8 but current UI font/input is ASCII; full international text input is not implemented.

Save Draft writes only wellofsouls.creator-draft-v1.bin using the existing OACREA1 source-catalogue envelope. Windows uses exclusive temp creation, FlushFileBuffers and MoveFileEx replacement. POSIX uses exclusive temp creation, fsync and rename. Invalid/unreadable existing drafts block replacement; missing drafts start defaults. No finalize/acknowledge/stat/buff/quest-start call is made. The displayed appearance preview explicitly says unavailable, and saving does not start a new game.

This is a USABLE DRAFT EDITOR, NOT completed character creation or cosmetics rendering. The running player remains the fixed Almain preview, and choosing another type does not change it. The creator screen hides the unrelated preview rather than presenting it as the selected character. Actual runtime appearance, skill/buff services and the source post-creator startup callback remain required.

## Validation so far
- Standalone actual C menu/input/state/file integration:14,460 checks,0 failures, including existing115 menu checks, keyboard/controller/touch events, all source option membership/duplicates, valid save/reload, pending-profile save rejection, corrupt load preservation and failed save preservation.
- Windows renderer and Android ARM64 shared library both compiled successfully, inputs stable: integration/final-renderer-build.json, build-receipts/20261106T204143.973510Z.
- Live Windows screenshots show all5 pages and changing Almain to Varani, source default-name update, and actual Save Draft.
- Independent decoder verified live105B draft d03eacaa02d268f2fa7a194606ce7c7a0a756341e33632ddfaf0c69fd0374932:Varani/Male,Stigandr,phaseDRAFT,transaction0,catalogueCRC0xa08d9075.
- Actual process restart and reopening Character Draft restored Varani/Male/Stigandr with Saved draft status. Draft hash stayed identical. Existing movement checkpoint, legacy save/settings/inventory existence+hashes and properties were unchanged: VALIDATION.json.
- No new APK or tablet runtime validation. Tablet remains v0.38/code40.

## Other current live/evidence deltas
The source ordinary CloseIdle container state is now proven to hold clip1789841 at time0. Seventeen supported rigid parts are added to a separate BASE-lighting asset root, probe-preview-closed-container. The live launcher uses it. This is static visual geometry, NOT an interactive/full animated door: remapped skin/sword portions, native opening state changes and collision/picking are not admitted.

CharacterHardLight root factory is now compiled and its independent ANGLE GPU fixture passes; current scene characters still use the old diffuse path. Native shared white COLOR1 and weighted VS375 basis rules are sealed in sibling audits. VS375 skins P/N/T but B gets entity-only transform; do not skin all three basis vectors or double-apply facing. A weighted four-clothing adapter is being staged independently.

Source MQ01 stage25 is undefined/no-op; full cursor proof under quest-start-audit. The staged gameplay host has real C/Lua tests but is NOT live. Actor/UI capabilities must remain unavailable until root admits actual actor/UI implementations. Devskip remains a skip, never creator completion.

The accepted lighting default remains BASE; do not enable the blue Start candidate by inference alone.

## Bounded skin-colour proof sealed (not implemented live)
../skin-colour-contract-audit/REPORT.md and equation-contract.json now close PLAYER.set_skin_color record mapping: word1 RGB with PREVIOUS character alpha preserved, word3 head diffuse/word4 body diffuse; instance block skinColor@32. Native multiplier is the exact promoted float32 reciprocal0.0039215688593685626983642578125, not mathematical double1/255; no tint gamma conversion. Root independently checked setter0102b250 and converter00b37520 excerpts against the staged reference equation. Captured body diffuse view is linear BC1 UNORM. Actual skin shader is alpha-test, mask GREEN at UV0, strict < native cutoff232 converted by that scale; VS461 matches proven weighted VS375.
Integration remains gated on fresh creator alpha initialization (StatsBlueprint payload+0x10 is unclosed), complete source mesh/texture/capture identity, and head/makeup/hair bindings. All9 recorded skin alphas were1 but this is not proof of a fresh creator default. Do not use the older opaque skin helper as the full skin material or take palette alphaFF as character alpha. Bounded investigation is finished; no further worker remains running and no skin shader/UI data was changed.
