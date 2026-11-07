"""Read-only Windows query for native initialization of G+0x154/+0x158.

Bounded linear disassembly is a lead finder, not proof of function boundaries.
Parent should confirm promising instructions in REA before admitting a key.
"""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import sys

root = Path.home() / "Documents" / "Opem Amalur"
sys.path.insert(0, str(root / "tools" / "python-libs"))
import capstone

parser = argparse.ArgumentParser()
parser.add_argument("--start", type=lambda s: int(s, 0), default=0x01070000)
parser.add_argument("--end", type=lambda s: int(s, 0), default=0x010e0000)
parser.add_argument("--string-tables", action="store_true")
args = parser.parse_args()
if not 0 < args.end - args.start <= 0x200000:
    raise ValueError("query must stay bounded to at most 2 MiB")
target = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning\koa.exe")
data = target.read_bytes()
digest = hashlib.sha256(data).hexdigest()
assert digest == "16a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314"
pe = struct.unpack_from("<I", data, 0x3c)[0]
assert data[pe:pe+4] == b"PE\0\0"
section_count = struct.unpack_from("<H", data, pe+6)[0]
optional_size = struct.unpack_from("<H", data, pe+20)[0]
base = struct.unpack_from("<I", data, pe+24+28)[0]
sections = []
for i in range(section_count):
    offset = pe+24+optional_size+40*i
    _, relative, size, raw = struct.unpack_from("<IIII", data, offset+8)
    sections.append((base+relative, size, raw))


def read(address, size):
    for start, length, raw in sections:
        if start <= address and address+size <= start+length:
            return data[raw+address-start:raw+address-start+size]
    raise ValueError(hex(address))


def describe(ins):
    out = {"address": hex(ins.address), "bytes": ins.bytes.hex(),
           "mnemonic": ins.mnemonic, "operands": ins.op_str}
    strings = []
    if ins.id:
        for operand in ins.operands:
            if operand.type != capstone.x86.X86_OP_IMM:
                continue
            try:
                blob = read(operand.imm, 96).split(b"\0", 1)[0]
            except ValueError:
                continue
            if blob and len(blob) < 96 and all(32 <= c < 127 for c in blob):
                strings.append({"address": hex(operand.imm), "ascii": blob.decode("ascii")})
    if strings:
        out["direct_immediate_strings"] = strings
    return out


dis = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
dis.detail = True
dis.skipdata = True
instructions = list(dis.disasm(read(args.start, args.end-args.start), args.start))
candidates = []
for i, ins in enumerate(instructions):
    if not ins.id:
        continue
    operands = ins.operands
    wanted = any((o.type == capstone.x86.X86_OP_MEM and o.mem.disp in (0x154, 0x158))
                 or (o.type == capstone.x86.X86_OP_IMM and o.imm in (0x154, 0x158)
                     and ins.mnemonic in ("add", "lea")) for o in operands)
    if wanted:
        candidates.append({"candidate": describe(ins),
                           "context": [describe(v) for v in instructions[max(0,i-12):i+13]]})
string_evidence = {}
if args.string_tables:
    # An interned-name array initializer may compute G+0x154 by loop indexing,
    # leaving no literal0x154 write. Find short-name pointer tables instead.
    n_addresses = set()
    for start, size, raw in sections:
        content = data[raw:raw+size]
        position = content.find(b"n\0")
        while position != -1:
            n_addresses.add(start+position)
            position = content.find(b"n\0", position+1)
    direct = []
    predefined = []
    stack_n = []
    intern_calls = []
    for i, ins in enumerate(instructions):
        if ins.id and any(o.type == capstone.x86.X86_OP_IMM and o.imm in n_addresses for o in ins.operands):
            direct.append({"candidate": describe(ins),
                           "context": [describe(v) for v in instructions[max(0,i-15):i+16]]})
        if not ins.id:
            continue
        if ins.mnemonic == "call" and any(o.type == capstone.x86.X86_OP_IMM and o.imm in (0x010c0520, 0x010c0b30) for o in ins.operands):
            intern_calls.append({"candidate":describe(ins),
                                 "context":[describe(v) for v in instructions[max(0,i-18):i+19]]})
        if ins.mnemonic == "mov" and any(o.type == capstone.x86.X86_OP_MEM for o in ins.operands) and any(o.type == capstone.x86.X86_OP_IMM and o.imm in (0x6e, 0x006e) for o in ins.operands):
            stack_n.append({"candidate":describe(ins),
                            "context":[describe(v) for v in instructions[max(0,i-15):i+21]]})
        desc = describe(ins)
        if any(v["ascii"] in ("__index", "__newindex", "_G", "not enough memory", "memory allocation error")
               for v in desc.get("direct_immediate_strings", [])):
            predefined.append({"candidate":desc,
                               "context":[describe(v) for v in instructions[max(0,i-15):i+26]]})
    tables = []
    for start, size, raw in sections:
        for offset in range(0, size-3, 4):
            value = struct.unpack_from("<I", data, raw+offset)[0]
            if value not in n_addresses:
                continue
            entries = []
            for relative in range(max(0,offset-64), min(size-3,offset+68), 4):
                pointer = struct.unpack_from("<I", data, raw+relative)[0]
                try:
                    blob = read(pointer, 64).split(b"\0", 1)[0]
                except ValueError:
                    continue
                if blob and len(blob) < 64 and all(32 <= c < 127 for c in blob):
                    entries.append({"slot":hex(start+relative),"pointer":hex(pointer),"ascii":blob.decode("ascii")})
            if len(entries) >= 3:
                tables.append({"n_pointer_slot":hex(start+offset),"entries":entries})
    string_evidence = {"literal_n_addresses":sorted(hex(v) for v in n_addresses),
                       "direct_n_code_references":direct,"pointer_table_candidates":tables,
                       "predefined_string_references":predefined,"stack_n_writes":stack_n,
                       "known_string_intern_calls":intern_calls}
output = root / "work" / "v05-cache" / "legacy-count-key-candidates.json"
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps({"target_sha256": digest,
                              "scope": "Original file bytes only; bounded linear-disassembly leads, no target execution",
                              "range": [hex(args.start), hex(args.end)],
                              "candidate_count": len(candidates), "candidates": candidates,
                              "string_evidence": string_evidence}, indent=2), encoding="utf-8")
print(json.dumps({"output": str(output), "candidate_count": len(candidates)}))
