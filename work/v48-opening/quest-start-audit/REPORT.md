# MQ01 startup and native stage semantics

Source-only targeted audit. No game/UI/native execution, no current user-state reads or edits, no core/source/save changes. Exact recovered function bodies, original stage definitions, cached native excerpts and bounded read-only disassembly are staged here.

## Normal new-game startup producer recovered

MQ01's callback is named cheat_start_quest, but the source normal new-game/creator path explicitly uses it. Its name alone was insufficient to classify it as cheat-only.

1. main_menu asset13493 root sets m_gamestart_quest=QUEST_ID("MQ01") (asset613083).
2. Its start_new_game function0/37, standalone rawSHA661b3f507fab09e74af81e0f3e75f0848b8fba158e626c8c73ae61dad3955305, takes the win32 platform585298 branch to start_game_at_quest(m_gamestart_quest).
3. start_game_at_quest0/12 resolves QUEST.get_quest_script_module, checks m_CHEAT_START_SPACE and cheat_start_quest, then calls enter_space(module.m_CHEAT_START_SPACE,module.cheat_start_quest).
4. enter_space0/1 passes both arguments unchanged to loading_screen.create_loading_screen(space,callback). Its ship-build branch does this directly; the debug-space selection route also passes the same callback after matching the selected source space.
5. loading_screen asset13488, standaloneSHA4dcd7f6a290a0f1aec308554d0252947b3359a56ea544118a1486ca82e10282f: create_loading_screen0/0 forwards to init0/3. DEFAULT-mode init validates type(callback)=="function" and stores it as m_cheat_func.
6. character_gen_manager asset417426, rawSHAd1963a864dd8246f799032b3b843a271a5d20b08fc8223ab54f3bd4d0f55ff32, finish_character_gen0/17 waits for loading to finish and m_ready_for_finish. Then PC54..66 reads and invokes loading_screen.m_cheat_func().
7. MQ01 script asset613082, rawSHA4f615429c46748631f2f525649e1450c4174e012deade93c11f60f5ff59758c4, cheat_start_quest0/0 performs, in order:
   QUEST.start_quest(QUEST_ID("MQ01"));
   QUEST.set_stage(QUEST_ID("MQ01"),5);
   set_game_start(true);
   Passive.set_disable_aggressive_mode(true);
   destiny_manager.lock_destiny();
   destiny_manager.lock_fateweaver().

MQ01 root m_CHEAT_START_SPACE is SPACE_ID("DGN_WellofSouls_1"), source first-room SPACE1417252. The init is associated with successful source creator finish. It is not a constructor default, arbitrary movement event or automatic response to cinematic skipped. No present dev-profile gameplay state is inferred.

The retained older packed main_menu and loading_screen variants preserve the same quest/callback handoff. Their menu platform guard uses old enum3; it is NOT identical to the standalone guard. The standalone matches current native WINDOW.get_platform:00b513e0 ->0103a510 returns10 ->0103a5f0 gives"win32" ->hash585298. Both variants are preserved distinctly; runtime source-selection equivalence is not claimed.

## Default/start/get/set contract

| Situation | Native result |
|---|---|
| Quest reference absent/invalid or unavailable to nonblocking lookup | get_stage returns bitsffffffff, signed native integer-1 |
| Loaded source-constructed quest, not started | current index-1; get_stage=-1 |
| set_stage(25) on that unstarted quest | no change, no activation/start |
| successful start_quest | current index0; get_stage=0, runtime-synthesized stageID0 |
| source creator-finish then explicit set_stage5 | valid stage5, current index1 |
| active MQ01 then set_stage25 | no change:25 is not a defined stage |

Exact native evidence:
- Quest constructor00ff1f00 (named BHG_Asset__xtor_6 in export) initializes +0x78 current-stage index toffffffff.
- Quest loader00ff1b00 allocates authoredStageCount+1, prepends runtime stageID0, then imports authored56B rows through00ff0350.
- QUEST.get_stage binding00e65610 ->00faeea0: validates reference>1, calls asset lookup with mode0, verifies index0<=index<count, returns that runtime row's stageID@+0x24. All other paths returnffffffff.
- LuaParameter ctor00aa18e0 stores that value with type6;00aadd20 writes the bits to native VM integer tag3. The-1 sentinel is a native int32 value, not a fabricated fallback20/0.
- QUEST.set_stage00e65a60 ->00ff0310 obtains/loads asset with mode1, then00fefe00. That function FIRST requires currentIndex>=0. It searches exact stageID and returns unchanged for missingID or currentID. It does not start an unstarted quest.
- QUEST.start_quest00e68ea0 ->00e65320 ->00fda620. On success the latter invokes00fd9a00(true) with the QUEST object as ECX. Bounded existing-EXE disassembly at00fda752..75d confirms mov ecx,ebx; call00fd9a00, avoiding an ambiguous decompiler implicit-this argument.00fd9a00 writes currentIndex0.

Constructor-1 is NOT evidence of initial gameplay state. Stage0 exists immediately after a successful start operation, but the recovered normal source immediately requests5 afterward. The documented first-room new-game stage is therefore5 only after the successful source creator-finish init sequence, with all mandatory effects implemented/acknowledged.

## Stage25 is not MQ01 progress

Both exact retained source versions:
- initial_0.pak:63942B
- patch_0.pak:90431B

have the same12authored stageIDs:
[5,10,20,30,40,45,50,60,65,80,90,100].

Stage25 is absent. Source Sword.open_initial_door still requests set_stage25 when current stage<=20, but native exact-ID lookup ignores it. The ACTOR.open_gateway effect is independent. Do not change the service to create25 or claim door opening advanced MQ01. The earlier source-bridge fixture's simulated host accepting25 was explicitly a mock; it must not be reused as native stage-semantic evidence.

MQ01.on_start_stage_5 is source function0/57 with a single RETURN. That callback has no Lua effects. Native manager transition/condition/event/UI effects generally exist; a complete quest-manager emulator is not supplied here.

## Integration boundary

A truthful SourceQuest service may distinguish "known source instance constructed but unstarted" from "host has no supported quest service": the former returns-1, the latter remains unavailable under the port's explicit capability policy. A source-correct setter on unstarted or undefined25 is a known guarded native no-op, not blanket unknown-service success. Log that ignored request and preserve state.

Run the original init only at the authorized counterpart of new-game creator completion; preserve all required game-start/passive/destiny effects. Do not fire it on restore or every frame. start_quest can returnfalse for an existing active/completed entry, and the original Lua does not check that return before requesting5, so arbitrary replay could regress an existing quest. Normal source UI lifecycle and host once-per-generation persistence must prevent accidental startup replay.

This audit does not modify runtime integration or current saves. The current explicit cinematic-skipped development path does not itself prove creator completion occurred. Any new host startup hook must preserve that distinction and atomic effect validation.

## Receipts

source-start-contract.json: typed states, exact source chain and limits.
script-provenance.json and scripts/:13unchanged guarded source functions, compact instruction evidence and metadata.
quest-definition-provenance.json and source/: both original quest definitions, stage offsets and hashes.
native-provenance.json and native/:15cached function excerpts plus3bounded static assembly ranges.
validation.json:11source/native consistency checks PASS; no gameplay/native execution claimed.
seal_quest_start_evidence.py: reproducible read-only evidence collection, writes only this audit folder.
