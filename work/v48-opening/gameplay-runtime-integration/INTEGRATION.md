# Staged first-room gameplay host

This is an independently tested CPU host, not integrated gameplay or proof of live
actor/UI/GPU/Android behavior. The standalone backend is explicitly a recorded
two-phase actor/UI fixture. No core, preview, user save, settings, source assets
or guarded Lua body was changed.

## Build and entry points

Compile oa_opening_gameplay.c plus ../quest-runtime-integration/oa_mq01_cursor.c,
and link the existing oa_opening_runtime target, which links the actual
work/v08-portable amalur_runtime C library and Lua5.1.5. CMakeLists.txt and
build-test.cmd are standalone staging targets. No Lupa or substitute interpreter.

oa_gameplay_create consumes the unchanged existing sixteen hash-pinned assets
through the same size/read callbacks as oa_opening_runtime. Paths/hashes are in
../runtime-integration/asset-integrity.json. Include movement_sha256.h and the
unchanged opening_movement_planes.h from this staging directory.

Required creation inputs: caller scene generation, explicit nonzero stable host
instance for SIMTYPE1360571, its real item index, dedicated checkpoint path,
failure reporter, and tutorial option (0/1 or -1 unavailable). Generation and item
identity must remain stable for this checkpoint lifetime; change the namespace
for another game/lifetime. This one profile is SPACE1417252/REGION1262814 only.

The real source object is GOR1790948 / authored instance1789992, with exactly
one item1360571. Fixture item index7 and instance0x123456789a are test mappings,
not claimed native object handles. The caller must map these to actual source
actors/inventory and authorize reach/visibility before calling take.

Public flow:
1. Create or migrate, then accept the real controller feet pose through
   oa_gameplay_update_pose. First containment only initializes; it emits no exit.
2. Explicit dev skipped-cinematic path: oa_gameplay_cinematic_skipped.
   It sets only the bridge's cinematic guard. It is NOT character creator finish.
3. oa_gameplay_update_pose performs source feet inside->outside tests for exactly
   WoS_Start_Room, Tutorial_Volume_Move and Tutorial_Volume_Move2. Exact six planes
   per volume are copied byte-identically from the sealed source-plane helper.
4. oa_gameplay_take_source_item requires exact GOR, container instance, stable
   item instance and generation. It removes the one authored container item into
   the C inventory candidate and invokes unchanged guarded source on_item_acquired.
5. oa_gameplay_equip_source_item requires that same owned instance/generation.
   It invokes source on_equip_item; no generic iron-sword event is exposed.
6. oa_gameplay_advance advances game time, not wall time. The source schedules
   its two 15ms callbacks. Individual steps are capped at1000ms as a host budget
   policy. The existing bridge schedules any replacement poll relative to the
   current advanced clock; native timer-manager catch-up semantics are not proven.
7. oa_gameplay_snapshot gives typed read-only C inventory, equipment, tutorial
   registry, secondary/compare flags, logical door, source Lua guards and timers.
   Use existing oa_ui/oa_menu for rendering and requests. No WINDOW UI exists here.
8. Save/Load through the separate gameplay checkpoint API below.

## Actor/UI admission and atomicity

Capabilities default to0. Required capabilities must also pass backend.available
at use time. Queries/actions report unavailable and latch on a failed source
transaction. A mask alone is insufficient. Root must supply real actor/item,
equipped rendering, door/collision and existing UI services before enabling them.

Backend.prepare receives a complete before/after state, operation, stable source
mapping and all borrowed source effects. It must validate and reserve EVERYTHING,
applying nothing. On failure it releases its own partial reservation. Successful
prepare returns an opaque token. Backend.abort releases it if later disk work
fails. Backend.commit is void, bounded and infallible: publish prevalidated state
or an already reserved actor/UI command queue. Never do allocation, fallible
storage/GL work, reentry or Lua calls there. No backend callback may retain
borrowed batch/state/effect pointers. The host owns all requests for this profile;
do not independently change its actor inventory/door without a future explicit
synchronization contract.

The host accumulates every effect for the complete public operation. Multiple
source volume callbacks in one movement update share one transaction. Lua may
mutate privately while the host is busy, but visible C/backend/file changes happen
only after the full candidate passes type/coherence/capability validation. The
source runtime and outer host both preserve/rebuild the previous Lua snapshot on
failure, including successful no-effect callbacks such as equip. If rebuilding
fails, poisoned status blocks further execution; recreate the host.

The atomic file rename, if requested by the original autosave effect, is the last
fallible operation. Only infallible backend commit and struct assignment follow.
The real Windows writer uses exclusive same-directory temporary creation, full
WriteFile, FlushFileBuffers and MoveFileExW(REPLACE_EXISTING|WRITE_THROUGH). Bad or
incompatible existing gameplay files are preserved. No directory is created by
the host. Windows app-data directory ownership remains with the caller.

Failed source operations report once, latch, and do not run Lua again each frame.
oa_gameplay_clear_failure only acknowledges the failure; it does not replay it.
Accepted containment is preserved: a subsequent deliberate movement update can
retry the crossing. The caller chooses any retry after fixing availability.

## MQ01 semantics

Only quest613083 is supported and explicitly constructed unstarted: stage/index-1.
oa_gameplay_quest_stage distinguishes this truthful -1 from unsupported quests.
The source open_initial_door stage25 request is validated against the real cursor
as NO_CHANGE/UNSTARTED and increments quest_noops. It never creates progress25.
No quest start API, creator-finish5, startup effects, active stage effects or full
QuestMgr is implemented. Other stage/effect requests fail.

Source evidence: ../quest-start-audit/REPORT.md:
constructor00ff1f00, absent/unstarted query00e65610->00faeea0,
set00e65a60->00ff0310->00fefe00 requires a started index, missing25 is also a no-op.
Normal startup is MainMenu13493 -> character_gen_manager417426.finish_character_gen
-> MQ01script613082.cheat_start_quest, distinct from this explicit dev skip.

## Registry and exact guarded subset

The five registry IDs are17524338,26339831,40879367,61835887,49968583.
The first three are movement/room kill targets. The sword queries fired61835887
and may launch modal49968583. They are preserved as distinct IDs; no invented
alias. Modal launch records49968583 active/fired. oa_gameplay_tutorial_set is only
for caller-reported actual registry/UI state, not a fake modal acknowledgement.

The exact unchanged eight reconstructed guarded functions remain manifest-pinned:
WoS_Start_Room {on_player_moved0/5,on_leave_starting_room0/4,on_volume_exit0/11};
Sword_WoS_InitialWeapon {on_item_acquired0/0,launch_equip_tutorial0/1,
on_equip_item0/2,check_open_initial_door0/3,open_initial_door0/4}.
These are byte-preserved guarded reconstructions of shipped compiled functions,
not newly invented quest code and not a claim of running the original native VM.
Each runtime operation runs through the production C memory/instruction limiter.
The stable player identity is a generation-qualified string in the admitted
primitive comparison domain, not guessed userdata equality.

## One-realm migration

oa_gameplay_migrate_movement takes supplied scene/generation, accepted pose, typed
Lua snapshot and exactly the three old movement registry rows. It accepts only a
fresh gameplay host and movement-only state (no sword flags, sword_get or timers),
validates the whole schema and optional current collision, then restores the one
new gameplay realm and its registry. On success the caller MUST retire the old
movement runtime and route future volume/timer/save events solely to this host.
On failure keep using the old host; no automatic ownership handover occurs.
The migration API does not read or rewrite an old movement file.

## Separate portable checkpoint

Only *.opening-gameplay-v1.bin is accepted. No88/92B legacy save, movement
checkpoint, settings, arbitrary quest/inventory progress or original userdata
format is accepted or modified.

Header48B: magic8 "OAGPCP1\0", LEu32version1, LEu32payloadBytes,
SHA256(payload)32. Payload uses field-wise LEu32/64 and IEEEbinary32; no C struct
padding/pointers are serialized. It pins the sealed volume and runtime profiles,
a gameplay schema SHA256, scene/region/generation, exact source item/container
mapping, item index/instance, supported quest and fixed unstarted stage, explicit
tutorial option and generated player identity. It then stores accepted pose,
containment, cinematic skip, inventory/equipment/door/UI states, revision/no-op
log, five typed tutorial rows, all supported Lua fields and authored timers.
Full offsets/independently decoded examples: checkpoint-byte-validation.json.

The bounded host schema accepts only state producible by this eight-function
subset: fixed unused/default Lua fields, coherent item/guard flags and at most
two timers. Each timer must use its original hash/argument domain, unique valid
serial and a future due time within the authored15ms interval. Max file8192B,
max Lua integer9007194959773695. A SHA256 checksum detects corruption, not malicious
tamper-proofing or authentication.

oa_gameplay_save_checkpoint stores current accepted state; it rejects uninitialized,
latched or poisoned hosts. Source movement autosave uses the same writer.
oa_gameplay_load_checkpoint first checks the entire byte/schema/profile candidate,
then calls optional validate_load_pose BEFORE Lua, registry or actor mutation.
Root should validate by staging opem_controller_spawn in a temporary controller.
Never mutate the live controller inside validation. Publish that temporary
controller only after load succeeds; discard it otherwise. External actor/UI
restoration must additionally pass backend.prepare before state commit.

## Evidence and remaining limits

gameplay-test.log: Windows actual production C/Lua fixture PASS1388checks.
checkpoint-mutation-test.log and checkpoint-byte-validation.json: three independently
decoded files,45checksum-valid typed/profile mutations rejected; every truncation
also rejected by the C test. Real private files only, fresh test output directory.
arm64-c99-check.log: strict Android ARM64 C99 SYNTAX check only; no ARM link/run,
device install, GPU/interaction/UI test or live gameplay integration.

Required production work remains: actual source item/actor mapping and authorized
interaction, existing UI rendering/input, equipped sword attachment/animation,
door motion and collision, controller loop/time wiring, gameplay checkpoint UI
and lifecycle handover from movement host. None is faked here. General tutorial,
combat, inventory, quest-start and active quest-stage services remain unavailable.
Source capsule-vs-volume tolerance and full native timer producer are not claimed.
