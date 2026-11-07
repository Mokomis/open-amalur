"""Row-order patches including holes: test seams between chunks and fit heights to ground references."""
import array, json, pickle, struct, zlib
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
s = (root / "work/v20-inputs/DATA_0.pak/431658.terrain_streamable_bin").read_bytes()
idx = pickle.load(open(root / "work/v20-char/terrain-index.pkl", "rb"))
refs = json.loads((root / "work/v20-char/terrain-refs.json").read_text())
SIDE, N = 19, 361
ORIGIN = -102425.0
M = struct.pack("<I", N)
HOLE = 65535


def grids(d):
    out, o = [], 0
    while True:
        o = d.find(M, o)
        if o < 0 or o + 734 > len(d):
            return out
        if d[o + 726:o + 730] == M and d[o + 730:o + 734] == b"\xff\xff\xff\xff":
            v = struct.unpack_from(f"<{N}H", d, o + 4)
            if not (v[0] == 65535 and v[1] == 65535 and v[2] == 65535 and v[20] == 65535 and min(v) == 65535):
                out.append([v[r * SIDE:(r + 1) * SIDE] for r in range(SIDE)])
                o += 726
                continue
        o += 4


cache = {}
for key, (at, comp) in idx.items():
    d = zlib.decompress(s[at:at + comp])
    cache[key] = (struct.unpack_from("<I", d, 0)[0], grids(d))
print("declared vs found", sum(1 for c, g in cache.values() if c == len(g)), "of", len(cache), "16-grid chunks", sum(1 for c, g in cache.values() if len(g) == 16))
for key in ((2048, 768),):
    G = cache[key][1]
    print(key, "chain within row", [all(G[i][r][16 + c] == G[i + 1][r][c] or HOLE in (G[i][r][16 + c], G[i + 1][r][c]) for r in range(SIDE) for c in range(3)) for i in range(len(G) - 1)])
    print("chain across rows", [all(G[i][16 + c][r] == G[i + 4][c][r] or HOLE in (G[i][16 + c][r], G[i + 4][c][r]) for r in range(SIDE) for c in range(3)) for i in range(max(0, len(G) - 4))])


def seam(a, b, horizontal):
    if len(a) != 16 or len(b) != 16:
        return None
    pairs = []
    for t in range(4):
        i, j = (t * 4 + 3, t * 4) if horizontal else (12 + t, t)
        for r in range(SIDE):
            for c in range(3):
                u, v = (a[i][r][16 + c], b[j][r][c]) if horizontal else (a[i][16 + c][r], b[j][c][r])
                if HOLE not in (u, v):
                    pairs.append(abs(u - v))
    return sum(pairs) / len(pairs) if pairs else None


stats = {}
for (x, y), (c, G) in cache.items():
    for step in (128,):
        for name, key in (("x", (x + step, y)), ("y", (x, y + step))):
            if key in cache:
                e = seam(G, cache[key][1], name == "x")
                if e is not None:
                    stats.setdefault((name, step), []).append(e)
print("seam mean error", {k: (len(v), round(sum(v) / len(v), 2), round(sorted(v)[len(v) // 2], 2)) for k, v in stats.items()})
W = 2048
H = array.array("H", [HOLE]) * (W * W)
for (cx, cy), (c, G) in cache.items():
    if len(G) != 16:
        continue
    for i, g in enumerate(G):
        col, row = i % 4, i // 4
        for r in range(SIDE):
            for k in range(SIDE):
                x = cx // 2 + col * 16 + k - 1
                y = cy // 2 + row * 16 + r - 1
                if 0 <= x < W and 0 <= y < W:
                    H[y * W + x] = g[r][k]
(root / "work/v20-char/terrain-height.u16").write_bytes(H.tobytes())
pairs = []
for n, (x, y, z) in refs:
    u = (x - ORIGIN) / 100; v = (y - ORIGIN) / 100
    px, py = int(u), int(v)
    fx, fy = u - px, v - py
    q = [H[py * W + px], H[py * W + px + 1], H[(py + 1) * W + px], H[(py + 1) * W + px + 1]]
    if HOLE in q:
        print("no sample", n); continue
    h = q[0] * (1 - fx) * (1 - fy) + q[1] * fx * (1 - fy) + q[2] * (1 - fx) * fy + q[3] * fx * fy
    pairs.append((h, z, n))
m = len(pairs); mx = sum(p[0] for p in pairs) / m; my = sum(p[1] for p in pairs) / m
k = sum((p[0] - mx) * (p[1] - my) for p in pairs) / sum((p[0] - mx) ** 2 for p in pairs); z0 = my - k * mx
e = sorted((abs(p[1] - k * p[0] - z0), p[2]) for p in pairs)
print("points", m, "k", round(k, 5), "z0", round(z0, 2), "median", round(e[m // 2][0], 2), "worst", [(round(a, 1), b) for a, b in e[-4:]], "best", [round(a, 2) for a, b in e[:6]])
