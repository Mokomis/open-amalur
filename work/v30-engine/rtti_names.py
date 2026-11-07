#!/usr/bin/env python3
"""rtti_names.py <koa.exe> <functions.tsv> <out dir>: recover classes from MSVC x86 RTTI and name their methods.
Writes classes.tsv (class, vtable, slots, offset, bases) and names.tsv (address, name, source). Names mark evidence:
vfN = slot N of the class's vtable, xtor = function storing the vtable pointer (constructor or destructor)."""
import bisect, collections, re, struct, sys

exe, ftsv, out = sys.argv[1:4]
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


def off(v):
    for a, vs, rp, rs in secs.values():
        if a <= v < a + min(vs, rs):
            return v - a + rp
    return None


def u32(v):
    x = off(v)
    return None if x is None or x + 4 > len(d) else struct.unpack_from("<I", d, x)[0]


def in_sec(v, n):
    a, vs, _, _ = secs[n]
    return a <= v < a + vs


def clean(m):
    """.?AVName@Ns@@ to Ns_Name. Template arguments are kept as mangled text, shortened."""
    m = m[4:]
    if "?$" in m:
        t = re.sub(r"[^A-Za-z0-9_]+", "_", m).strip("_")
        return "T_" + t[:90]
    parts = [p for p in m.rstrip("@").split("@") if p]
    return "_".join(reversed(parts))


def tname(td):
    x = off(td + 8)
    if x is None or d[x:x + 3] not in (b".?A",):
        return None
    return clean(d[x:d.index(b"\0", x)].decode("latin1"))


def bases(cd):
    if not cd or u32(cd) != 0:
        return []
    n, arr = u32(cd + 8), u32(cd + 12)
    if not n or n > 200 or not arr:
        return []
    r = []
    for i in range(n):
        b = u32(arr + 4 * i)
        t = u32(b) if b else None
        nm = tname(t) if t else None
        if nm:
            r.append(nm)
    return r


rd_va, rd_vs, rd_rp, rd_rs = secs[".rdata"]
vtables = []
for p in range(0, min(rd_vs, rd_rs) - 8, 4):
    col = struct.unpack_from("<I", d, rd_rp + p)[0]
    if not in_sec(col, ".rdata") or u32(col) != 0:
        continue
    td, cd = u32(col + 12), u32(col + 16)
    if not td or not cd or u32(cd) != 0:
        continue
    nm = tname(td)
    if not nm:
        continue
    vt = rd_va + p + 4
    slots = []
    q = vt
    while True:
        f = u32(q)
        if f is None or not in_sec(f, ".text"):
            break
        slots.append(f)
        q += 4
        if q != vt and q - vt > 4 and False:
            break
    if slots:
        vtables.append((nm, vt, slots, u32(col + 4), bases(cd)))

print("vtables", len(vtables), "classes", len({v[0] for v in vtables}))
funcs = []
for line in open(ftsv, encoding="utf-8"):
    p = line.rstrip("\n").split("\t")
    if p[0] == "address":
        continue
    funcs.append((int(p[0], 16), int(p[1])))
funcs.sort()
starts = [f[0] for f in funcs]


def owner(a):
    i = bisect.bisect_right(starts, a) - 1
    return starts[i] if i >= 0 and a < funcs[i][0] + max(funcs[i][1], 1) else None


with open(out + "/classes.tsv", "w") as w:
    w.write("class\tvtable\tslots\toffset\tbases\n")
    for nm, vt, sl, of, ba in sorted(vtables):
        w.write(f"{nm}\t{vt:08x}\t{len(sl)}\t{of}\t{','.join(ba)}\n")

# A function in several vtables is named for the class with the fewest bases: the one most likely to define it.
best = {}
depth = {}
for nm, vt, sl, of, ba in vtables:
    for i, f in enumerate(sl):
        k = (len(ba), of != 0, nm)
        if f not in best or k < depth[f]:
            depth[f] = k
            best[f] = (f"{nm}__vf{i}" + (f"_o{of}" if of else ""), "vtable")

# Constructors and destructors store the vtable address: C7 /0 imm32 with the vtable as the immediate.
tx_va, tx_vs, tx_rp, tx_rs = secs[".text"]
text = d[tx_rp:tx_rp + tx_rs]
vt_of = {v[1]: v[0] for v in vtables}
xtor = collections.defaultdict(set)
for m in re.finditer(rb"\xc7[\x00-\x07\x40-\x47\x80-\x87]", text):
    i = m.start()
    mod = text[i + 1]
    # register memory operands only; skip SIB and disp32 forms, which do not hold vtable stores in the common shape.
    rm = mod & 7
    if rm == 4 or (mod >> 6 == 0 and rm == 5):
        continue
    dl = {0: 0, 1: 1, 2: 4}[mod >> 6]
    p = i + 2 + dl
    if p + 4 > len(text):
        continue
    v = struct.unpack_from("<I", text, p)[0]
    if v in vt_of:
        f = owner(tx_va + i)
        if f is not None:
            xtor[f].add(vt_of[v])
xn = 0
for f, cs in xtor.items():
    c = sorted(cs, key=lambda s: (-len(s), s))[0]
    if f not in best:
        best[f] = (f"{c}__xtor", "xtor")
        xn += 1
print("named from vtables", sum(1 for b in best.values() if b[1] == "vtable"), "from vtable stores", xn, "of", len(funcs))
known = set(starts)
seen = collections.Counter()
with open(out + "/names.tsv", "w") as w:
    w.write("address\tname\tsource\tin_ghidra\n")
    for f in sorted(best):
        n, s = best[f]
        seen[n] += 1
        if seen[n] > 1:
            n = f"{n}_{seen[n]}"
        w.write(f"{f:08x}\t{n}\t{s}\t{int(f in known)}\n")
print("vtable functions missing from ghidra's list", sum(1 for f in best if f not in known))
c = collections.Counter(re.match(r"([A-Za-z0-9]*)", n).group(1) for n, _ in best.values())
print("top prefixes", c.most_common(12))
print("render classes", sorted({v[0] for v in vtables if re.search(r"Render|Shader|D3D|Texture|Mesh|Graphics|Gfx", v[0]) and not v[0].startswith("T_")})[:50])
