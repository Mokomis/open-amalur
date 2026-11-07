"""Conservative register-level Lua reconstruction for confirmed Amalur opcodes.

Consumes the existing structural parser, preserves raw instruction provenance,
and refuses to turn unsupported semantics into successful-looking Lua.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from amalur_script import ParseError, parse_file, same_file


KINDS = {"move", "loadk", "getglobal", "setglobal", "getfield_k", "getfield_cached_k",
         "call_fixed", "return_fixed", "closure_no_upvalues", "jump"}


class ReconstructionError(ValueError):
    pass


def lua_bytes(hex_bytes):
    """Byte-exact Lua 5.1 literal, including non-UTF8 strings and digit boundaries."""
    chunks = []
    for b in bytes.fromhex(hex_bytes):
        if 32 <= b <= 126 and b not in (34, 92):
            chunks.append(chr(b))
        elif b in (34, 92):
            chunks.append("\\" + chr(b))
        else:
            chunks.append("\\" + str(b).zfill(3))
    return '"' + "".join(chunks) + '"'


def check_profile(profile):
    if profile.get("schema_version") != 1:
        raise ReconstructionError("unsupported semantic profile schema")
    for code, spec in profile.get("opcodes", {}).items():
        if not code.isdecimal() or not 0 <= int(code) <= 127:
            raise ReconstructionError("invalid opcode profile key")
        if spec.get("kind") not in KINDS:
            raise ReconstructionError("unsupported semantic kind")
        if not isinstance(spec.get("inline_data_words", 0), int) or not 0 <= spec.get("inline_data_words", 0) <= 8:
            raise ReconstructionError("invalid inline-data count")
        if spec.get("inline_cache_constant_slots", 0) not in (0, 2):
            raise ReconstructionError("invalid inline cache-slot count")
        if not isinstance(spec.get("evidence"), list) or not spec["evidence"]:
            raise ReconstructionError("opcode profile requires evidence references")


def confirmed(spec):
    return spec.get("confirmation") == "native_static" and bool(spec.get("evidence"))


def constant_literal(constant, profile):
    kind = constant["type"]
    if kind == "nil":
        return "nil"
    if kind == "boolean":
        return "true" if constant["value"] else "false"
    if kind == "string":
        return lua_bytes(constant["value"]["bytes_hex"])
    if kind == "number" and confirmed(profile.get("number_encoding", {})):
        if profile["number_encoding"].get("kind") == "signed_int32":
            return str(int.from_bytes(bytes.fromhex(constant["raw_hex"]), "big", signed=True))
    raise ReconstructionError("constant encoding is not confirmed for Lua emission: " + kind)


def lift_function(fn, path, profile):
    code = fn["instructions"]
    opcodes = profile.get("opcodes", {})
    rows, unknowns = [], []
    if not confirmed(profile.get("instruction_layout", {})):
        unknowns.append({"reason": "instruction bit layout is not natively confirmed"})
    if fn["upvalue_count"]:
        unknowns.append({"reason": "captured upvalues are not yet reconstructed"})
    if fn["vararg_flags"] not in (0, 2):
        unknowns.append({"reason": "unsupported vararg flags"})
    if fn["maximum_stack_size"] > 190:
        unknowns.append({"reason": "register-local emission limit exceeded"})
    pc = 0
    while pc < len(code):
        ins = code[pc]
        spec = opcodes.get(str(ins["opcode"]), {})
        row = {"pc": pc, "file_offset": ins["file_offset"], "word_hex": ins["word_hex"],
               "opcode": ins["opcode"], "name": ins["opcode_name_provisional"],
               "A": ins["A"], "B": ins["B_raw"], "C": ins["C_raw"], "Bx": ins["Bx_raw"],
               "reads": [], "writes": [], "metadata_pcs": [], "metadata_words": [], "successors": None,
               "status": "unknown", "evidence": spec.get("evidence", [])}
        rows.append(row)
        if not confirmed(spec):
            unknowns.append({"pc": pc, "reason": "opcode semantics not confirmed", "opcode": ins["opcode"]})
            pc += 1
            continue
        row["kind"] = kind = spec["kind"]
        skip = spec.get("inline_data_words", 0)
        next_pc = pc + 1 + skip
        if next_pc > len(code):
            raise ReconstructionError(f"{path} pc {pc}: inline data exceeds function")
        expected_data = profile.get("inline_data_opcode")
        for data_pc in range(pc + 1, next_pc):
            if code[data_pc]["opcode"] != expected_data:
                raise ReconstructionError(f"{path} pc {pc}: expected inline DATA at {data_pc}")
            row["metadata_pcs"].append(data_pc)
            row["metadata_words"].append({"pc":data_pc,"file_offset":code[data_pc]["file_offset"],
                                          "word_hex":code[data_pc]["word_hex"]})
        cache_slots = spec.get("inline_cache_constant_slots", 0)
        if cache_slots:
            if not skip:
                raise ReconstructionError(f"{path} pc {pc}: cache-slot profile lacks payload")
            cache_index = code[pc+1]["Bx_raw"]
            if cache_index + cache_slots > len(fn["constants"]):
                raise ReconstructionError(f"{path} pc {pc}: inline cache constant slots outside pool")
            row["cache_constant_indices"] = list(range(cache_index, cache_index + cache_slots))
        row["status"] = "confirmed_static"
        row["successors"] = [next_pc] if next_pc < len(code) else []
        a, b, c, bx = row["A"], row["B"], row["C"], row["Bx"]
        if kind == "move":
            row.update(reads=[b], writes=[a])
        elif kind in ("loadk", "getglobal"):
            row.update(writes=[a], constant_index=bx)
        elif kind == "setglobal":
            row.update(reads=[a], constant_index=bx)
        elif kind in ("getfield_k", "getfield_cached_k"):
            if kind == "getfield_cached_k":
                if c > 255:
                    unknowns.append({"pc": pc, "reason": "GETFIELD_R1 high operand flag is not yet modeled"})
                    row["status"] = "unsupported_operands"
                previous = rows[-2] if len(rows) >= 2 else None
                previous_spec = opcodes.get(str(previous["opcode"]), {}) if previous else {}
                if (not previous or previous.get("kind") != "getglobal"
                        or previous.get("status") != "confirmed_static"
                        or not previous_spec.get("produces_cached_result")
                        or previous["A"] != b):
                    unknowns.append({"pc": pc, "reason": "hidden last-result register relation is not established"})
                    row["status"] = "unsupported_operands"
                else:
                    row["cached_result_producer_pc"] = previous["pc"]
                c &= 255
            row.update(reads=[b], writes=[a], constant_index=c)
        elif kind == "call_fixed":
            if c > 255:
                unknowns.append({"pc": pc, "reason": "CALL high operand flag is not yet modeled"})
                row["status"] = "unsupported_operands"
            elif not b or not c:
                unknowns.append({"pc": pc, "reason": "open argument/result lists are unsupported"})
                row["status"] = "unsupported_operands"
            else:
                row.update(reads=list(range(a, a + b)), writes=list(range(a, a + c - 1)))
        elif kind == "return_fixed":
            row["successors"] = []
            if not b:
                unknowns.append({"pc": pc, "reason": "open return list is unsupported"})
                row["status"] = "unsupported_operands"
            else:
                row["reads"] = list(range(a, a + b - 1))
        elif kind == "closure_no_upvalues":
            if bx >= len(fn["children"]) or fn["children"][bx]["upvalue_count"]:
                unknowns.append({"pc": pc, "reason": "closure target or captured upvalues unsupported"})
                row["status"] = "unsupported_operands"
            row.update(writes=[a], child_index=bx)
        elif kind == "jump":
            row["successors"] = [pc + 1 + ins["sBx_provisional"]]
            unknowns.append({"pc": pc, "reason": "control-flow source structuring not yet implemented"})
        for reg in row["reads"] + row["writes"]:
            if not 0 <= reg < fn["maximum_stack_size"]:
                raise ReconstructionError(f"{path} pc {pc}: register {reg} outside stack")
        if "constant_index" in row:
            index = row["constant_index"]
            if index >= len(fn["constants"]):
                raise ReconstructionError(f"{path} pc {pc}: constant index outside pool")
            try:
                row["constant_lua"] = constant_literal(fn["constants"][index], profile)
            except ReconstructionError as exc:
                unknowns.append({"pc": pc, "reason": str(exc)})
                row["status"] = "unsupported_constant"
        pc = next_pc
    starts = {r["pc"] for r in rows}
    leaders = {0} if rows else set()
    for row in rows:
        if row["successors"] is not None:
            for target in row["successors"]:
                if target not in starts:
                    raise ReconstructionError(f"{path} pc {row['pc']}: edge enters inline data or leaves code")
            if row.get("kind") in ("jump", "return_fixed"):
                leaders.update(row["successors"])
                after = row["pc"] + len(row["metadata_pcs"]) + 1
                if after in starts:
                    leaders.add(after)
        else:
            leaders.add(row["pc"])
            if row["pc"] + 1 in starts:
                leaders.add(row["pc"] + 1)
    blocks = []
    for row in rows:
        if not blocks or row["pc"] in leaders:
            blocks.append({"start_pc": row["pc"], "instruction_pcs": []})
        blocks[-1]["instruction_pcs"].append(row["pc"])
        blocks[-1]["successors"] = row["successors"]
    initialized = set(range(fn["parameter_count"]))
    for row in rows:
        missing = sorted(set(row["reads"]) - initialized)
        if missing:
            unknowns.append({"pc": row["pc"], "reason": "register read before a known definition", "registers": missing})
        initialized.update(row["writes"])
    if not rows or rows[-1].get("kind") != "return_fixed":
        unknowns.append({"reason": "function does not end with a supported explicit RETURN"})
    if any(r.get("kind") == "return_fixed" for r in rows[:-1]):
        unknowns.append({"reason": "instructions after an earlier RETURN require control-flow structuring"})
    children = [lift_function(child, path + "/" + str(n), profile)
                for n, child in enumerate(fn["children"])]
    return {"path": path, "parameter_count": fn["parameter_count"],
            "maximum_stack_size": fn["maximum_stack_size"], "vararg_flags": fn["vararg_flags"],
            "instructions": rows, "blocks": blocks, "unknowns": unknowns,
            "body_emittable": not unknowns, "children": children}


def emit_function(ir, indent=0):
    pad = "  " * indent
    params = [f"r{i}" for i in range(ir["parameter_count"])]
    if ir["vararg_flags"]:
        params.append("...")
    lines = ["function(" + ", ".join(params) + ")"]
    if not ir["body_emittable"]:
        reasons = "; ".join(dict.fromkeys(u["reason"] for u in ir["unknowns"]))
        lines.append(pad + "  -- UNRESOLVED function " + ir["path"] + ": " + reasons)
        message = "Unresolved Amalur function " + ir["path"] + "; inspect reconstruction IR"
        lines.append(pad + "  __unresolved(" + lua_bytes(message.encode().hex()) + ")")
        lines.append(pad + "end")
        return lines
    local_regs = [f"r{i}" for i in range(ir["parameter_count"], ir["maximum_stack_size"])]
    if local_regs:
        lines.append(pad + "  local " + ", ".join(local_regs))
    for row in ir["instructions"]:
        a,b,c = row["A"],row["B"],row["C"]
        kind = row["kind"]
        lines.append(pad + f"  -- pc {row['pc']} / file 0x{row['file_offset']:x}: {row['name']}")
        if kind == "move":
            statement = f"r{a} = r{b}"
        elif kind == "loadk":
            statement = f"r{a} = {row['constant_lua']}"
        elif kind == "getglobal":
            statement = f"r{a} = __getfenv(1)[{row['constant_lua']}]"
        elif kind == "setglobal":
            statement = f"__getfenv(1)[{row['constant_lua']}] = r{a}"
        elif kind in ("getfield_k", "getfield_cached_k"):
            statement = f"r{a} = r{b}[{row['constant_lua']}]"
        elif kind == "call_fixed":
            call = f"r{a}(" + ", ".join(f"r{i}" for i in range(a+1,a+b)) + ")"
            statement = ((", ".join(f"r{i}" for i in range(a,a+c-1)) + " = ") if c > 1 else "") + call
        elif kind == "return_fixed":
            statement = "return" + ((" " + ", ".join(f"r{i}" for i in range(a,a+b-1))) if b > 1 else "")
        elif kind == "closure_no_upvalues":
            child = emit_function(ir["children"][row["child_index"]], indent + 1)
            lines.append(pad + f"  r{a} = " + child[0])
            lines.extend(child[1:])
            continue
        else:
            raise ReconstructionError("emitter received unsupported kind")
        lines.append(pad + "  " + statement)
    lines.append(pad + "end")
    return lines


def reconstruct(parsed, profile):
    check_profile(profile)
    root = lift_function(parsed["chunk"]["root_function"], "0", profile)
    all_functions = []
    def visit(fn):
        all_functions.append(fn)
        for child in fn["children"]:
            visit(child)
    visit(root)
    emitted = sum(fn["body_emittable"] for fn in all_functions)
    ir = {"schema_version":1, "input_sha256": parsed["input_sha256"],
          "native_binary_sha256": profile.get("binary_sha256"),
          "profile": profile, "root_function": root,
          "summary": {"functions": len(all_functions), "emittable_function_bodies": emitted,
                      "unresolved_function_bodies": len(all_functions)-emitted},
          "limitations": ["Register-level Lua 5.1 reconstruction, not original source.",
                          "Static opcode confirmation does not prove runtime equivalence.",
                          "No control-flow structuring, captured upvalues, or open argument/result lists yet.",
                          "Generated code has not been executed in the game."]}
    header = ["-- Opem Amalur: initial register-level Lua 5.1 reconstruction.",
              "-- Input SHA-256: " + parsed["input_sha256"],
              "-- Static interpretation; not original source or runtime-equivalence proof.",
              "-- Unresolved function bodies are explicit error stubs, never silent no-ops.",
              "-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.",
              "local __getfenv, __unresolved = getfenv, error", ""]
    body = emit_function(root)
    header.append("return (" + body[0])
    header.extend(body[1:-1])
    header.append(body[-1] + ")(...)")
    return ir, "\n".join(header) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", type=Path)
    ap.add_argument("--profile", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--ir", required=True, type=Path)
    args = ap.parse_args()
    if any(same_file(dest, src) for dest in (args.output,args.ir) for src in (args.input,args.profile)):
        ap.error("output must not overwrite input or semantic profile")
    if same_file(args.output,args.ir):
        ap.error("Lua and IR outputs must differ")
    try:
        profile = json.loads(args.profile.read_text(encoding="utf-8-sig"))
        parsed = parse_file(args.input)
        ir, lua = reconstruct(parsed, profile)
        args.output.write_text(lua,encoding="utf-8")
        args.ir.write_text(json.dumps(ir,indent=2)+"\n",encoding="utf-8")
    except (OSError, ValueError, ParseError) as exc:
        ap.exit(1,str(exc)+"\n")
    print(json.dumps(ir["summary"]))


if __name__ == "__main__":
    main()
