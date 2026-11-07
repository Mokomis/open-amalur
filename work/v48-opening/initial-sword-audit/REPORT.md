# Initial tutorial sword — source acquisition path

The sword is an authored inventory item of the placed tutorial door/skeleton object, not a loose generic longsword at a guessed point.

| Link | Exact source |
|---|---|
| Global object reference |1790948,MQ01_Start_Door_01 |
| SPACE / instance / Type |1417252 /1789992 /1789987 |
| Position |(-1666.246582,2861.428711,40.572464)cm |
| Quaternion XYZW / scale |(0,0,0.718055785,0.695985615) / (1,1,1) |
| Container model |FAB1789717,wos_start_door01,PartRendering+0x14 |
| Container script |1794170,Door_Std_WOS_Start |
| Direct authored inventory entry |SIMTYPE1360571,Sword_WoS_InitialWeapon; parallel authored value1 |
| Item script |1360572,Sword_WoS_InitialWeapon |
| Item model references |FAB1880465,01_rusty_sword at PartRendering+0x18/+0x1c/+0x20 |

The GOR is copied here as mq01_start_door_01.gor_bxml. It records the actual container position. There is no source-backed free-sword drop position in this result, and none is invented.

## Acquisition behavior

Door_Std_WOS_Start.on_interact checks the InteractionLoot enum. The recovered source script routes the loot interaction through its tutorial/animation delay to loot_skeleton(actor,interactor,interactionType). That function calls ACTOR.set_allow_looting(actor), ACTOR.create_loot_objects(actor), then loot_summary.on_loot. The authored container's inventory list selects1360571. The item's own on_item_acquired/on_equip_item callbacks are the recovered Sword_WoS_InitialWeapon script, not generic weapon callbacks.

This is a static source route, not an observed original interaction or a completed port backend. The script drafts preserve raw bytecode provenance and their existing recovery limitations in script-evidence/. Actor handles, generation IDs, delayed callback state and original UI remain separate integration work.

## Compiled inventory proof

The earlier compact SimType representation was not guessed. Existing native-validated compiled134225858_ksmt.batch and native_type_catalog.py provide the original compiled Type carrier. Native batch readers00a969b0/00a996f0 and Type reader01001070 were already validated in v15; the corresponding original binary remains unchanged.

Type1789987's PartInventoryBlueprint(kind9) starts at member file0xb4. At+4/+8 it has pointer468/count1 to u32[1360571]. At+0xc/+0x10 it has pointer472/count1 to u32[1]. Native00f0cfc0 resolves the first array's resource keys;00ef2b60 confirms kind9.00f74790 copies the item references into instance+0x88 and the parallel values into instance+0x98.

The optional inventory resource at+0x2c is0. No nonzero external loot-table link was found for this entry; no random-table inference is needed. The exact semantic interpretation of parallel value1 as quantity was not independently traced, so it is retained as an authored value rather than renamed silently. The initial queue producer is the narrow remaining seed if that field's semantics are required.

ACTOR.create_loot_objects is native binding00e7cdf0, as recorded in the existing engine binding registry. It resolves PartInventory9 and requires the active-part bit plus00e37b70 actor permission before invoking00f97260.00f97260 consumes pending inventory queue entries at+0x6c,stride0x1c, through00f967c0. These native guards are not replaced by an unconditional item grant in this audit.

## Alternative references and provenance

Six compiled Type payloads reference1360571. A bounded scan of6612 already-cached GORs and the11 requested SPACE104 placement sets finds only the tutorial door container as a placed match. candidate-placement-matches.json and compiled-sword-reverse-references.json retain the scope. This does not exclude arbitrary future/runtime instantiation elsewhere.

WoS_InitialCorpse1411370 only forwards its parent corpse interaction and tutorial cleanup; it does not grant the sword. No compiled Type in the existing27350-entry patch catalog directly uses that script. This is not proof against a runtime script attachment, but its name is not used as placement evidence.

The container's compiled bytes are identical in initial and patch archives, SHA448d4159ca4ed6f40d36279979131162dde53f3e8c341e1476ee83e6072e9e25. The sword Type differs across variants; the patch Type SHA is88b0a4784f358709a74984b1ea10050985fb726abba989a57e384cad7740b0aa. compiled-source-provenance.json pins both variants and batch spans.

Original FAB metadata/streams and the two bundles are extracted only into inputs/ here, with archive/SHA receipts. No geometry is baked, no material/model substitution is made, and no all-LOD display policy is guessed. Sword rendering+0x14 is0; its authored rusty model appears in the other three fields, whose individual equipment/LOD roles remain unassigned.

No live asset/core/database edits, original game actions, save changes, Mac copies or arbitrary item grants were performed.
