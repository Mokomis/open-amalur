# Initial sword authored quantity — native proof

The parallel integer1 is a requested item quantity: one unit of SIMTYPE1360571 in the initial door/container inventory. It is not a weight, percentage or probability.

## Source bytes

Compiled Type1789987, SHA448d4159ca4ed6f40d36279979131162dde53f3e8c341e1476ee83e6072e9e25; exact source copied beside this report.
Inventory blueprint kind9 begins at file180(0xb4):
-+4/file184 pointer468; +8/file188 count1. u32 at468 is1360571.
-+0c/file192 pointer472; +10/file196 count1. i32 at472 is1, bytes01000000 (not float1.0).
-+2c/file224 optional resource0.
GOR1790948 / source instance1789992 in SPACE1417252 selects this Type. No random-loot resource is inferred.

## Consumed as quantity

00f0cfc0 resolves only type references and optional resource.00f74790 copies the type array to Inventory+88 with count+8c, and parallel numeric array to+98 with count+9c.

00f8e400 loops type indexi and calls:
createByType(out,&types[i],InventoryFlags&1,quantities[i],0),
where createByType is00f8e0c0 and the numeric value is its signed integer param5.

00f8e0c0 tests count>0. For single-item stack limit it creates via00fc6170 and decrements the request once per item. For stackable types it repeatedly creates stacks, adds up to stackLimit-1 into Item+90 and subtracts that many requested units. This is discrete quantity arithmetic. The authored scalar is never compared with a random sample, normalized against other entries or multiplied by100.
For value1, one requested unit reaches the factory/inventory-add route when source Type and owning actor/location are valid. Zero/negative values do not create units.

## Native lifecycle and interaction route

Direct authored inventory is initialized BEFORE loot interaction:
-Object::vf4 at00f916f0, when its firstboolean istrue and secondboolean isfalse, resolves active Inventory9 and calls00f8e400.
-Inventory deserialize::vf28 at00f965b0 calls00f8e400 only if persisted Inventory+0xc0 bit0x1000 isclear.
-00f8e400 finishes by setting that initialized bit.00f8e0c0 realizes the item and00f8dcb0 adds it to the owning inventory under active/membership checks.

This is distinct from recovered Door_Std_WOS_Start.loot_skeleton:
ACTOR.set_allow_looting -> ACTOR.create_loot_objects -> loot_summary.on_loot.
The create_loot_objects binding00e7cdf0 checks active Inventory9 and00e37b70 permission, then00f97260 processes a separate pending array at Inventory+6c/+70 (28B entries). That function does not read the initial authored quantity array+98.
Thus the script does not grant an arbitrary sword, and scalar1 does not mean one pending random roll. The sword is an authored container item exposed/transferred through normal loot handling.

00f8dcb0 optionally builds Lua parameters and dispatches through00df6ef0, but the hidden receiver/event symbolic name is not recovered in this bounded pass. Literal2 at the decompiled call must NOT be labeled an eventID. Existing Sword_WoS_InitialWeapon callback proof remains separate.

## Confidence and limits

Static native/source proof from existing cached exports only. Exact method bodies copied here. No native game execution, savedata actions, core/live asset changes or DB writes.
This proves quantity semantics and lifecycle call conditions, not that a particular current save/container remains unlooted or that player acquisition has already happened. Full stack-limit property naming and optional-loot queue producer were not needed and were not expanded.
