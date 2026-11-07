import json, re, struct, subprocess
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
g = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning")
syms = json.loads((root / "work/v20-inputs/symbols.json").read_text())
fab = syms["fab"]
hits = {k: v for k, v in fab.items() if re.search(r"head|face|hair|helm|hood|neck", v, re.I)}
print(len(hits), sorted(hits.values())[:150])
b = (root / "outputs/DATA-archive-list.txt").read_bytes()
names = set(x.strip() for x in b.decode("utf-16" if b[:2] == b"\xff\xfe" else "utf-8-sig").splitlines())
want = [k for k, v in hits.items() if re.search(r"(almain|varani|human|player|peasant|male).*(head|face)|(head|face).*(almain|varani|human|male)|me_", v, re.I) and not re.search("female|statue", v, re.I)][:60]
d = root / "work/v20-inputs/DATA_0.pak"
sel = [f"{k}.fab_visual_data_streamable_bin" for k in want if f"{k}.fab_visual_data_streamable_bin" in names]
sel = [n for n in sel if not (d / n).exists()]
if sel:
    subprocess.run([str(g / "modding/pakfileunpacker.exe"), str(g / "data/DATA_0.pak"), "unpack", str(d), *sel], cwd=g / "modding", capture_output=True, timeout=200)
rows = []
for k in want:
    p = d / f"{k}.fab_visual_data_streamable_bin"
    if p.exists():
        v = p.read_bytes()
        if len(v) < 40: continue
        a, bb, c, st, _, n = struct.unpack_from("<6I", v, 0)
        if st < 20 or n == 0: continue
        z = [struct.unpack_from("<f", v, 24 + i * st + 8)[0] for i in range(0, n, max(1, n // 200))]
        rows.append((fab[k], k, st, n, round(min(z)), round(max(z))))
print(sorted(rows))
