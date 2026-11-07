"""Assign absolute positions per detail level, sample the finest level, and fit height to ground references."""
import collections, json, pickle, struct, zlib
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
s = (root / "work/v20-inputs/DATA_0.pak/431658.terrain_streamable_bin").read_bytes()
idx = pickle.load(open(root / "work/v20-char/terrain-index.pkl", "rb"))
refs = json.loads((root / "work/v20-char/terrain-refs.json").read_text())
grids = pickle.load(open(root / "work/v20-char/terrain-grids.pkl", "rb"))
place = pickle.load(open(root / "work/v20-char/terrain-place.pkl", "rb"))
heads = {}
counts = collections.Counter(g[0] for g in grids)
for key, (at, comp) in idx.items():
    d = zlib.decompress(s[at:at + comp])
    heads[key] = struct.unpack_from("<I8H", d, 0)
print("chunk width histogram", collections.Counter(h[2] - h[1] for h in heads.values()).most_common(), "height range sizes", collections.Counter(h[4] - h[3] for h in heads.values()).most_common(5))
by_comp = collections.defaultdict(list)
for n, g in enumerate(grids):
    by_comp[place[n][2]].append(n)
abs_pos = {}
votes_bad = 0
for comp, members in by_comp.items():
    offs = collections.Counter()
    for n in members:
        key, i, _ = grids[n]
        if counts[key] == 16:
            w = heads[key][2] - heads[key][1]
            offs[(key[0] + (i % 4) * w - place[n][0] * w, key[1] + (i // 4) * w - place[n][1] * w, w)] += 1
    if not offs:
        continue
    (ox, oy, w), votes = offs.most_common(1)[0]
    votes_bad += sum(offs.values()) - votes
    for n in members:
        abs_pos[n] = (ox + place[n][0] * w, oy + place[n][1] * w, w)
print("placed grids", len(abs_pos), "of", len(grids), "disagreeing votes", votes_bad, "widths", collections.Counter(p[2] for p in abs_pos.values()).most_common())
level = collections.defaultdict(dict)
for n, (x, y, w) in abs_pos.items():
    level[w][(x, y)] = n
HOLE = 65535
ORIGIN = -102425.0
def sample(wx, wy, fine=None):
    ux, uy = (wx - ORIGIN) / 50, (wy - ORIGIN) / 50
    for w in sorted(level):
        if fine and w != fine:
            continue
        px, py = int(ux // w) * w, int(uy // w) * w
        n = level[w].get((px, py))
        if n is None:
            continue
        v = grids[n][2]
        fx, fy = (ux - px) * 16 / w + 1, (uy - py) * 16 / w + 1
        ix, iy = int(fx), int(fy)
        q = [v[iy * 19 + ix], v[iy * 19 + ix + 1], v[(iy + 1) * 19 + ix], v[(iy + 1) * 19 + ix + 1]]
        if HOLE in q:
            continue
        ax, ay = fx - ix, fy - iy
        return q[0] * (1 - ax) * (1 - ay) + q[1] * ax * (1 - ay) + q[2] * (1 - ax) * ay + q[3] * ax * ay, w
    return None
pairs = []
for n, (x, y, z) in refs:
    r = sample(x, y)
    if r:
        pairs.append((r[0], z, n, r[1]))
m = len(pairs); mx = sum(p[0] for p in pairs) / m; my = sum(p[1] for p in pairs) / m
k = sum((p[0] - mx) * (p[1] - my) for p in pairs) / sum((p[0] - mx) ** 2 for p in pairs); z0 = my - k * mx
e = sorted((round(abs(p[1] - k * p[0] - z0), 1), p[2][:30], p[3]) for p in pairs)
print("points", m, "k", round(k, 6), "z0", round(z0, 2), "median", e[m // 2][0])
print(e)
door = sample(1575.1, -62759.2)
print("door", door, "predicted z", door and round(door[0] * k + z0, 1), "actual 5152.1")
json.dump({"k": k, "z0": z0}, open(root / "work/v20-char/terrain-fit.json", "w"))
pickle.dump(abs_pos, open(root / "work/v20-char/terrain-abs.pkl", "wb"))
