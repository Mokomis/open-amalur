"""Scout what going outside needs: exterior spaces, the shop's doors, terrain files and placement scale."""
import collections, json, re, struct, subprocess
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
g = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning")
inp = root / "work/v20-inputs"
syms = json.loads((inp / "symbols.json").read_text())
listing = {}
for arch, n in (("DATA_0.pak", "DATA"), ("initial_0.pak", "initial"), ("patch_0.pak", "patch")):
    b = (root / f"outputs/{n}-archive-list.txt").read_bytes()
    listing[arch] = [x.strip() for x in b.decode("utf-16" if b[:2] == b"\xff\xfe" else "utf-8-sig").splitlines() if x.strip()]


def extract(names):
    out = {}
    for arch, have in listing.items():
        hs = set(have)
        sel = [n for n in names if n in hs]
        if sel:
            d = inp / arch
            d.mkdir(parents=True, exist_ok=True)
            todo = [n for n in sel if not (d / n).exists()]
            if todo:
                subprocess.run([str(g / "modding/pakfileunpacker.exe"), str(g / "data" / arch), "unpack", str(d), *todo], cwd=g / "modding", capture_output=True, timeout=280)
            for n in sel:
                if (d / n).exists():
                    out[n] = d / n
    return out


sp = syms["simspace"]
print("simspace count", len(sp), "samples", list(sp.values())[:12])
print("dal/gorhart spaces", [(k, v) for k, v in sp.items() if re.search(r"gorh|gorhart|dalent|dal_|canneroc|odarath", v, re.I)][:60])
print("shop", sp.get("524859"), "| terrain syms", syms["terrain"])
print("load doors", [v for v in syms["globalobjectref"].values() if re.search(r"loaddoor", v, re.I) and re.search(r"gorh|dal", v, re.I)][:30])
for arch, have in listing.items():
    c = collections.Counter(Path(x).suffix for x in have if "terrain" in x or "veggie" in x)
    print(arch, dict(c))
terr = [x for x in listing["DATA_0.pak"] if x.endswith(".terrain_bin")]
print("terrain_bin sample", terr[:15])
files = extract(terr[:3] + [x.replace(".terrain_bin", ".terrain_streamable_bin") for x in terr[:3]])
for n, p in sorted(files.items()):
    d = p.read_bytes()
    print("==", n, len(d), d[:96].hex())
    print("   u32", struct.unpack_from("<16I", d, 0))
    print("   f32", [round(x, 2) for x in struct.unpack_from("<16f", d, 0)])

# Scale of exterior spaces: file sizes as a proxy, and what the largest named ones reference.
spaces = [x for x in listing["DATA_0.pak"] if x.endswith(".space_bxml")]
want = [k for k, v in sp.items() if re.search(r"gorh|dalent|ext_dal", v, re.I)][:12]
files = extract([f"{k}.space_bxml" for k in want])
terrain_ids = set(int(x.split(".")[0]) for x in terr if x.split(".")[0].isdigit())
for n, p in sorted(files.items()):
    d = p.read_bytes()
    sid = n.split(".")[0]
    words = struct.unpack_from(f"<{len(d) // 4}I", d, 0)
    print(n, sp.get(sid), len(d), "terrain refs", sorted(set(w for w in words if w in terrain_ids))[:5], "region", struct.unpack_from("<I", d, 8 + 0x34)[0], "count@152", struct.unpack_from("<I", d, 8 + 156)[0])
shop = extract(["524859.space_bxml"]).get("524859.space_bxml")
if shop:
    d = shop.read_bytes()
    words = struct.unpack_from(f"<{len(d) // 4}I", d, 0)
    print("shop refs to globalobjectref", [syms["globalobjectref"][str(w)] for w in set(words) if str(w) in syms["globalobjectref"]][:40])
    print("shop refs to simspace", [sp[str(w)] for w in set(words) if str(w) in sp][:20])
