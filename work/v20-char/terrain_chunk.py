"""Index terrain chunks by grid position and dump the one under the shop door."""
import collections, json, pickle, struct, zlib
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
s = (root / "work/v20-inputs/DATA_0.pak/431658.terrain_streamable_bin").read_bytes()
records = []
i = 16777236
while True:
    i = s.find(b"\x78\x9c", i)
    if i < 0:
        break
    if i >= 24:
        raw, total, zero, raw2, comp = struct.unpack_from("<5I", s, i - 20)
        if raw == raw2 and zero == 0 and comp <= total <= comp + 32 and i + comp <= len(s):
            records.append((i, raw, comp)); i += comp; continue
    i += 1
chunks = {}
for at, raw, comp in records:
    if raw == 66568:
        continue
    d = zlib.decompress(s[at:at + comp])
    h = struct.unpack_from("<I8H", d, 0)
    chunks[(h[1], h[3])] = (at, comp, d)
print("chunks", len(chunks), "x range", min(k[0] for k in chunks), max(k[0] for k in chunks), "y range", min(k[1] for k in chunks), max(k[1] for k in chunks))
cx, cy = (1575.1 + 102425) / 50, (-62759.2 + 102425) / 50
print("door cell", cx, cy)
near = sorted(chunks, key=lambda k: (k[0] + 8 - cx) ** 2 + (k[1] + 8 - cy) ** 2)[:6]
print("nearest", near)
k = near[0]
at, comp, d = chunks[k]
h = struct.unpack_from("<I8H", d, 0)
print("hdr", h, len(d))
print("floats 20..", [round(x, 2) for x in struct.unpack_from("<8f", d, 20)], "ints", struct.unpack_from("<12I", d, 52))
print("bytes 20-140", d[20:140].hex())
# Scan for where a run of plausible heights or vertices starts: stride tests against z near header z.
zc = struct.unpack_from("<f", d, 28)[0]
for stride in (8, 12, 16, 20, 24, 28, 32, 36, 40, 44, 48):
    for start in range(52, 400, 4):
        ok = 0
        for n in range(40):
            at2 = start + n * stride + 8
            if at2 + 4 > len(d):
                break
            z = struct.unpack_from("<f", d, at2)[0]
            if abs(z - zc) < 3000:
                ok += 1
        if ok >= 38:
            print("stride", stride, "start", start, [tuple(round(x, 1) for x in struct.unpack_from("<3f", d, start + n * stride)) for n in range(4)])
            break
print("tail", d[-96:].hex())
print("words", struct.unpack_from("<40I", d, 64))
print("h16", struct.unpack_from("<60H", d, 64))
hist = collections.Counter(len(v[2]) for v in chunks.values())
print("size hist", hist.most_common(6))
pickle.dump({k: (v[0], v[1]) for k, v in chunks.items()}, open(root / "work/v20-char/terrain-index.pkl", "wb"))
