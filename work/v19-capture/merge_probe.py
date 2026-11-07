"""Find the merge and final shaders by code shape, and test the region's table against the live one."""
import json, struct, sys
from pathlib import Path

root = Path.home() / "Documents" / "Opem Amalur"
stage = root / "work/v19-capture/run3"
sys.path.insert(0, str(root / "work/v19-lighting"))
from decode_scene_lighting import decode_region

shaders = root / "outputs/scene-v19/shaders"
print("=== Candidates")
for path in sorted(shaders.glob("*.asm")):
    code = [l for l in path.read_text(errors="replace").splitlines() if not l.startswith("//")]
    if not code or not code[0].startswith("ps_"):
        continue
    tex2 = sum("dcl_resource_texture2d" in l for l in code)
    text = "\n".join(code)
    cube = "texturecube" in text
    if cube or "o1." in text or len(code) > 90 or not 2 <= tex2 <= 5:
        continue
    lutish = "round_ni" in text or "frc" in text or "l(0.299" in text or "0.212600" in text
    if lutish and "CB4" in text.replace("cb4", "CB4"):
        print("---", path.stem, "lines", len(code), "tex", tex2)
        print("\n".join(l for l in code if not l.startswith(("dcl_sampler", "dcl_temps", "dcl_input", "dcl_resource", "dcl_constant"))))

meta = json.loads(next(stage.glob("tex_*_merge_in_lut.json")).read_text())
lut = next(stage.glob("tex_*_merge_in_lut.raw")).read_bytes()
pitch = meta["pitch"]
live = [lut[i * pitch + (i * 16 + i) * 4] for i in range(16)]
print("=== Live grey axis", live)

ids = {}
for path in (root / "work").rglob("*.region_bxml"):
    try:
        r = decode_region(path.read_bytes())
    except Exception:
        continue
    env = r["environment"]
    d = env["directional_light_direction"]["value"]
    if any(v is None for v in d) or abs(d[1] - 0.56426) > 0.0005 or abs(d[2] + 0.8256) > 0.0005:
        continue
    for key in env["keys"]:
        ids.setdefault(env["time_keyed"]["color_correction_texture_id"][key]["value"], set()).add((path.name, key))
print("=== Table ids for matching regions")
for tid, rows in ids.items():
    print(tid, len(rows), sorted(rows)[:3])
    hits = [p for p in (root / "work").rglob("%s.dds" % tid) if p.is_file()] if tid else []
    if hits:
        body = hits[0].read_bytes()
        print("  file", hits[0].name, len(body), "grey", [body[38:][(i * 256 + i * 16 + i) * 4] for i in range(16)])
