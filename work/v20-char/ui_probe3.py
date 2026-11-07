import json, re, subprocess, struct
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
g = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning")
dest = root / "work/v21-ui/raw"
L = (root / "outputs/initial-archive-list.txt").read_text(errors="replace").split()
ntx = [x for x in L if x.endswith(".ntx") and not re.search(r"_p\d\d_\d\d\.ntx$", x)]
print("NTX", ntx)
print("FONTPAGES", [x for x in L if re.search(r"(byngve|savapro).*\.ntx$", x)])
for i in range(0, len(ntx), 30):
    subprocess.run([str(g/"modding/pakfileunpacker.exe"), str(g/"data/initial_0.pak"), "unpack", str(dest), *ntx[i:i+30]], cwd=g/"modding", capture_output=True, timeout=240)
for n in ("ui_hud.ntx", "ui_icon_steal.ntx", "ui_mouse_input.ntx"):
    b = (dest/n).read_bytes()
    print(n, len(b), "HEAD", b[:210].hex())
    print(" TAIL", b[-64:].hex())
for f in sorted(dest.glob("*.ntx")):
    if re.search(r"_p\d\d_", f.name): continue
    b = f.read_bytes()
    print(f.name, len(b), b[16:64].hex())
s = json.loads((root / "work/v20-inputs/symbols.json").read_text())
t = s["texture"]
print("TEX", sorted(n for k, n in t.items() if re.search(r"(?i)^ui_|_ui_|^hud|icon|loot_|ledger|frame|compass|reticle", str(n))))
print("UIXML", sorted(s["uixml"].values())[:210])
b = (dest/"iconlist.koaiconlist").read_bytes()
print("ICONS", [x.decode() for x in re.findall(rb"[a-z][\w\-.]{3,}", b)][:220])
b = (dest/"fontlist_common.koafontlist").read_bytes()
print("FONTS", [x.decode() for x in re.findall(rb"[a-z][\w\-.]{3,}", b)][:120])
