"""Find the shop exit object, the matching outdoor door, and the outdoor space and terrain that hold it."""
import json, re, struct, subprocess
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
g = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning")
inp = root / "work/v20-inputs"
syms = json.loads((inp / "symbols.json").read_text())
gor, sp = syms["globalobjectref"], syms["simspace"]
listing = {}
for arch, n in (("DATA_0.pak", "DATA"), ("initial_0.pak", "initial"), ("patch_0.pak", "patch")):
    b = (root / f"outputs/{n}-archive-list.txt").read_bytes()
    listing[arch] = [x.strip() for x in b.decode("utf-16" if b[:2] == b"\xff\xfe" else "utf-8-sig").splitlines() if x.strip()]


def extract(names):
    out = {}
    for arch, have in listing.items():
        hs = set(have)
        sel = [n for n in names if n in hs]
        d = inp / arch
        d.mkdir(parents=True, exist_ok=True)
        for start in range(0, len(sel), 40):
            todo = [n for n in sel[start:start + 40] if not (d / n).exists()]
            if todo:
                subprocess.run([str(g / "modding/pakfileunpacker.exe"), str(g / "data" / arch), "unpack", str(d), *todo], cwd=g / "modding", capture_output=True, timeout=280)
        for n in sel:
            if (d / n).exists():
                out[n] = d / n
    return out


related = {k: v for k, v in gor.items() if re.search(r"alchemist|gorhart", v, re.I)}
print(len(related), sorted(related.values())[:70])
files = extract([f"{v}.gor_bxml" for k, v in related.items() if "alchemist" in v.lower()] + ["int_dal_gorhart_alchemistshop_exit.gor_bxml"])
for n, p in files.items():
    d = p.read_bytes()
    print("==", n, len(d), d[:120].hex())
    f = struct.unpack_from("<12f", d, 24) if len(d) > 72 else ()
    print("   ids", struct.unpack_from("<6I", d, 0), "pos?", [round(x, 1) for x in f[:3]])
    print("   text", [x.decode() for x in re.findall(rb"[A-Za-z_][A-Za-z0-9_]{4,}", d)][:8])

out_ids = [k for k, v in sp.items() if v.startswith(("out_dal", "out_"))]
print("outdoor spaces", len(out_ids))
files = extract([f"{k}.space_bxml" for k in out_ids])
print("extracted", len(files))
terrain = {int(x.split(".")[0]) for a in listing.values() for x in a if x.endswith(".terrain_bin") and x.split(".")[0].isdigit()}
ids = {int(k) for k in related}
hits = []
for n, p in files.items():
    d = p.read_bytes()
    words = set(struct.unpack_from(f"<{len(d) // 4}I", d, 0))
    found = words & ids
    if found:
        hits.append((n, sp.get(n.split(".")[0]), len(d), sorted(gor[str(x)] for x in found)[:12], sorted(words & terrain)[:4], p.parent.name))
for h in sorted(hits, key=lambda r: -len(r[3])):
    print(h)
print("all outdoor by size", sorted(((p.stat().st_size, sp.get(n.split('.')[0])) for n, p in files.items()), reverse=True)[:12])
# Which outdoor spaces reference any terrain, by position in file: list a few to learn the link.
print("terrain links", [(sp.get(n.split('.')[0]), sorted(set(struct.unpack_from(f"<{p.stat().st_size // 4}I", p.read_bytes(), 0)) & terrain)[:2]) for n, p in list(files.items())[:25]])
