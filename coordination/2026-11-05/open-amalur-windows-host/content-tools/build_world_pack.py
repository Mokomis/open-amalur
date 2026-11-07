"""Cut a built town scene into streamable cells: three LODs, per-cell collision, textures on demand.
Usage: build_world_pack.py <scene dir> <out dir> [grass clumps per square metre]
LODs are global vertex clustering, so neighbouring cells agree on seams. Grass is a load test:
real game textures with authored placement, because the game's veggie data is not decoded yet."""
import json, shutil, struct, subprocess, sys
from pathlib import Path
import numpy as np
root = Path.home() / "Documents/Opem Amalur"
sys.path[:0] = [str(root / "work/v09-textures")]
import keen_texture
src, out = Path(sys.argv[1]), Path(sys.argv[2])
grass_density = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
CELL = 6400.0
LOD_GRID = (None, 400.0, 1600.0)
if out.exists():
    shutil.rmtree(out)
out.mkdir(parents=True)

if (src / "zone_pos.npy").exists():
    import pickle
    pos = np.load(src / "zone_pos.npy"); nor = np.load(src / "zone_nor.npy"); uv = np.load(src / "zone_uv.npy")
    zone_tex = np.load(src / "zone_tex.npy"); textures = []; count = len(pos); draws = []
    zone_meta = json.loads((src / "zone_materials.json").read_text())
    print("zone", count // 3, "triangles", len(zone_meta["materials"]), "materials")
else:
    zone_tex = None
    scene = (src / "town_scene.bin").read_bytes()
    assert scene[:8] == b"OMSC07\0\0"
    count = struct.unpack_from("<I", scene, 8)[0]
    soup = np.frombuffer(scene, "<f4", count * 9, 36).reshape(-1, 9)
    pos, nor = soup[:, :3].copy(), soup[:, 3:6].copy()
    mat = (src / "town_materials.bin").read_bytes()
    assert mat[:8] == b"OMAT09\0\0"
    _, mcount, dcount, tcount = struct.unpack_from("<4I", mat, 8)
    assert mcount == count
    at = 56
    uv = np.frombuffer(mat, "<f4", count * 2, at).reshape(-1, 2).copy()
    at += count * 8
    draws = [struct.unpack_from("<4I", mat, at + i * 16) for i in range(dcount)]
    at += dcount * 16
    textures = []
    for i in range(tcount):
        w, h, n, _ = struct.unpack_from("<4I", mat, at)
        textures.append((w, h, mat[at + 16:at + 16 + n]))
        at += 16 + n
    print("scene", count // 3, "triangles", dcount, "draws", tcount, "textures")




def decode_best(name, limit=256):
    syms = json.loads((root / "work/v20-inputs/symbols.json").read_text())["texture"]
    tid = next(k for k, v in syms.items() if v == name)
    g = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning")
    d = root / "work/v22-stress/flora"
    d.mkdir(parents=True, exist_ok=True)
    best = None
    for pak in ("patch_0.pak", "initial_0.pak", "DATA_0.pak"):
        for fn in [f"{tid}.dds"] + [f"{tid}_{k}.dds" for k in range(6)]:
            q = d / pak / fn
            if not q.exists():
                q.parent.mkdir(exist_ok=True)
                subprocess.run([str(g / "modding/pakfileunpacker.exe"), str(g / "data" / pak), "unpack", str(q.parent), fn], cwd=g / "modding", capture_output=True, timeout=60)
            if not q.exists():
                continue
            data = q.read_bytes()
            if data[16:20] != b"KEEN" or data[29] not in (1, 5):
                continue
            w, h, fmt, mips = *struct.unpack_from("<HH", data, 20), data[29], struct.unpack_from("<H", data, 35)[0]
            o, block = 38, 8 if fmt == 1 else 16
            for _ in range(mips):
                size = ((w + 3) // 4) * ((h + 3) // 4) * block
                if o + size > len(data):
                    break
                if max(w, h) <= limit:
                    if best is None or w > best[0]:
                        best = (w, h, bytes(keen_texture.decode_blocks(data[o:o + size], w, h, fmt)))
                    break
                o += size
                w, h = max(1, w // 2), max(1, h // 2)
        if best:
            break
    if not best:
        raise SystemExit("texture unavailable: " + name)
    return best


cx = np.floor(pos[::3, 0] + pos[1::3, 0] + pos[2::3, 0]) / 3 / CELL
cy = np.floor(pos[::3, 1] + pos[1::3, 1] + pos[2::3, 1]) / 3 / CELL
tri_cell_x, tri_cell_y = np.floor(cx).astype(np.int32), np.floor(cy).astype(np.int32)
tri_tex = zone_tex if zone_tex is not None else np.zeros(count // 3, np.uint32)
for first, n, tex, _ in draws:
    tri_tex[first // 3:(first + n) // 3] = tex


def cluster(grid):
    key = np.floor(pos / grid).astype(np.int64)
    key = (key[:, 0] + (1 << 20)) | ((key[:, 1] + (1 << 20)) << 21) | ((key[:, 2] + (1 << 20)) << 42)
    _, inverse = np.unique(key, return_inverse=True)
    groups = inverse.max() + 1
    weight = np.bincount(inverse, minlength=groups).astype(np.float64)
    p = np.stack([np.bincount(inverse, pos[:, k], groups) / weight for k in range(3)], 1).astype(np.float32)[inverse]
    tri = inverse.reshape(-1, 3)
    keep = (tri[:, 0] != tri[:, 1]) & (tri[:, 1] != tri[:, 2]) & (tri[:, 0] != tri[:, 2])
    return p, keep


lods = [(pos, np.ones(count // 3, bool))] + [cluster(g) for g in LOD_GRID[1:]]
print("lod triangles", [int(k.sum()) for _, k in lods])

# Terrain triangles sit on the 1 m build grid. Only they get skirts, which hide cracks between levels.
on_grid = (np.abs(pos[:, :2] / 100.0 - np.round(pos[:, :2] / 100.0)) < 1e-3).all(1).reshape(-1, 3).all(1)
SKIRT = (120.0, 500.0, 1800.0)
grass_tex = None
extra = {}
if grass_density > 0:
    w, h, rgba = decode_best("for_flora_grass01_d")
    aw, ah, arg = decode_best("for_flora_grass01_a")
    px = bytearray(rgba)
    for y in range(h):
        for x in range(w):
            px[(y * w + x) * 4 + 3] = arg[((y * ah // h) * aw + x * aw // w) * 4]
    grass_tex = len(textures)
    textures.append((w, h, bytes(px)))
    ground = draws[0][2]
    rng = np.random.default_rng(431638)
    mask = tri_tex == ground
    tris = pos.reshape(-1, 3, 3)[mask]
    tcx, tcy = tri_cell_x[mask], tri_cell_y[mask]
    area = np.linalg.norm(np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0]), axis=1) * .5
    keys = (tcx.astype(np.int64) << 32) ^ (tcy.astype(np.int64) & 0xffffffff)
    for key in np.unique(keys):
        sel = np.nonzero(keys == key)[0]
        total = area[sel].sum() / 10000.0
        n = int(total * grass_density)
        if n < 1:
            continue
        pick = rng.choice(sel, n, p=area[sel] / area[sel].sum())
        a, b = rng.random(n), rng.random(n)
        flip = a + b > 1
        a[flip], b[flip] = 1 - a[flip], 1 - b[flip]
        base = tris[pick, 0] + (tris[pick, 1] - tris[pick, 0]) * a[:, None] + (tris[pick, 2] - tris[pick, 0]) * b[:, None]
        ang = rng.random(n) * 3.14159
        half = 45 * (.7 + rng.random(n) * .6)
        tall = 60 * (.7 + rng.random(n) * .6)
        extra[(int(tcx[sel[0]]), int(tcy[sel[0]]))] = (base, ang, half, tall)
    print("grass clumps", sum(len(v[0]) for v in extra.values()))


def grass_mesh(item, cells=None):
    base, ang, half, tall = item
    vs, ids = [], []
    for plane in (0.0, 1.5708):
        dx, dy = np.cos(ang + plane) * half, np.sin(ang + plane) * half
        o = len(vs) * 4 * 1
        b = base
        rows = np.zeros((len(b), 4, 8), np.float32)
        rows[:, 0, :3] = b - np.stack([dx, dy, np.zeros_like(dx)], 1)
        rows[:, 1, :3] = b + np.stack([dx, dy, np.zeros_like(dx)], 1)
        rows[:, 2, :3] = rows[:, 1, :3] + np.stack([np.zeros_like(dx), np.zeros_like(dx), tall], 1)
        rows[:, 3, :3] = rows[:, 0, :3] + np.stack([np.zeros_like(dx), np.zeros_like(dx), tall], 1)
        rows[:, :, 5] = 1
        rows[:, 0, 6:] = (0, 1); rows[:, 1, 6:] = (1, 1); rows[:, 2, 6:] = (1, 0); rows[:, 3, 6:] = (0, 0)
        if cells is not None:
            rows[:, :, 6] = cells[:, 0, None] + rows[:, :, 6] * cells[:, 2, None]; rows[:, :, 7] = cells[:, 1, None] + rows[:, :, 7] * cells[:, 3, None]
        vs.append(rows.reshape(-1, 8))
    v = np.concatenate(vs)
    q = np.arange(len(v) // 4, dtype=np.uint32)[:, None] * 4
    i = (q + np.array([0, 1, 2, 0, 2, 3], np.uint32)).reshape(-1)
    return v, i


VERTEX = np.dtype([("p", "<f4", 3), ("n", "<i2", 4), ("t", "<f4", 2)])
cell_keys = np.unique((tri_cell_x.astype(np.int64) << 32) ^ (tri_cell_y.astype(np.int64) & 0xffffffff))
order = np.argsort((tri_cell_x.astype(np.int64) << 32) ^ (tri_cell_y.astype(np.int64) & 0xffffffff), kind="stable")
sorted_keys = ((tri_cell_x.astype(np.int64) << 32) ^ (tri_cell_y.astype(np.int64) & 0xffffffff))[order]
index_rows = []
stats = {"bytes": [0, 0, 0], "verts": [0, 0, 0], "tris": [0, 0, 0]}
for key in cell_keys:
    ix, iy = int(key >> 32), int(np.int32(key & 0xffffffff))
    s, e = np.searchsorted(sorted_keys, key), np.searchsorted(sorted_keys, key, side="right")
    tids = order[s:e]
    tris_by_lod = []
    lo, hi = [1e30] * 3, [-1e30] * 3
    for lod, (p, keep) in enumerate(lods):
        sel = tids[keep[tids]]
        blocks, vtotal, itotal, recs = [], 0, 0, []
        ibuf = []
        for tex in np.unique(tri_tex[sel]):
            t = sel[tri_tex[sel] == tex]
            vid = (t[:, None] * 3 + np.array([0, 1, 2])).reshape(-1)
            rec = np.zeros(len(vid), VERTEX)
            rec["p"] = p[vid]
            ln = np.linalg.norm(nor[vid], axis=1, keepdims=True)
            rec["n"][:, :3] = np.round(nor[vid] / np.where(ln > 1e-6, ln, 1) * 32767).astype(np.int16)
            rec["n"][:, 3] = np.round(np.minimum(np.ravel(ln), 1) * 32767).astype(np.int16)
            rec["t"] = uv[vid]
            # Skirts: terrain edges used by one triangle in this cell and texture drop straight down.
            ground = on_grid[t]
            if ground.any():
                g_ids = np.arange(len(t))[ground]
                corners = np.stack([g_ids * 3, g_ids * 3 + 1, g_ids * 3 + 2], 1)
                px = np.round(p[vid][corners.reshape(-1)] * 8).astype(np.int64)
                keys = (px[:, 0] + (1 << 28)) * (1 << 30) + (px[:, 1] + (1 << 28))
                keys = keys.reshape(-1, 3)
                edges = np.concatenate([np.stack([keys[:, a], keys[:, b], corners[:, a], corners[:, b]], 1) for a, b in ((0, 1), (1, 2), (2, 0))])
                lo_key, hi_key = np.minimum(edges[:, 0], edges[:, 1]), np.maximum(edges[:, 0], edges[:, 1])
                both = np.stack([lo_key, hi_key], 1)
                _, inv_edge, counts = np.unique(both, axis=0, return_inverse=True, return_counts=True)
                lone = edges[counts[inv_edge.reshape(-1)] == 1]
                if len(lone):
                    a_rec, b_rec = rec[lone[:, 2]], rec[lone[:, 3]]
                    a_low, b_low = a_rec.copy(), b_rec.copy()
                    a_low["p"][:, 2] -= SKIRT[lod]; b_low["p"][:, 2] -= SKIRT[lod]
                    rec = np.concatenate([rec, np.stack([a_rec, a_low, b_rec, b_rec, a_low, b_low], 1).reshape(-1)])
            uniq, inv = np.unique(rec, return_inverse=True)
            blocks.append(uniq)
            ibuf.append(inv.astype(np.uint32) + vtotal)
            recs.append((int(tex), itotal, len(inv)))
            vtotal += len(uniq); itotal += len(inv)
        if lod == 0 and (ix, iy) in extra:
            v, i = grass_mesh(extra[(ix, iy)])
            rec = np.zeros(len(v), VERTEX)
            rec["p"] = v[:, :3]; rec["n"][:, 2] = 32767; rec["t"] = v[:, 6:]
            blocks.append(rec); ibuf.append(i + vtotal); recs.append((grass_tex, itotal, len(i)))
            vtotal += len(rec); itotal += len(i)
        data = b"OAWC" + struct.pack("<III", vtotal, itotal, len(recs))
        for r in recs:
            data += struct.pack("<III", *r)
        if blocks:
            all_v = np.concatenate(blocks)
            data += all_v.tobytes() + np.concatenate(ibuf).tobytes()
            if lod == 0:
                lo = np.minimum(lo, all_v["p"].min(0)); hi = np.maximum(hi, all_v["p"].max(0))
        (out / f"c{ix}_{iy}_{lod}.bin").write_bytes(data)
        tris_by_lod.append(itotal // 3)
        stats["bytes"][lod] += len(data); stats["verts"][lod] += vtotal; stats["tris"][lod] += itotal // 3
    if tris_by_lod[0]:
        index_rows.append((ix, iy, [float(x) for x in lo], [float(x) for x in hi], tris_by_lod))

# Per-cell collision: a triangle goes in every cell its bounds touch.
if (src / "zone_col.npy").exists():
    ctri = np.load(src / "zone_col.npy")
else:
    col = (src / "town_collision.bin").read_bytes()
    ccount = struct.unpack_from("<I", col, 8)[0]
    ctri = np.frombuffer(col, "<f4", ccount * 9, 36).reshape(-1, 9)[:, :3].reshape(-1, 3, 3)
centre = ctri.mean(1)
kx, ky = np.floor(centre[:, 0] / CELL).astype(int), np.floor(centre[:, 1] / CELL).astype(int)
ckeys = (kx.astype(np.int64) << 32) ^ (ky.astype(np.int64) & 0xffffffff)
buckets = {}
corder = np.argsort(ckeys, kind="stable")
csorted = ckeys[corder]
for key in np.unique(ckeys):
    s, e = np.searchsorted(csorted, key), np.searchsorted(csorted, key, side="right")
    buckets[(int(key >> 32), int(np.int32(key & 0xffffffff)))] = [ctri[corder[s:e]]]
cbytes = 0
for (ix, iy), parts in buckets.items():
    a = np.concatenate(parts).astype("<f4")
    (out / f"k{ix}_{iy}.bin").write_bytes(struct.pack("<I", len(a)) + a.tobytes())
    cbytes += 4 + a.nbytes

for i, (w, h, rgba) in enumerate(textures):
    (out / f"t{i}.bin").write_bytes(struct.pack("<II", w, h) + rgba)
# Real foliage in its own cell files, so it can load only nearby.
ATLAS = [(0.0, 0.0, 98 / 256, 105 / 256), (98 / 256, 0.0, 74 / 256, 105 / 256), (172 / 256, 0.0, 84 / 256, 105 / 256), (0.0, 105 / 256, 96 / 256, 151 / 256), (96 / 256, 105 / 256, 76 / 256, 151 / 256), (172 / 256, 105 / 256, 84 / 256, 151 / 256)]
grass_tris = {}
if (src / "zone_grass.npy").exists():
    G = np.load(src / "zone_grass.npy"); rng = np.random.default_rng(431658)
    gx_, gy_ = np.floor(G[:, 0] / CELL).astype(int), np.floor(G[:, 1] / CELL).astype(int); gk = (gx_.astype(np.int64) << 32) ^ (gy_.astype(np.int64) & 0xffffffff)
    for key in np.unique(gk):
        ix, iy = int(key >> 32), int(np.int32(key & 0xffffffff)); pts_ = G[gk == key]; n = len(pts_)
        # The flora texture is an atlas of six plants; which layer shows which plant is authored, not recovered.
        atlas = np.array(ATLAS, np.float32)[pts_[:, 3].astype(int) % len(ATLAS)]
        tall = 70 * (.7 + rng.random(n) * .6)
        v, i = grass_mesh((pts_[:, :3], rng.random(n) * 3.14159, tall * atlas[:, 2] / atlas[:, 3] / 2, tall), atlas)
        rec = np.zeros(len(v), VERTEX); rec["p"] = v[:, :3]; rec["n"][:, 2] = 32767; rec["t"] = v[:, 6:]
        (out / f"g{ix}_{iy}.bin").write_bytes(b"OAWC" + struct.pack("<III", len(rec), len(i), 1) + struct.pack("<III", zone_meta["grass"], 0, len(i)) + rec.tobytes() + i.tobytes())
        grass_tris[(ix, iy)] = len(i) // 3
head = b"OAWI" + struct.pack("<fIII", CELL, len(index_rows), 0, 0)
for ix, iy, lo, hi, tris in index_rows:
    head += struct.pack("<ii6f4I", ix, iy, *lo, *hi, *tris, grass_tris.get((ix, iy), 0))
(out / "index.bin").write_bytes(head)
summary = dict(cells=len(index_rows), grass_tris=sum(grass_tris.values()), lod_bytes=stats["bytes"], lod_vertices=stats["verts"], lod_triangles=stats["tris"], collision_bytes=cbytes, collision_cells=len(buckets), grass_density=grass_density)
(out / "pack-receipt.json").write_text(json.dumps(summary, indent=1))
print(json.dumps(summary))
