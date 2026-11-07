"""Bounded structural reader for the observed Amalur Havok Script 0x08 profile.

This is a structural parser and provisional bytecode listing, not a Lua
decompiler or a runtime verifier. Layout and opcode names have been corroborated
against the hash-bound Re-Reckoning native reader and opcode metadata table.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
from dataclasses import dataclass

REFERENCE_BINARY_SHA256 = "16a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314"
NATIVE_EVIDENCE = {
    "kind": "native_static",
    "binary_sha256": REFERENCE_BINARY_SHA256,
    "header_reader": "0x010c5df0",
    "function_reader": "0x010c1730",
    "constant_reader": "0x010c1190",
    "number_reader": "0x0109bf90",
    "opcode_metadata": "0x01973560",
    "interpreter": "0x010adce0",
    "format_evidence_id": "ev_d0e99c481093460073683be4ca4ac0f83e732b0a66a6eef6daed2c8204e59a43",
    "opcode_evidence_id": "ev_165a047ff1c9b54ef2dca71da1038a3aad11c3e4407556c372765509dc168336",
}

SOURCE_REFERENCES = [
    "https://github.com/Kender2/amalur/blob/master/korevm.md",
    "https://github.com/Jake-NotTheMuss/hksc/blob/master/src/lundump.c",
    "https://github.com/Jake-NotTheMuss/hksc/blob/master/src/lundump.h",
    "https://github.com/Jake-NotTheMuss/hksc/blob/master/src/lopcodes.h",
]

OPCODE_NAMES = """GETFIELD TEST CALL_I CALL_C EQ EQ_BK GETGLOBAL MOVE SELF RETURN
GETTABLE_S GETTABLE_N GETTABLE LOADBOOL TFORLOOP SETFIELD SETTABLE_S SETTABLE_S_BK
SETTABLE_N SETTABLE_N_BK SETTABLE SETTABLE_BK TAILCALL_I TAILCALL_C TAILCALL_M LOADK
LOADNIL SETGLOBAL JMP CALL_M CALL TAILCALL GETUPVAL SETUPVAL ADD ADD_BK SUB SUB_BK
MUL MUL_BK DIV DIV_BK MOD MOD_BK POW POW_BK NEWTABLE UNM NOT LEN LT LT_BK LE LE_BK
CONCAT TESTSET FORPREP FORLOOP SETLIST CLOSE CLOSURE VARARG TAILCALL_I_R1 CALL_I_R1
SETUPVAL_R1 TEST_R1 NOT_R1 GETFIELD_R1 SETFIELD_R1 NEWSTRUCT DATA SETSLOTN SETSLOTI
SETSLOT SETSLOTS SETSLOTMT CHECKTYPE CHECKTYPES GETSLOT GETSLOTMT SELFSLOT SELFSLOTMT
GETFIELD_MM CHECKTYPE_D GETSLOT_D GETGLOBAL_MEM""".split()

TYPE_NAMES = ["TNIL", "TBOOLEAN", "TLIGHTUSERDATA", "TNUMBER", "TSTRING",
              "TTABLE", "TFUNCTION", "TUSERDATA", "TTHREAD", "TIFUNCTION",
              "TCFUNCTION", "TUI64", "TSTRUCT"]


@dataclass(frozen=True)
class Limits:
    max_file_bytes: int = 16 * 1024 * 1024
    max_string_bytes: int = 1024 * 1024
    max_functions: int = 10000
    max_depth: int = 64
    max_instructions: int = 1000000
    max_constants: int = 1000000


class ParseError(ValueError):
    def __init__(self, message: str, offset: int):
        self.offset = offset
        super().__init__(f"at file offset 0x{offset:x}: {message}")


class Reader:
    def __init__(self, data: bytes, base: int, limits: Limits):
        self.data, self.base, self.limits = data, base, limits
        self.pos = 0

    @property
    def remaining(self):
        return len(self.data) - self.pos

    @property
    def offset(self):
        return self.base + self.pos

    def fail(self, message):
        raise ParseError(message, self.offset)

    def take(self, count, label):
        if count < 0 or count > self.remaining:
            self.fail(f"truncated {label}: need {count}, have {self.remaining}")
        start = self.pos
        self.pos += count
        return self.data[start:self.pos]

    def u8(self, label):
        return self.take(1, label)[0]

    def u32(self, label, endian=">"):
        return struct.unpack(endian + "I", self.take(4, label))[0]

    def count(self, label, maximum, minimum_item_bytes=1):
        start = self.offset
        n = self.u32(label)
        if n > maximum:
            raise ParseError(f"{label} {n} exceeds limit {maximum}", start)
        if n > self.remaining // minimum_item_bytes:
            raise ParseError(f"{label} {n} cannot fit in remaining input", start)
        return n

    def string(self, label):
        start = self.offset
        n = self.u32(label + " length")
        if n > self.limits.max_string_bytes:
            raise ParseError(f"{label} length exceeds limit", start)
        if not n:
            return None
        raw = self.take(n, label)
        if raw[-1] != 0:
            raise ParseError(f"{label} lacks terminating NUL", start)
        body = raw[:-1]
        return {"offset": start, "byte_length_with_nul": n,
                "text": body.decode("utf-8", errors="replace"),
                "bytes_hex": body.hex()}


def decode_instruction(word: int, offset: int, pc: int):
    opcode = (word >> 25) & 0x7f
    if opcode >= len(OPCODE_NAMES):
        raise ParseError(f"opcode 0x{opcode:02x} outside observed Amalur table", offset)
    return {"pc": pc, "file_offset": offset, "word_hex": f"{word:08x}",
            "opcode": opcode, "opcode_name": OPCODE_NAMES[opcode],
            "opcode_name_provisional": OPCODE_NAMES[opcode],  # Legacy schema alias.
            "A": word & 255, "B_raw": (word >> 17) & 255,
            "C_raw": (word >> 8) & 511, "Bx_raw": (word >> 8) & 0x1ffff,
            "sBx_provisional": ((word >> 8) & 0x1ffff) - 65535}


class ChunkParser:
    def __init__(self, data, base, limits):
        self.r = Reader(data, base, limits)
        self.limits = limits
        self.total_functions = self.total_instructions = self.total_constants = 0

    def function(self, depth=0):
        r, lim = self.r, self.limits
        if depth > lim.max_depth:
            r.fail("function nesting exceeds limit")
        self.total_functions += 1
        if self.total_functions > lim.max_functions:
            r.fail("total function count exceeds limit")
        start = r.offset
        prefix_string_1 = r.string("function prefix string 1")
        prefix_string_2 = r.string("function prefix string 2")
        line_first = r.u32("function first source line")
        line_last = r.u32("function last source line")
        nups = r.u32("upvalue count")
        params = r.u32("parameter count")
        vararg = r.u8("vararg flags")
        stack = r.u32("maximum stack size")
        if nups > 255 or params > 255 or stack > 255 or params > stack:
            r.fail("unreasonable function register or upvalue counts")
        instruction_count = r.count("instruction count", lim.max_instructions, 4)
        self.total_instructions += instruction_count
        if self.total_instructions > lim.max_instructions:
            r.fail("total instruction count exceeds limit")
        # Unlike the later hksc format, observed 0x08 code is not aligned.
        padding = b""
        code_offset = r.offset
        instructions = [decode_instruction(r.u32("instruction"), code_offset + i * 4, i)
                        for i in range(instruction_count)]
        count = r.count("constant count", lim.max_constants)
        self.total_constants += count
        if self.total_constants > lim.max_constants:
            r.fail("total constant count exceeds limit")
        constants = []
        for index in range(count):
            at = r.offset
            tag = r.u8("constant type")
            entry = {"index": index, "file_offset": at, "type_id": tag}
            if tag == 0:
                entry.update(type="nil", value=None)
            elif tag == 1:
                b = r.u8("boolean constant")
                if b not in (0, 1):
                    r.fail("invalid boolean constant")
                entry.update(type="boolean", value=bool(b))
            elif tag == 2:
                entry.update(type="lightuserdata", value=r.u32("lightuserdata"))
            elif tag == 3:
                raw = r.take(4, "number constant")
                entry.update(type="number", raw_hex=raw.hex(),
                             integer_value=struct.unpack(">i", raw)[0],
                             declared_integral_value=struct.unpack(">i", raw)[0])
            elif tag == 4:
                entry.update(type="string", value=r.string("string constant"))
                if entry["value"] is None:
                    r.fail("null string constant")
            elif tag == 11:
                entry.update(type="uint64", value=int.from_bytes(r.take(8,"uint64"),"big"))
            else:
                raise ParseError(f"unsupported constant type {tag}", at)
            constants.append(entry)
        children_count = r.count("child function count", lim.max_functions, 25)
        children = [self.function(depth + 1) for _ in range(children_count)]
        debug_offset = r.offset
        debug_counts = [r.u32("stripped debug section count") for _ in range(3)]
        if any(debug_counts):
            raise ParseError("nonempty debug arrays are not yet supported; refusing to skip them", debug_offset)
        # Only validate indices whose roles are stable in both research tables.
        for ins in instructions:
            op, bx = ins["opcode"], ins["Bx_raw"]
            if op in (0x06, 0x19, 0x1b, 0x55) and bx >= len(constants):
                raise ParseError("constant index outside this function", ins["file_offset"])
            if op == 0x3c and bx >= len(children):
                raise ParseError("closure index outside child function array", ins["file_offset"])
            if op in (0x1c, 0x38, 0x39):
                target = ins["pc"] + 1 + ins["sBx_provisional"]
                ins["branch_target_pc_provisional"] = target
                if not 0 <= target < len(instructions):
                    raise ParseError("branch target outside function", ins["file_offset"])
        return {"file_offset": start, "end_file_offset": r.offset,
                "prefix_string_1":prefix_string_1,"prefix_string_2":prefix_string_2,
                "source_line_first":line_first,"source_line_last":line_last,
                "upvalue_count": nups, "parameter_count": params,
                "vararg_flags": vararg, "maximum_stack_size": stack,
                "instruction_alignment_hex": padding.hex(),
                "code_file_offset": code_offset, "instructions": instructions,
                "constants": constants, "stripped_debug_counts": debug_counts,
                "children": children}

    def parse(self):
        r = self.r
        header = r.take(14, "Havok Script header")
        expected = bytes.fromhex("1b4c756151080004040404010100")
        if header != expected:
            raise ParseError("unsupported header; this parser admits only the observed 0x08 profile", r.base)
        type_count = r.count("type count", 32, 9)
        types = []
        for expected_ident in range(type_count):
            at = r.offset
            ident = r.u32("type identifier")
            name = r.string("type name")
            if ident != expected_ident:
                raise ParseError("type table order differs from native reader", at)
            if ident >= len(TYPE_NAMES) or name is None or name["text"] != TYPE_NAMES[ident]:
                raise ParseError("unexpected type-table entry", at)
            if any(t["id"] == ident for t in types):
                raise ParseError("duplicate type identifier", at)
            types.append({"id":ident,"name":name["text"],"file_offset":at})
        if len(types) != len(TYPE_NAMES):
            r.fail("incomplete type table")
        root = self.function()
        trailer_offset = r.offset
        marker = r.u32("structure trailer marker")
        if marker != 1:
            raise ParseError("unexpected structure trailer marker",trailer_offset)
        if r.string("structure name") is not None:
            r.fail("nonempty structure declarations are not yet supported")
        if r.remaining:
            r.fail(f"{r.remaining} unparsed trailing bytes; unsupported section or layout")
        return {"header_hex": header.hex(" "), "format_version": 8,
                "byte_order": "big", "integer_bytes": 4, "size_t_bytes": 4,
                "instruction_bytes": 4, "number_bytes": 4,
                "header_numeric_marker": header[11], "header_compatibility_bits":header[12],
                "header_sharing_flag":header[13], "type_table":types,
                "structure_trailer":{"file_offset":trailer_offset,"marker":marker,"declarations":[]},
                "root_function": root,
                "summary":{"functions":self.total_functions,
                           "instructions":self.total_instructions,
                           "constants":self.total_constants},
                "payload_bytes_consumed":r.pos,"payload_bytes":len(r.data)}


def parse_bytes(data: bytes, limits: Limits | None = None):
    lim = limits or Limits()
    if len(data) > lim.max_file_bytes:
        raise ParseError("file exceeds configured size limit", 0)
    if data.startswith(b"\x1bLua"):
        payload, base, wrapper = data, 0, None
    else:
        r = Reader(data, 0, lim)
        n = r.u32("wrapper name length", "<")
        if n > min(4096,lim.max_string_bytes):
            r.fail("wrapper name length exceeds limit")
        name = r.take(n,"wrapper name")
        # The initial three fixtures have count zero. Broader archive samples
        # establish a counted list of length-prefixed, non-NUL metadata strings.
        # Their role (references/exports/etc.) is not yet established natively.
        metadata_count = r.u32("wrapper metadata string count", "<")
        if metadata_count > 4096 or metadata_count > r.remaining // 4:
            r.fail("wrapper metadata count exceeds limit or remaining bytes")
        metadata = []
        for index in range(metadata_count):
            at = r.offset
            length = r.u32("wrapper metadata string length", "<")
            if length > lim.max_string_bytes:
                r.fail("wrapper metadata string length exceeds limit")
            raw = r.take(length, "wrapper metadata string")
            metadata.append({"index": index, "file_offset": at,
                             "text": raw.decode("utf-8", errors="replace"),
                             "bytes_hex": raw.hex()})
        size = r.u32("wrapper payload length", "<")
        if size != r.remaining:
            r.fail("wrapper payload size does not equal remaining file size")
        base = r.pos
        payload = r.take(size,"wrapper payload")
        wrapper = {"name":name.decode("utf-8",errors="replace"),
                   "name_bytes_hex":name.hex(), "opaque_word":metadata_count,
                   "metadata_string_count":metadata_count, "metadata_strings":metadata,
                   "payload_file_offset":base,"declared_payload_bytes":size}
    parsed = ChunkParser(payload,base,lim).parse()
    return {"schema_version":1,"tool":"opem-amalur-script-parser",
            "input_sha256":hashlib.sha256(data).hexdigest(),"input_bytes":len(data),
            "wrapper":wrapper,"chunk":parsed,
            "coverage":"complete structural consumption within the admitted profile",
            "native_static_evidence": NATIVE_EVIDENCE,
            "limitations":["Opcode names match the reference executable; instruction semantics are only partially confirmed.",
                           "This is not reconstructed Lua source or proof of runtime behavior.",
                           "Only stripped debug arrays, an empty structure trailer, and the exact observed header are supported.",
                           "Function prefix string roles remain unverified; both are null in the first two samples.",
                           "Number constants are signed 32-bit integers; stock Lua arithmetic may differ from this VM."],
            "source_references":SOURCE_REFERENCES}


def parse_file(path: Path, limits: Limits | None = None):
    """Bound the actual read, including a file that grows after stat()."""
    lim = limits or Limits()
    if path.stat().st_size > lim.max_file_bytes:
        raise ParseError("file exceeds configured size limit",0)
    with path.open("rb") as stream:
        data = stream.read(lim.max_file_bytes + 1)
    return parse_bytes(data,lim)


def disassemble(result):
    lines = ["Amalur 0x08 bytecode listing (native-confirmed opcode names)", "Not decompiled Lua source; operand semantics are only partially confirmed.",
             "SHA-256: " + result["input_sha256"], ""]
    def visit(fn, path):
        lines.append(f"FUNCTION {path} file=0x{fn['file_offset']:x} params={fn['parameter_count']} stack={fn['maximum_stack_size']} upvalues={fn['upvalue_count']}")
        for c in fn["constants"]:
            lines.append("  K" + str(c["index"]) + " " + json.dumps(c, ensure_ascii=True))
        for i in fn["instructions"]:
            lines.append(f"  {i['pc']:5d} @{i['file_offset']:08x} {i['word_hex']} {i['opcode_name_provisional']:<20} A={i['A']} B={i['B_raw']} C={i['C_raw']} Bx={i['Bx_raw']}")
        lines.append("")
        for n, child in enumerate(fn["children"]):
            visit(child,path + "/" + str(n))
    visit(result["chunk"]["root_function"],"0")
    return "\n".join(lines) + "\n"


def same_file(left: Path, right: Path):
    """Recognize aliases, including existing hard links, before writing outputs."""
    return (left.resolve() == right.resolve()
            or (left.exists() and right.exists() and left.samefile(right)))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", type=Path)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--disassembly", type=Path)
    args = ap.parse_args()
    for dest in (args.output,args.disassembly):
        if dest and same_file(dest,args.input):
            ap.error("output must not overwrite input")
    if args.disassembly and same_file(args.output,args.disassembly):
        ap.error("JSON and disassembly outputs must use different files")
    try:
        result = parse_file(args.input)
        args.output.write_text(json.dumps(result,indent=2,ensure_ascii=True)+"\n",encoding="utf-8")
        if args.disassembly:
            args.disassembly.write_text(disassemble(result),encoding="utf-8")
    except (OSError,ParseError) as exc:
        ap.exit(1,str(exc)+"\n")
    print(json.dumps({"input":str(args.input),"wrapper":result["wrapper"],
                      "summary":result["chunk"]["summary"],"consumed":result["chunk"]["payload_bytes_consumed"]}))


if __name__ == "__main__":
    main()
