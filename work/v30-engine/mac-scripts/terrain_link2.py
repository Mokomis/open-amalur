"""Typed references keep the asset id in the low 28 bits: search for terrain that way, and read town render arrays."""
import collections, json, math, struct
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
inp = root / "work/v20-inputs"
syms = json.loads((inp / "symbols.json").read_text())
d = (inp / "patch_0.pak/431638.space_bxml").read_bytes()
pl = struct.unpack_from("<I", d, 0)[0]; b = d[8:8 + pl]
ids = {}
for a in ("DATA_0.pak", "patch_0.pak"):
    for p in (inp / a).glob("*.terrain_bin"):
        if p.stem.isdigit():
            ids[int(p.stem)] = p
hits = collections.Counter()
where = {}
for i in range(0, pl - 3, 4):
    v = struct.unpack_from("<I", b, i)[0]
    if (v & 0xfffffff) in ids and v >> 28:
        hits[v] += 1; where.setdefault(v, i)
print("typed hits", [(hex(k), k & 0xfffffff, c, where[k]) for k, c in hits.most_common(12)])
print("type nibbles for all", collections.Counter(struct.unpack_from("<I", b, i)[0] >> 28 for i in range(0, pl - 3, 4)).most_common(16))
print("slots 0x130-0x200")
for s in range(0x130, 0x210, 8):
    ptr, cnt = struct.unpack_from("<II", b, s)
    print(hex(s), ptr - 8, cnt, end=" | ")
print()
ptr, cnt = struct.unpack_from("<II", b, 0x1b0); refs = [struct.unpack_from("<I", b, ptr - 8 + i * 4)[0] for i in range(cnt)]
print("0x1b0 refs", cnt, collections.Counter(r >> 28 for r in refs).most_common(), [(hex(r), syms["fab"].get(str(r & 0xfffffff))) for r in refs[:6]])
kinds = collections.Counter(r >> 28 for r in refs)
others = [r for r in refs if r >> 28 != 15]
print("non-fab refs", [(hex(r), (r & 0xfffffff) in ids) for r in others[:30]])
ptr, rc = struct.unpack_from("<II", b, 0x160)
print("0x160 renders", rc)
DOOR = (1575.1, -62759.2, 5152.1)
rows = []
for i in range(rc):
    r = b[ptr - 8 + i * 84:ptr - 8 + (i + 1) * 84]
    sp = struct.unpack_from("<4f", r)
    rows.append((math.dist(sp[:3], DOOR), sp[3], struct.unpack_from("<I", r, 68)[0], sp[:3]))
for radius in (1000, 2000, 4000, 8000, 16000, 1e9):
    print("within", radius, sum(1 for x in rows if x[0] <= radius))
print("closest", [(round(x[0]), round(x[1]), x[2]) for x in sorted(rows)[:10]])
