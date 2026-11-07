"""Build a whole outdoor zone's scene soup: every space's placed models, all terrain, all collision.
Usage: build_zone.py <out dir> [terrain step]. Writes arrays for build_world_pack.py."""
import collections, math, pickle, re, struct, sys, time
from pathlib import Path
import numpy as np
root = Path.home() / "Documents/Opem Amalur"
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
STEP_ARG = float(sys.argv[2]) if len(sys.argv) > 2 else 100.0
# The town builder's archive, terrain and material helpers, up to where it starts placing models.
source = (root / "work/v20-char/build_town.py").read_text()
sys.argv = ["build_town.py", "1", str(OUT)]
exec(source[:source.index("# Placed models")])
STEP = STEP_ARG
T0 = time.time()
def log(*a): print(round(time.time() - T0), *a, flush=True)
ZONE = __import__("os").environ.get("OA_ZONE", "dal")
# Each zone has its own ground set; which of them goes where is still chosen by slope, not by the game's paint maps.
TP = {"dal": "for", "poe": "pln", "det": "det", "ala": "ala", "klu": "klu"}[ZONE]
spaces = sorted((int(k), str(v)) for k, v in syms["simspace"].items() if re.match(rf"out_{ZONE}_(north|south|west|east|central|tran|[a-z0-9])", str(v)))
log("spaces", len(spaces), [n for _, n in spaces])
def qrots(q, v):
    x, y, z, w = q
    u = np.array([x, y, z], np.float64)
    t = 2 * np.cross(u, v)
    return v + w * t + np.cross(u, t)
mesh_cache, per_texture = {}, collections.defaultdict(list)
# Materials keep all their maps; build_textures.py compresses them.
MATS, mat_index = [], {}
def material_maps(mid):
    if mid in mat_index:
        return mat_index[mid]
    entry = dict(d=None, a=None, n=None, s=None)
    files = extract([f"{mid}.mat_bxml"])
    if files:
        data = next(iter(files.values())).read_bytes(); refs = []
        for i in range(0, len(data) - 3, 4):
            v = struct.unpack_from("<I", data, i)[0]; name = syms["texture"].get(str(v))
            if name and v not in [r[0] for r in refs]:
                refs.append((v, name.lower()))
        pick = lambda tail: next((v for v, nm in refs if nm.endswith(tail) and "par_color" not in nm), None)
        entry.update(d=pick("_d") or next((v for v, nm in refs if not nm.endswith(("_n", "_s", "_g", "_cubemap", "_a", "_e"))), None), a=pick("_a"), n=pick("_n"), s=pick("_s"))
        # Water and veils have their own shaders. Parameters are read by their hash; which hash is which name is inferred from the shader's parameters and these values.
        shader = str(syms["shader"].get(str(struct.unpack_from("<I", data, 24)[0]), ""))
        words = struct.unpack_from(f"<{len(data) // 4}I", data); floats = struct.unpack_from(f"<{len(data) // 4}f", data)
        def param(key, n=1, default=0.0):
            at = next((i for i, w in enumerate(words) if w == key), None)
            return [floats[at + 1 + k] for k in range(n)] if at is not None else [default] * n
        ordered = [v for v, nm in refs]
        if shader in ("river", "rivernopointlights"):
            nm = {name: v for v, name in refs}; find = lambda *tails: next((v for v, name in refs if name.endswith(tails)), None)
            detail = next((v for v, name in refs if "detail" in name and name.endswith("_n")), None); base_n = next((v for v, name in refs if name.endswith("_n") and "detail" not in name), None)
            entry.update(kind="river", d=next((v for v, name in refs if "base_d" in name), entry["d"]), a=None, t=[next((v for v, name in refs if "base_d" in name), entry["d"]), base_n, find("_b"), detail, next((v for v, name in refs if "froth" in name), None), None],
                         p=[floats[10], param(0x144e03f)[0], param(0x62c2a8)[0], param(0x1bcc5e8)[0], param(0x10869bd)[0], param(0x4e562b)[0], param(0x9049b2)[0]] + param(0xaf568c, 4, 1.0))
        elif shader == "scrollingwaterfall":
            d = [v for v, name in refs if name.endswith("_d")]; al = [v for v, name in refs if name.endswith("_a")]; no = [v for v, name in refs if name.endswith("_n")]
            entry.update(kind="fall", a=None, t=[d[0], d[-1], al[0] if al else None, al[-1] if al else None, no[0] if no else None, no[-1] if no else None],
                         p=[floats[10], param(0x7217ed)[0], param(0x726fde)[0], param(0x7aa1de)[0]] + param(0x7af9cf, 2) + param(0x9f6969, 3))
        elif shader == "emissivewithalphafog":
            entry.update(kind="veil", p=[])
    mat_index[mid] = len(MATS); MATS.append(entry)
    return mat_index[mid]
tex_id = lambda name: next((int(k) for k, v in syms["texture"].items() if v == name), None)
total = collections.Counter()
for sid, sname in spaces:
    d = extract([f"{sid}.space_bxml"]).get(f"{sid}.space_bxml")
    if d is None:
        log("missing space", sname); continue
    d = d.read_bytes(); pl = struct.unpack_from("<I", d, 0)[0]; b = d[8:8 + pl]
    def array(slot, stride):
        ptr, count = struct.unpack_from("<II", b, slot)
        return [b[ptr - 8 + i * stride:ptr - 8 + (i + 1) * stride] for i in range(count)]
    refs = [struct.unpack("<I", r)[0] for r in array(0x1b0, 4)]
    centers = [struct.unpack("<3f", r) for r in array(0x1a8, 12)]
    renders = array(0x160, 84)
    by_center = {tuple(round(x, 2) for x in struct.unpack_from("<3f", r)): r for r in renders}
    instances = []
    for typed, center in zip(refs, centers):
        r = by_center.get(tuple(round(x, 2) for x in center))
        # The top four bits vary and are not understood; the model id is the low 28 bits for every value seen (2 to 7 and 15).
        if r is not None and str(typed & 0xfffffff) in syms["fab"]:
            instances.append((typed & 0xfffffff, r))
    for a, r in zip(array(0x148, 80), array(0x150, 84)):
        fab = struct.unpack_from("<I", a, 52)[0]
        if str(fab) in syms["fab"]:
            instances.append((fab, r))
    # Two more groups hold what is drawn with blending: rivers, ponds, waterfalls, webs, clouds, smoke.
    for group, renders2 in ((0x138, 0x170), (0x140, 0x180)):
        for a, r in zip(array(group, 16), array(renders2, 84)):
            fab = struct.unpack_from("<I", a, 8)[0]
            if str(fab) in syms["fab"]:
                instances.append((fab, r)); total["blended_instances"] += 1
    vis = extract([f"{f}.fab_visual_data_streamable_bin" for f in {i[0] for i in instances}])
    for fab, r in instances:
        key = f"{fab}.fab_visual_data_streamable_bin"
        if key not in vis:
            total["missing_visual"] += 1; continue
        if fab not in mesh_cache:
            try:
                mesh_cache[fab] = (amalur_mesh.parse_file(vis[key]), vis[key].read_bytes())
            except Exception:
                mesh_cache[fab] = None; total["parse_failures"] += 1
        if mesh_cache[fab] is None:
            continue
        mesh, raw = mesh_cache[fab]
        sphere = struct.unpack_from("<4f", r); t = np.array(struct.unpack_from("<3f", r, 16)); q = struct.unpack_from("<4f", r, 32); scale = np.array(struct.unpack_from("<3f", r, 48)); material, asm_index = struct.unpack_from("<II", r, 64)
        if asm_index >= len(mesh["assemblies"]):
            total["bad_assembly"] += 1; continue
        asm = mesh["assemblies"][asm_index]; vb = mesh["vertex_buffers"][asm["vertex_buffer"]]
        layout = {48: (12, 20), 56: (12, 28), 60: (24, 32)}.get(vb["stride_bytes"])
        if layout is None:
            total["other_stride"] += 1; continue
        if re.search("shadow|for_temp", str(syms["material"].get(str(material), "")), re.I):
            total["shadow_proxy"] += 1; continue
        idx = np.array(mesh["index_buffers"][asm["index_buffer"]]["indices"], np.int64)
        P = np.array(vb["positions"], np.float64)
        cq = (-q[0], -q[1], -q[2], q[3])
        centre_local = qrots(q, (np.array(sphere[:3]) - t)[None, :])[0]
        world = qrots(cq, centre_local + (P - centre_local) * scale) + t
        used = np.unique(idx)
        reach = np.sqrt(((world[used] - np.array(sphere[:3])) ** 2).sum(1)).max() if len(used) else 0
        if sphere[3] <= 0 or reach > sphere[3] * 1.25 + 60:
            total["sphere_rejected"] += 1; continue
        n_vert, stride, base = vb["vertex_count"], vb["stride_bytes"], vb["data_file_offset"]
        uv = np.ndarray((n_vert, 2), "<f4", raw, base + layout[0], (stride, 4))
        n0 = np.ndarray((n_vert, 3), "<i2", raw, base + layout[1], (stride, 2)).astype(np.float64)
        safe = np.where(np.abs(scale) > 1e-4, scale, 1.0)
        n1 = n0 / safe
        n1 /= np.maximum(np.linalg.norm(n1, axis=1, keepdims=True), 1e-9)
        n2 = qrots(cq, n1)
        tex = material_maps(material)
        if MATS[tex].get("kind") == "fall":
            # Blended water fades by vertex alpha, the last colour byte. It travels as the normal's length.
            alpha = np.ndarray((n_vert,), "u1", raw, base + stride - 1, (stride,)).astype(np.float64) / 255
            n2 = n2 * np.maximum(alpha, 0.02)[:, None]
        per_texture[tex].append((world[idx].astype(np.float32), n2[idx].astype(np.float32), uv[idx].copy()))
        total["assemblies"] += 1; total["model_triangles"] += len(idx) // 3
    log(sname, "instances", len(instances), dict(total), "materials", len(MATS))
# Terrain: every cell of the zone's height data.
xs = [x * 50 + ORIGIN for x, y, w in abs_pos.values()]; ys = [y * 50 + ORIGIN for x, y, w in abs_pos.values()]
x1 = [x * 50 + ORIGIN + w * 50 for x, y, w in abs_pos.values()]; y1 = [y * 50 + ORIGIN + w * 50 for x, y, w in abs_pos.values()]
gx = np.arange(math.floor(min(xs) / STEP) * STEP, max(x1) + STEP, STEP); gy = np.arange(math.floor(min(ys) / STEP) * STEP, max(y1) + STEP, STEP)
log("terrain grid", len(gx), len(gy), "extent m", (gx[-1] - gx[0]) / 100, (gy[-1] - gy[0]) / 100)
H = np.full((len(gy), len(gx)), np.nan, np.float32)
for j, wy in enumerate(gy):
    for i, wx in enumerate(gx):
        h = ground(float(wx), float(wy))
        if h is not None:
            H[j, i] = h
    if j % 300 == 0:
        log("heights row", j)
log("heights valid", int(np.isfinite(H).sum()))
Hf = np.where(np.isfinite(H), H, 0)
nx = np.zeros_like(Hf); ny = np.zeros_like(Hf)
nx[:, 1:-1] = (Hf[:, :-2] - Hf[:, 2:]) / (2 * STEP); ny[1:-1, :] = (Hf[:-2, :] - Hf[2:, :]) / (2 * STEP)
ln = np.sqrt(nx * nx + ny * ny + 1); N = np.stack([nx / ln, ny / ln, 1 / ln], -1).astype(np.float32)
X, Y = np.meshgrid(gx.astype(np.float32), gy.astype(np.float32))
PG = np.stack([X, Y, Hf], -1)
UVG = np.stack([X / 400.0, Y / 400.0], -1).astype(np.float32)
ok = np.isfinite(H[:-1, :-1]) & np.isfinite(H[:-1, 1:]) & np.isfinite(H[1:, :-1]) & np.isfinite(H[1:, 1:])
jj, ii = np.nonzero(ok)
log("terrain quads", len(jj))
a, c, e, f = (jj, ii), (jj, ii + 1), (jj + 1, ii + 1), (jj + 1, ii)
tri_a = np.stack([np.stack([PG[v] for v in (a, c, e)], 1), np.stack([PG[v] for v in (a, e, f)], 1)])
tri_n = np.stack([np.stack([N[v] for v in (a, c, e)], 1), np.stack([N[v] for v in (a, e, f)], 1)])
tri_u = np.stack([np.stack([UVG[v] for v in (a, c, e)], 1), np.stack([UVG[v] for v in (a, e, f)], 1)])
tri_a = tri_a.reshape(-1, 3, 3); tri_n = tri_n.reshape(-1, 3, 3); tri_u = tri_u.reshape(-1, 3, 2)
up = tri_n[:, :, 2].mean(1)
ids = {band: next((k for k, v in syms["texture"].items() if v == name), None) for band, name in (("grass", f"{TP}_terrain_grass01_d"), ("rock", f"{TP}_terrain_rock01_d"), ("cliff", f"{TP}_terrain_cliff01_d"))}
TERRAIN = len(MATS)
MATS.append(dict(terrain=1, d=[ids["grass"], ids["rock"], ids["cliff"]], n=[tex_id(f"{TP}_terrain_grass01_n"), tex_id(f"{TP}_terrain_rock01_n"), tex_id(f"{TP}_terrain_cliff01_n")]))
per_texture[TERRAIN].append((tri_a.reshape(-1, 3), tri_n.reshape(-1, 3), tri_u.reshape(-1, 2)))
total["ground"] = len(tri_a)
GRASS = len(MATS)
MATS.append(dict(d=tex_id(f"{TP}_flora_grass01_d"), a=tex_id(f"{TP}_flora_grass01_a"), n=None, s=None))
# Collision: terrain plus each space's set.
coll = [tri_a]
names = {str(v): int(k) for k, v in syms["collisionset"].items()}
for sid, sname in spaces:
    cid = names.get(sname)
    f_ = extract([f"{cid}.collision_set_bin"]).get(f"{cid}.collision_set_bin") if cid else None
    if f_ is None:
        total["no_collision_set"] += 1; continue
    c_ = f_.read_bytes(); gp, gc = struct.unpack_from("<II", c_, 16)
    for i in range(gc):
        _, _, mp, mc = struct.unpack_from("<4I", c_, gp + i * 16)
        for j in range(mc):
            _, vp, vc, tp, tc = struct.unpack_from("<5I", c_, mp + j * 20)
            if not tc or not vc: continue
            V = np.frombuffer(c_, "<f4", vc * 3, vp).reshape(-1, 3) * 100
            I = np.frombuffer(c_, "<u4", tc * 4, tp).reshape(-1, 4)[:, :3]
            I = I[(I < vc).all(1)]
            coll.append(V[I].astype(np.float32)); total["collision_source"] += len(I)
log(dict(total))
order = sorted(per_texture)
parts = [p for t in order for p in per_texture[t]]
tri_tex = np.concatenate([np.full(sum(len(p[0]) for p in per_texture[t]) // 3, t, np.uint32) for t in order])
np.save(OUT / "zone_pos.npy", np.concatenate([p[0] for p in parts]))
np.save(OUT / "zone_nor.npy", np.concatenate([p[1] for p in parts]))
np.save(OUT / "zone_uv.npy", np.concatenate([p[2] for p in parts]))
np.save(OUT / "zone_tex.npy", tri_tex)
np.save(OUT / "zone_col.npy", np.concatenate(coll))
import json
(OUT / "zone_materials.json").write_text(json.dumps(dict(materials=MATS, terrain=TERRAIN, grass=GRASS)))
# Live-play lighting data, Noon key: every point light in the zone, plus fog and bloom.
rb = extract([f"{REGION}.region_bxml"])[f"{REGION}.region_bxml"].read_bytes(); rd = D.decode_region(rb); TK = rd["environment"]["time_keyed"]; K = "Noon"
lights = []
for sid, sname in spaces:
    f_ = extract([f"{sid}.space_bxml"]).get(f"{sid}.space_bxml")
    if f_ is None:
        continue
    L = D.decode_space_lights(f_.read_bytes())
    for it in (L if isinstance(L, list) else L.get("lights", [])):
        n_ = it["time_keyed"][K]; m_ = n_["multiplier"]
        lights.append([*it["position"], n_["attenuation_start"], *[c_ * m_ for c_ in n_["color"]], n_["attenuation_end"]])
val = lambda k: TK[k][K]["value"]
fc = val("fog_color"); fc = fc["rgb"] if isinstance(fc, dict) else fc
fmt_ = lambda v: ",".join(format(float(x), ".6e") + "f" for x in v)
inc = ["/* Generated from Dalentarth by build_zone.py, Noon key. */", f"enum{{OA_LIVE_LIGHTS={len(lights)}}};", "static const float oa_live_lights[OA_LIVE_LIGHTS][8]={" + ",".join("{" + fmt_(l) + "}" for l in lights) + "};", "static const float oa_live_fog_color[3]={" + fmt_(fc) + "};", f"static const float oa_live_fog_start={float(val('fog_start')):.6e}f,oa_live_fog_density={float(val('fog_density')):.6e}f,oa_live_bloom={float(val('bloom_strength')):.6e}f,oa_live_bloom_cut={float(val('post_bloom_cutoff')):.6e}f;"]
(OUT / "town_live.inc").write_text("\n".join(inc) + "\n")
if ZONE == "dal":
    (root / "work/v19-host/town_live.inc").write_text("\n".join(inc) + "\n")
log("lights", len(lights), "fog", fc, val("fog_start"), val("fog_density"), "bloom", val("bloom_strength"), val("post_bloom_cutoff"))
log("written triangles", len(tri_tex), "materials", len(MATS), "collision", sum(len(x) for x in coll))
