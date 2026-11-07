"""Extract the human skeleton, core hero animations and player motion tree, and dump their structure."""
import json, re, struct, subprocess
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
g = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning")
want = ["456813.fab_bxml", "456813.fab_visual_data_streamable_bin", "467100.fab_bxml", "5437.anm_bxml", "5446.anm_bxml", "5475.anm_bxml", "100644.mtn_tree_bxml", "669805.gor_bxml", "player_human_male.gor_bxml"]
found = {}
for arch, listing in (("DATA_0.pak", "DATA"), ("initial_0.pak", "initial"), ("patch_0.pak", "patch")):
    b = (root / f"outputs/{listing}-archive-list.txt").read_bytes()
    names = set(x.strip() for x in b.decode("utf-16" if b[:2] == b"\xff\xfe" else "utf-8-sig").splitlines())
    sel = [n for n in want if n in names]
    print(arch, sel)
    if sel:
        d = root / "work/v20-inputs" / arch
        d.mkdir(parents=True, exist_ok=True)
        subprocess.run([str(g / "modding/pakfileunpacker.exe"), str(g / "data" / arch), "unpack", str(d), *sel], cwd=g / "modding", capture_output=True, timeout=250)
        for n in sel:
            if (d / n).exists():
                found[n] = d / n
for n, p in found.items():
    d = p.read_bytes()
    print("=====", n, p.parent.name, len(d))
    a, c = struct.unpack_from("<II", d, 0)
    print("u32 header", a, c, "sum check", 8 + a + c == len(d))
    print(d[:112].hex())
    s = [x.decode()[:40] for x in re.findall(rb"[A-Za-z_][A-Za-z0-9_./-]{3,}", d)]
    print("strings", len(s), s[:70])
    if n.endswith("anm_bxml"):
        print("floats", [round(x, 3) for x in struct.unpack_from("<12f", d, 8)])
        print("u16", struct.unpack_from("<24H", d, 20))
syms = json.loads((root / "work/v20-inputs/symbols.json").read_text())
fab = syms["fab"]
print("armor-ish", [(s, v) for s, v in fab.items() if re.search(r"armor|cloth|robe|peasant|naked|nude|underwear|prisoner|corpse", v, re.I)][:60])
print("hero anim all", [(s, v) for s, v in syms["animation"].items() if v.lower().startswith("hero_")][:12])
