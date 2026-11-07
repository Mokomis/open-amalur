#!/usr/bin/env python3
"""gaps.py <koa.exe> <recomp dir>: what the bytes outside Ghidra's functions are, and the shape of the computed jumps."""
import collections, json, math, re, struct, sys

import capstone

exe, out = sys.argv[1:3]
d = open(exe, "rb").read()
pe = struct.unpack_from("<I", d, 0x3c)[0]
ns = struct.unpack_from("<H", d, pe + 6)[0]
oh = struct.unpack_from("<H", d, pe + 20)[0]
o = pe + 24
base = struct.unpack_from("<I", d, o + 28)[0]
secs = {}
for i in range(ns):
    s = o + oh + 40 * i
    n = d[s:s + 8].rstrip(b"\0").decode()
    vs, va, rs, rp = struct.unpack_from("<IIII", d, s + 8)
    secs[n] = (base + va, vs, rp, rs)
text_lo, _, rp, rs = secs[".text"]
text_hi = text_lo + rs
text = d[rp:rp + rs]
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
gaps = json.load(open(out + "/gaps.json"))
print("non-padding gaps", len(gaps), "bytes", sum(g[1] for g in gaps))

def entropy(b):
    if not b: return 0.0
    c = collections.Counter(b)
    return -sum(v / len(b) * math.log2(v / len(b)) for v in c.values())

for a, n in sorted(gaps, key=lambda g: -g[1])[:6]:
    b = text[a - text_lo:a - text_lo + n]
    print(f"gap {a:08x} size {n} entropy {entropy(b):.2f} first {b[:24].hex(' ')}")
    print("   decode:", [f"{m} {x}"[:26] for _, _, m, x in list(md.disasm_lite(b[:64], a))[:6]])
hist = collections.Counter()
for a, n in gaps:
    hist[min(int(math.log2(max(n, 1))), 20)] += n
print("bytes by gap size, log2:", sorted(hist.items()))

# Code entry evidence: direct call and jump targets, and pointers from .rdata and .data, that land in a gap.
in_gap = bytearray(rs)
for a, n in gaps: in_gap[a - text_lo:a - text_lo + n] = b"\1" * n
callt = collections.Counter()
for m in re.finditer(rb"[\xe8\xe9]", text):
    i = m.start()
    if i + 5 > rs: break
    t = text_lo + i + 5 + struct.unpack_from("<i", text, i + 1)[0]
    if text_lo <= t < text_hi and in_gap[t - text_lo] and not in_gap[i]: callt[t] += 1
print("direct call or jmp from known code into gaps: targets", len(callt), "sites", sum(callt.values()))
ptr = set()
for name in (".rdata", ".data"):
    lo, vs, p, r = secs[name]
    b = d[p:p + r]
    for i in range(0, r - 3, 4):
        v = struct.unpack_from("<I", b, i)[0]
        if text_lo <= v < text_hi and in_gap[v - text_lo]: ptr.add(v)
print("data pointers into gaps", len(ptr))
for a, n in sorted(gaps, key=lambda g: -g[1])[:2]:
    print(f"  in largest gap {a:08x}: data pointers", sum(1 for v in ptr if a <= v < a + n), "call targets", sum(1 for v in callt if a <= v < a + n))

# Reachable code in gaps from that evidence, by following direct control flow.
seen = set()
work = list(set(callt) | ptr)
bytes_found = 0
badstart = 0
while work:
    a = work.pop()
    if a in seen or not (text_lo <= a < text_hi) or not in_gap[a - text_lo]: continue
    seen.add(a)
    pos = a
    ok = False
    for ad, sz, mnem, x in md.disasm_lite(text[a - text_lo:min(a - text_lo + 65536, rs)], a):
        if not in_gap[ad - text_lo]: ok = True; break
        bytes_found += sz
        if mnem in ("call", "jmp") or mnem.startswith("j"):
            if x.startswith("0x"): work.append(int(x, 16))
        if mnem in ("ret", "retf", "jmp", "int3"): ok = True; break
    if not ok: badstart += 1
print("code reachable in gaps by direct flow: blocks", len(seen), "bytes (may overlap)", bytes_found, "unterminated", badstart)

# Computed jumps.
shape = collections.Counter()
ex = {}
for line in open(out + "/computed_jumps.tsv"):
    a, f, t = (line.rstrip("\n").split("\t") + [""])[:3]
    ia = int(a, 16)
    ins = list(md.disasm_lite(text[ia - text_lo:ia - text_lo + 15], ia, 1))
    x = ins[0][3] if ins else "?"
    k = re.sub(r"0x[0-9a-f]+", "N", x)
    k = re.sub(r"\b(eax|ebx|ecx|edx|esi|edi|ebp)\b", "R", k)
    key = ("resolved " if t else "unresolved ") + k
    shape[key] += 1
    ex.setdefault(key, a)
print("computed jump shapes:")
for k, v in shape.most_common(16): print(f"  {v:5} {k}  e.g. {ex[k]}")
