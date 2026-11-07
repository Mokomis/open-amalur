import json, re, subprocess, struct, collections
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
g = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning")
dest = root / "work/v21-ui/raw"; dest.mkdir(parents=True, exist_ok=True)
L = {n: (root / f"outputs/{n}-archive-list.txt").read_text(errors="replace").split() for n in ("initial", "patch")}
def unpack(pak, names):
    for i in range(0, len(names), 40):
        subprocess.run([str(g/"modding/pakfileunpacker.exe"), str(g/"data"/f"{pak}_0.pak"), "unpack", str(dest), *names[i:i+40]], cwd=g/"modding", capture_output=True, timeout=240)
for e in ("koafontlist", "koaiconlist", "font", "ntx"):
    print(e, "initial", [x for x in L["initial"] if x.endswith("."+e)][:90])
    print(e, "patch", [x for x in L["patch"] if x.endswith("."+e)][:10])
unpack("initial", [x for x in L["initial"] if x.endswith((".koafontlist", ".koaiconlist", ".font"))])
unpack("patch", [x for x in L["patch"] if x.endswith((".koafontlist", ".font"))])
ntx = [x for x in L["initial"] if x.endswith(".ntx")]
unpack("initial", ntx[:6])
for f in sorted(dest.iterdir()):
    b = f.read_bytes()
    print(f.name, len(b), b[:48].hex(), re.findall(rb"[A-Za-z][\w ./\-]{5,}", b[:4000])[:12])
s = json.loads((root / "work/v20-inputs/symbols.json").read_text())
print("cats", {k: len(v) for k, v in s.items()} if all(hasattr(v,'__len__') for v in s.values()) else list(s)[:80])
for cat, v in s.items():
    if isinstance(v, dict):
        hit = [(k, n) for k, n in v.items() if re.search(r"(?i)^ui_|_ui_|^hud|icon|compass|minimap", str(n))]
        if hit and len(hit) > 5: print("CAT", cat, len(hit), hit[:60])
