"""Split one terrain chunk into sections by scanning for count-prefixed u16 runs and dump them as grids."""
import math, pickle, struct, zlib
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
s = (root / "work/v20-inputs/DATA_0.pak/431658.terrain_streamable_bin").read_bytes()
idx = pickle.load(open(root / "work/v20-char/terrain-index.pkl", "rb"))
at, comp = idx[(2048, 768)]
d = zlib.decompress(s[at:at + comp])
i = 52
print("prefix words", struct.unpack_from("<8I", d, 52))
marks = []
for o in range(0, len(d) - 8):
    a, n = struct.unpack_from("<II", d, o)
    if a in (0, 1, 2, 3, 4) and 8 <= n <= 5000 and o + 8 + n * 2 <= len(d):
        run = struct.unpack_from(f"<{min(n, 64)}H", d, o + 8)
        spread = max(run) - min(run)
        steps = sum(abs(run[k + 1] - run[k]) for k in range(len(run) - 1)) / (len(run) - 1)
        if steps < 400 and spread > 0:
            marks.append((o, a, n, min(run), max(run), round(steps, 1)))
print("runs", marks[:40])
for o, a, n, *_ in marks[:4]:
    side = int(math.sqrt(n))
    run = struct.unpack_from(f"<{n}H", d, o + 8)
    print("run at", o, "n", n, "side", side, "next bytes", d[o + 8 + n * 2:o + 8 + n * 2 + 40].hex())
    for r in range(min(side, 6)):
        print("   ", run[r * side:(r + 1) * side][:20])

pos = 0
for o, a, n, *_ in marks:
    if o < pos:
        continue
    print("section gap", o - pos, "then count", n, "a", a, "gap bytes", d[pos:min(o, pos + 48)].hex())
    pos = o + 8 + n * 2
print("end", pos, len(d))
