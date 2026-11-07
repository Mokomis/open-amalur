"""Place patches by exact edge matching across all chunks, then relate placement to chunk headers and world points."""
import collections, json, pickle, struct, zlib
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
s = (root / "work/v20-inputs/DATA_0.pak/431658.terrain_streamable_bin").read_bytes()
idx = pickle.load(open(root / "work/v20-char/terrain-index.pkl", "rb"))
refs = json.loads((root / "work/v20-char/terrain-refs.json").read_text())
SIDE, N = 19, 361
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
            if min(v) != 65535:
                out.append(v)
                o += 726
                continue
        o += 4


G = []
for key, (at, comp) in idx.items():
    d = zlib.decompress(s[at:at + comp])
    head = struct.unpack_from("<I8H", d, 0)
    for i, v in enumerate(grids(d)):
        G.append((key, i, head, v))
print("grids", len(G))
col = lambda v, c: tuple(v[r * SIDE + c] for r in range(SIDE))
row = lambda v, r: tuple(v[r * SIDE + c] for c in range(SIDE))
starts_c, starts_r = collections.defaultdict(list), collections.defaultdict(list)
for n, g in enumerate(G):
    v = g[3]
    a = (col(v, 0), col(v, 1), col(v, 2))
    if HOLE not in a[0] + a[1] + a[2] and len(set(a[1])) > 2:
        starts_c[a].append(n)
    b = (row(v, 0), row(v, 1), row(v, 2))
    if HOLE not in b[0] + b[1] + b[2] and len(set(b[1])) > 2:
        starts_r[b].append(n)
place = {}
right = {}; down = {}
for n, g in enumerate(G):
    v = g[3]
    a = (col(v, 16), col(v, 17), col(v, 18))
    for m in starts_c.get(a, []):
        if m != n:
            right[n] = m
    b = (row(v, 16), row(v, 17), row(v, 18))
    for m in starts_r.get(b, []):
        if m != n:
            down[n] = m
print("right links", len(right), "down links", len(down))
adj = collections.defaultdict(list)
for a, b in right.items():
    adj[a].append((b, 1, 0)); adj[b].append((a, -1, 0))
for a, b in down.items():
    adj[a].append((b, 0, 1)); adj[b].append((a, 0, -1))
seen = {}
comps = []
for n in range(len(G)):
    if n in seen:
        continue
    seen[n] = (0, 0, len(comps)); stack = [n]; size = 0; conflicts = 0
    while stack:
        a = stack.pop(); size += 1; x, y, c = seen[a]
        for b, dx, dy in adj[a]:
            if b in seen:
                if seen[b][:2] != (x + dx, y + dy):
                    conflicts += 1
            else:
                seen[b] = (x + dx, y + dy, c); stack.append(b)
    comps.append((size, conflicts))
print("components", len(comps), sorted(comps, reverse=True)[:6])
main = max(range(len(comps)), key=lambda c: comps[c][0])
# Relate placement to headers: which header scale explains patch position within the main component?
rows = [(seen[n][0], seen[n][1], G[n][0], G[n][1], G[n][2]) for n in seen if seen[n][2] == main]
sx = collections.Counter(); sy = collections.Counter()
for px, py, key, i, h in rows:
    sx[(key[0] - 0) - 0] += 0
sample = rows[:12]
print("sample (patch x,y, chunk key, index, head)", sample)
def regress(xs, ys):
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    k = sum((a - mx) * (b - my) for a, b in zip(xs, ys)) / sum((a - mx) ** 2 for a in xs)
    return k, my - k * mx, max(abs(b - k * a - (my - k * mx)) for a, b in zip(xs, ys))
print("chunk x key vs patch x", regress([r[2][0] + 0.0 for r in rows], [r[0] - r[3] % 4 for r in rows]))
print("chunk y key vs patch y", regress([r[2][1] + 0.0 for r in rows], [r[1] - r[3] // 4 for r in rows]))
print("widths", collections.Counter(r[4][2] - r[4][1] for r in rows).most_common(6))
pickle.dump({n: seen[n] for n in seen}, open(root / "work/v20-char/terrain-place.pkl", "wb"))
pickle.dump([(g[0], g[1], g[3]) for g in G], open(root / "work/v20-char/terrain-grids.pkl", "wb"))
