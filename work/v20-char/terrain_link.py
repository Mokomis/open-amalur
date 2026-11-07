"""Find terrain references at any byte alignment, and describe the outdoor render list."""
import collections, json, re, struct
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
inp = root / "work/v20-inputs"
syms = json.loads((inp / "symbols.json").read_text())
d = (inp / "patch_0.pak/431638.space_bxml").read_bytes()
pl = struct.unpack_from("<I", d, 0)[0]; b = d[8:8 + pl]
ids = sorted(int(p.stem) for a in ("DATA_0.pak", "patch_0.pak") for p in (inp / a).glob("*.terrain_bin") if p.stem.isdigit())
for t in ids:
    at = [m.start() for m in re.finditer(re.escape(struct.pack("<I", t)), b)]
    if at:
        print("terrain", t, "at", at[:6], "ctx", b[max(0, at[0] - 16):at[0] + 16].hex())
base = 43272
print("render list head", b[base:base + 340].hex())
slots = sorted(struct.unpack_from(f"<{struct.unpack_from('<I', d, 4)[0] // 4}I", d, 8 + pl))
big = [s for s in slots if s >= base]
print("slots in list", len(big), big[:24], "gaps", collections.Counter(big[i + 1] - big[i] for i in range(min(400, len(big) - 1))).most_common(8))
fab = {int(k) for k in syms["fab"]}
near = collections.Counter()
for i in range(base, pl - 3):
    v = struct.unpack_from("<I", b, i)[0]
    if v in fab:
        near[v] += 1
print("fab refs in render list", len(near), "total", sum(near.values()), [(syms["fab"][str(k)], c) for k, c in near.most_common(30)])
