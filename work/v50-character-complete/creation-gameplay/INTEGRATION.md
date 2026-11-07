# Creator to active gameplay integration

This package is staged, not live-integrated. The standalone appearance publisher
is a CPU reservation fixture, not GPU/UI/Android validation.

## Build and assets

Compile oa_creation_gameplay.c, oa_creator_game.c, oa_mq01_cursor.c. Link the ROOT'S
CURRENT oa_creation.c +oa_creation_source_tables.c ONCE, existing oa_opening_runtime,
production amalur_runtime and Lua5.1.5. Current shared files are copied and pinned
in shared-core-snapshot.json. No Lupa/substitute runtime is used.

Include creation_{patron,global,item,skill}_tables.inc, creation_startup_assets.inc,
movement_sha256.h, opening_movement_planes.h and the supplied headers.

Keep existing16opening assets unchanged. Additional8paths/hashes are enumerated
in startup-asset-integrity.json: creation/{amalur_uint64.lua,
amalur_engine_handles.lua,engine_binding_registry.lua,amalur_engine_bindings.lua,
amalur_native_math.lua,mq01-cheat-start.lua,mq01-stage5.lua,stealth-condition.lua}.
Staged physical files are assets/<basename>. Route through supplied size/read
callbacks. Other source/proof files are NOT product assets.

## Mandatory root hooks

1. Config: actual scene generation, explicit stable source sword instance/index,
   separate *.creation-gameplay-v1.bin path, actual tutorial option, current HP and
   UNMODIFIED base maxHP, actual enabled package4 state, failure reporter and
   temporary-controller collision validator. Do not reuse already patron-buffed
   maxHP as the base. Source concrete final actor base maxHealth is50
   (PartTarget+4=50,+8progressionKey0; native00f76af0->00dfdfd0), before other real
   host modifiers. Package4 is actual engine activation0/1; -1 fails completion.
   Asset presence is not proof of original license ownership.
   The NATIVE shipped constructor explicitly defaults package3/4active (table
   01961040, entitlement sentinel-1). source_package_default() exposes these
   source defaults without claiming current user overrides. See
   source-content-package-table.json; source-normal package4=1 gives165items.
2. appearance.prepare(loading,active,renderSelection,token) must reserve ALL
   actual selected CPU/GPU appearance, final actor/race/gender/name/title, exact
   equipment/inventory and owner-state publication. Apply NOTHING. A failed
   prepare releases its partial reservations. commit(token) is void, infallible,
   bounded and non-reentrant; only publish reserved objects/queues. abort(token)
   releases after later disk failure. No allocation/fallible GL/storage in commit.
   Never retain borrowed pointers. loading=0 publishes initial source Fateless One
   title and its DestinyChange notification; loading=1 restores without replaying
   initial creator events. Platform telemetry/Steam rich-context/native FX
   execution are not silently acknowledged by this module.
3. After final actual creator/name confirmation, call complete(session,draft,
   uniqueTransaction,acceptedPose). Draft remains byte-identical on failure AND
   success. All candidates/source execution are private until one file commit.
   Existing valid active file returns ALREADY_ACTIVE; load it or start an
   explicitly new namespace. No unrelated old profile is overwritten.
4. On success retire old movement/dev opening realm, then drive the ONE borrowed
   oa_creation_gameplay_game() host through oa_creator_game motion/item/equip/time
   APIs. On failure retain old realm/controller/avatar. New Lua cinematic guard
   starts false. Actual post-cine completion calls cinematic_completed; explicit
   skip calls cinematic_skipped. Neither starts MQ01 or completes the creator.
   Source3convexvolumes and exact8guarded opening functions are reused.
5. Publish owner name/profile/race/sex/title/skills/vitals into actual menus,
   controller and combat services. Initial title is Fateless One buff385357 under
   identifier9325294; authored stat list EMPTY, so no hidden health adjustment.
   Realize exact source owner equipment, not generic substituted items.
6. Use health(delta) as clamped integer owner resource state and read it back for
   combat/UI; feed actual damage/heal deltas. stat(key,integerMode,actualBase)
   evaluates real patron/global source modifiers. Integer mode follows native
   signed truncation per op. Known source keys: Health1657941,Power981938,
   Critical3817837,exp_amount_multiplier25760551. Other original keys/float bits
   remain exact, without guessed English semantics.
7. action_allowed enforces actual destiny selection/fateweaver/aggressive MODE
   admission. Passive aggressive mode is NOT a general attack prohibition.
   Source locks stay enforced until a future supported unlock path.
8. Feed actual Stealth_Exiting, target visibility, and owner ReckoningMode624629
   membership to combat_gates. stat() enforces those conditions. actor_state(name)
   exposes exact45source skill states plus those two actual owner states. Sparse
   thresholds are preserved; unknown names/tiers are unavailable. buff(index0..3)
   exposes exact permanent IDs/identifiers/duration(-1), not merely UI labels.
9. Source item/door/UI calls require gameplay_backend real readiness and
   prepare/commit/abort. Exact initial containerGOR1790948/instance1789992 has one
   source sword1360571. No generic iron-sword event. Game-time step1000ms cap is
   explicit port budgeting, not a claim of native timer-manager catch-up parity.
10. Pause Save/Resume use OUTER save/load. Inner source autosaves use this SAME
    combined profile/gameplay envelope; inner load rejects outer storage.
    Collision validation stages a temporary controller and publishes it only
    after success; discard it otherwise. No old movement autosave remains active.

## Implemented source effects

All24allowed race/patron pairs and both sexes (48cases) use source raw racial
skills,10units/rank, and13unique authored patron buffs. None is real buff1697849.
The45source named skill states use exact sparse thresholds (Alchemy1/3/5/10,
not an invented tier2). Initial raw ranks are real authoritative owner values.

Source common grants: bags749605/749606/749604/749607/749608; arrows615585count5;
TattersTorso1321542slot0,TattersLegs1321543slot0,Unarmed_0 type1330206slot0,
Unarmed_1 type1330207slot1,NoShield1381439slot0. All4final root native inventory
blueprints are initially empty. get_default_chargen_equipment returns EMPTY table;
do not invent temporary clothing destruction. Base owner table162actual common/
hidden/recipe rows includes13Hidden-pocket potions. Package4 adds ONLY recipes
2105162/2105163/2105164. No placeholders, random grants or inferred ownership.
This is concrete bounded owner inventory, not a full item-use/crafting engine.

Permanent buff instances: selected patron(tag1731073),FatelessOne385357(tag9325294),
Stealth_GlobalCritBonus1621687(tag35299876),All_reckoning633989(tag11334545).
Native records12B{key,op,floatBits}: op1multiply/op3add. All13patron conditions
are opcode0 TRUE. Stealth Critical+1 applies only while Stealth_Exiting(owner)
and NOT target.can_see_player. Its unchanged source Lua runs in the production
C/Lua truth-table fixture. Reckoning compact opcode32/id624629/polarity1 goes
through actual native actor-state membership (00dcd6f0->00f0df30); default inactive.

MQ01 cursor constructs unstarted(-1), then UNCHANGED guarded source
MQ01.cheat_start_quest executes under production C/Lua budgets:
start0 -> set5 -> gameStarted -> Passive mode disabled -> destiny/fateweaver locks.
Exact source stage5 RETURN callback executes too. No creator completion is wired
to cinematic skip. Subsequent sword set25 remains native NO_CHANGE at stage5.
Other quest transitions/full native QuestMgr are unavailable.

## Persistence / scope

One field-wise little-endian OACGCP1 envelope contains committed active appearance,
authoritative skills/buffs/vitals/title/locks/inventory, source quest5 and complete
nested guarded opening state (pose,registries,guards,timers). SHA256 framing,
source/schema hashes,catalogueCRC,scene/generation/item mapping reject unrelated
progress. Max32KiB. No pointers/raw C structs. Same-directory exclusive temporary
file,full WriteFile,FlushFileBuffers,MoveFileExW(REPLACE_EXISTING|WRITE_THROUGH) is
the logical commit. Only infallible publication follows. Invalid prior files are
preserved. Old drafts/checkpoints/88/92B saves/settings/source assets are untouched.

This port transaction intentionally makes source effects atomic after confirmation;
it does not claim original native creator ordering/save format. Full original
creator window/cinematic/render/telemetry bodies are not executed. Required bounded
owner effects plus original startup callback ARE implemented. Root must still
wire actual actor/GPU/UI/controller/combat and verify live Windows/Android before
claiming integrated completion. Original native name sanitization/counting parity
is not newly claimed; current shared oa_creation host guards are preserved.

Proof: source-runtime-contract.json,source-patrons.json,source-startup-items.json,
source-skill-states.json,source-stat-blueprint-colors.json,shared-core-snapshot.json,
startup-asset-integrity.json. Live product source/asset roots were never edited.
