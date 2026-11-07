"""Find native magic constants, full player clip names, and raw skinned vertex bytes."""
import json, re, struct
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
inp = root / "work/v20-inputs"
syms = json.loads((inp / "symbols.json").read_text())
anim = {int(k): v for k, v in syms["animation"].items()}
exe = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning\koa.exe").read_bytes()
pe = struct.unpack_from("<I", exe, 0x3c)[0]
base = struct.unpack_from("<I", exe, pe + 52)[0]
n = struct.unpack_from("<H", exe, pe + 6)[0]; o = pe + 24 + struct.unpack_from("<H", exe, pe + 20)[0]
secs = [struct.unpack_from("<8sIIII", exe, o + i * 40) for i in range(n)]
def va(off):
    for name, vs, rva, size, raw in secs:
        if raw <= off < raw + size:
            return base + rva + off - raw, name.strip(b"\0").decode()
for magic in (b"50AE", b"30SE", b"30AE", b"40AE", b"60AE"):
    print(magic, [va(m.start()) for m in re.finditer(re.escape(magic), exe)][:20])
names = sorted((v, s) for s, v in anim.items() if v.lower().startswith(("player_", "playera_", "playerm_")))
print(len(names))
print("non-attack", [v for v, s in names if not re.search(r"atk|attk|attack|hit|block|parry|finish|dodge|bow|spr|mag|fate|nisk|staff|hammer|dag|chak|sce|blade|fist|swd|spear|wpn|stone|shield", v)])
print("human loco", [(s, v) for s, v in anim.items() if re.search(r"^human(male)?_?.*(idle|walk|run)(_?0?1|fwd)?$", v, re.I)][:80])
print("hm", [(s, v) for s, v in anim.items() if re.match(r"hm|humanmale", v, re.I)][:70])
vis = (inp / "DATA_0.pak/1926576.fab_visual_data_streamable_bin").read_bytes()
for i in (0, 1, 2, 700, 1333):
    v = vis[24 + i * 60:24 + (i + 1) * 60]
    print(i, v.hex(), [round(x, 3) for x in struct.unpack("<15f", v)][:15], list(v[12:16]))
fb = (inp / "patch_0.pak/1926576.fab_bxml").read_bytes()
print("fab bone table", [(syms["ragdoll_bone_mappings"].get(str(x)) or x) for x in struct.unpack_from("<31I", fb, 1716 + 8 + 0)][:40])
