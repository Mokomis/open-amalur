# MQ01 cursor: staged portable C99 service

Files oa_mq01_cursor.c/.h; standalone test_mq01_cursor.c. No live binding/core/UI/save changes. This is an AUTHORED host cursor implementing the narrow native stage contract, not a QuestMgr, source startup implementation, checkpoint format or gameplay validation.

## Proven source state table

Quest asset613083 / script613082. The table is runtime synthetic0 followed by authored:
5,10,20,30,40,45,50,60,65,80,90,100.
Both exact source quest definitions agree.25 is absent.

Creation yields stage_index=-1,stage_id=-1,revision0. Querying an unsupported host quest returns UNSUPPORTED and does not write the output; it does not invent stage-1 for unsupported capabilities. A real unstarted supported cursor legitimately queries-1.

prepare_start does not activate. Only a successful host acknowledgement in commit advances to synthetic stage0. Starting an already active cursor is a known no-change; a future Lua adapter should return false for that native start result, not treat PREPARE as successful start.

Setter on unstarted cursor, undefined stage(including25), or current stage issues NO_CHANGE with a specific reason and does not call a host callback. Native guard precedence is preserved: unstarted25 reports UNSTARTED. Existing active5+set25 stays5; physical door opening is separate.

Defined transitions require acknowledgement. An explicit fresh request may go backward, including100->5 or20->5; no invented monotonic quest rule is applied.

Source normal new-game stage5 belongs to actual creator finish:
MainMenu13493 ->Loading13488 callback ->character_gen_manager417426.finish_character_gen ->MQ01.cheat_start_quest(start then5 plus game-start/passive/destiny effects).
This cursor NEVER fires that callback, auto-starts on cinematic skip, invents startup side effects, or assumes the present dev profile ran creator completion.

## API and lifetime

All functions are owner-thread only. The cursor is opaque and heap-allocated with bounded fixed storage. Create only for613083, with a caller-owned nonzero NEW generation and initially NULL output pointer.

1. oa_mq01_create(613083,generation,&cursor).
2. oa_mq01_query(cursor,613083,generation,&snapshot).
3. oa_mq01_prepare_start(cursor,&snapshot,&request,&reason), or oa_mq01_prepare_set(...targetStage...).
4. On OK, review/prepare required host effects. No quest state/revision has changed.
5. oa_mq01_commit(cursor,generation,&request,apply,context,error,capacity).
6. apply must return0 ONLY after atomically validating/applying the real required transition effects. Missing callback fails; rejection applies no cursor stage/revision change and consumes the request.
7. Query the committed state. Use oa_mq01_cancel to explicitly abandon a pending request. Destroy via oa_mq01_destroy(&cursor).

The complete expected snapshot (quest/generation/revision/index/ID) is checked at prepare. Commit checks caller generation, issuer cookie, version, quest, operation, request ID, previous revision/index/ID and target against the exact pending plan BEFORE callback. Stale/forged tokens leave the valid pending request intact and never call effects. One pending request per cursor. Query is allowed during pending preparation and still returns the old stage; reentry on the cursor during apply is rejected BUSY, including destruction.

Rejection consumes its request so a later success needs a fresh PREPARE. A missing callback leaves the request pending for explicit cancellation/review. Success increments revision once; no-change/cancel/rejection do not increment quest revision. Request IDs advance independently, preventing replay after a failed/cancelled attempt. Counter overflow fails closed.

Generation must change on logical reset/recreate/restore/newgame. Never reuse a generation while old requests may exist, even if an allocator reuses an address. Requests contain an internal uintptr issuer identity; they are ephemeral C tokens, not userdata equality, native identifiers or portable save records. Do not serialize these structs. No persistence/restore API is supplied. In particular, do not replay creator startup just to restore a save.

## Host acknowledgement boundary

START acknowledgement covers a real supported native-equivalent quest start. SET acknowledgement covers required stage transition callbacks/events/conditions/UI effects. The module supplies none of those systems and cannot undo side effects if a callback violates the apply-nothing-on-rejection contract.

The six-step creator init is a MULTI-EFFECT outer operation, while this module commits one cursor transition at a time. It does not by itself make an entire Lua effect batch atomic. A future binding must validate/coordinate the full outer batch and only acknowledge actual effects; if that cannot be guaranteed, keep the capability unavailable. No binding is installed by this stage.

The module does not implement completed/failed quest lists, objective counters, quest log, script callbacks, native condition scheduling, quest selection or startup flags. stage100 here is only an acknowledged stage cursor; it is not a claim that native quest completion machinery ran.

## Tests and builds

build-test.cmd uses existing VS18BuildTools and Android NDKr30 only, in this directory.
- Windows MSVC /W4 /WX: test_mq01_cursor.exe PASS241checks.
- ARM64 Android26 clang -std=c99 -Wall -Wextra -Werror: standalone test and module compile/link PASS. ELF64little-endian AArch64 verified.
- ARM executable was NOT run on a device. No app/engine build, install or game launch.

Recorded test backend explicitly models atomic acknowledged effects; it is NOT a native QuestMgr/startup backend. Coverage includes ctor/query-1 vs unsupported quest, prepare does not start, successful acknowledged start0/set5, ignored25, same-stage/already-started no-ops, missing callback, rejected start AND rejected active transition rollback, stale generation/snapshot/forged request, cross-cursor issuer, cancellation/replay, rejected request replay, old regression token at100, valid fresh100->5, all13defined IDs, and callback reentry/destruction guards.

validate_artifacts.py cross-checks the compiled source table against BOTH pinned source quest definitions and checks Windows/ARM output headers, test results and source-audit hashes. validation-receipt.json and delivery.json pin exact artifacts. No broad native research or source data changes were performed.
