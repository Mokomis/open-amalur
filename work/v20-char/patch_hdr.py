import pickle, struct, zlib
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
s = (root / "work/v20-inputs/DATA_0.pak/431658.terrain_streamable_bin").read_bytes()
idx = pickle.load(open(root / "work/v20-char/terrain-index.pkl", "rb"))
at, comp = idx[(2048, 768)]
d = zlib.decompress(s[at:at + comp])
print("chunk head", struct.unpack_from("<I8H", d, 0), "ints", struct.unpack_from("<6I", d, 68))
marker = struct.pack("<I", 361)
o = 0; n = 0; last = 0
while True:
    o = d.find(marker, o)
    if o < 0 or o + 726 > len(d):
        break
    v = struct.unpack_from("<361H", d, o + 4)
    if max(v) < 65000:
        print(f"grid {n} at {o} gap {o - last}: tail of previous/hdr:", d[max(last, o - 72):o].hex())
        print("    first row", v[:4], "edge", v[16:19], "hdr u32", struct.unpack_from("<6I", d, o - 24) if o > 24 else "")
        last = o + 726; o += 726; n += 1
    else:
        print(f"  mask at {o}", d[o + 4:o + 12].hex()); o += 4
print("trailer", d[last:last + 100].hex(), len(d) - last)
