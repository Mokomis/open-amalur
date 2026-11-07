"""Must-alias analysis for Amalur's hidden interpreter value (uVar29).

Input rows must already have validated operands, CFG edges, and register effects.
This pass proves cache/register equality only; it never admits an opcode, repairs
an operand error, or proves its runtime domain. Call it after open-list effects
have populated may_writes/kills. Consumers still require their ordinary operand,
type-domain, initialization and capture checks.

Evidence: interpreter 0x010adce0, ev_b43d96bdb035be913311172a76bad68bec6088b63f3df7c11c58b9476a01375b.
Scope: original koa.exe hash below, admitted primitive/plain-table domains.
The input slot is unknown at function entry: Lua callees share the interpreter's
cache, and starting the native interpreter is distinct from entering a function.
"""

TARGET_SHA256 = "16a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314"
EVIDENCE = "ev_b43d96bdb035be913311172a76bad68bec6088b63f3df7c11c58b9476a01375b"

# Native handler identities, not profile's historical immediate-producer flags.
# A producer must independently have native_static confirmation in the profile.
RESULT_PRODUCERS = {0, 6, 8, 32, 46, 67, 85}
SOURCE_A_PRODUCERS = {1, 15, 33}
CALLS = {2, 3, 14, 22, 23, 24, 29, 30, 31, 62, 63}
CONSUMERS = {62: "A", 63: "A", 64: "A", 65: "A", 66: "B", 67: "B", 68: "A"}

# No assignment to native uVar29 in these handlers. Their admitted domains must
# forbid metamethod callbacks; SETGLOBAL (27) is intentionally excluded because
# current emission permits environment metamethods that can mutate open cells.
PRESERVERS = {4, 5, 9, 10, 11, 12, 13, 16, 17, 18, 19, 20, 21, 25, 26, 28,
              34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45,
              47, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61,
              64, 65, 66, 68}


def _confirmed(row, profile):
    spec = profile.get("opcodes", {}).get(str(row["opcode"]), {})
    return (bool(row.get("kind")) and spec.get("confirmation") == "native_static"
            and bool(spec.get("evidence")))


def _overwritten(row, target):
    return (set(row.get("writes", [])) | set(row.get("kills", []))
            | set(row.get("may_writes", []))
            | set(row.get("edge_writes", {}).get(str(target), [])))


def _effect(row, profile):
    if not _confirmed(row, profile):
        return "unconfirmed_invalidates"
    op = row["opcode"]
    if op in CALLS:
        return "call_invalidates"
    if op in RESULT_PRODUCERS:
        return "result_A"
    if op in SOURCE_A_PRODUCERS:
        return "source_A"
    if op == 7:
        return "move_source_B"
    if op == 48:
        return "not_source_B"
    if op in PRESERVERS:
        return "preserve"
    return "unmodeled_invalidates"


def _transfer(row, incoming, target, profile):
    effect = _effect(row, profile)
    a, b = row["A"], row["B"]
    killed = _overwritten(row, target)
    if effect == "result_A":
        # The handler stores the same fresh value in cache and A, including
        # ordinary GETFIELD and SELF. A is the post-write destination.
        return {a}
    if effect in ("source_A", "move_source_B", "not_source_B"):
        source = a if effect == "source_A" else b
        # If the source already equals the old cache, other aliases survive.
        state = set(incoming) if source in incoming else {source}
        state -= killed
        if effect == "move_source_B":
            state.add(a)
        # NOT writes the boolean opposite, while cache remains the input. In
        # particular NOT A,A removes A from the alias set, even for booleans.
        return state
    if effect != "preserve":
        return set()
    state = set(incoming) - killed
    if row["opcode"] == 55:
        # TESTSET copies only on the taken edge. When both outcomes lead to
        # the same PC, no unconditional assignment can be inferred.
        taken = row.get("jump_target")
        other = row.get("fallthrough_target")
        if target == taken:
            if taken != other:
                state.discard(a)
                if b in incoming:
                    state.add(a)
            elif not (a in incoming and b in incoming):
                # edge_writes records definite assignments only; a merged
                # TESTSET edge still has a conditional overwrite to consider.
                state.discard(a)
    return state


def analyze_cache_aliases(rows, profile, maximum_stack_size, entry_pc=0):
    """Return per-PC must-alias sets and cached-operand proof records.

    The join is intersection, so independent producers on separate branches can
    establish the same register relation without naming one producer PC. A
    descending finite-lattice fixed point handles loops and kills on backedges.
    No runtime or profile state is mutated.
    """
    if profile.get("binary_sha256") != TARGET_SHA256:
        raise ValueError("cache analysis profile does not match native evidence")
    by_pc = {row["pc"]: row for row in rows}
    if len(by_pc) != len(rows):
        raise ValueError("duplicate instruction PC")
    if not rows:
        return {}
    if entry_pc not in by_pc:
        raise ValueError("entry PC absent from CFG")
    reachable, pending = set(), [entry_pc]
    while pending:
        pc = pending.pop()
        if pc in reachable:
            continue
        if pc not in by_pc:
            raise ValueError("CFG edge targets absent instruction")
        reachable.add(pc)
        pending.extend(by_pc[pc].get("successors") or [])
    predecessors = {pc: set() for pc in reachable}
    for pc in reachable:
        for target in by_pc[pc].get("successors") or []:
            predecessors[target].add(pc)
    universe = set(range(maximum_stack_size))
    incoming = {pc: (set() if pc == entry_pc else set(universe)) for pc in reachable}
    changed = True
    while changed:
        changed = False
        for pc in sorted(reachable):
            paths = [set()] if pc == entry_pc else []
            paths += [_transfer(by_pc[p], incoming[p], pc, profile)
                      for p in sorted(predecessors[pc])]
            new = set.intersection(*paths) if paths else set()
            new &= universe
            if new != incoming[pc]:
                incoming[pc] = new
                changed = True
    result = {}
    for pc in sorted(reachable):
        row = by_pc[pc]
        field = CONSUMERS.get(row["opcode"])
        register = row[field] if field else None
        result[pc] = {
            "cached_aliases_in": sorted(incoming[pc]),
            "cache_consumer_register": register,
            "cache_register_proven": (register in incoming[pc]) if field else None,
            "cache_effect": _effect(row, profile),
            "cache_predecessor_pcs": sorted(predecessors[pc]),
            "cache_evidence": EVIDENCE,
        }
    return result
