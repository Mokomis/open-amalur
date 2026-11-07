import json, re, struct, subprocess
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
g = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning")
inp = root / "work/v20-inputs"
syms = json.loads((inp / "symbols.json").read_text())
anim = {int(k): v for k, v in syms["animation"].items()}
b = (root / "outputs/initial-archive-list.txt").read_bytes()
have = set(x.strip() for x in b.decode("utf-16" if b[:2] == b"\xff\xfe" else "utf-8-sig").splitlines())
ids = [(v, k) for k, v in anim.items() if re.search(r"sword|attack|atk|swd|onehand|1h", v, re.I) and re.match(r"(human|hm|player)", v, re.I) and not re.search(r"_f$|_g$|2h|spear|bow|dagger|hammer|staff|_f_|lower|upper", v, re.I)]
d = inp / "initial_0.pak"
names = [f"{k}.anm_bxml" for _, k in ids if f"{k}.anm_bxml" in have]
for s in range(0, len(names), 60):
    todo = [n for n in names[s:s + 60] if not (d / n).exists()]
    if todo:
        subprocess.run([str(g / "modding/pakfileunpacker.exe"), str(g / "data/initial_0.pak"), "unpack", str(d), *todo], cwd=g / "modding", capture_output=True, timeout=280)
rows = []
for v, k in sorted(ids):
    p = d / f"{k}.anm_bxml"
    if p.exists():
        c = p.read_bytes()
        j = struct.unpack_from("<H", c, 8 + 0xe)[0]
        if j == 64:
            rows.append((v, k, round(struct.unpack_from("<f", c, 12)[0], 2)))
print(len(ids), "64-joint", len(rows))
print(rows[:110])
