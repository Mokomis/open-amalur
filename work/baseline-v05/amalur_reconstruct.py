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
         "call_fixed", "return_fixed", "closure_no_upvalues", "jump",
         "test_branch", "test_cached_branch", "eq_branch", "lt_branch", "le_branch",
         "testset_branch", "loadbool", "loadnil", "not", "getupval", "setupval",
         "setupval_cached", "close", "closure", "call_cached_fixed", "newtable",
         "setfield", "setfield_cached", "gettable", "forprep", "forloop", "tforloop", "vararg", "length", "setlist", "integer_division",
         "integer_add", "integer_subtract", "integer_multiply", "integer_modulo", "integer_power", "integer_negate", "self", "settable", "tailcall", "tailcall_cached", "not_cached", "concat"}


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
    if kind == "uint64" and confirmed(profile.get("uint64_transport", {})):
        raw=constant.get("raw_hex")
        if raw is None:
            value=constant.get("value")
            if not isinstance(value,int) or isinstance(value,bool) or not 0<=value<2**64:
                raise ReconstructionError("uint64 requires exact integer or serialized bytes")
            raw=f"{value:016x}"
        if len(raw)!=16 or any(c not in "0123456789abcdefABCDEF" for c in raw):
            raise ReconstructionError("uint64 serialized payload must be exactly eight bytes")
        return '__uint64("'+raw.lower()+'")'
    raise ReconstructionError("constant encoding is not confirmed for Lua emission: " + kind)


def lift_function_legacy(fn, path, profile):
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


def emit_function_legacy(ir, indent=0):
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


BRANCH_KINDS = {"test_branch", "test_cached_branch", "eq_branch", "lt_branch", "le_branch", "testset_branch"}


def lift_function(fn, path, profile):
    if not (confirmed(profile.get("control_flow", {})) or confirmed(profile.get("captures", {}))):
        return lift_function_legacy(fn, path, profile)
    code = fn["instructions"]
    opcodes = profile.get("opcodes", {})
    rows, unknowns = [], []
    flow = confirmed(profile.get("control_flow", {}))
    captures = confirmed(profile.get("captures", {}))
    open_lists = confirmed(profile.get("open_lists", {}))
    numeric_loops = confirmed(profile.get("numeric_loops", {}))
    generic_loops = confirmed(profile.get("generic_loops", {}))
    if not confirmed(profile.get("instruction_layout", {})):
        unknowns.append({"reason": "instruction bit layout is not natively confirmed"})
    if fn["upvalue_count"] and not captures:
        unknowns.append({"reason": "captured upvalues are not yet reconstructed"})
    legacy_args=confirmed(profile.get("legacy_args",{})) and profile["legacy_args"].get("count_key")=="n"
    if fn["vararg_flags"] not in ((0,2,3,7) if legacy_args else (0,2,3)):
        unknowns.append({"reason": "unsupported vararg flags"})
    if fn["vararg_flags"]==7 and fn["parameter_count"]>=fn["maximum_stack_size"]:
        unknowns.append({"reason":"legacy argument table requires an in-frame implicit slot"})
    if fn["maximum_stack_size"] > 190:
        unknowns.append({"reason": "register-local emission limit exceeded"})

    def unknown(row, reason):
        unknowns.append({"pc": row["pc"], "reason": reason})
        row["status"] = "unsupported_operands"

    def literal(index, row):
        if not 0 <= index < len(fn["constants"]):
            raise ReconstructionError(f"{path} pc {row['pc']}: constant index outside pool")
        try:
            value=constant_literal(fn["constants"][index], profile)
            if fn["constants"][index]["type"]=="uint64":
                raw=fn["constants"][index].get("raw_hex")
                if raw is None:raw=f'{fn["constants"][index]["value"]:016x}'
                row.setdefault("uint64_constants",[]).append({"index":index,"serialized_hex":raw})
            return value
        except ReconstructionError as exc:
            unknown(row, str(exc))
            return "nil"  # Unemittable body; never emitted as substitute semantics.

    def operand(index, row):
        if index >= 256:
            return {"kind": "constant", "index": index & 255, "lua": literal(index & 255, row)}
        row["reads"].append(index)
        return {"kind": "register", "index": index}

    pc = 0
    while pc < len(code):
        ins = code[pc]
        spec = opcodes.get(str(ins["opcode"]), {})
        row = {"pc": pc, "file_offset": ins["file_offset"], "word_hex": ins["word_hex"],
               "opcode": ins["opcode"], "name": ins["opcode_name_provisional"],
               "A": ins["A"], "B": ins["B_raw"], "C": ins["C_raw"], "Bx": ins["Bx_raw"],
               "reads": [], "writes": [], "edge_writes": {}, "metadata_pcs": [],
               "metadata_words": [], "successors": None, "status": "unknown",
               "evidence": spec.get("evidence", [])}
        rows.append(row)
        if not confirmed(spec):
            unknowns.append({"pc": pc, "reason": "opcode semantics not confirmed", "opcode": ins["opcode"]})
            pc += 1
            continue
        kind = row["kind"] = spec["kind"]
        a, b, c, bx = row["A"], row["B"], row["C"], row["Bx"]
        skip = spec.get("inline_data_words", 0)
        tail=kind in {"tailcall","tailcall_cached"}
        if tail:skip=1
        if kind=="setlist" and not c: skip=1
        descriptor_count = 0
        if kind == "closure":
            if bx >= len(fn["children"]):
                raise ReconstructionError(f"{path} pc {pc}: closure target outside children")
            descriptor_count = fn["children"][bx]["upvalue_count"]
            skip = descriptor_count
        paired = kind in BRANCH_KINDS or kind == "tforloop"
        if paired:
            skip = 1
        next_pc = pc + 1 + skip
        if next_pc > len(code):
            raise ReconstructionError(f"{path} pc {pc}: inline data exceeds function")
        for data_pc in range(pc + 1, next_pc):
            raw = code[data_pc]
            if tail:
                if raw["opcode"]!=9 or raw["A"]!=a or raw["B_raw"]!=0:
                    raise ReconstructionError(f"{path} pc {pc}: tail call must own a matching open RETURN")
            elif paired:
                if raw["opcode"] != 28 or not confirmed(opcodes.get("28", {})):
                    raise ReconstructionError(f"{path} pc {pc}: conditional must own a confirmed JMP")
            elif kind != "closure" and raw["opcode"] != profile.get("inline_data_opcode"):
                raise ReconstructionError(f"{path} pc {pc}: expected inline DATA at {data_pc}")
            row["metadata_pcs"].append(data_pc)
            row["metadata_words"].append({"pc":data_pc,"file_offset":raw["file_offset"],"word_hex":raw["word_hex"]})
        slots = spec.get("inline_cache_constant_slots", 0)
        if slots:
            if not skip:
                raise ReconstructionError(f"{path} pc {pc}: cache-slot profile lacks payload")
            index = code[pc+1]["Bx_raw"]
            if index + slots > len(fn["constants"]):
                raise ReconstructionError(f"{path} pc {pc}: inline cache constant slots outside pool")
            row["cache_constant_indices"] = list(range(index,index+slots))
        row["status"] = "confirmed_static"
        row["successors"] = [next_pc] if next_pc < len(code) else []
        if paired:
            row["jump_target"] = pc + 2 + code[pc+1]["sBx_provisional"]
            row["fallthrough_target"] = pc + 2
            row["successors"] = list(dict.fromkeys([row["jump_target"], row["fallthrough_target"]]))
            if not flow:
                unknown(row,"control-flow semantics are not confirmed")
        if kind == "move":
            row.update(reads=[b], writes=[a])
        elif kind in ("loadk", "getglobal"):
            row.update(writes=[a], constant_index=bx, constant_lua=literal(bx,row))
        elif kind == "setglobal":
            row.update(reads=[a], constant_index=bx, constant_lua=literal(bx,row))
        elif kind in ("getfield_k", "getfield_cached_k"):
            if c>255:unknown(row,"field operand high flags are outside the admitted subset")
            if kind == "getfield_cached_k":
                previous = rows[-2] if len(rows)>1 else None
                ps = opcodes.get(str(previous["opcode"]),{}) if previous else {}
                if (c>255 or not previous
                        or previous.get("status")!="confirmed_static" or not ps.get("produces_cached_result")
                        or previous["A"]!=b):
                    unknown(row,"hidden last-result register relation is not established")
                else:
                    row["cached_result_producer_pc"] = previous["pc"]
                c &= 255
            c &= 255
            row.update(reads=[b],writes=[a],constant_index=c,constant_lua=literal(c,row))
            if fn["constants"][c]["type"]!="string":unknown(row,"field key must be a string constant")
        elif kind=="newtable":
            row.update(writes=[a],capacity_hint_bytes={"B":b,"C":c&255})
            def capacity(hint):return hint if hint<8 else ((hint&7)+8) << ((hint>>3)-1)
            row["decoded_capacities"]={"array":capacity(b),"hash":capacity(c&255)}
            if (b or c) and not confirmed(profile.get("table_constructors",{})):
                unknown(row,"nonzero NEWTABLE capacity hints are outside the admitted subset")
            if c>255:unknown(row,"NEWTABLE high hint flags are outside the admitted subset")
            if any(value>65536 for value in row["decoded_capacities"].values()):
                unknown(row,"NEWTABLE capacity exceeds bounded allocation-hint domain")
        elif kind in ("setfield","setfield_cached"):
            row["reads"]=[a]
            row["field_key"]=literal(b,row)
            if fn["constants"][b]["type"]!="string":
                unknown(row,"SETFIELD key is not a confirmed string constant")
            row["value_operand"]=operand(c,row)
            if kind=="setfield_cached":
                previous=rows[-2] if len(rows)>1 else None
                ps=opcodes.get(str(previous["opcode"]),{}) if previous else {}
                if (not previous or previous.get("status")!="confirmed_static"
                        or not ps.get("produces_cached_result") or previous["A"]!=a):
                    unknown(row,"hidden cached table is not established")
                else:row["cached_result_producer_pc"]=previous["pc"]
        elif kind=="gettable":
            row.update(reads=[b],writes=[a])
            row["key_operand"]=operand(c,row)
        elif kind=="self":
            row.update(reads=[b],writes=[a,a+1])
            row["key_operand"]=operand(c,row)
        elif kind=="settable":
            row["reads"]=[a]
            word=int(row["word_hex"],16)
            row["key_operand"]=operand((word>>17)&511,row)
            row["value_operand"]=operand(c,row)
        elif kind=="integer_negate":
            row.update(reads=[b],writes=[a])
        elif kind=="length":
            row.update(reads=[b],writes=[a])
        elif kind in {"integer_division","integer_add","integer_subtract","integer_multiply","integer_modulo","integer_power"}:
            word=int(row["word_hex"],16)
            row["writes"]=[a]
            row["left_operand"]=operand((word>>17)&511,row)
            row["right_operand"]=operand(c,row)
        elif kind=="setlist":
            if not confirmed(profile.get("table_lists",{})):
                unknown(row,"table list semantics are not confirmed")
            block=c if c else code[pc+1]["Bx_raw"]
            if not block:unknown(row,"SETLIST block zero is outside the admitted domain")
            row.update(reads=[a]+list(range(a+1,a+b+1)),list_block=block,open_top_effect=None)
            if not b:row["open_read_start"]=a+1
        elif kind in ("call_fixed", "call_cached_fixed", "tailcall", "tailcall_cached"):
            if c>255 or ((not b or not c) and not open_lists):
                unknown(row,"open call lists or high operand flags are unsupported")
            else:
                row["reads"] = list(range(a,a+b)) if b else [a]
                row["writes"] = list(range(a,fn["maximum_stack_size"])) if c and open_lists else list(range(a,a+c-1))
                row["result_count"] = c-1 if c else None
                row["clear_fixed_tail"] = open_lists
                if not b: row["open_read_start"] = a+1
                row["open_top_effect"] = a if not c else None
                row["may_writes"] = list(range(a,fn["maximum_stack_size"]))
                if not c: row["kills"] = list(range(a,fn["maximum_stack_size"]))
                if c and a+c-1>fn["maximum_stack_size"]:
                    unknown(row,"fixed result list extends outside frame")
            if tail:
                row["successors"]=[]
                if c:unknown(row,"tail call requires canonical all-result encoding")
            if kind in {"call_cached_fixed","tailcall_cached"}:
                previous=rows[-2] if len(rows)>1 else None
                ps=opcodes.get(str(previous["opcode"]),{}) if previous else {}
                if (not previous or previous.get("status")!="confirmed_static"
                        or not ps.get("produces_call_cached_result") or previous["A"]!=a):
                    unknown(row,"hidden cached callable is not established")
                else:
                    row["cached_result_producer_pc"]=previous["pc"]
        elif kind == "return_fixed":
            row["successors"]=[]
            if not b:
                if not open_lists: unknown(row,"open return list is unsupported")
                else: row["open_read_start"] = a
            else:
                row["reads"]=list(range(a,a+b-1))
        elif kind == "vararg":
            if not 0<=a<fn["maximum_stack_size"]:
                raise ReconstructionError(f"{path} pc {pc}: VARARG destination outside frame")
            if not open_lists or not (fn["vararg_flags"] & 2):
                unknown(row,"VARARG requires confirmed lists and a vararg function")
            if b:
                # Native fixed VARARG clears one slot beyond its B-1 results.
                row["writes"] = list(range(a,a+b))
                row["vararg_count"] = b-1
            else:
                row["open_top_effect"] = a
                row["may_writes"] = list(range(a,fn["maximum_stack_size"]))
        elif kind in ("forprep", "forloop"):
            if not numeric_loops: unknown(row,"numeric loop semantics are not confirmed")
            row["jump_target"] = pc+1+ins["sBx_provisional"]
            if kind == "forprep":
                row.update(reads=[a,a+1,a+2],writes=[a,a+1,a+2,a+3],successors=[row["jump_target"]])
            else:
                row.update(reads=[a,a+1,a+2],fallthrough_target=pc+1,
                           successors=list(dict.fromkeys([row["jump_target"],pc+1])))
                row["edge_writes"][str(row["jump_target"])]=[a,a+1,a+3]
        elif kind == "tforloop":
            if not generic_loops: unknown(row,"generic loop semantics are not confirmed")
            if not c or c>255: unknown(row,"generic loop requires 1..255 fixed results")
            row.update(reads=[a,a+1,a+2],writes=list(range(a+2,a+3+c)),
                       iterator_result_count=c,open_top_effect=None)
            if a+3+c>fn["maximum_stack_size"]:
                unknown(row,"generic iterator result list extends outside frame")
        elif kind in ("closure", "closure_no_upvalues"):
            if bx>=len(fn["children"]):
                raise ReconstructionError(f"{path} pc {pc}: closure target outside children")
            if fn["children"][bx]["upvalue_count"] and (not captures or kind!="closure"):
                unknown(row,"closure captured upvalues are unsupported")
            row.update(writes=[a],child_index=bx,captures=[])
            for n in range(descriptor_count):
                raw=code[pc+1+n]; flag=raw["A"]; index=raw["Bx_raw"]
                if flag not in (0,1):
                    unknown(row,"unknown closure capture descriptor kind")
                    continue
                limit=fn["maximum_stack_size"] if flag else fn["upvalue_count"]
                if index>=limit:
                    raise ReconstructionError(f"{path} pc {pc}: capture index outside parent scope")
                row["captures"].append({"kind":"register" if flag else "upvalue","index":index,
                                        "descriptor_pc":pc+1+n})
        elif kind in ("getupval", "setupval", "setupval_cached"):
            if not captures:
                unknown(row,"upvalue semantics are not confirmed")
            if b>=fn["upvalue_count"]:
                raise ReconstructionError(f"{path} pc {pc}: upvalue index outside function")
            row["upvalue_index"]=b
            if kind=="getupval":row["writes"]=[a]
            elif kind=="setupval":row["reads"]=[a]
            else:
                previous=rows[-2] if len(rows)>1 else None
                ps=opcodes.get(str(previous["opcode"]),{}) if previous else {}
                if (not previous or previous.get("status")!="confirmed_static"
                        or not ps.get("produces_cached_result") or previous["A"]!=a):
                    unknown(row,"hidden cached value for SETUPVAL_R1 is not established")
                else:row["cached_result_producer_pc"]=previous["pc"]
                row["reads"]=[a]
        elif kind=="close":
            if not captures:unknown(row,"upvalue-close semantics are not confirmed")
            if a>=fn["maximum_stack_size"]:
                raise ReconstructionError(f"{path} pc {pc}: close threshold outside stack")
        elif kind=="jump":
            row["successors"]=[pc+1+ins["sBx_provisional"]]
            if not flow:unknown(row,"control-flow semantics are not confirmed")
        elif kind in ("test_branch","test_cached_branch"):
            if c not in (0,1):unknown(row,"truth-test polarity outside admitted boolean range")
            row["reads"]=[a]
            if kind=="test_cached_branch":
                previous=rows[-2] if len(rows)>1 else None
                ps=opcodes.get(str(previous["opcode"]),{}) if previous else {}
                if not previous or not ps.get("produces_test_cached_result") or previous["A"]!=a:
                    unknown(row,"hidden truth-test cached result is not established")
                else:row["cached_result_producer_pc"]=previous["pc"]
        elif kind=="testset_branch":
            if c not in (0,1):unknown(row,"truth-test polarity outside admitted boolean range")
            row["reads"]=[b]
            row["conditional_write"]=a
            if row["jump_target"]!=row["fallthrough_target"]:
                row["edge_writes"][str(row["jump_target"])]=[a]
        elif kind in ("eq_branch","lt_branch","le_branch"):
            if a not in (0,1):unknown(row,"comparison polarity outside admitted boolean range")
            word=int(row["word_hex"],16)
            row["left_operand"]=operand((word>>17)&511,row)
            row["right_operand"]=operand(c,row)
        elif kind=="loadbool":
            if b not in (0,1) or c>255:unknown(row,"boolean load operands outside admitted range")
            row.update(writes=[a],boolean_value=bool(b))
            row["successors"]=[pc+1+c]
        elif kind=="loadnil":
            if b<a:unknown(row,"reversed nil-load register range")
            row["writes"]=list(range(a,b+1))
        elif kind=="concat":
            if c>255 or b>c:
                unknown(row,"CONCAT requires a nonempty ascending B8..C8 range")
            row.update(reads=list(range(b,c+1)),writes=[a])
        elif kind in {"not","not_cached"}:
            row.update(reads=[b],writes=[a])
            if kind=="not_cached" and not confirmed(profile.get("cached_dataflow",{})):
                unknown(row,"hidden cached NOT operand lacks a native alias proof")
        else:
            unknown(row,"semantic kind not implemented by extended lifter")
        for reg in row["reads"]+row["writes"]+([row["conditional_write"]] if "conditional_write" in row else []):
            if not 0<=reg<fn["maximum_stack_size"]:
                raise ReconstructionError(f"{path} pc {pc}: register {reg} outside stack")
        pc=next_pc

    by_pc={r["pc"]:r for r in rows}
    predecessors={pc:set() for pc in by_pc}
    for row in rows:
        for target in row["successors"] or []:
            if target not in by_pc:
                raise ReconstructionError(f"{path} pc {row['pc']}: edge enters inline data or leaves code")
            predecessors[target].add(row["pc"])
    reachable=set(); pending=[0] if rows else []
    while pending:
        pc=pending.pop()
        if pc in reachable:continue
        reachable.add(pc);pending.extend(by_pc[pc]["successors"] or [])
    uncertain_reachability=any(by_pc[pc]["successors"] is None for pc in reachable)
    for row in rows:
        row["reachability"]=("reachable" if row["pc"] in reachable else "unknown" if uncertain_reachability else "unreachable")
        row["reachable"]=True if row["pc"] in reachable else None if uncertain_reachability else False
        if not row["reachable"]:continue
        producer=row.get("cached_result_producer_pc")
        if producer is not None and predecessors[row["pc"]]&reachable != {producer}:
            unknown(row,"branch bypasses cached-result producer")
        if row["successors"]==[] and row.get("kind") not in {"return_fixed","tailcall","tailcall_cached"}:
            unknown(row,"reachable function path falls off code")
    unknowns=[u for u in unknowns if "pc" not in u or u["pc"] in reachable or uncertain_reachability]
    for issue in unknowns:
        if "pc" in issue:issue["reachability"]=by_pc[issue["pc"]]["reachability"]
    # A dynamic list has a proven first register, but an unknown exact length.
    # Carry every possible base through joins; a consumer requires one base on
    # every incoming path. None denotes entry/fixed-call top, not an open list.
    tops={pc:set() for pc in reachable}
    if 0 in tops: tops[0].add(None)
    changed=True
    while changed:
        changed=False
        for pc in sorted(reachable):
            row=by_pc[pc]
            state={row["open_top_effect"]} if "open_top_effect" in row else tops[pc]
            for target in row["successors"] or []:
                new=tops[target]|state
                if new!=tops[target]:tops[target]=new;changed=True
    for pc in sorted(reachable):
        row=by_pc[pc]
        if row.get("kind")=="setlist":
            bases={base for base in tops[pc] if base is not None}
            if bases:row["may_writes"]=list(range(min(bases),fn["maximum_stack_size"]))
            if len(tops[pc])==1 and bases:
                row["writes"]=list(range(next(iter(bases)),fn["maximum_stack_size"]))
        if row.get("kind") in {"tforloop","concat"} and tops[pc]!={None}:
            unknown(row,"temporary stack overlaps an open list")
        if "open_read_start" not in row:continue
        starts=tops[pc]
        if len(starts)!=1 or None in starts or next(iter(starts))<row["open_read_start"]:
            unknown(row,"open list lacks a compatible producer on every incoming path")
        else:
            base=next(iter(starts))
            row["open_list_base"]=base
            row["reads"].extend(range(row["open_read_start"],base))

    if confirmed(profile.get("cached_dataflow", {})):
        from cache_flow import analyze_cache_aliases
        proofs=analyze_cache_aliases(rows,profile,fn["maximum_stack_size"])
        old_cache_reasons={
            "hidden last-result register relation is not established",
            "hidden cached table is not established",
            "hidden cached callable is not established",
            "hidden truth-test cached result is not established",
            "hidden cached value for SETUPVAL_R1 is not established",
            "branch bypasses cached-result producer"}
        for pc,proof in proofs.items():
            row=by_pc[pc];row.update(proof)
            if proof["cache_consumer_register"] is None:continue
            if proof["cache_register_proven"]:
                unknowns=[u for u in unknowns if not (u.get("pc")==pc and u["reason"] in old_cache_reasons)]
                if not any(u.get("pc")==pc for u in unknowns) and confirmed(opcodes.get(str(row["opcode"]),{})):
                    row["status"]="confirmed_static"
            else:
                unknown(row,"hidden cached operand lacks a register alias on every incoming path")

    # FORPREP installs an internal tagged counter, not a public Lua number.
    # Initially admit canonical compiler pairs and prohibit bypassed entries or
    # body writes to that counter. Other register mutations retain native order.
    loops={}
    for row in rows:
        if row.get("kind")!="forprep" or row["pc"] not in reachable:continue
        target=by_pc.get(row["jump_target"])
        if (not target or target.get("kind")!="forloop" or target["A"]!=row["A"]
                or target["pc"]<=row["pc"] or target["jump_target"]!=row["pc"]+1):
            unknown(row,"numeric loop lacks a canonical matching FORLOOP")
            continue
        prep,end,a=row["pc"],target["pc"],row["A"]
        if any(cap["kind"]=="register" and cap["index"]==a+1
               for other in rows if other["pc"] in reachable for cap in other.get("captures",[])):
            unknown(row,"numeric loop counter register is captured by a closure")
        if end in loops:
            unknown(row,"numeric loop has multiple preparation entries")
            continue
        loops[end]=prep
        row["loop_id"]=target["loop_id"]=prep
        for body in rows:
            if not prep<body["pc"]<=end or body["pc"] not in reachable:continue
            if any(pred<prep or pred>end or (pred==prep and body["pc"]!=end)
                   for pred in predecessors[body["pc"]]&reachable):
                unknown(body,"branch bypasses numeric loop preparation")
            written=set(body["writes"])|set(body.get("may_writes",[]))
            written.update(reg for regs in body["edge_writes"].values() for reg in regs)
            if a+1 in written and body is not target:
                unknown(body,"numeric loop internal counter is overwritten in its body")
    for row in rows:
        if row.get("kind")=="forloop" and row["pc"] in reachable and row["pc"] not in loops:
            unknown(row,"FORLOOP lacks a proven preparation")
    tags={pc:set() for pc in reachable}
    changed=True
    while changed:
        changed=False
        for pc in sorted(reachable):
            row=by_pc[pc]
            state=tags[pc]-set(row["writes"])
            if row.get("kind")=="forprep":state.add(row["A"]+1)
            for target in row["successors"] or []:
                new=tags[target]|state
                if new!=tags[target]:tags[target]=new;changed=True
    for pc in sorted(reachable):
        row=by_pc[pc]
        reads=set(row["reads"])|{cap["index"] for cap in row.get("captures",[]) if cap["kind"]=="register"}
        if row.get("kind")=="forloop" and "loop_id" in row:reads.discard(row["A"]+1)
        if reads&tags[pc]:unknown(row,"internal numeric loop counter escapes to an ordinary value")
    # Native callees reuse the caller's outgoing register window. An open
    # upvalue into that window could observe transient native scratch values;
    # isolated generated invocations cannot reproduce that aliasing.
    live_captures={pc:set() for pc in reachable}
    changed=True
    while changed:
        changed=False
        for pc in sorted(reachable):
            row=by_pc[pc]
            state=live_captures[pc]|{cap["index"] for cap in row.get("captures",[]) if cap["kind"]=="register"}
            if row.get("kind")=="close":state={r for r in state if r<row["A"]}
            for target in row["successors"] or []:
                new=live_captures[target]|state
                if new!=live_captures[target]:live_captures[target]=new;changed=True
    for pc in sorted(reachable):
        row=by_pc[pc]
        if row.get("kind") in {"call_fixed","call_cached_fixed","tailcall","tailcall_cached"} and any(r>=row["A"] for r in live_captures[pc]):
            unknown(row,"callee register window aliases an open captured cell")
    universe=set(range(fn["maximum_stack_size"]))
    initial=set(range(fn["parameter_count"]))
    if (fn["vararg_flags"] in (2,3) or (legacy_args and fn["vararg_flags"]==7)) and fn["parameter_count"]<fn["maximum_stack_size"]:
        initial.add(fn["parameter_count"])  # Native implicit slot: nil for 2/3, fresh arg table for 7.
    inputs={pc:(initial.copy() if pc==0 else universe.copy()) for pc in reachable}
    changed=True
    while changed:
        changed=False
        for pc in sorted(reachable):
            incoming=[]
            if pc==0:incoming.append(initial)
            for pred in predecessors[pc]&reachable:
                r=by_pc[pred]
                incoming.append((inputs[pred]-set(r.get("kills",[])))|set(r["writes"])|set(r["edge_writes"].get(str(pc),[])))
            new=set.intersection(*incoming) if incoming else set()
            if new!=inputs[pc]:inputs[pc]=new;changed=True
    for pc in sorted(reachable):
        row=by_pc[pc];row["definitely_initialized_in"]=sorted(inputs[pc])
        missing=set(row["reads"])-inputs[pc]
        if missing:unknowns.append({"pc":pc,"reason":"register read before a known definition on every path","registers":sorted(missing)})
        capture_missing={cap["index"] for cap in row.get("captures",[]) if cap["kind"]=="register"} - inputs[pc] - {row["A"]}
        if capture_missing:
            unknowns.append({"pc":pc,"reason":"captured register lacks a known initial value","registers":sorted(capture_missing)})
    if not rows:unknowns.append({"reason":"empty function body"})
    leaders={0} if rows else set()
    for row in rows:
        successors=row["successors"]
        if successors is None or row.get("kind") in BRANCH_KINDS|{"jump","return_fixed","loadbool","forprep","forloop","tforloop"}:
            leaders.update(successors or [])
            following=row["pc"]+1+len(row["metadata_pcs"])
            if following in by_pc:leaders.add(following)
    blocks=[]
    for row in rows:
        if not blocks or row["pc"] in leaders:blocks.append({"start_pc":row["pc"],"instruction_pcs":[]})
        blocks[-1]["instruction_pcs"].append(row["pc"])
        blocks[-1]["successors"]=row["successors"]
    children=[lift_function(child,path+"/"+str(n),profile) for n,child in enumerate(fn["children"])]
    return {"path":path,"parameter_count":fn["parameter_count"],"maximum_stack_size":fn["maximum_stack_size"],
            "vararg_flags":fn["vararg_flags"],"upvalue_count":fn["upvalue_count"],"instructions":rows,
            "blocks":blocks,"unknowns":unknowns,"body_emittable":not unknowns,"children":children,
            "requires_uint64_adapter":any(r.get("uint64_constants") for r in rows if r.get("reachable") is not False),
            "extended":True,"emission_form":"program-counter dispatcher with shared cells",
            "external_upvalue_cells_required":fn["upvalue_count"],
            "runtime_guards":
                (["Primitive equality only; numeric inputs must be signed 32-bit integers"]
                 if any(r.get("kind") in {"eq_branch","lt_branch","le_branch"} for r in rows) else [])
                +(["Table reads/writes require ordinary Lua tables without metatables; keys must be strings or signed-int32 numbers"]
                  if any(r.get("kind") in {"gettable","setfield","setfield_cached"} for r in rows) else [])}


def emit_function(ir, indent=0, upvalue_name=None):
    if not ir.get("extended"):
        return emit_function_legacy(ir,indent)
    if ir.get("upvalue_count") and upvalue_name is None:
        pad="  "*indent
        body=emit_function(ir,indent+1,"__uv")
        return ["function(__uv)",pad+"  -- Capture factory: zero-indexed shared cells {value=...} required.",
                pad+"  return "+body[0],*body[1:],pad+"end"]
    pad="  "*indent
    params=[f"r{i}" for i in range(ir["parameter_count"])]
    if ir["vararg_flags"]&2:params.append("...")
    lines=["function("+", ".join(params)+")"]
    if not ir["body_emittable"]:
        reasons="; ".join(dict.fromkeys(u["reason"] for u in ir["unknowns"]))
        lines += [pad+"  -- UNRESOLVED function "+ir["path"]+": "+reasons,
                  pad+"  __unresolved("+lua_bytes(("Unresolved Amalur function "+ir["path"]).encode().hex())+")",pad+"end"]
        return lines
    if ir.get("requires_uint64_adapter"):
        lines += [pad+"  -- Host must share one amalur_uint64 adapter per Lua realm; type11 remains opaque.",
                  pad+"  local function __uint64(raw)",
                  pad+"    local adapter=__getfenv(0).__amalur_uint64",
                  pad+'    if __type(adapter)~="table" or __type(adapter.from_hex)~="function" or __type(adapter.is)~="function" or __type(adapter.hex)~="function" then __unresolved("Amalur uint64 adapter required") end',
                  pad+"    local token=adapter.from_hex(raw)",
                  pad+'    if __type(token)~="userdata" or not adapter.is(token) or adapter.hex(token)~=raw:sub(1,15).."b" then __unresolved("Invalid Amalur uint64 adapter result") end',
                  pad+"    return token",pad+"  end"]
    lines.append(pad+"  -- Explicit PC dispatch preserves native edges; shared cells preserve capture aliases.")
    values=[f"[{i}] = {{value = "+(f"r{i}" if i<ir["parameter_count"] else "nil")+"}" for i in range(ir["maximum_stack_size"])]
    lines.append(pad+"  local __r = {"+", ".join(values)+"}")
    active=[row for row in ir["instructions"] if row.get("reachable",True)]
    large=len(active)>1000
    lists=large or ir["vararg_flags"]==7 or any(r.get("kind") in {"vararg","tforloop","setlist"} or "open_read_start" in r
              or (r.get("kind") in {"call_fixed","call_cached_fixed"} and not r["C"]) for r in active)
    loops=any(r.get("kind") in {"forprep","forloop","concat"} or r.get("kind","").startswith("integer_") for r in active)
    lines.append(pad+"  local __top")
    if lists:
        lines += [pad+"  local __select, __unpack = __getfenv(0).select, __getfenv(0).unpack",
                  pad+"  local function __pack(...) return {n=__select('#', ...), ...} end",
                  pad+"  local function __put(base, values, count)",
                  pad+'    if count < 0 or count > 32767 then __unresolved("Amalur list count outside admitted frame domain") end',
                  pad+"    for i=0,count-1 do local cell=__r[base+i]; if not cell then cell={}; __r[base+i]=cell end; cell.value=values[i+1] end",
                  pad+"  end",
                  pad+"  local function __list(first)",
                  pad+'    if __top == nil or __top < first or __top-first > 32767 then __unresolved("Invalid Amalur open-list top") end',
                  pad+"    local values={}; for i=first,__top-1 do values[i-first+1]=__r[i].value end",
                  pad+"    return __unpack(values,1,__top-first)",
                  pad+"  end"]
        if ir["vararg_flags"]&2:
            lines += [pad+"  local __va = __pack(...)",
                      pad+'  if __va.n > 32767 then __unresolved("Amalur vararg count outside signed frame domain") end']
            if ir["vararg_flags"]==7:
                lines += [pad+"  local __arg = {n=__va.n}",
                          pad+"  for __i=1,__va.n do __arg[__i]=__va[__i] end",
                          pad+f"  __r[{ir['parameter_count']}].value=__arg"]
    if loops:
        lines += [pad+"  local __loops = {}",
                  pad+"  local function __integer(value)",
                  pad+'    if __type(value) ~= "number" or value < -2147483648 or value > 2147483647 or value % 1 ~= 0 then __unresolved("Unmodeled Amalur numeric-loop domain") end',
                  pad+"    return value == 0 and 0 or value",
                  pad+"  end",
                  pad+"  local function __wrap(value) return (value+2147483648)%4294967296-2147483648 end",
                  pad+"  local function __multiply(left, right)",
                  pad+"    left=left%4294967296; right=right%4294967296",
                  pad+"    local al, bl=left%65536, right%65536; local ah, bh=(left-al)/65536, (right-bl)/65536",
                  pad+"    return __wrap(al*bl + ((al*bh+ah*bl)%65536)*65536)",pad+"  end"]
    if any(r.get("kind")=="concat" for r in active):
        lines += [pad+"  local function __decimal(value)",
                  pad+"    value=__integer(value); if value==0 then return '0' end",
                  pad+"    local negative=value<0; if negative then value=-value end",
                  pad+"    local digits={[0]='0','1','2','3','4','5','6','7','8','9'}; local result=''",
                  pad+"    while value>0 do local digit=value%10; result=digits[digit]..result; value=(value-digit)/10 end",
                  pad+"    return (negative and '-' or '')..result",pad+"  end"]
    if large:lines.append(pad+"  local __setfenv = __getfenv(0).setfenv")
    lines.append(pad+"  local __pc = 0")
    if not large:lines.append(pad+"  while true do")
    case_starts=[]
    def reg(i):return f"__r[{i}].value"
    def operand(value):return reg(value["index"]) if value["kind"]=="register" else value["lua"]
    for n,row in enumerate(active):
        case_starts.append(len(lines))
        level=pad+"      ";a,b,c=row["A"],row["B"],row["C"];kind=row["kind"]
        lines.append(pad+"    "+("if" if n==0 else "elseif")+f" __pc == {row['pc']} then")
        lines.append(level+f"-- file 0x{row['file_offset']:x}: {row['name']}")
        statements=[];transition=True
        if kind=="move":statements=[f"{reg(a)} = {reg(b)}"]
        elif kind=="loadk":statements=[f"{reg(a)} = {row['constant_lua']}"]
        elif kind=="getglobal":statements=[f"{reg(a)} = __getfenv(1)[{row['constant_lua']}]"]
        elif kind=="setglobal":statements=[f"__getfenv(1)[{row['constant_lua']}] = {reg(a)}"]
        elif kind in ("getfield_k","getfield_cached_k"):
            statements=[f'if __type({reg(b)}) ~= "table" or __getmetatable({reg(b)}) ~= nil then __unresolved("Unmodeled Amalur field domain") end',
                        f"{reg(a)} = {reg(b)}[{row['constant_lua']}]"]
        elif kind=="newtable":statements=[reg(a)+" = {}"]
        elif kind=="length":
            statements=[f"local __value = {reg(b)}",
                        'if __type(__value) == "string" then',f"  {reg(a)} = #__value",
                        'elseif __type(__value) == "table" and __getmetatable(__value) == nil then',
                        "  local __count, __maximum = 0, 0",
                        "  for __key in __getfenv(0).next, __value do",
                        '    if __type(__key) == "number" and __key >= 1 and __key % 1 == 0 then',
                        '      if __key > 2147483647 then __unresolved("Unmodeled Amalur length key") end',
                        "      __count=__count+1; if __key>__maximum then __maximum=__key end",
                        "    end","  end",
                        '  if __count ~= __maximum then __unresolved("Unmodeled sparse Amalur length") end',
                        f"  {reg(a)} = __count",'else __unresolved("Unmodeled Amalur length domain") end']
        elif kind=="integer_division":
            statements=[f"local __left, __right = __integer({operand(row['left_operand'])}), __integer({operand(row['right_operand'])})",
                        'if __right == 0 or (__left == -2147483648 and __right == -1) then __unresolved("Amalur integer division trap") end',
                        "local __quotient = __left/__right",
                        "if __quotient < 0 then __quotient = -((-__quotient)-((-__quotient)%1)) else __quotient = __quotient-(__quotient%1) end",
                        reg(a)+" = __quotient == 0 and 0 or __quotient"]
        elif kind in {"integer_add","integer_subtract","integer_multiply","integer_modulo","integer_power"}:
            statements=[f"local __left, __right = __integer({operand(row['left_operand'])}), __integer({operand(row['right_operand'])})"]
            if kind=="integer_add":statements += [reg(a)+" = __wrap(__left+__right)"]
            elif kind=="integer_subtract":statements += [reg(a)+" = __wrap(__left-__right)"]
            elif kind=="integer_multiply":statements += [reg(a)+" = __multiply(__left,__right)"]
            elif kind=="integer_modulo":
                statements += ['if __right == 0 or (__left == -2147483648 and __right == -1) then __unresolved("Amalur integer remainder trap") end',
                               "local __magnitude = (__left < 0 and -__left or __left) % (__right < 0 and -__right or __right)",
                               reg(a)+" = __magnitude == 0 and 0 or (__left < 0 and -__magnitude or __magnitude)"]
            else:
                statements += ["local __result, __base, __exponent = 1, __left, __right",
                               "if __exponent < 0 then __result=0 else",
                               "  while __exponent > 0 do",
                               "    local __odd=__exponent%2; if __odd==1 then __result=__multiply(__result,__base) end",
                               "    __exponent=(__exponent-__odd)/2; if __exponent>0 then __base=__multiply(__base,__base) end",
                               "  end","end",reg(a)+" = __result"]
        elif kind=="integer_negate":statements=[reg(a)+f" = __wrap(-__integer({reg(b)}))"]
        elif kind=="setlist":
            statements=[f"local __table = {reg(a)}",
                        'if __type(__table) ~= "table" or __getmetatable(__table) ~= nil then __unresolved("Unmodeled Amalur list table") end']
            count=str(b) if b else f"(__top-{a+1})"
            if not b:statements += [f'if __top == nil or __top < {a+1} then __unresolved("Invalid Amalur SETLIST top") end']
            statements += [f"local __count = {count}",
                           'if __count < 0 or __count > 32767 then __unresolved("Unmodeled Amalur list size") end',
                           f"for __i=1,__count do __table[{(row['list_block']-1)*50}+__i]=__r[{a}+__i].value end",
                           f"if __top ~= nil then for __i=__top,{ir['maximum_stack_size']-1} do __r[__i].value=nil end end",
                           "__top = nil"]
        elif kind in ("setfield","setfield_cached","gettable","settable","self"):
            table=reg(b if kind in {"gettable","self"} else a)
            key=operand(row["key_operand"]) if kind in {"gettable","settable","self"} else row["field_key"]
            lines.append(level+"local __table, __key = "+table+", "+key)
            lines.append(level+'if __type(__table) ~= "table" or __getmetatable(__table) ~= nil then __unresolved("Unmodeled Amalur table domain") end')
            lines.append(level+'local __kt = __type(__key)')
            lines.append(level+'if not (__kt == "string" or (__kt == "number" and __key >= -2147483648 and __key <= 2147483647 and __key % 1 == 0)) then __unresolved("Unmodeled Amalur table-key domain") end')
            if kind=="self":
                statements=['if __kt ~= "string" then __unresolved("Unmodeled Amalur method key") end',
                            reg(a+1)+" = __table",reg(a)+" = __table[__key]"]
            elif kind=="gettable":statements=[reg(a)+" = __table[__key]"]
            else:statements=["__table[__key] = "+operand(row["value_operand"])]
        elif kind in ("call_fixed","call_cached_fixed"):
            args=", ".join(reg(i) for i in range(a+1,a+b)) if b else f"__list({a+1})"
            call=reg(a)+"("+args+")"
            statements=[f'if __type({reg(a)}) ~= "function" then __unresolved("Unmodeled Amalur callable domain") end']
            if not c:
                statements += ["local __values = __pack("+call+")",f"__put({a}, __values, __values.n)",f"__top = {a}+__values.n"]
            else:
                statements += [(" , ".join(reg(i) for i in range(a,a+c-1))+" = " if c>1 else "")+call]
                if row.get("clear_fixed_tail"):
                    statements += [f"for __i={a+c-1},{ir['maximum_stack_size']-1} do __r[__i].value=nil end"]
                statements += ["__top = nil"]
        elif kind in {"tailcall","tailcall_cached"}:
            args=", ".join(reg(i) for i in range(a+1,a+b)) if b else f"__list({a+1})"
            statements=[f'if __type({reg(a)}) ~= "function" then __unresolved("Unmodeled Amalur tail-call domain") end',
                        "return "+reg(a)+"("+args+")"]
            transition=False
        elif kind=="return_fixed":
            statements=[f"return __list({a})"] if not b else ["return"+(" "+", ".join(reg(i) for i in range(a,a+b-1)) if b>1 else "")]
            transition=False
        elif kind=="vararg":
            if b:
                statements=[f"__put({a}, __va, {b-1})",f"{reg(a+b-1)} = nil"]
            else:
                statements=[f"__put({a}, __va, __va.n)",f"__top = {a}+__va.n"]
        elif kind=="forprep":
            statements=[f"local __start, __limit, __step = __integer({reg(a)}), __integer({reg(a+1)}), __integer({reg(a+2)})",
                        "local __difference = __wrap(__limit-__start)",
                        'if __step == 0 or (__difference == -2147483648 and __step == -1) then __unresolved("Amalur numeric-loop division trap") end',
                        "local __quotient = __difference/__step",
                        "if __quotient < 0 then __quotient = -((-__quotient)-((-__quotient)%1)) else __quotient = __quotient-(__quotient%1) end",
                        "if __quotient < 0 or __quotient > 1073741823 then __quotient = -1 end",
                        f"__loops[{row['loop_id']}] = __quotient+1",
                        f"{reg(a)} = __wrap(__start-__step)",f"{reg(a+1)} = nil -- native internal counter is kept private",
                        f"{reg(a+2)}, {reg(a+3)} = __step, __start"]
        elif kind=="forloop":
            statements=[f"local __count = __loops[{row['loop_id']}]",
                        'if __count == nil then __unresolved("Numeric loop lacks preparation") end',
                        "if __count > 0 then",
                        f"  local __next = __wrap(__integer({reg(a)})+__integer({reg(a+2)}))",
                        f"  __loops[{row['loop_id']}] = __count-1",
                        f"  {reg(a)}, {reg(a+3)} = __next, __next",
                        f"  __pc = {row['jump_target']}","else",f"  __pc = {row['fallthrough_target']}","end"]
            transition=False
        elif kind=="tforloop":
            statements=[f'if __type({reg(a)}) ~= "function" then __unresolved("Unmodeled Amalur iterator domain") end',
                        f"local __values = __pack({reg(a)}({reg(a+1)}, {reg(a+2)}))",
                        f"__put({a+3}, __values, {c})",
                        f"{reg(a+2)} = {reg(a+3)}","__top = nil",
                        f"if {reg(a+3)} ~= nil then __pc = {row['jump_target']} else __pc = {row['fallthrough_target']} end"]
            transition=False
        elif kind in ("closure","closure_no_upvalues"):
            child=ir["children"][row["child_index"]]
            if row.get("captures"):
                cells=[f"[{i}] = "+(f"__r[{cap['index']}]" if cap["kind"]=="register" else f"{upvalue_name}[{cap['index']}]") for i,cap in enumerate(row["captures"])]
                body=emit_function(child,indent+4,"__uv")
                lines.append(level+f"{reg(a)} = (function(__uv)")
                lines.append(level+"  return "+body[0]);lines.extend(body[1:])
                lines.append(level+"end)({"+", ".join(cells)+"})")
            else:
                body=emit_function(child,indent+3)
                lines.append(level+reg(a)+" = "+body[0]);lines.extend(body[1:])
        elif kind=="getupval":statements=[f"{reg(a)} = {upvalue_name}[{b}].value"]
        elif kind in ("setupval","setupval_cached"):
            statements=[f"{upvalue_name}[{b}].value = {reg(a)}"]
        elif kind=="close":statements=[f"for __i = {a}, {ir['maximum_stack_size']-1} do __r[__i] = {{value = __r[__i].value}} end"]
        elif kind=="jump":statements=[f"__pc = {row['successors'][0]}"];transition=False
        elif kind in BRANCH_KINDS:
            if kind in ("test_branch","test_cached_branch","testset_branch"):
                truth=f"(not not {reg(b if kind=='testset_branch' else a)})"
                condition=truth+" == "+("true" if c else "false")
            else:
                relation={"eq_branch":"==","lt_branch":"<","le_branch":"<="}[kind]
                left,right=operand(row["left_operand"]),operand(row["right_operand"])
                lines.append(level+"local __left, __right = "+left+", "+right)
                lines.append(level+"local __lt, __rt = __type(__left), __type(__right)")
                def primitive(value,typ):
                    return f'({typ} == "nil" or {typ} == "boolean" or {typ} == "string" or ({typ} == "number" and {value} >= -2147483648 and {value} <= 2147483647 and {value} % 1 == 0))'
                admitted=primitive("__left","__lt")+" and "+primitive("__right","__rt")
                if kind!="eq_branch":admitted+=' and __lt == __rt and (__lt == "number" or __lt == "string")'
                lines.append(level+'if not ('+admitted+') then __unresolved("Unmodeled Amalur comparison domain") end')
                condition="(__left "+relation+" __right) == "+("true" if a else "false")
            statements=["if "+condition+" then"]
            if kind=="testset_branch":statements.append("  "+reg(a)+" = "+reg(b))
            statements += ["  __pc = "+str(row["jump_target"]),"else","  __pc = "+str(row["fallthrough_target"]),"end"]
            transition=False
        elif kind=="loadbool":statements=[reg(a)+" = "+("true" if row["boolean_value"] else "false")]
        elif kind=="loadnil":statements=[", ".join(reg(i) for i in range(a,b+1))+" = "+", ".join("nil" for i in range(a,b+1))]
        elif kind=="concat":
            if b==c:statements=[reg(a)+" = "+reg(b)]
            else:
                statements=["local __joined = ''", f"for __i={b},{c} do local __value=__r[__i].value",
                            '  if __type(__value)=="number" then __value=__decimal(__value) elseif __type(__value)~="string" then __unresolved("Unmodeled Amalur CONCAT domain") end',
                            "  __joined=__joined..__value", "end", reg(a)+" = __joined"]
        elif kind in {"not","not_cached"}:statements=[reg(a)+" = not "+reg(b)]
        else:raise ReconstructionError("unsupported extended emitter kind: "+kind)
        lines.extend(level+statement for statement in statements)
        if transition:lines.append(level+"__pc = "+str(row["successors"][0]))
    if large:
        boundaries=case_starts+[len(lines)]
        cases=[(row["pc"],lines[boundaries[i]:boundaries[i+1]]) for i,row in enumerate(active)]
        groups=[cases[i:i+64] for i in range(0,len(cases),64)]
        lines=lines[:case_starts[0]]
        lines += [pad+"  local __env = __getfenv(1)",pad+"  local __blocks = {}",
                  pad+"  local __bounds = {"+", ".join(str(group[0][0]) for group in groups)+"}",
                  pad+"  local function __dispatch()",
                  pad+f"    local lo, hi = 1, {len(groups)}",
                  pad+"    while lo < hi do local mid=(lo+hi+1)/2; mid=mid-mid%1; if __pc < __bounds[mid] then hi=mid-1 else lo=mid end end",
                  pad+"    __setfenv(__blocks[lo], __env)",pad+"    return __blocks[lo]()",pad+"  end"]
        for group_index,group in enumerate(groups,1):
            lines.append(pad+f"  __blocks[{group_index}] = function()")
            for index,(_,body) in enumerate(group):
                first=body[0].replace("elseif", "if", 1) if index==0 else body[0]
                lines += [first]+body[1:]
            lines += [pad+"    else",pad+'      __unresolved("Invalid reconstructed program counter")',pad+"    end",
                      pad+"    __env = __getfenv(1)",pad+"    return __dispatch()",pad+"  end"]
        lines += [pad+"  local __results = __pack(__dispatch())",
                  pad+"  __setfenv(1, __env)",
                  pad+"  return __unpack(__results, 1, __results.n)",pad+"end"]
    else:
        lines += [pad+"    else",pad+"      __unresolved(\"Invalid reconstructed program counter\")",pad+"    end",pad+"  end",pad+"end"]
    return lines


def reconstruct(parsed, profile):
    check_profile(profile)
    root = lift_function(parsed["chunk"]["root_function"], "0", profile)
    if root.get("extended") and root.get("upvalue_count"):
        root["unknowns"].append({"reason":"root script has unbound captured cells"})
        root["body_emittable"]=False
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
                          "Branches and loops use explicit PC dispatch; open lists require proven stack-top provenance.",
                          "Captured cells preserve aliases; comparison guards reject unmodeled custom types and non-int32 numbers.",
                          "Generated code has not been executed in the game."]}
    header = ["-- Opem Amalur: initial register-level Lua 5.1 reconstruction.",
              "-- Input SHA-256: " + parsed["input_sha256"],
              "-- Static interpretation; not original source or runtime-equivalence proof.",
              "-- Unresolved function bodies are explicit error stubs, never silent no-ops.",
              "-- Requires Lua 5.1 getfenv semantics; names r0... are generated registers.",
              "local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable", ""]
    body = emit_function(root,upvalue_name="__unbound_root" if root.get("upvalue_count") else None)
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
