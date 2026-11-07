"""Test whether paint maps follow chunks in stream order, by correlating ground slope with paint channels."""
import math, struct, zlib
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
s = (root / "work/v20-inputs/DATA_0.pak/431658.terrain_streamable_bin").read_bytes()
recs = []
i = 16777236
while True:
    i = s.find(b"\x78\x9c", i)
    if i < 0:
        break
    raw, total, zero, raw2, comp = struct.unpack_from("<5I", s, i - 20)
    if raw == raw2 and zero == 0 and comp <= total <= comp + 32 and i + comp <= len(s):
        recs.append((i, raw, comp)); i += comp; continue
    i += 1
chunks = [r for r in recs if r[1] != 66568]
paints = [r for r in recs if r[1] == 66568]
M = struct.pack("<I", 361)


def full_grid(d):
    out, o = [], 0
    while True:
        o = d.find(M, o)
        if o < 0 or o + 734 > len(d):
            break
        if d[o + 726:o + 730] == M and d[o + 730:o + 734] == b"\xff\xff\xff\xff":
            v = struct.unpack_from("<361H", d, o + 4)
            out.append(v); o += 726
        else:
            o += 4
    if len(out) != 16 or any(max(v) > 60000 for v in out):
        return None
    H = [[0] * 64 for _ in range(64)]
    for g, v in enumerate(out):
        for r in range(16):
            for c in range(16):
                H[(g // 4) * 16 + r][(g % 4) * 16 + c] = v[(r + 1) * 19 + c + 1]
    return H


slopes = {}
for k, r in enumerate(chunks):
    H = full_grid(zlib.decompress(s[r[0]:r[0] + r[2]]))
    if H is None:
        continue
    S = []
    for y in range(1, 63, 2):
        for x in range(1, 63, 2):
            S.append(math.hypot(H[y][x + 1] - H[y][x - 1], H[y + 1][x] - H[y - 1][x]))
    m = sum(S) / len(S)
    if m > 15:
        slopes[k] = (S, m)
    if len(slopes) >= 80:
        break
print("slope samples", len(slopes), "first keys", list(slopes)[:12])
paint_cache = {}


def paint(j):
    if j not in paint_cache:
        d = zlib.decompress(s[paints[j][0]:paints[j][0] + paints[j][2]])
        ch = []
        for c in range(4):
            row = []
            for y in range(1, 63, 2):
                for x in range(1, 63, 2):
                    row.append(d[4 + ((y * 2) * 129 + x * 2) * 4 + c])
            ch.append(row)
        paint_cache[j] = ch
    return paint_cache[j]


def corr(a, b):
    n = len(a); ma = sum(a) / n; mb = sum(b) / n
    sa = sum((x - ma) ** 2 for x in a); sb = sum((x - mb) ** 2 for x in b)
    if sa < 1e-6 or sb < 1e-6:
        return 0.0
    return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / math.sqrt(sa * sb)


# Is there a fixed index relationship between chunk and paint?
tests = {}
keys = list(slopes)[:24]
for offset in range(-160, 161):
    total = n = 0
    for k in keys:
        j = k + offset
        if 0 <= j < len(paints):
            best = max(abs(corr(slopes[k][0], c)) for c in paint(j))
            total += best; n += 1
    if n >= 12:
        tests[offset] = total / n
top = sorted(tests.items(), key=lambda kv: -kv[1])[:6]
print("best fixed offsets", [(k, round(v, 3)) for k, v in top], "median", round(sorted(tests.values())[len(tests) // 2], 3))
# Per-chunk best match anywhere: strong one-to-one matches would reveal another ordering.
rows = []
for k in keys[:10]:
    best = max(((abs(corr(slopes[k][0], c)), j, ci) for j in range(0, len(paints), 1) for ci, c in enumerate(paint(j))), key=lambda t: t[0])
    rows.append((k, round(best[0], 3), best[1], best[2]))
print("global best per chunk", rows)
d = zlib.decompress(s[paints[0][0]:paints[0][0] + paints[0][2]])
print("paint 0", [round(sum(d[4 + c::4]) / 16641) for c in range(4)], "unused", d[:4].hex())
