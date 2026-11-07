"""Version 0.20.0: foliage cutouts, non-square textures, slope-chosen ground, Workbench texture."""
import hashlib, struct, sys
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
host = root / "work/v19-host"
wc = root / "work/v20-char"


def edit_text(t, name, pairs):
    for old, new in pairs:
        if t.count(old) != 1:
            raise SystemExit("%s: expected one match for %r, found %d" % (name, old[:90], t.count(old)))
        t = t.replace(old, new)
    return t


p = wc / "build_town.py"
t = edit_text(p.read_text(encoding="utf-8"), "build_town", [
 ('''def load_texture(tid):
    if tid in tex_index:
        return tex_index[tid]
    names = [f"{tid}.dds"] + [f"{tid}_{k}.dds" for k in range(6)]
    files = extract(names)
    best = None
    for name in names:
        if name not in files:
            continue
        try:
            data = files[name].read_bytes()
            for level_index in range(len(keen_texture.parse(data)["mips"])):
                rgba, info = keen_texture.decode(data, level_index)
                w, h = info["decoded_width"], info["decoded_height"]
                if max(w, h) <= TEXTURE_LIMIT:
                    if best is None or w > best[0]:
                        best = (w, h, bytes(rgba), info["alpha_min"])
                    break
        except Exception:
            report["texture_decode_failures"] += 1
    if best is None:
        tex_index[tid] = (FALLBACK, 255)
    else:
        tex_index[tid] = (len(tex_rgba), best[3])
        tex_rgba.append(dict(width=best[0], height=best[1], rgba=best[2]))
    return tex_index[tid]
''', '''def decode_best(tid):
    """Largest stored level within the limit. Non-square carriers stop at their declared mip count."""
    names = [f"{tid}.dds"] + [f"{tid}_{k}.dds" for k in range(6)]
    files = extract(names)
    best = None
    for name in names:
        if name not in files:
            continue
        data = files[name].read_bytes()
        if data[16:20] != b"KEEN" or data[29] not in (1, 5):
            report["texture_unsupported_format"] += 1
            continue
        w, h, fmt, mips = *struct.unpack_from("<HH", data, 20), data[29], struct.unpack_from("<H", data, 35)[0]
        at = 38
        block = 8 if fmt == 1 else 16
        for _ in range(mips):
            size = ((w + 3) // 4) * ((h + 3) // 4) * block
            if at + size > len(data):
                report["texture_truncated"] += 1
                break
            if max(w, h) <= TEXTURE_LIMIT:
                if best is None or w > best[0]:
                    best = (w, h, bytes(keen_texture.decode_blocks(data[at:at + size], w, h, fmt)))
                break
            at += size
            w, h = max(1, w // 2), max(1, h // 2)
    return best


def load_texture(tid, alpha_tid=None):
    key = (tid, alpha_tid)
    if key in tex_index:
        return tex_index[key]
    best = decode_best(tid)
    if best is None:
        tex_index[key] = FALLBACK
        return FALLBACK
    w, h, rgba = best
    out_rgba = bytearray(rgba)
    # Stored alpha is not opacity on these materials unless a separate _a map exists.
    out_rgba[3::4] = b"\\xff" * (w * h)
    mask = decode_best(alpha_tid) if alpha_tid else None
    if mask:
        mw, mh, mr = mask
        for y in range(h):
            for x in range(w):
                out_rgba[(y * w + x) * 4 + 3] = mr[((y * mh // h) * mw + x * mw // w) * 4]
    tex_index[key] = len(tex_rgba)
    tex_rgba.append(dict(width=w, height=h, rgba=bytes(out_rgba)))
    return tex_index[key]
'''),
 ('''    result = (FALLBACK, 255)
    if files:''', '''    result = FALLBACK
    if files:'''),
 ('''        for tid, name in order:
            result = load_texture(tid)
            if result[0] != FALLBACK:
                break
''', '''        alpha = next((r[0] for r in refs if r[1].lower().endswith("_a")), None)
        for tid, name in order:
            result = load_texture(tid, alpha)
            if result != FALLBACK:
                break
'''),
 ('''    texture, alpha = material_texture(material)
    if alpha < 128:
        report["alpha_assemblies_skipped"] += 1
        continue
''', '''    texture = material_texture(material)
'''),
 ('''ground_tris = []
ground_verts = bytearray()
''', '''ground_tris = []
ground_blocks = {"grass": bytearray(), "rock": bytearray(), "cliff": bytearray()}
'''),
 ('''            for p, n, uv in tri:
                ground_verts += struct.pack("<9f", *p, *n, .35, .42, .22) + struct.pack("<2f", *uv)
''', '''            # Authored approximation: texture by slope, because paint maps are not linked to patches yet.
            upness = (tri[0][1][2] + tri[1][1][2] + tri[2][1][2]) / 3
            band = "grass" if upness > .84 else "rock" if upness > .62 else "cliff"
            for p, n, uv in tri:
                ground_blocks[band] += struct.pack("<9f", *p, *n, .35, .42, .22) + struct.pack("<2f", *uv)
'''),
 ('''ground_name = next((k for k, v in syms["texture"].items() if v == "for_terrain_grass01_d"), None)
ground_tex = load_texture(int(ground_name))[0] if ground_name else FALLBACK
print("ground texture", ground_name, ground_tex)
per_texture[ground_tex].insert(0, ground_verts)
''', '''ground_ids = {band: next((k for k, v in syms["texture"].items() if v == name), None) for band, name in (("grass", "for_terrain_grass01_d"), ("rock", "for_terrain_rock01_d"), ("cliff", "for_terrain_cliff01_d"))}
print("ground textures", ground_ids)
ground_tex = FALLBACK
for band, block in ground_blocks.items():
    tid = load_texture(int(ground_ids[band]))
    if band == "grass":
        ground_tex = tid
    per_texture[tid].insert(0, block)
    report["ground_" + band + "_triangles"] = len(block) // 132
'''),
 ('''print("dark textures", {i: v for i, v in stats.items() if sum(v[2:5]) < 90})
print("who uses dark", collections.Counter((a[1], a[3], a[2], tuple(a[4])) for a in audit if a[2] in stats and sum(stats[a[2]][2:5]) < 90).most_common(14))
''', '''print("cutout textures", {i: v for i, v in stats.items() if v[5] < 250})
'''),
])
p.write_text(t, encoding="utf-8", newline="\n")

# Shop sidecar: give the Workbench's fallback draw the texture the old reader rejected.
sys.path[:0] = [str(root / "work/v09-textures")]
import keen_texture
from material_package import encode, FALLBACK
scene = (root / "outputs/scene-v17/scene.bin").read_bytes()
side = (root / "outputs/scene-v17/scene_materials.bin").read_bytes()
version, vc, dc, tc = struct.unpack_from("<4I", side, 8)
assert side[:8] == b"OMAT09\0\0" and side[24:56] == hashlib.sha256(scene).digest()
uvs = [struct.unpack_from("<2f", side, 56 + 8 * i) for i in range(vc)]
at = 56 + 8 * vc
draws = []
for i in range(dc):
    first, n, tex, _ = struct.unpack_from("<4I", side, at)
    draws.append(dict(first_vertex=first, vertex_count=n, texture_index=tex))
    at += 16
textures = []
for i in range(tc):
    w, h, n, _ = struct.unpack_from("<4I", side, at)
    at += 16
    textures.append(dict(width=w, height=h, rgba=side[at:at + n]))
    at += n
placement = (host / "workbench_visual.inc").read_text()
print("workbench inc", placement.strip()[:200])
import re
first = int(re.search(r"OA_WORKBENCH_FIRST_VERTEX\s+(\d+)", placement).group(1))
candidates = [d for d in draws if d["first_vertex"] >= first and d["texture_index"] == FALLBACK]
print("workbench fallback draws", candidates, "fallback draws in whole shop", sum(1 for d in draws if d["texture_index"] == FALLBACK))
data = None
for suffix in ("_1.dds", "_2.dds", "_3.dds", "_0.dds", "_4.dds"):
    q = root / f"work/v17-inputs/DATA_0.pak/697080{suffix}"
    if not q.exists():
        continue
    b = q.read_bytes()
    w, h, fmt, mips = *struct.unpack_from("<HH", b, 20), b[29], struct.unpack_from("<H", b, 35)[0]
    print("workbench texture file", q.name, w, h, fmt, mips)
    a = 38
    block = 8 if fmt == 1 else 16
    for _ in range(mips):
        size = ((w + 3) // 4) * ((h + 3) // 4) * block
        if max(w, h) <= 512 and a + size <= len(b):
            data = (w, h, bytearray(keen_texture.decode_blocks(b[a:a + size], w, h, fmt)))
            break
        a += size
        w, h = max(1, w // 2), max(1, h // 2)
    if data:
        break
out = root / "work/v20-town/scene_materials.bin"
if data and candidates:
    data[2][3::4] = b"\xff" * (data[0] * data[1])
    textures.append(dict(width=data[0], height=data[1], rgba=bytes(data[2])))
    for d in candidates:
        d["texture_index"] = len(textures) - 1
    blob, _ = encode(scene, uvs, draws, textures)
    out.write_bytes(blob)
    print("workbench texture applied", data[0], data[1], len(blob))
else:
    out.write_bytes(side)
    print("workbench texture unavailable; sidecar copied unchanged")


def edit(name, pairs):
    f = host / name
    f.write_bytes(edit_text(f.read_bytes().decode("utf-8"), name, pairs).encode("utf-8"))


edit("room_lighting_shader.h", [
 ('"uniform int has_texture;uniform sampler2D base_texture;"', '"uniform int has_texture;uniform sampler2D base_texture;uniform float alpha_cut;"'),
 ('"vec3 base=has_texture!=0?texture(base_texture,uv).rgb:color;vec3 illumination;"', '"vec4 texel=has_texture!=0?texture(base_texture,uv):vec4(color,1.0);if(texel.a<alpha_cut)discard;vec3 base=texel.rgb;vec3 illumination;"'),
])
edit("android_scene.c", [
 ("glUniformMatrix4fv(g->matrix_location,1,GL_FALSE,matrix);", 'glUniformMatrix4fv(g->matrix_location,1,GL_FALSE,matrix);glUniform1f(glGetUniformLocation(g->program,"alpha_cut"),g->room_lights.outdoor?.5f:0.f);'),
])
edit("AndroidManifest.xml", [('android:versionCode="20" android:versionName="0.19.0"', 'android:versionCode="21" android:versionName="0.20.0"')])
edit("CMakeLists.txt", [("VERSION 0.19.0", "VERSION 0.20.0")])
edit("package_android.py", [
 ("opem-amalur-scene-v0.19-arm64.apk", "opem-amalur-scene-v0.20-arm64.apk"),
 ("files['assets/scene_materials.bin']=renderout/'scene_materials.bin'", "files['assets/scene_materials.bin']=root/'work/v20-town/scene_materials.bin'"),
])
print("patched")
