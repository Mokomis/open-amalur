"""Why foliage textures fail, and what the terrain paint data looks like near the door."""
import json, re, struct, sys, zlib, collections, subprocess
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
sys.path[:0] = [str(root / "work/v09-textures")]
import keen_texture
g = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning")
inp = root / "work/v20-inputs"
syms = json.loads((inp / "symbols.json").read_text())
listing = {}
for arch, n in (("DATA_0.pak", "DATA"), ("initial_0.pak", "initial"), ("patch_0.pak", "patch")):
    b = (root / f"outputs/{n}-archive-list.txt").read_bytes()
    listing[arch] = [x.strip() for x in b.decode("utf-16" if b[:2] == b"\xff\xfe" else "utf-8-sig").splitlines() if x.strip()]
src = (root / "work/v09-textures/keen_texture.py").read_text()
print(src[src.index("def parse"):src.index("def decode(data")][:2600])
for name in ("for_flora_treebranch", "vil_bannerstand"):
    mid = next(k for k, v in syms["material"].items() if v == name)
    p = next((inp / a / f"{mid}.mat_bxml" for a in ("patch_0.pak", "initial_0.pak") if (inp / a / f"{mid}.mat_bxml").exists()))
    d = p.read_bytes()
    refs = []
    for i in range(0, len(d) - 3, 4):
        v = struct.unpack_from("<I", d, i)[0]
        if str(v) in syms["texture"] and v not in refs:
            refs.append(v)
    print(name, mid, [(v, syms["texture"][str(v)]) for v in refs])
    for v in refs[:2]:
        names = [(a, x) for a, have in listing.items() for x in have if x.startswith(f"{v}_") or x.startswith(f"{v}.")]
        print("  files", names[:8])
        for a, x in names[:5]:
            q = inp / a / x
            if not q.exists():
                subprocess.run([str(g / "modding/pakfileunpacker.exe"), str(g / "data" / a), "unpack", str(inp / a), x], cwd=g / "modding", capture_output=True, timeout=120)
            if q.exists():
                b = q.read_bytes()
                print("   ", x, len(b), b[:44].hex())
                try:
                    info = keen_texture.parse(b)
                    print("     ", {k: info[k] for k in info if k in ("observed_format", "original_width", "original_height", "selected_mip_shift")}, info["mips"][:3])
                except Exception as e:
                    print("      parse:", e)

h = (inp / "DATA_0.pak/431658.terrain_bin").read_bytes()
s = (inp / "DATA_0.pak/431658.terrain_streamable_bin").read_bytes()
base = 16777236 - 16777216 + 16
print("first block sample hex", s[:40].hex())
for offset in (20, 24, 36):
    row = 793; col = 2080
    v = s[offset + row * 4096 + col - 8:offset + row * 4096 + col + 8]
    print("offset", offset, "door row bytes", v.hex())
counter = collections.Counter(s[36 + 700 * 4096 + 1900 + i] for i in range(400))
print("value hist at door rows", collections.Counter(s[36 + r * 4096 + c] for r in range(760, 830, 2) for c in range(2040, 2120, 2)).most_common(12))
print("whole map hist (sampled)", collections.Counter(s[36 + i] for i in range(0, 16777216, 997)).most_common(16))
# Paint map records and how they relate to chunk order
i = 16777236
recs = []
while True:
    i = s.find(b"\x78\x9c", i)
    if i < 0:
        break
    raw, total, zero, raw2, comp = struct.unpack_from("<5I", s, i - 20)
    if raw == raw2 and zero == 0 and comp <= total <= comp + 32 and i + comp <= len(s):
        recs.append((i, raw, comp, struct.unpack_from("<I", s, i - 24)[0])); i += comp; continue
    i += 1
kinds = [("P" if r[1] == 66568 else "C") for r in recs]
print("sequence start", "".join(kinds[:120]), "first P", kinds.index("P"), "counts", collections.Counter(kinds))
pr = [r for r in recs if r[1] == 66568]
print("paint prefix u32", [r[3] for r in pr[:12]])
d = zlib.decompress(s[pr[800][0]:pr[800][0] + pr[800][2]])
print("paint head", d[:8].hex(), "channel means", [round(sum(d[4 + c::4]) / 16641, 1) for c in range(4)])
print("bin after header", struct.unpack_from("<30I", h, 0x50))
print("palette file", [(a, x) for a, have in listing.items() for x in have if x.startswith("4720.") or x.startswith("4720_") or x == "terrainpal-odayle_valley"][:6])
ids = {int(k): v for k, v in syms["texture"].items()}
print("forest terrain textures", sorted(v for v in ids.values() if v.startswith("for_terrain")))
