# Patron UI: original domains and missing detail

Fire and Wisdom are the ORIGINAL creator choice labels. The current24race-option rows and13buff identities are correct. The presentation gap is the missing separate deity/detail and bonus panel, not incorrect deity selection or an invented bonus. Keep saved choice indices, IDs and profile CRC semantics unchanged.

## Ready presentation metadata

patron-presentation.json is keyed by all13buffIDs. It includes original choice labels, exact original creator deity/detail line, original post-selection blessing title/lore, exact stat-key/name/operator/float-bit records, readable derived bonus lines, per-race6-option ordering and every localization lookup witness.

oa_patron_presentation.h/.c is an optional small C99 presentation table and lookup by buffID. It contains only text, no choice/state/save/gameplay changes. Bonus summary wording is explicitly source-derived; exact original labels/details/lore remain separate fields. Both Windows C and ARM64 Android26 C99 compile with warnings treated as errors.

## Original source UI separation

Source character_gen_win417410.lua_bxml SHA2b644ef265295689d26e7350380e2bbb9adf6bb1f170c3e6b93f0de38876369c:
- Root PC196 publishes description_package, PC368 publishes m_option_to_loc.
- add_template0/17 reads m_option_to_loc atPC37/file15989 and passes the label to WINDOW.set_label_text (PC33/file15973).
- get_description0/15/file12098 reads the selected option and returns description_package[m_display_options_data.param_name][selected]; lookups atPC11/18/21.
- update_visibility0/16 gets character_data.m_patron_buffs, buff_utils.get_param_data and get_buffed_parameter_list_for_display to populate separate bonus rows.

original-ui-tables.json was evaluated from the cached exact reconstructed top-level declarations in isolated Lua5.1 with inert require and SL retaining its raw two-word carrier. No native UI or game binding executed. original-ui-lookup-proof.json preserves the exact relevant instruction/file-offset witnesses.

The shipped patch symbol_table_64_localization_keys.bin resolves SLhash=(uint32(SL1)<<32)|uint32(SL2). All26patron label/detail hashes resolve exactly. They independently match the installed English main localization table.25of26rows have creator source owner417410 in parallel loc_table_symbols records. None reuses generic None entry2449 (owner1293218); the sourceUI SLhash directly resolves None as well. Example:
- Fire label hash1dab27e8f0559ee9 ->Fire, English main index3655/file153314.
- Fire detail hash6ff0dd72e2864c63 ->Vraekor - God of Fire, and Patron of the Forge, index3703/file155293.
- Wisdom label hash72a489db9146b0fe ->Wisdom, index3651/file153281.
- Wisdom detail hash035d5d2fbff0e4de ->Ethene - Goddess of Wisdom and Art, index3686/file154289.
These are the original choice-vs-detail split, not a request to recreate the old menu. Parent keeps the existing new UI.

## Race order and stable IDs

Recovered source character_data751829 supplies m_patrons_by_race and m_patron_buffs. The live oa_creation_source_tables.c matches all24ordered domain/ID pairs exactly; the same tables serve both sexes.

Almain: Fire1254092, Wisdom1254094, War1254095, Order1254099, Justice1254101, None1697849.
Varani: Fire1254092, Water1254093, War1254095, Death1254097, Mischief1254102, None1697849.
Ljosalfar: Earth1254079, Air1254091, Wisdom1254094, Order1254099, Justice1254101, None1697849.
Dokkalfar: Wisdom1254094, Love1254096, Death1254097, Fate1254098, Mischief1254102, None1697849.

## Benefit identity and English wording qualification

Existing creation-gameplay/source-patrons.json retains all13exact buff graphs, raw float bits and op1multiply/op3add; the earlier13buff/48race-sex-option gameplay tests are reused, not rerun or newly claimed here.

This pass closes all18stat names and localization references from patch buff_vars.koabuffvariables:144records at raw file16, stride16(key,nameptr,SLhash), all144source name hashes independently equal their stored keys. Native00da3e80 reads/imports this exact filename, iterates16Bsource rows, stores names toMgr+e0 and calls00da0800 withMgr+bc and row+8 locale. The retained asm atda3fc9 confirms the implicit manager+bc ABI.00d94d50 reads keyBC/localizationCC;00d8fc60 reads parameter namesE0.00eb56e0->00eb5100 converts actual graph values to native UI whole/fraction fields. Exact100/.5constants are pinned in source-validation.json.

Buff graph raw file+48 contains its blessing-title SLhash; +56 contains its blessing-lore SLhash. Each resolves through the original localization-key table; no lore invented. The creator description itself is the short full deity line; longer lore belongs to the selected blessing and is supplied as an optional separate field.

Readable bonuses:
Earth/Gaea+5%ElementalResistance; Air/Ohnshan+6%LightningDamage/+6%LightningResistance; Fire/Vraekor+6%FireDamage/+6%FireResistance; Water/Njordir+6%IceDamage/+6%IceResistance; Wisdom/Ethene+10%Mana; War/Thyrdon+5%PhysicalDamage/+5%Armor; Love/Aryllia+5%Health/+1%CriticalHitChance; Death/Belen+1%CriticalHitChance/+8%CriticalHitDamage; Fate/Lyria+5%Mana/+5%ManaRegeneration; Order/Mitharu+5%Health/+5%Mana; Justice/Ynadon+10%Health; Mischief/Lupoku+6%PoisonDamage/+6%PoisonResistance; None+1%Experience.

These readable lines are DERIVED from exact source names/values and original formatting rules, rather than a captured original UI line raster or punctuation claim. Some source stat localization keys retain developer annotations such as Fire Damage -1 default; those annotations are preserved in proof fields and are not product display text.

Original buff_utils686835 has m_do_not_display.PowerRecovery=true; Fate's noncombat regen stat is hidden from its separate UI list while combat PowerRecoveryCombat remains. Both actual regen modifiers are retained in metadata; no gameplay effect is removed. Original Critical special fraction-as-whole rule turns sourceadd0.01 into1%chance. None is a REAL buff1697849, not no-benefit; its experience multiplier1.0099999904632568 means+1%.

Exact source Ohnshan creator text says God while blessing lore says goddess; both are preserved without editorial correction. No original game launch, new database/session, live source/UI/asset/save modification or inferred entitlement behavior was used.
