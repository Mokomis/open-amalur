"""Build assets/character.bin: skinned player parts, textures and baked clips, plus a preview image.
Part selection is an explicit preview choice (bonus armor plus a peasant head), not native player assembly."""
import json, math, struct, subprocess, sys, zlib
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
sys.path[:0] = [str(root / "work/v07-mesh"), str(root / "work/v07-bxml"), str(root / "work/v09-textures")]
import amalur_mesh
from keen_texture import decode as decode_texture
g = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning")
inp = root / "work/v20-inputs"
out = root / "work/v20-char"
syms = json.loads((inp / "symbols.json").read_text())
HEADS = [v for name in ("promo_melee_nonset_head", "majestic_head", "04_rogue_nonset_unique_head", "03_silk_head", "promo_magic_set_head") for v, n in syms["fab"].items() if n == name]
PARTS = [(1926576, "torso"), (1926575, "legs"), (1926574, "hands"), (1923507, "feet")]
CLIPS = [(673754, "combat_idle"), (673863, "combat_walk"), (673928, "combat_run"), (673833, "attack_b"), (1893691, "attack_special"), (673835, "attack_x"), (673903, "react_front"), (1926549, "react_death")]
MAX_TEXTURE = 512


def qmul(a, b):
    x1, y1, z1, w1 = a; x2, y2, z2, w2 = b
    return (w1*x2+x1*w2+y1*z2-z1*y2, w1*y2-x1*z2+y1*w2+z1*x2, w1*z2+x1*y2-y1*x2+z1*w2, w1*w2-x1*x2-y1*y2-z1*z2)
def conj(q): return (-q[0], -q[1], -q[2], q[3])
def rot(q, v): return qmul(qmul(q, (v[0], v[1], v[2], 0.0)), conj(q))[:3]


def extract(names):
    found = {}
    for arch, listing in (("DATA_0.pak", "DATA"), ("initial_0.pak", "initial"), ("patch_0.pak", "patch")):
        b = (root / f"outputs/{listing}-archive-list.txt").read_bytes()
        have = set(x.strip() for x in b.decode("utf-16" if b[:2] == b"\xff\xfe" else "utf-8-sig").splitlines())
        sel = [n for n in names if n in have]
        if sel:
            d = inp / arch
            d.mkdir(parents=True, exist_ok=True)
            todo = [n for n in sel if not (d / n).exists()]
            if todo:
                subprocess.run([str(g / "modding/pakfileunpacker.exe"), str(g / "data" / arch), "unpack", str(d), *todo], cwd=g / "modding", capture_output=True, timeout=250)
            for n in sel:
                if (d / n).exists():
                    found[n] = d / n  # later archives win, matching the explicit patch-over-base preview choice
    return found


def skeleton(fb):
    n = struct.unpack_from("<H", fb, 4 + 0x10)[0]
    pose = 4 + 0x18 + struct.unpack_from("<i", fb, 4 + 0x18)[0]
    par = struct.unpack_from(f"<{n}H", fb, 4 + 0x1c + struct.unpack_from("<I", fb, 4 + 0x1c)[0])
    names = struct.unpack_from(f"<{n}I", fb, 4 + 0x20 + struct.unpack_from("<I", fb, 4 + 0x20)[0])
    world = []
    for i in range(n):
        r = struct.unpack_from("<12f", fb, pose + i * 48)
        q, t = conj(r[:4]), r[4:7]
        if par[i] == 0xffff:
            world.append((q, tuple(t)))
        else:
            pq, pt = world[par[i]]
            v = rot(pq, t)
            world.append((qmul(pq, q), tuple(pt[k] + v[k] for k in range(3))))
    return n, par, names, world


def palette(fb, joints):
    """Longest chain of 52-byte records: inverse bind t, q, s, count, joint index."""
    best = []
    for start in range(0, len(fb) - 52, 4):
        chain, at = [], start
        while at + 52 <= len(fb):
            s = struct.unpack_from("<3f", fb, at + 32)
            q = struct.unpack_from("<4f", fb, at + 16)
            count, idx = struct.unpack_from("<II", fb, at + 44)
            if not all(abs(x - 1) < .02 for x in s) or abs(sum(x * x for x in q) - 1) > .02 or idx >= joints or count > 300:
                break
            chain.append((idx, struct.unpack_from("<3f", fb, at), q))
            at += 52
        if len(chain) > len(best):
            best = chain
    return best



def sword_part():
    """Sword as a rigid part on RGTHAND_ATTACH. Its vertices are used directly in that joint's space."""
    fid = 1327249
    f = extract([f"{fid}.fab_bxml", f"{fid}.fab_visual_data_streamable_bin"])
    vis = f[f"{fid}.fab_visual_data_streamable_bin"]
    m = amalur_mesh.parse_file(vis)
    raw = vis.read_bytes()
    asm = m["assemblies"][0]
    vb = m["vertex_buffers"][asm["vertex_buffer"]]
    verts = bytearray()
    for i in range(vb["vertex_count"]):
        a = vb["data_file_offset"] + i * vb["stride_bytes"]
        p = struct.unpack_from("<3f", raw, a)
        uv = struct.unpack_from("<2f", raw, a + 12)
        n = [x / 32767.0 for x in struct.unpack_from("<3h", raw, a + 20)]
        verts += struct.pack("<8f4B4f", *p, *n, *uv, 0, 0, 0, 0, 1.0, 0.0, 0.0, 0.0)
    return verts, m["index_buffers"][asm["index_buffer"]]["indices"], [(55, (0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0))]

# Skeleton and clips
main = (inp / "patch_0.pak/456813.fab_bxml").read_bytes()
J, parents, jnames, jworld = skeleton(main)
jindex = {n: i for i, n in enumerate(jnames)}
blob = bytearray(b"OACHAR01")
clips = []
extract([f"{c}.anm_bxml" for c, _ in CLIPS])
out.joinpath("baked").mkdir(exist_ok=True)
for cid, name in CLIPS:
    baked = out / f"baked/{cid}.bin"
    if not baked.exists():
        r = subprocess.run([str(out / "clip-bake.exe"), str(g / "koa.exe"), str(inp / "patch_0.pak/456813.fab_bxml"), str(inp / f"initial_0.pak/{cid}.anm_bxml"), str(baked)], capture_output=True, text=True)
        if r.returncode:
            raise SystemExit(f"bake {cid}: {r.stderr}")
    b = baked.read_bytes()
    j, frames, fps = struct.unpack_from("<IIf", b)
    rows = bytearray()
    for i in range(frames * j):
        v = struct.unpack_from("<7f", b, 12 + i * 48)
        q = conj(v[:4])
        rows += struct.pack("<7f", *q, *v[4:7])
    clips.append((name, frames, fps, bytes(rows)))


# Parts and textures
textures, tex_index, parts = [], {}, []
def texture_for(mat_id):
    files = extract([f"{mat_id}.mat_bxml"])
    if not files:
        return None, []
    d = next(iter(files.values())).read_bytes()
    refs = []
    for i in range(0, len(d) - 3, 4):
        v = struct.unpack_from("<I", d, i)[0]
        name = syms["texture"].get(str(v))
        if name and v not in [r[0] for r in refs]:
            refs.append((v, name))
    return d, refs

report = {"parts": [], "clips": [(n, f, s) for n, f, s, _ in clips]}
# Choose the first helmet whose geometry actually surrounds the head joint.
for hid in HEADS:
    files = extract([f"{hid}.fab_bxml", f"{hid}.fab_visual_data_streamable_bin"])
    vis = files.get(f"{hid}.fab_visual_data_streamable_bin")
    if not vis or vis.stat().st_size < 100:
        continue
    head = amalur_mesh.parse_file(vis)
    zs = [p[2] for b in head["vertex_buffers"] for p in b["positions"]]
    print("head candidate", syms["fab"][hid], hid, "stride", head["vertex_buffers"][0]["stride_bytes"], len(zs), round(min(zs)), round(max(zs)), file=sys.stderr)
    if head["vertex_buffers"][0]["stride_bytes"] == 60 and min(zs) < 165 and max(zs) > 172:
        PARTS.append((int(hid), "head"))
        break
for fid, label in PARTS:
    fab = extract([f"{fid}.fab_bxml", f"{fid}.fab_visual_data_streamable_bin"])
    fb = fab[f"{fid}.fab_bxml"].read_bytes()
    n, fpar, fnames, fworld = skeleton(fb)
    pal = palette(fb, n)
    entries = []
    worst = 0.0
    for idx, inv_t, inv_q in pal:
        cur = idx
        while cur != 0xffff and fnames[cur] not in jindex:
            cur = fpar[cur]
        joint = jindex[fnames[cur]] if cur != 0xffff else 1
        wq, wt = fworld[idx]
        iq = conj(wq)
        it = tuple(-x for x in rot(iq, wt))
        err = max(abs(it[k] - inv_t[k]) for k in range(3))
        worst = max(worst, err)
        # Models whose skeleton copy disagrees with their stored inverse bind use the stored one.
        entries.append((joint, it, iq) if err < 1 else (joint, tuple(inv_t), conj(tuple(inv_q))))
    r = amalur_mesh.parse_file(fab[f"{fid}.fab_visual_data_streamable_bin"])
    raw = fab[f"{fid}.fab_visual_data_streamable_bin"].read_bytes()
    verts, inds = bytearray(), []
    base = 0
    for asm in r["assemblies"]:
        vb = r["vertex_buffers"][asm["vertex_buffer"]]
        ib = r["index_buffers"][asm["index_buffer"]]
        if vb["stride_bytes"] != 60:
            raise SystemExit(f"{fid}: stride {vb['stride_bytes']}")
        for i in range(vb["vertex_count"]):
            a = vb["data_file_offset"] + i * 60
            p = struct.unpack_from("<3f", raw, a)
            idx = raw[a + 12:a + 16]
            w = [x / 32767.0 for x in struct.unpack_from("<4H", raw, a + 16)]
            # The shader reads three weights and gives the fourth the remainder.
            w[3] = max(0.0, 1.0 - sum(w[:3]))
            uv = struct.unpack_from("<2f", raw, a + 24)
            nn = [x / 32767.0 for x in struct.unpack_from("<3h", raw, a + 32)]
            verts += struct.pack("<8f4B4f", *p, *nn, *uv, *idx, *w)
        key = next(k for k in ib if k in ("data_file_offset", "file_offset"))
        count = ib.get("index_count") or ib.get("count")
        inds += [base + x for x in struct.unpack_from(f"<{count}H", raw, ib[key])]
        base += vb["vertex_count"]
    mats = [v for v in (struct.unpack_from("<I", fb, i)[0] for i in range(0, len(fb) - 3, 4)) if str(v) in syms["material"]]
    mid = mats[0] if mats else 0
    _, refs = texture_for(mid)
    order = sorted(refs, key=lambda x: (0 if x[1].lower().endswith(("_d", "_dif", "_diff", "_diffuse", "_c", "_col", "_color")) else 2 if x[1].lower().endswith(("_n", "_nrm", "_norm", "_normal", "_s", "_spec", "_g")) else 1))
    tindex, pick = -1, None
    for cand in order:
        if cand[0] in tex_index:
            tindex, pick = tex_index[cand[0]], cand
            break
        names = [f"{cand[0]}.dds"] + [f"{cand[0]}_{k}.dds" for k in range(6)]
        f = extract(names)
        image = None
        for name in names:
            if name not in f:
                continue
            try:
                data = f[name].read_bytes()
                count = len(__import__("keen_texture").parse(data)["mips"])
                for level in range(count):
                    rgba, info = decode_texture(data, level)
                    w, h = info["decoded_width"], info["decoded_height"]
                    if max(w, h) <= MAX_TEXTURE:
                        if image is None or w > image[0]:
                            image = (w, h, bytes(rgba), name)
                        break
            except Exception as e:
                print("texture", name, "failed", repr(e)[:160], file=sys.stderr)
        if image is None:
            continue
        tex_index[cand[0]] = len(textures)
        textures.append(image[:3])
        tindex, pick = tex_index[cand[0]], (cand[0], cand[1] + " from " + image[3] + f" {image[0]}x{image[1]}")
        break
    parts.append((label, verts, inds, entries, tindex))
    report["parts"].append(dict(label=label, fab=fid, vertices=base, indices=len(inds), palette=len(entries), max_vertex_joint=max(max(verts[32 + i * 52:36 + i * 52]) for i in range(base)), inverse_bind_error=round(worst, 3), material=syms["material"].get(str(mid)), textures=[x[1] for x in refs], chosen=pick[1] if pick else None))

sword_verts, sword_inds, sword_entries = sword_part()
_, refs = texture_for(next(int(k) for k, v in syms["material"].items() if v == "02_steel_sword_1h"))
pick = next((x for x in refs if x[1].lower().endswith("_d")), None)
sword_tex = -1
if pick:
    # Sword textures are not square, so walk the stored levels by the header's own mip count.
    f = extract([f"{pick[0]}_{k}.dds" for k in range(6)])
    best = None
    for name, q in f.items():
        data = q.read_bytes()
        w, h, fmt, mips = *struct.unpack_from("<HH", data, 20), data[29], struct.unpack_from("<H", data, 35)[0]
        at, block = 38, 8 if fmt == 1 else 16
        for _ in range(mips):
            size = ((w + 3) // 4) * ((h + 3) // 4) * block
            if at + size > len(data):
                break
            if max(w, h) <= MAX_TEXTURE:
                if best is None or w > best[0]:
                    best = (w, h, bytes(__import__("keen_texture").decode_blocks(data[at:at + size], w, h, fmt)))
                break
            at += size
            w, h = max(1, w // 2), max(1, h // 2)
    if best:
        sword_tex = len(textures)
        textures.append(best)
parts.append(("sword", sword_verts, sword_inds, sword_entries, sword_tex))
report["parts"].append(dict(label="sword", vertices=len(sword_verts) // 52, texture=sword_tex))
blob += struct.pack("<IIII", J, len(clips), len(parts), len(textures))
blob += struct.pack(f"<{J}h", *[(-1 if p == 0xffff else p) for p in parents])
for name, frames, fps, rows in clips:
    blob += struct.pack("<If", frames, fps) + rows
for w, h, rgba in textures:
    blob += struct.pack("<II", w, h) + rgba
for label, verts, inds, entries, tindex in parts:
    blob += struct.pack("<IIIi", len(verts) // 52, len(inds), len(entries), tindex)
    for joint, it, iq in entries:
        blob += struct.pack("<I7f", joint, *iq, *it)
    blob += bytes(verts) + struct.pack(f"<{len(inds)}I", *inds)
(out / "character.bin").write_bytes(blob)
report["bytes"] = len(blob)


# Preview: skin every vertex at chosen frames and plot front and side views
def pose(rows, frame):
    world = []
    for i in range(J):
        v = struct.unpack_from("<7f", rows, (frame * J + i) * 28)
        q, t = v[:4], v[4:7]
        if parents[i] == 0xffff:
            world.append((q, t))
        else:
            pq, pt = world[parents[i]]
            r = rot(pq, t)
            world.append((qmul(pq, q), tuple(pt[k] + r[k] for k in range(3))))
    return world


W, H = 900, 520
img = bytearray(b"\x20" * (W * H * 3))
def plot(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        img[(y * W + x) * 3:(y * W + x) * 3 + 3] = bytes(c)
colors = {"sword": (255, 40, 40), "torso": (220, 80, 80), "legs": (80, 200, 90), "hands": (90, 140, 240), "feet": (230, 200, 70), "head": (240, 240, 240)}
for slot, (ci, fr) in enumerate(((0, 0), (3, 22), (7, 60))):
    world = pose(clips[ci][3], fr)
    for label, verts, inds, entries, tindex in parts:
        skins = []
        for joint, it, iq in entries:
            wq, wt = world[joint]
            skins.append((qmul(wq, iq), (lambda v: tuple(wt[k] + v[k] for k in range(3)))(rot(wq, it))))
        for i in range(0, len(verts) // 52, 2):
            v = struct.unpack_from("<8f4B4f", verts, i * 52)
            p = v[:3]; ids = v[8:12]; ws = v[12:16]
            o = [0.0, 0.0, 0.0]
            for b, weight in zip(ids, ws):
                if weight > 0 and b < len(skins):
                    q, t = skins[b]
                    r = rot(q, p)
                    for k in range(3):
                        o[k] += weight * (r[k] + t[k])
            plot(int(150 + slot * 300 + o[1] * 1.15 ), int(480 - o[2] * 2.2), colors[label])
(lambda rows: (out / "character-preview.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"".join(struct.pack(">I", len(b)) + t + b + struct.pack(">I", zlib.crc32(t + b)) for t, b in ((b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)), (b"IDAT", zlib.compress(rows, 6)), (b"IEND", b"")))))(bytes(b"".join(b"\0" + bytes(img[y * W * 3:(y + 1) * W * 3]) for y in range(H))))
# Strike moments: peaks of right hand speed in each attack clip, and clip lengths, for the combat rules.
strikes, seconds = [], []
for name, frames, fps, rows in clips:
    seconds.append((frames - 1) / fps)
    if not name.startswith("attack"):
        strikes.append([0.0, 0.0, 0.0, 0.0])
        continue
    speed = []
    last = None
    for fr in range(frames):
        p = pose(rows, fr)[55][1]
        speed.append(0.0 if last is None else math.dist(p, last) * fps)
        last = p
    top = max(speed)
    peaks = []
    for fr in range(2, frames - 2):
        if speed[fr] > top * .6 and speed[fr] == max(speed[fr - 2:fr + 3]):
            t = fr / fps
            if not peaks or t - peaks[-1] > .3:
                peaks.append(t)
    strikes.append((peaks + [0.0, 0.0, 0.0, 0.0])[:4])
header = "/* Generated by build_character.py: clip lengths and right hand speed peaks. */\n#define OA_COMBAT_CLIPS %d\n#define OA_COMBAT_STRIKES 4\nstatic const float oa_combat_seconds[OA_COMBAT_CLIPS]={%s};\nstatic const float oa_combat_strikes[OA_COMBAT_CLIPS][OA_COMBAT_STRIKES]={%s};\n" % (len(clips), ",".join("%.4ff" % s for s in seconds), ",".join("{" + ",".join("%.4ff" % t for t in row) + "}" for row in strikes))
(root / "work/v19-host/oa_combat_clips.h").write_text(header, encoding="utf-8", newline="\n")
report["strikes"] = {c[0]: s for c, s in zip(clips, strikes)}
report["seconds"] = seconds
print(json.dumps(report, indent=0))
