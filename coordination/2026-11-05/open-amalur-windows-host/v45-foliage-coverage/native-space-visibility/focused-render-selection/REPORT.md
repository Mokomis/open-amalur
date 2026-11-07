# Focused native render-selection attempt: bounded result

No static collection LOD or SPACE-admission predicate was recovered that explains source198 versus the33 captured native leaf fixtures. The eight-body cap was reached and native-body investigation stopped. A real runtime `FabInstanceRender` state predicate was recovered, but it cannot be evaluated for these static fixtures from the retained GPU capture. No cutoff, SPACE whitelist, source edit or live asset change is proposed.

## Observed runtime component predicate

`BHG_FabInstanceRender::vf6 @00ce2b00` selects `00cae900` or `00cae970` using the same condition also guarding vf3 `00c8ab60`. Shared consumer `00ccc110` expresses the resulting boolean exactly as:

```c
state = ((flags_at_1d0 & 0x000e2004) != 0)
     || (byte_at_1d5 != 0 && byte_at_1d6 == 0);
```

`00cae900` clears bit0x4 in the component state at+0x1d0; `00cae970` sets it. Both invoke `00ccc110` and propagate to child handles in the+0x24 array/count+0x28. `00ccc110` caches the effective boolean in component bit0x10000. On a state change, it walks20-byte records at component+0x14/count+0x18, using the handle at record+8. For each nonzero handle it allocates opcode0x1e,16bytes through `00cb55d0`, and writes:

```c
command[1] = child_render_handle;
command[2] = 0xfffffdff;          // mask with bit0x200 clear
command[3] = state ? 0x200 : 0;
```

Those field writes and predicates are direct cached-source observations. Interpreting this as render-disable/visibility propagation is strongly suggested by the matching runtime branch and mask/value message, but the opcode consumer was not opened. The exact engine names of bytes+0x1d5/+0x1d6 and individual mask bits remain unknown. It is not a recovered camera-distance or active-SPACE predicate.

`vf5 @00cccaf0` and vf6 send slot/state notifications through `00cbdea0`. That function is a listener broadcaster with virtual callbacks and listener removal; it is not a scene admission or mesh draw submission function. This distinction corrects the initial forward-edge hypothesis.

## Why this does not classify source198 or the33 positives

The static source collection uses80-byte bounds records with source flags at+72, paired with84-byte render records. The recovered runtime component flags are at+0x1d0 in a `FabInstanceRender` object. These are different records and different fields. Source flags7/23 must not be treated as the recovered runtime flags. Applying that substitution would set component mask bit0x4 and reject known native positives as well as source198.

The retained GPU capture supplies native draw/resource identities, object matrices and shader constant buffers. It does not supply the CPU component state at+0x1d0/+0x1d5/+0x1d6, the child render-handle records, or the command target’s current bit0x200 for any of these fixtures. These absent values are unknown, not zero. Consequently, the recovered runtime predicate is unevaluable for all33 native-positive fixtures and source198. [Per-fixture comparison](fixture-comparison.json).

The existing range evidence is unchanged: strict selected-assembly raw-origin or bound-center ranges preserve22/33 positives; exactVB+IB+same-material alias unions preserve31/33. Both raw-origin and bound-center rules exclude source198 but still reject native68819/source451 and native69083/source478. This attempt supplies no new justification for overriding that guard.

## Static source fixture and admission boundary

The exact current extra leaf remains `l-3_-12.bin`, triangle33/index99, source198, SOUTH431642, FAB340232/assembly6/MID359202, rawT=(-19209.921875,-74337.1953125,6912.13134765625),unit scale. It reproduces current depth24=16762614 exactly, while the original pixel is clear. Its source render offsets are604328 (group0/record1096) and1082692 (group1/record358). Actual current Windows alpha679 equals all captured authored mips; a generated-alpha explanation is not supported for this Windows point.

The55 previously matched SPACE anchors come only from WEST431646(54) and transition431650(1); source198 is SOUTH431642. Active-SPACE/streaming/PVS remains a hypothesis supported by that correlation, not a recovered rule or causal proof. The successful regional collection restoration and separate source-authored shadow stage do not resolve this static SPACE membership question.

## Budget, preflight and exact scope

Body-free inventory first reused `v30-engine/PLAN.md`, names/classes/function-size tables, the existing backend C rewrites, registration call edges and previous SPACE lifecycle notes. Registration wrappers00cd24e0/00cd2570 have the common collection loader00fec370 as their sole direct cached caller. Main draw backend00c961e0 has the packet wrapper00c97e20 as its direct cached caller.

The initial four small bodies were00c8ab60,00c97e20,00cccaf0,00ce2b00. Expansion followed the concrete vf6 state branch into00cae900/00cae970, common notification00cbdea0 and shared state consumer00ccc110. All were preflighted; the largest is293 machine bytes and1559 pseudocode characters. No ninth body was opened. [Body ledger](opened-bodies.json), [scope](scope.json), [body-free inventory](body-free-inventory.json).

| Address | Observed role | Machine bytes |
|---|---|---:|
|00c8ab60|FabInstanceRender vf3 runtime guard|205|
|00c97e20|Select already-built packet groups by pass; calls backend00c961e0|101|
|00cccaf0|FabInstanceRender vf5 slot/listener notification|205|
|00ce2b00|FabInstanceRender vf6 runtime branch and propagation|293|
|00cae900|Clear runtime component bit0x4 and propagate|97|
|00cae970|Set runtime component bit0x4 and propagate|97|
|00cbdea0|Listener broadcast/removal, not admission|143|
|00ccc110|Effective-state cache and opcode0x1e mask/value update|280|

The backend wrapper00c97e20 compares a requested pass with an already-built group field and invokes00c961e0 over packet intervals. It contains no object LOD/admission test. The larger SceneRenderController bodies were preflighted and deferred, not opened. A body-free opcode-case inventory found no direct renderer-range `case0x1e` dispatcher. The uninspected allocator00cb55d0 was recorded only as a deferred opcode seed; it is not the recommended continuation for this static collection problem.

## Precise blocker and next seed

The missing link is the actual static collection registration/admission producer and its runtime membership state. The useful continuation is the exact source198 static record and the native-positive68811 fixture, whose source geometry shares the same full VB/IB identity (VB SHA4968cb1013ce449e72c7f181d46287644a9e9037158889b8beaa5f30db634e72; IB SHAcc5268d418772828ba0540fd68c94e7a935a55b17f7f3d5ce04e8de139eb1fac). Trace those paired bounds/render records through common loader00fec370 → bounds/render registration00cd24e0/00cd2570, then identify the consumer that places or excludes that registered static geometry in the scene’s admitted list. The existing wrapper/body-free call graph does not identify that consumer address.

A future pass must correlate that actual static handle/membership route with the native VB and raw pose. Another actor virtual walk, a fitted distance factor, or a capture-specific SOUTH exclusion would not fill the evidence gap. No more research was performed after the cap. Original files, analysis databases, game/runtime state and deployed assets were preserved.
