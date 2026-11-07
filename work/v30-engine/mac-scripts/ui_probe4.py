import re, struct, subprocess, sys, zlib, tarfile, collections
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
sys.path[:0] = [str(root / "work/v09-textures")]
import keen_texture, json
g = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning")
raw = root / "work/v21-ui/raw"; out = root / "work/v21-ui/png"
sym = json.loads((root / "work/v20-inputs/symbols.json").read_text())["texture"]
ids = {str(n): k for k, n in sym.items()}
def png(path, w, h, rgba):
    c = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d))
    rows = b"".join(b"\0" + bytes(rgba[y*w*4:(y+1)*w*4]) for y in range(h))
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + c(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)) + c(b"IDAT", zlib.compress(rows, 6)) + c(b"IEND", b""))
for n in ("savapro_mediumsavapro_medium_p00_00", "byngve_boldbyngve_bold_p00_00"):
    a = (raw/f"{n}.ntx").read_bytes()[80:80+262144]
    png(out/f"{n}.png", 512, 512, b"".join(bytes((x, x, x, 255)) for x in a))
D = root/"work/v21-ui/dds"
extra = ["ui_icons_inv_weapons_armor","ui_icons_inv_weapons_armor_02","ui_icons_inv_weapons_common_02","ui_icons_inv_weapons_mit_01","ui_icons_inv_armor_02","ui_icons_craft_components","ui_icons_gem_shards","ui_main_menu_4","ui_main_menu_5","ui_main_menu_6","ui_main_menu_7"]
names = [f"{ids[n]}.dds" for n in extra if n in ids]
subprocess.run([str(g/"modding/pakfileunpacker.exe"), str(g/"data/initial_0.pak"), "unpack", str(D), *names], cwd=g/"modding", capture_output=True, timeout=300)
for n in extra:
    q = D/f"{ids[n]}.dds"
    if not q.exists(): print("nofile", n); continue
    data = q.read_bytes(); w,h,fmt = *struct.unpack_from("<HH", data, 20), data[29]
    size = ((w+3)//4)*((h+3)//4)*(8 if fmt==1 else 16)
    png(out/f"{n}.png", w, h, bytes(keen_texture.decode_blocks(data[38:38+size], w, h, fmt))); print(n, w, h)
with tarfile.open(root/"work/v21-ui/png.tar","w") as t: t.add(out, arcname="png")
# Localization: find English UI and item strings.
L = (root/"outputs/initial-archive-list.txt").read_text(errors="replace").split()
print("EN paks", [p.name for p in (g/"data").iterdir()][:8])
en = g/"data/en_us_0.pak"
loc = [x for x in L if x.endswith(".localization_table")]
print("loc sample", loc[:6], len(loc))
ld = root/"work/v21-ui/loc"; ld.mkdir(parents=True, exist_ok=True)
pick = [x for x in loc if re.search(r"(?i)item|ui|menu|interface|weapon|armor|ability|ledger|common|global", x)][:60]
print("pick", pick[:40])
