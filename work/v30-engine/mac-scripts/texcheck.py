import json, re, sys
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
s = json.loads((root / "work/v20-inputs/symbols.json").read_text())["texture"]
ids = {k: v for k, v in s.items() if v in ("me_torso_d", "me_legs_d", "me_hands_d", "me_armor_feet_d", "01_ljosalfar_peasant_male_head_d")}
print(ids)
for n in ("DATA", "initial", "patch"):
    b = (root / f"outputs/{n}-archive-list.txt").read_bytes()
    names = [x.strip() for x in b.decode("utf-16" if b[:2] == b"\xff\xfe" else "utf-8-sig").splitlines()]
    for k in ids:
        print(n, ids[k], [x for x in names if x.startswith(k + "_") or x.startswith(k + ".")][:8])
sys.path[:0] = [str(root / "work/v09-textures")]
src = (root / "work/v09-textures/keen_texture.py").read_text()
i = src.index("def decode(data,level=0)")
print(src[:900]); print(src[i:i + 900])
t = (root / "work/v11-textures/build_scene_materials.py").read_text()
for m in re.finditer(r".*(_3|_0|\.dds|mip|decode_texture).*", t):
    print("B:", m.group(0).strip()[:150])
