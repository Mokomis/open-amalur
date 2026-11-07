"""Stitch the whole terrain height grid and fit it to ground-standing objects under each axis convention."""
import array, json, math, pickle, struct, zlib
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
s = (root / "work/v20-inputs/DATA_0.pak/431658.terrain_streamable_bin").read_bytes()
idx = pickle.load(open(root / "work/v20-char/terrain-index.pkl", "rb"))
refs = json.loads((root / "work/v20-char/terrain-refs.json").read_text())
SIDE, N, W = 19, 361, 2048
ORIGIN = -102425.0
marker = struct.pack("<I", N)


def grids(d):
    out, o = [], 0
    while True:
        o = d.find(marker, o)
        if o < 0 or o + 4 + N * 2 > len(d):
            return out
        v = struct.unpack_from(f"<{N}H", d, o + 4)
        if max(v) < 65000 and sum(abs(v[k + 1] - v[k]) for k in range(SIDE - 1)) < 6000:
            out.append([v[r * SIDE:(r + 1) * SIDE] for r in range(SIDE)])
            o += 4 + N * 2
        else:
            o += 4


H = array.array("H", [0]) * (W * W)
done = 0; counts = {}; unplaced = 0
for (cx, cy), (at, comp) in idx.items():
    G = grids(zlib.decompress(s[at:at + comp]))
    counts[len(G)] = counts.get(len(G), 0) + 1
    if not G:
        continue
    right, down = {}, {}
    for i, a in enumerate(G):
        for j, b in enumerate(G):
            if i != j:
                if all(a[r][16 + c] == b[r][c] for r in range(SIDE) for c in range(3)):
                    right[i] = j
                if all(a[16 + c][r] == b[c][r] for r in range(SIDE) for c in range(3)):
                    down[i] = j
    # Place relative to any grid, then normalise so the smallest coordinates sit at the chunk origin.
    place = {0: (0, 0)}
    changed = True
    rl, dl = {v: k for k, v in right.items()}, {v: k for k, v in down.items()}
    while changed:
        changed = False
        for i, (col, row) in list(place.items()):
            for table, dc, dr in ((right, 1, 0), (rl, -1, 0), (down, 0, 1), (dl, 0, -1)):
                j = table.get(i)
                if j is not None and j not in place:
                    place[j] = (col + dc, row + dr); changed = True
    unplaced += len(G) - len(place)
    mc = min(p[0] for p in place.values()); mr = min(p[1] for p in place.values())
    bx, by = cx // 2, cy // 2
    for i, (col, row) in place.items():
        for r in range(SIDE):
            for c in range(SIDE):
                x = bx + (col - mc) * 16 + c - 1
                y = by + (row - mr) * 16 + r - 1
                if 0 <= x < W and 0 <= y < W:
                    H[y * W + x] = G[i][r][c]
    done += 1
print("chunks", done, "grid counts", counts, "unplaced", unplaced)
(root / "work/v20-char/terrain-height.u16").write_bytes(H.tobytes())


def fit(pairs):
    n = len(pairs)
    mx = sum(p[0] for p in pairs) / n; my = sum(p[1] for p in pairs) / n
    den = sum((p[0] - mx) ** 2 for p in pairs) or 1
    k = sum((p[0] - mx) * (p[1] - my) for p in pairs) / den
    z0 = my - k * mx
    e = sorted(abs(p[1] - (k * p[0] + z0)) for p in pairs)
    return k, z0, e[n // 2], e[-1]


for name, fn in (("x,y", lambda u, v: (u, v)), ("y,x", lambda u, v: (v, u)), ("x,-y", lambda u, v: (u, W - 1 - v)), ("-x,y", lambda u, v: (W - 1 - u, v)), ("-x,-y", lambda u, v: (W - 1 - u, W - 1 - v)), ("y,-x", lambda u, v: (v, W - 1 - u)), ("-y,x", lambda u, v: (W - 1 - v, u))):
    pairs = []
    for n, (x, y, z) in refs:
        u = (x - ORIGIN) / 100; v = (y - ORIGIN) / 100
        px, py = fn(int(round(u)), int(round(v)))
        if 0 <= px < W and 0 <= py < W:
            h = H[py * W + px]
            if h:
                pairs.append((h, z))
    if len(pairs) > 3:
        print(name, "points", len(pairs), "k %.5f z0 %.1f median err %.1f max %.1f" % fit(pairs))
door = (1575.1, -62759.2, 5152.1)
u, v = int((door[0] - ORIGIN) / 100), int((door[1] - ORIGIN) / 100)
print("door sample", H[v * W + u], "neighbourhood", [H[(v + dv) * W + u + du] for dv in (-3, 0, 3) for du in (-3, 0, 3)])
