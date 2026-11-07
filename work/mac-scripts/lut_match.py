"""Extract table 1426979 with the game's own unpacker and compare it with the live 256x16 table."""
import json, subprocess
from pathlib import Path
root = Path.home() / "Documents" / "Opem Amalur"
g = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning")
ID = "1426979"
body = None
for n, a in (("DATA", "DATA_0.pak"), ("initial", "initial_0.pak"), ("patch", "patch_0.pak")):
    b = (root / f"outputs/{n}-archive-list.txt").read_bytes()
    names = [x.strip() for x in b.decode("utf-16" if b[:2] == b"\xff\xfe" else "utf-8-sig").splitlines()]
    hits = [x for x in names if x.startswith(ID)]
    print(a, hits)
    if hits:
        d = root / "work/v19-inputs" / a
        d.mkdir(parents=True, exist_ok=True)
        subprocess.run([str(g / "modding/pakfileunpacker.exe"), str(g / "data" / a), "unpack", str(d), *hits], cwd=g / "modding", capture_output=True, timeout=200)
        q = d / hits[0]
        if q.exists():
            body = q.read_bytes()
            print(q.name, len(body), body[:48].hex())
if body is None:
    raise SystemExit("not extracted")
stage = root / "work/v19-capture/run4"
m = json.loads(next(stage.glob("tex_*_merge_in_lut.json")).read_text())
live = next(stage.glob("tex_*_merge_in_lut.raw")).read_bytes()
tex = body[38:]
print("grey asset", [tex[(i * 256 + i * 16 + i) * 4] for i in range(16)])
print("grey live ", [live[i * m["pitch"] + (i * 16 + i) * 4] for i in range(16)])
for name, order in (("asset index (b,g,r)", lambda r, g, b: (b * 256 + g * 16 + r)), ("asset index (r,g,b)", lambda r, g, b: (r * 256 + g * 16 + b))):
    total = n = worst = 0
    for b in range(16):
        for g_ in range(16):
            for r in range(16):
                row = g_ * m["pitch"] + (b * 16 + r) * 4
                at = order(r, g_, b) * 4
                for c in range(3):
                    e = abs(live[row + c] - tex[at + c]); total += e; n += 1; worst = max(worst, e)
    print(name, "mean error", round(total / n, 3), "worst", worst)
