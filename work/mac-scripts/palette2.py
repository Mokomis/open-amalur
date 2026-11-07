"""Find the per-mesh bone palette inside FAB files by value patterns, and dump FAB tails."""
import json, struct
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
inp = root / "work/v20-inputs"
syms = json.loads((inp / "symbols.json").read_text()); bn = syms["ragdoll_bone_mappings"]
fid = 1926574
fb = (inp / f"patch_0.pak/{fid}.fab_bxml").read_bytes()
N = 4 + 0x20 + struct.unpack_from("<I", fb, 4 + 0x20)[0]
n = struct.unpack_from("<H", fb, 4 + 0x10)[0]
names = struct.unpack_from(f"<{n}I", fb, N)
print("order", [(i, str(bn.get(str(x), x))[5:16]) for i, x in enumerate(names)])
end = struct.unpack_from("<I", fb, 0)[0] + 8
print("payload end", end, "size", len(fb), "tail hex", fb[end:end + 600].hex())
for width, fmt in ((1, "B"), (2, "H"), (4, "I")):
    for i in range(0, len(fb) - 4 * width):
        v = struct.unpack_from("<4" + fmt, fb, i)
        if v == (6, 7, 8, 9) or v == (7, 8, 9, 10) or (v[1] == v[0] + 1 and v[2] == v[1] + 1 and v[3] == v[2] + 1 and 0 < v[0] < 40 and width > 1):
            print("run", width, i, struct.unpack_from("<16" + fmt, fb, i) if i + 16 * width <= len(fb) else v)
vis = (inp / f"DATA_0.pak/{fid}.fab_visual_data_streamable_bin").read_bytes()
print("vis tail", vis[-120:].hex())
data = 24 + 1220 * 60
print("after vb", vis[data:data + 32].hex())
print("all idx max", max(max(vis[24 + i * 60 + 12:24 + i * 60 + 16]) for i in range(1220)))
