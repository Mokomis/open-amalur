#!/usr/bin/env python3
"""census.py <koa.exe> <recomp dir>: instruction census over Ghidra's function ranges, plus what the unattributed .text bytes are."""
import collections, json, struct, sys

import capstone

exe, out = sys.argv[1:3]
d = open(exe, "rb").read()
pe = struct.unpack_from("<I", d, 0x3c)[0]
oh = struct.unpack_from("<H", d, pe + 20)[0]
o = pe + 24
base = struct.unpack_from("<I", d, o + 28)[0]
vs, va, rs, rp = struct.unpack_from("<IIII", d, o + oh + 8)
text_lo, text_hi = base + va, base + va + rs
text = d[rp:rp + rs]

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.skipdata = False
covered = bytearray(rs)
mn = collections.Counter()
mn_funcs = collections.Counter()
ops = collections.Counter()
special = collections.Counter()
ex = {}
nf = ni = bad = thunks = 0
for line in open(out + "/func_ranges.tsv"):
    a, th, ranges = line.rstrip("\n").split("\t")
    nf += 1
    thunks += th == "true"
    seen = set()
    for r in ranges.split(","):
        lo, hi = (int(x, 16) for x in r.split("-"))
        if not (text_lo <= lo and hi < text_hi):
            bad += 1
            continue
        off = lo - text_lo
        n = hi - lo + 1
        covered[off:off + n] = b"\1" * n
        end = lo
        for ad, sz, m, opstr in md.disasm_lite(text[off:off + n], lo):
            ni += 1
            mn[m] += 1
            seen.add(m)
            ex.setdefault(m, f"{ad:08x} {m} {opstr}")
            end = ad + sz
            if "fs:" in opstr: special["fs: segment"] += 1
            if m in ("jmp", "call") and not opstr.startswith("0x"): special["indirect " + m] += 1
            if m.startswith("rep"): special["rep prefix"] += 1
            if m.startswith("lock"): special["lock prefix"] += 1
            if "xmm" in opstr: special["xmm operand"] += 1
            if "st(" in opstr or m.startswith("f"): special["x87-like"] += 1
        if end != hi + 1: special["range not fully decoded"] += 1
    for m in seen: mn_funcs[m] += 1

print("functions", nf, "thunks", thunks, "ranges outside .text", bad)
print("instructions", ni, "distinct mnemonics", len(mn))
print("special", special.most_common())
with open(out + "/mnemonics.tsv", "w") as w:
    for m, c in mn.most_common():
        w.write(f"{m}\t{c}\t{mn_funcs[m]}\t{ex[m]}\n")
print("top", mn.most_common(40))

# What is outside the functions?
un = rs - sum(covered)
print("text bytes", rs, "covered", sum(covered), "not covered", un)
cls = collections.Counter()
gaps = []
i = 0
while i < rs:
    if covered[i]:
        i += 1
        continue
    j = i
    while j < rs and not covered[j]: j += 1
    gaps.append((i, j))
    i = j
ptrs = 0
for a, b in gaps:
    g = text[a:b]
    if all(x in (0xcc, 0x90, 0) for x in g):
        cls["padding"] += b - a
        continue
    # Jump tables: runs of aligned pointers into .text.
    k = a + ((-(a + text_lo)) & 3)
    tab = 0
    while k + 4 <= b:
        if text_lo <= struct.unpack_from("<I", text, k)[0] < text_hi: tab += 4
        k += 4
    if tab >= (b - a) * 0.7:
        cls["pointer tables"] += b - a
        continue
    # Would it decode as code from the start?
    dec = 0
    pos = a + text_lo
    for ad, sz, m, _ in md.disasm_lite(g, pos):
        dec += sz
        if m in ("ret", "retf", "int3"): break
    if g[:1] in (b"\x55", b"\x56", b"\x53", b"\x57", b"\x83", b"\x81", b"\x8b", b"\x51", b"\x6a", b"\x68", b"\xa1") and dec >= min(b - a, 8):
        cls["looks like code"] += b - a
    else:
        cls["other data"] += b - a
print("gaps", len(gaps), "classes", cls.most_common())
big = sorted(gaps, key=lambda g: g[0] - g[1])[:8]
print("largest gaps", [(hex(text_lo + a), b - a) for a, b in big])
json.dump([[text_lo + a, b - a] for a, b in gaps if not all(x in (0xcc, 0x90, 0) for x in text[a:b])], open(out + "/gaps.json", "w"))
