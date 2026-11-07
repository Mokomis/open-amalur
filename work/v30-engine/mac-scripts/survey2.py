import re, struct, subprocess, sys
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
g = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning")
for p in (root / "work/v07-mesh/batch_decode_meshes.py", root / "work/v07-bxml/amalur_scene.py"):
    print("=====", p.name, p.stat().st_size)
    print(p.read_text(errors="replace")[:5200])
b = (root / "outputs/initial-archive-list.txt").read_bytes()
names = [x.strip() for x in b.decode("utf-16" if b[:2] == b"\xff\xfe" else "utf-8-sig").splitlines() if x.strip()]
for ext in (".anm_bxml", ".mtns_bxml", ".mtn_tree_bxml", ".animset", ".gor_bxml"):
    sample = [n for n in names if n.endswith(ext)]
    print(ext, len(sample), sample[:12])
print([n for n in names if re.search(r"symbol_table", n)][:40])
pick = [next(n for n in names if n.endswith(e)) for e in (".anm_bxml", ".mtns_bxml", ".mtn_tree_bxml", ".gor_bxml")] + [n for n in names if n in ("symbol_table_animation.bin", "symbol_table_motionset.bin")]
dest = root / "work/v20-inputs/initial_0.pak"
dest.mkdir(parents=True, exist_ok=True)
subprocess.run([str(g / "modding/pakfileunpacker.exe"), str(g / "data/initial_0.pak"), "unpack", str(dest), *pick], cwd=g / "modding", capture_output=True, timeout=200)
for n in pick:
    q = dest / n
    if not q.exists():
        print(n, "missing"); continue
    d = q.read_bytes()
    print("-----", n, len(d), d[:64].hex())
    strs = re.findall(rb"[A-Za-z_][A-Za-z0-9_./ -]{5,}", d)
    print([s.decode()[:48] for s in strs[:40]])
