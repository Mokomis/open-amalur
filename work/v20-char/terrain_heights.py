"""Find how heights are stored inside one chunk."""
import pickle, struct, zlib
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
s = (root / "work/v20-inputs/DATA_0.pak/431658.terrain_streamable_bin").read_bytes()
idx = pickle.load(open(root / "work/v20-char/terrain-index.pkl", "rb"))
at, comp = idx[(2048, 768)]
d = zlib.decompress(s[at:at + comp])
print(len(d))
zc = 5158.1
runs = []
start = None
for i in range(0, len(d) - 3, 4):
    v = struct.unpack_from("<f", d, i)[0]
    good = v == v and abs(v - zc) < 2500 and abs(v) > 1
    if good and start is None:
        start = i
    if not good and start is not None:
        if i - start >= 40:
            runs.append((start, (i - start) // 4))
        start = None
print("float z runs", runs[:20])
# Map non-mask regions: entropy per 256 bytes
for o in range(0, len(d), 1024):
    b = d[o:o + 1024]
    print(o, len(set(b)), b[:24].hex())
# Try layouts: header section offsets
print("ints@52", struct.unpack_from("<24I", d, 52))
for o in (112, 144, 160, 176, 192, 256, 512, 1024, 2048, 4096):
    print(o, d[o:o + 40].hex())
