First-room opening bridge — integration contract

Stage: work/v48-opening/script-audit. No live/core/menu/save files changed.

Runnable entry points
Load opening_state_accessors.lua and opening_bridge.lua as trusted Lua5.1 chunks returning tables. Compile the EIGHT fresh recovered function chunks listed in opening-function-manifest.json into a plain name→function table; verify each generated-function SHA and original-input SHA. These functions are guarded reconstructions, not original plaintext or a native-runtime equivalence claim. Do not share the function objects between bridges because the bridge assigns their environments.

Create:
  local opening = bridge.new(functions, services, {accessors=accessors})
Call methods with DOT, not colon:
  opening.set_cinematic_finished(boolean)
  opening.volume_exit(volumeName, enteringObjectIdentity)
  opening.sword_acquired(itemIndex, recipientIdentity, originalArg3)
  opening.sword_equipped(itemIndex)
  opening.advance(deltaGameMilliseconds)
  opening.snapshot()
  opening.restore(snapshot)
All event/update calls return true, effects on success, or false, diagnostic on rejection. The first-room bridge does not run the full cinematic; deliver completion only after an actual completed or explicitly skipped cinematic.

Host services, all mandatory
player_identity() returns an engine-registry identity STRING including scene/slot/generation. This is an authored transport that fits the recovered primitive equality domain; native object userdata equality is unproven here. Reject expired source objects before invoking the bridge.
resolve_gor("MQ01_Start_Door_01") resolves source GOR1790948.
resolve_quest("MQ01") resolves source quest613083.
is_equipped(itemIndex), is_gateway_open(gor), tutorials_enabled(), has_tutorial_fired(hash), is_tutorial_active(hash) return actual booleans.
get_quest_stage(quest) returns an actually known int32; nil/unknown fails.
warn(message) records diagnostics.
apply_effects(batch, candidateSnapshot, sourceCallbackName) returns EXACT true only after implementing the complete batch; otherwise false, reason WITHOUT applying any batch command. Validate/prepare every effect before committing. The candidate snapshot allows checkpoint saving without reentering the bridge during its transaction.

Effect names are ACTOR.open_gateway, QUEST.set_stage, tutorial_win.kill_tutorial, tutorial_win.launch_modal_tutorial, tutorial_win.disable_secondary_weapon, loot_popup.enable_compare, interfaceLibrary.autosave_request. Each row has {name, args={n=..., ...}} preserving argument count. These are requests, not successful no-ops. The autosave request preserves the outer original interfaceLibrary call; the host must apply its real autosave capability/profile policy and persistence. Door opening must update its actual collision/render state. Inventory callbacks must occur AFTER actual source item acquisition/equipping; initial sword is SIMTYPE1360571, not an arbitrary generic longsword. No items are granted by this bridge.

Proven route
cinematic_post_char_gen_2 asset1411319 sets post-cinematic location(4312,2806,-314), angle-180. Geometry agent independently matched only SPACE1417252/REGION1262814, floor-314.79069.
WoS_Start_Room asset1374929 routes EXIT of Tutorial_Volume_Move or Move2 to on_player_moved. Both are source convex volumes, not a guessed movement threshold. With cinematic_finished=true and player_has_moved=false, it sets that flag, kills17524338/26339831, requests autosave(0), once.
Sword_WoS_InitialWeapon asset1360572: player acquisition while not equipped and acquired_once=false sets source guards/looted/MQ01.sword_get and secondary-weapon lock; schedules equip prompt151774118 and door poll165407883, both delay15. Original equip callback sets equipped_once/player_has_equipped. Poll opens source GOR1790948 only when equipped_once OR tutorials disabled; if closed, requests compare-enable and stage25 only when current stage<=20. Later stages are not regressed.
Only these two delayed hashes are admitted, independently reproduced by the previously recovered native00af09a0 ASCII hash of their fully qualified names. Other hashes fail. The queue uses host-supplied paused-game milliseconds and current-frame rescheduling, deterministic due/serial ordering and explicit capacities. Native scheduler/pause/catch-up details are not claimed.

State and failure behavior
opening_state_accessors.lua preserves current_state/getters/setters/internal_module_state and source type-change warning/no-write behavior for this primitive subset, keeping the existing seeall metatable unchanged. Full native ModuleVariableStorage function-valued __index remains outside current VM admission.
Source state/timers are restored on original-callback or unacknowledged-effect failure, so late missing services do not strand once-only guards. External atomicity depends on the host batch contract. Callbacks cannot reenter this bridge.
Snapshots contain this bridge's source booleans, minimal MQ01.sword_get, clock and closed timer records. Restore validates before mutation. They are an AUTHORED port envelope, not a native save format. Couple them with the SAME inventory index mapping, quest stage, door state and scene identity; these are host-owned. Existing88/92B save prefix and184/188/192B settings remain unchanged. Do not claim full MQ01 persistence from this subset.

Verification
test_opening_bridge.py:46 checks,8 recovered bodies, full route plus duplicate/nonplayer/unknown-volume guards, negative host acknowledgements, retry, typed/corrupt snapshot, unknown stage, missing services.
run_original_opening_fixtures.py:95 original-body checks/14scenarios; --accessor-adapter repeats all95 with identical effects.
test_state_accessors.py:23 checks comparing original ModuleVariableStorage getter/setter bodies, unchanged metatable, typed rejection and atomic restore.
All run on existing Windows Python312+Lupa Lua5.1; no native game/input, installs, full-engine build or user-save writes.

Explicit limits
Normal quest startup/current initial stage is not recovered; bridge NEVER invents start_quest or stage5. Patched613083.quest_bxml differs from initial; condition/objective decoding and first enemy completion are outside this finalized first-room scope.
MQ01_StartRat703040 references nonexistent catalog GOR MQ01_Start_Door (without_01), so its stage20/death route is NOT an active-source witness.
229 tutorial descriptors are staged in tutorial-data-literals.json with raw localization pairs/input symbols/PC redirects; translated UI/audio are not supplied.
The full original dependency diagnostic is197 modules/68,651,904source bytes with unresolved entitlements variants; modules-candidate is NOT a deployable or boot-validated package.
