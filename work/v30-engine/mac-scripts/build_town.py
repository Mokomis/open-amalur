"""Build Gorhart's first outdoor scene around the shop door: terrain, placed models, collision and lighting.
Radius, single ground texture, skipped alpha foliage and texture size are explicit first-version choices."""
import collections, hashlib, json, math, pickle, re, struct, subprocess, sys
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
sys.path[:0] = [str(root / p) for p in ("work/v07-mesh", "work/v07-bxml", "work/v09-textures", "work/v19-lighting")]
import amalur_mesh, keen_texture
from material_package import encode, FALLBACK
import decode_scene_lighting as D
g = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning")
inp = root / "work/v20-inputs"
wc = root / "work/v20-char"
out = root / "work/v20-town"
out.mkdir(exist_ok=True)
syms = json.loads((inp / "symbols.json").read_text())
SPACE, REGION, DOOR = 431638, 431608, (1575.1, -62759.2, 5152.1)
RADIUS, TEXTURE_LIMIT, STEP = float(sys.argv[1]) if len(sys.argv) > 1 else 6000.0, 256, 100.0
listing = {}
for arch, n in (("DATA_0.pak", "DATA"), ("initial_0.pak", "initial"), ("patch_0.pak", "patch")):
    b = (root / f"outputs/{n}-archive-list.txt").read_bytes()
    listing[arch] = set(x.strip() for x in b.decode("utf-16" if b[:2] == b"\xff\xfe" else "utf-8-sig").splitlines() if x.strip())


def extract(names, patched=True):
    """Later archives win, the same explicit patch-over-base choice used for the character."""
    found = {}
    for arch in ("DATA_0.pak", "initial_0.pak", "patch_0.pak"):
        sel = [n for n in names if n in listing[arch]]
        d = inp / arch
        d.mkdir(parents=True, exist_ok=True)
        for start in range(0, len(sel), 40):
            todo = [n for n in sel[start:start + 40] if not (d / n).exists()]
            if todo:
                subprocess.run([str(g / "modding/pakfileunpacker.exe"), str(g / "data" / arch), "unpack", str(d), *todo], cwd=g / "modding", capture_output=True, timeout=280)
        for n in sel:
            if (d / n).exists():
                found[n] = d / n
    return found


def qrot(q, v):
    x, y, z, w = q
    tx, ty, tz = 2 * (y * v[2] - z * v[1]), 2 * (z * v[0] - x * v[2]), 2 * (x * v[1] - y * v[0])
    return (v[0] + w * tx + y * tz - z * ty, v[1] + w * ty + z * tx - x * tz, v[2] + w * tz + x * ty - y * tx)


# Terrain sampler
s = (inp / "DATA_0.pak/431658.terrain_streamable_bin").read_bytes()
grids = pickle.load(open(wc / "terrain-grids.pkl", "rb"))
abs_pos = pickle.load(open(wc / "terrain-abs.pkl", "rb"))
fit = json.loads((wc / "terrain-fit.json").read_text())
level = collections.defaultdict(dict)
for n, (x, y, w) in abs_pos.items():
    level[w][(x, y)] = n
HOLE, ORIGIN = 65535, -102425.0


def ground(wx, wy):
    ux, uy = (wx - ORIGIN) / 50, (wy - ORIGIN) / 50
    for w in sorted(level):
        px, py = int(ux // w) * w, int(uy // w) * w
        n = level[w].get((px, py))
        if n is None:
            continue
        v = grids[n][2]
        fx, fy = (ux - px) * 16 / w + 1, (uy - py) * 16 / w + 1
        ix, iy = int(fx), int(fy)
        q = (v[iy * 19 + ix], v[iy * 19 + ix + 1], v[(iy + 1) * 19 + ix], v[(iy + 1) * 19 + ix + 1])
        if max(q) > 60000:  # 65535 marks a hole; nearby values this high are unusable spikes.
            continue
        ax, ay = fx - ix, fy - iy
        h = q[0] * (1 - ax) * (1 - ay) + q[1] * ax * (1 - ay) + q[2] * (1 - ax) * ay + q[3] * ax * ay
        return h * fit["k"] + fit["z0"]
    return None


# Textures
tex_rgba, tex_index = [], {}
report = collections.Counter()


def load_texture(tid):
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


material_cache = {}


def material_texture(mid):
    if mid in material_cache:
        return material_cache[mid]
    files = extract([f"{mid}.mat_bxml"])
    result = (FALLBACK, 255)
    if files:
        d = next(iter(files.values())).read_bytes()
        refs = []
        for i in range(0, len(d) - 3, 4):
            v = struct.unpack_from("<I", d, i)[0]
            name = syms["texture"].get(str(v))
            if name and v not in [r[0] for r in refs]:
                refs.append((v, name))
        order = [r for r in refs if r[1].lower().endswith("_d") and "par_color" not in r[1]] or [r for r in refs if not r[1].lower().endswith(("_n", "_s", "_g", "_cubemap"))]
        for tid, name in order:
            result = load_texture(tid)
            if result[0] != FALLBACK:
                break
    material_cache[mid] = result
    return result


# Placed models
d = extract([f"{SPACE}.space_bxml"])[f"{SPACE}.space_bxml"].read_bytes()
pl = struct.unpack_from("<I", d, 0)[0]
b = d[8:8 + pl]
def array(slot, stride):
    ptr, count = struct.unpack_from("<II", b, slot)
    return [b[ptr - 8 + i * stride:ptr - 8 + (i + 1) * stride] for i in range(count)]
refs = [struct.unpack("<I", r)[0] for r in array(0x1b0, 4)]
centers = [struct.unpack("<3f", r) for r in array(0x1a8, 12)]
renders = array(0x160, 84)
by_center = {}
for r in renders:
    c = struct.unpack_from("<3f", r)
    by_center[tuple(round(x, 2) for x in c)] = r
instances = []
rejected = collections.Counter()
audit = []
normals = collections.defaultdict(list)
for typed, center in zip(refs, centers):
    r = by_center.get(tuple(round(x, 2) for x in center))
    if r is None:
        report["unmatched_refs"] += 1
        continue
    if typed >> 28 != 15:
        report["non_fab_refs"] += 1
        continue
    if math.dist(center[:2], DOOR[:2]) > RADIUS:
        continue
    instances.append((typed & 0xfffffff, center, r))
# The larger list pairs 80-byte placements (FAB id at +52) with 84-byte render records.
place80, render84 = array(0x148, 80), array(0x150, 84)
for a, r in zip(place80, render84):
    center = struct.unpack_from("<3f", r)
    fab = struct.unpack_from("<I", a, 52)[0]
    if math.dist(center[:2], DOOR[:2]) <= RADIUS and str(fab) in syms["fab"]:
        instances.append((fab, center, r))
print("instances", len(instances), collections.Counter(syms["fab"].get(str(i[0]), "?") for i in instances).most_common(40))
vis = extract([f"{f}.fab_visual_data_streamable_bin" for f in {i[0] for i in instances}])
meshes = {}
per_texture = collections.defaultdict(list)
for fab, center, r in instances:
    key = f"{fab}.fab_visual_data_streamable_bin"
    if key not in vis:
        report["missing_visual"] += 1
        continue
    if fab not in meshes:
        try:
            meshes[fab] = (amalur_mesh.parse_file(vis[key]), vis[key].read_bytes())
        except Exception as e:
            meshes[fab] = None
            report["mesh_parse_failures"] += 1
    if meshes[fab] is None:
        continue
    mesh, raw = meshes[fab]
    sphere = struct.unpack_from("<4f", r)
    t = struct.unpack_from("<3f", r, 16)
    q = struct.unpack_from("<4f", r, 32)
    scale = struct.unpack_from("<3f", r, 48)
    material, asm_index = struct.unpack_from("<II", r, 64)
    if asm_index >= len(mesh["assemblies"]):
        report["bad_assembly"] += 1
        continue
    asm = mesh["assemblies"][asm_index]
    vb = mesh["vertex_buffers"][asm["vertex_buffer"]]
    indices = mesh["index_buffers"][asm["index_buffer"]]["indices"]
    layout = {48: (12, 20), 56: (12, 28), 60: (24, 32)}.get(vb["stride_bytes"])
    if layout is None:
        report[f"stride_{vb['stride_bytes']}_skipped"] += 1
        continue
    if re.search("shadow|for_temp", str(syms["material"].get(str(material), "")), re.I):
        report["shadow_proxies_skipped"] += 1
        continue
    texture, alpha = material_texture(material)
    if alpha < 128:
        report["alpha_assemblies_skipped"] += 1
        continue
    cq = (-q[0], -q[1], -q[2], q[3])
    inverse = q
    center_local = qrot(inverse, tuple(sphere[i] - t[i] for i in range(3)))
    def world(p):
        local = tuple(center_local[i] + (p[i] - center_local[i]) * scale[i] for i in range(3))
        r2 = qrot(cq, local)
        return tuple(r2[i] + t[i] for i in range(3))
    verts = bytearray()
    positions = vb["positions"]
    # Reject any placement whose geometry disagrees with its stored bounding sphere.
    reach = max(math.dist(world(positions[i]), sphere[:3]) for i in set(indices))
    if sphere[3] <= 0 or reach > sphere[3] * 1.25 + 60:
        report["sphere_rejected"] += 1
        rejected[syms["fab"].get(str(fab), str(fab))] += 1
        continue
    for index in indices:
        p = world(positions[index])
        at = vb["data_file_offset"] + index * vb["stride_bytes"]
        uv = struct.unpack_from("<2f", raw, at + layout[0])
        n0 = struct.unpack_from("<3h", raw, at + layout[1])
        n1 = [n0[k] / (scale[k] if abs(scale[k]) > 1e-4 else 1.0) for k in range(3)]
        ln = math.sqrt(sum(x * x for x in n1)) or 1.0
        n = qrot(cq, tuple(x / ln for x in n1))
        verts += struct.pack("<9f", *p, *n, .8, .8, .8) + struct.pack("<2f", *uv)
    agree = up = area = 0.0
    for k in range(0, len(verts), 132):
        a0 = struct.unpack_from("<6f", verts, k); a1 = struct.unpack_from("<3f", verts, k + 44); a2 = struct.unpack_from("<3f", verts, k + 88)
        u = [a1[e] - a0[e] for e in range(3)]; v = [a2[e] - a0[e] for e in range(3)]
        gx, gy, gz = u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]
        agree += gx * a0[3] + gy * a0[4] + gz * a0[5]; up += a0[5] * math.sqrt(gx * gx + gy * gy + gz * gz); area += math.sqrt(gx * gx + gy * gy + gz * gz)
    normals[syms["material"].get(str(material), str(material))].append((round(agree / (area or 1), 2), round(up / (area or 1), 2)))
    zs_i = [world(positions[i])[2] for i in set(indices)]
    audit.append((round(max(zs_i)), syms["fab"].get(str(fab), str(fab)), texture, syms["material"].get(str(material), material), [round(x, 2) for x in scale], round(sphere[3]), vb["stride_bytes"]))
    per_texture[texture].append(verts)
    report["assemblies"] += 1
    report["model_triangles"] += len(indices) // 3


# Ground grid and its collision triangles
cells = int(RADIUS / STEP)
ox, oy = round(DOOR[0] / STEP) * STEP, round(DOOR[1] / STEP) * STEP
heights = {}
for j in range(-cells - 1, cells + 2):
    for i in range(-cells - 1, cells + 2):
        heights[(i, j)] = ground(ox + i * STEP, oy + j * STEP)
ground_tris = []
ground_verts = bytearray()
def corner(i, j):
    z = heights[(i, j)]
    zx0, zx1, zy0, zy1 = heights.get((i - 1, j)), heights.get((i + 1, j)), heights.get((i, j - 1)), heights.get((i, j + 1))
    nx = ((zx0 if zx0 is not None else z) - (zx1 if zx1 is not None else z)) / (2 * STEP)
    ny = ((zy0 if zy0 is not None else z) - (zy1 if zy1 is not None else z)) / (2 * STEP)
    length = math.sqrt(nx * nx + ny * ny + 1)
    x, y = ox + i * STEP, oy + j * STEP
    return (x, y, z), (nx / length, ny / length, 1 / length), (x / 400.0, y / 400.0)
for j in range(-cells, cells):
    for i in range(-cells, cells):
        if math.hypot(i, j) > cells:
            continue
        quad = ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))
        if any(heights[c] is None for c in quad):
            report["ground_holes"] += 1
            continue
        for a, c, e in ((quad[0], quad[1], quad[2]), (quad[0], quad[2], quad[3])):
            tri = [corner(*a), corner(*c), corner(*e)]
            ground_tris.append(tuple(x for v in tri for x in v[0]))
            for p, n, uv in tri:
                ground_verts += struct.pack("<9f", *p, *n, .35, .42, .22) + struct.pack("<2f", *uv)
ground_name = next((k for k, v in syms["texture"].items() if v == "for_terrain_grass01_d"), None)
ground_tex = load_texture(int(ground_name))[0] if ground_name else FALLBACK
print("ground texture", ground_name, ground_tex)
per_texture[ground_tex].insert(0, ground_verts)
report["ground_triangles"] = len(ground_tris)

# Scene and sidecar
scene_v, uvs, draws = bytearray(), [], []
count = 0
for texture in sorted(per_texture, key=lambda t: (t != ground_tex, t)):
    start = count
    for block in per_texture[texture]:
        for i in range(0, len(block), 44):
            scene_v += block[i:i + 36]
            uvs.append(struct.unpack_from("<2f", block, i + 36))
            count += 1
    if count > start:
        draws.append(dict(first_vertex=start, vertex_count=count - start, texture_index=texture))
lo = [min(struct.unpack_from("<f", scene_v, i * 36 + k)[0] for i in range(count)) for k in (0, 4, 8)]
hi = [max(struct.unpack_from("<f", scene_v, i * 36 + k)[0] for i in range(count)) for k in (0, 4, 8)]
scene = b"OMSC07\0\0" + struct.pack("<I6f", count, *lo, *hi) + bytes(scene_v)
(out / "town_scene.bin").write_bytes(scene)
side, receipt = encode(scene, uvs, draws, tex_rgba)
(out / "town_materials.bin").write_bytes(side)

# Collision: nearby source triangles plus the ground
c = extract(["485422.collision_set_bin"])["485422.collision_set_bin"].read_bytes()
gp, gc = struct.unpack_from("<II", c, 16)
tris = list(ground_tris)
source = 0
for i in range(gc):
    _, _, mp, mc = struct.unpack_from("<4I", c, gp + i * 16)
    for j in range(mc):
        _, vp, vc, tp, tc = struct.unpack_from("<5I", c, mp + j * 20)
        V = struct.unpack_from(f"<{vc * 3}f", c, vp)
        for k in range(tc):
            a, e, f, _ = struct.unpack_from("<4I", c, tp + k * 16)
            if a < vc and e < vc and f < vc:
                t = tuple(V[n * 3 + q2] * 100 for n in (a, e, f) for q2 in range(3))
                if math.hypot(t[0] - DOOR[0], t[1] - DOOR[1]) < RADIUS + 400:
                    tris.append(t); source += 1
report["collision_source_triangles"] = source
cv = bytearray()
for t in tris:
    for v in range(3):
        cv += struct.pack("<9f", t[v * 3], t[v * 3 + 1], t[v * 3 + 2], 0, 0, 1, 1, 1, 1)
xs, ys, zs = [t[k] for t in tris for k in (0, 3, 6)], [t[k] for t in tris for k in (1, 4, 7)], [t[k] for t in tris for k in (2, 5, 8)]
(out / "town_collision.bin").write_bytes(b"OMSC07\0\0" + struct.pack("<I6f", len(tris) * 3, min(xs), min(ys), min(zs), max(xs), max(ys), max(zs)) + bytes(cv))

# Lighting
rb = extract([f"{REGION}.region_bxml"])[f"{REGION}.region_bxml"].read_bytes()
r = D.decode_region(rb)
p = rb[8:]
E = r["environment"]; T = E["time_keyed"]; K = "Noon"
amb = r["ambient_cubes"][T["ambient_cube_index"][K]["value"]]
faces = [p[o:o + 256] for o in amb["face_texel_offsets"]]
sun = T["directional_light_color"][K]["value"]
scale_sun = sun["intensity"] * T["directional_light_intensity"][K]["value"]
shadow = T["shadow_color"][K]["value"]
op = T["shadow_opacity"][K]["value"]
lut_id = T["color_correction_texture_id"][K]["value"]
lut = extract([f"{lut_id}.dds"])[f"{lut_id}.dds"].read_bytes()[38:]
assert len(lut) == 16384
fmt = lambda v: ",".join(format(float(x), ".9e") + "f" for x in v)
L = [f"/* Generated from region {REGION} by work/v20-char/build_town.py, Noon key. */",
     "static const float opem_town_sun_color[3]={%s};" % fmt([x * scale_sun for x in sun["rgb"]]),
     "static const float opem_town_sun_direction[3]={%s};" % fmt([-x for x in E["directional_light_direction"]["value"]]),
     "static const float opem_town_shadow_color[4]={%s};" % fmt([*shadow["rgb"], op]),
     "static const unsigned char opem_town_cube[6][256]={" + ",".join("{" + ",".join(map(str, f)) + "}" for f in faces) + "};",
     "static const unsigned char opem_town_lut[16384]={" + ",".join(map(str, lut)) + "};"]
(out / "town_environment.inc").write_text("\n".join(L) + "\n", encoding="utf-8")
print("sphere rejected", rejected.most_common(20))
print("tallest", sorted(audit, reverse=True)[:4])
print("normal agreement by material", {k: (len(v), round(sum(x[0] for x in v) / len(v), 2), round(sum(x[1] for x in v) / len(v), 2)) for k, v in normals.items()})
stats = {}
for i, tx in enumerate(tex_rgba):
    rgba = tx["rgba"]
    n = len(rgba) // 4
    stats[i] = (tx["width"], tx["height"], round(sum(rgba[::4]) / n), round(sum(rgba[1::4]) / n), round(sum(rgba[2::4]) / n), round(sum(rgba[3::4]) / n))
print("dark textures", {i: v for i, v in stats.items() if sum(v[2:5]) < 90})
print("who uses dark", collections.Counter((a[1], a[3], a[2], tuple(a[4])) for a in audit if a[2] in stats and sum(stats[a[2]][2:5]) < 90).most_common(14))
print("negative scales", collections.Counter(a[1] for a in audit if min(a[4]) < 0).most_common(10), "fallback", collections.Counter(a[3] for a in audit if a[2] == FALLBACK).most_common(10))
summary = dict(radius=RADIUS, vertices=count, triangles=count // 3, draws=len(draws), textures=len(tex_rgba), scene_sha256=hashlib.sha256(scene).hexdigest(), materials_bytes=len(side), scene_bytes=len(scene), collision_triangles=len(tris), spawn_hint=DOOR, door_ground=ground(*DOOR[:2]), bounds=[lo, hi], sun=[x * scale_sun for x in sun["rgb"]], lut=lut_id, counts=dict(report))
(out / "town-receipt.json").write_text(json.dumps(summary, indent=1))
print(json.dumps(summary, indent=1))
