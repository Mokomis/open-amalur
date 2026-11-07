"""Compare live captured values with shader code, the color table and decoded authored regions."""
import json, math, re, struct, sys
from pathlib import Path

root = Path.home() / "Documents" / "Opem Amalur"
capture = root / "work/v19-capture"
stage = capture / "run3"
sys.path.insert(0, str(root / "work/v19-lighting"))
from decode_scene_lighting import decode_region, DecodeError


def load(label):
    path = next(stage.glob("tex_*_%s.json" % label))
    meta = json.loads(path.read_text())
    return meta, path.with_suffix(".raw").read_bytes()


# Live 256x16 table: 16 slices across, each 16x16.
meta, lut = load("merge_in_lut")
pitch = meta["pitch"]
print("=== Live color table (input -> output, 8-bit), identity would equal the input")
rows = []
for level in range(16):
    slice_ = level
    x = slice_ * 16 + level
    y = level
    r, g, b, a = lut[y * pitch + x * 4:y * pitch + x * 4 + 4]
    rows.append((level * 17, r, g, b))
    print(level * 17, "->", r, g, b)
diff = sum(abs(s[0] - c) for s in rows for c in s[1:]) / (3 * len(rows))
print("mean distance from identity on the grey axis:", round(diff, 2))

asset = next((p for p in (root / "work").rglob("1525613*") if p.is_file()), None)
if asset:
    raw = asset.read_bytes()
    print("=== Asset LUT 1525613 grey axis", asset.name, len(raw))
    body = raw[38:]
    print([(i * 17, body[(i * 256 + i * 16 + i) * 4]) for i in range(16)])


def stats(label):
    m, d = load(label)
    w, h, p, fmt = m["w"], m["h"], m["pitch"], m["fmt"]
    out = [0.0, 0.0, 0.0]
    peak = [0.0, 0.0, 0.0]
    n = 0
    for y in range(0, h, 8):
        for x in range(0, w, 8):
            if fmt == 10:
                c = struct.unpack_from("<3e", d, y * p + x * 8)
            else:
                c = [v / 255 for v in d[y * p + x * 4:y * p + x * 4 + 3]]
            if any(math.isnan(v) or math.isinf(v) for v in c):
                continue
            n += 1
            for i in range(3):
                out[i] += c[i]
                peak[i] = max(peak[i], c[i])
    print("%-22s fmt %2d mean %s max %s" % (label, fmt, [round(v / n, 4) for v in out], [round(v, 3) for v in peak]))


print("=== Stage levels")
for label in ("combine_in_lit0", "combine_in_lit1", "combine_in_lit2", "combine_in_lit3", "combine_out", "merge_in_second", "merge_in_bloom", "merge_out"):
    stats(label)
m, d = load("combine_in_ramp")
print("ramp 8x1", list(d[:32]))

print("=== Merge-family shaders")
shaders = root / "outputs/scene-v19/shaders"
for path in sorted(shaders.glob("*.asm")):
    code = [l for l in path.read_text(errors="replace").splitlines() if not l.startswith("//")]
    if not code or not code[0].startswith("ps_"):
        continue
    tex2 = sum("dcl_resource_texture2d" in l for l in code)
    tex3 = sum("dcl_resource_texture3d" in l for l in code)
    outs = sum(l.startswith("dcl_output o") for l in code)
    cb0 = any("CB0[3]" in l for l in code) or any("CB0[4]" in l for l in code)
    if outs == 1 and len(code) < 110 and ((tex2 == 4 and tex3 == 0 and cb0) or tex3 >= 2):
        print("---", path.stem, "lines", len(code))
        print("\n".join(l for l in code if not l.startswith(("dcl_sampler", "dcl_temps", "dcl_input"))))

print("=== Regions matching live sun direction")
live_dir = (0.0, -0.56426, 0.8256)
live_sun = (0.25529, 0.23059, 0.15765)
files = [p for p in (root / "work").rglob("*.region_bxml")]
print("region files", len(files))
matches = {}
for path in files:
    try:
        r = decode_region(path.read_bytes())
    except (DecodeError, struct.error, ValueError):
        continue
    env = r["environment"]
    d = env["directional_light_direction"]["value"]
    if any(v is None for v in d) or max(abs(-d[i] - live_dir[i]) for i in range(3)) > 0.0005:
        continue
    for key in r["environment"]["keys"]:
        c = env["time_keyed"]["directional_light_color"][key]["value"]
        i = env["time_keyed"]["directional_light_intensity"][key]["value"]
        sun = [c["rgb"][k] * c["intensity"] * i for k in range(3)]
        fog = env["time_keyed"]["fog_density"][key]["value"]
        fc = env["time_keyed"]["fog_color"][key]["value"]
        tint = env["time_keyed"]["environment_tint"][key]["value"]
        sky = env["time_keyed"]["sky_light_color"][key]["value"]
        err = max(abs(sun[k] - live_sun[k]) for k in range(3))
        cc = env["time_keyed"]["color_correction_texture_id"][key]["value"]
        if r["source_sha256"] not in matches or err < matches[r["source_sha256"]][0]:
            matches[r["source_sha256"]] = (err, path.name, key, [round(v, 4) for v in sun], fog, fc, tint, sky, cc)
print("matching direction:", len(matches))
for row in sorted(matches.values(), key=lambda m: m[0])[:6]:
    print(row)
