"""Stitch terrain patches by their overlaps and calibrate height against ground-standing objects."""
import json, math, pickle, re, struct, subprocess, zlib
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
g = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning")
inp = root / "work/v20-inputs"
syms = json.loads((inp / "symbols.json").read_text())
s = (root / "work/v20-inputs/DATA_0.pak/431658.terrain_streamable_bin").read_bytes()
idx = pickle.load(open(root / "work/v20-char/terrain-index.pkl", "rb"))
SIDE, N = 19, 361
ORIGIN, CELL = -102425.0, 50.0


def runs(d):
    out, o = [], 0
    marker = struct.pack("<I", N)
    while True:
        o = d.find(marker, o)
        if o < 0 or o + 4 + N * 2 > len(d):
            break
        # Each grid is followed by its count again in the samples seen so far.
        v = struct.unpack_from(f"<{N}H", d, o + 4)
        steps = sum(abs(v[k + 1] - v[k]) for k in range(SIDE - 1)) / (SIDE - 1)
        out.append((o, v))
        o += 4 + N * 2
    return out


def grid(v):
    return [v[r * SIDE:(r + 1) * SIDE] for r in range(SIDE)]


# Patch relationship in one chunk
at, comp = idx[(2048, 768)]
d = zlib.decompress(s[at:at + comp])
R = runs(d)
print("grids in chunk", len(R), [o for o, _ in R][:20])
G = [grid(v) for _, v in R]
right, down = {}, {}
for i, a in enumerate(G):
    for j, b in enumerate(G):
        if i == j:
            continue
        ev = sum(abs(a[r][16 + c] - b[r][c]) for r in range(SIDE) for c in range(3))
        eh = sum(abs(a[16 + c][r] - b[c][r]) for r in range(SIDE) for c in range(3))
        if ev <= 3 * SIDE:
            right[i] = j
        if eh <= 3 * SIDE:
            down[i] = j
print("next along row", right)
print("next along column", down)
print("order of grids", [(i, i in right, i in down) for i in range(len(G))])
# Between chunks
for key in ((2176, 768), (2048, 896)):
    if key in idx:
        at2, comp2 = idx[key]
        e = zlib.decompress(s[at2:at2 + comp2])
        E = [grid(v) for _, v in runs(e)]
        a1 = sum(1 for a in G for b in E if sum(abs(a[r][16 + c] - b[r][c]) for r in range(SIDE) for c in range(3)) <= 3 * SIDE)
        a2 = sum(1 for a in G for b in E if sum(abs(a[16 + c][r] - b[c][r]) for r in range(SIDE) for c in range(3)) <= 3 * SIDE)
        h = struct.unpack_from("<8H", e, 4)
        print("neighbour", key, "hdr", h, "grids", len(E), "row matches", a1, "column matches", a2)

# Ground-standing references in this space
listing = (root / "outputs/initial-archive-list.txt").read_bytes()
names = [x.strip() for x in listing.decode("utf-16" if listing[:2] == b"\xff\xfe" else "utf-8-sig").splitlines() if x.endswith(".gor_bxml")]
cand = [n for n in names if re.search(r"citizen|npc_|guard|merchant", n, re.I)]
dest = inp / "initial_0.pak"
missing = [n for n in cand if not (dest / n).exists()]
for start in range(0, len(missing), 60):
    subprocess.run([str(g / "modding/pakfileunpacker.exe"), str(g / "data/initial_0.pak"), "unpack", str(dest), *missing[start:start + 60]], cwd=g / "modding", capture_output=True, timeout=250)
refs = []
for n in cand:
    p = dest / n
    if not p.exists():
        continue
    b = p.read_bytes()
    if len(b) < 40 or struct.unpack_from("<I", b, 8)[0] != 431638:
        continue
    refs.append((n, struct.unpack_from("<3f", b, 24)))
print("people in this space", len(refs), refs[:8])
(root / "work/v20-char/terrain-refs.json").write_text(json.dumps(refs))
