"""Build work/v20-town/town_npcs.bin from each townsperson's own bundle, placement record and idle clip.
Idle-only behaviour and the texture size limit are explicit first-version choices."""
import json, math, re, struct, subprocess, sys, zlib, collections
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
sys.path[:0] = [str(root / p) for p in ("work/v07-mesh", "work/v07-bxml", "work/v09-textures")]
import amalur_mesh, keen_texture
g = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning")
inp = root / "work/v20-inputs"
wc = root / "work/v20-char"
out = root / "work/v20-town"
syms = json.loads((inp / "symbols.json").read_text())
SPACE, DOOR, RADIUS, TEXTURE_LIMIT = 431638, (1575.1, -62759.2, 5152.1), 5600.0, 256
BIN = wc / "clip-bake.exe"
listing = {}
files_by_id = collections.defaultdict(list)
for arch, n in (("DATA_0.pak", "DATA"), ("initial_0.pak", "initial"), ("patch_0.pak", "patch")):
    b = (root / f"outputs/{n}-archive-list.txt").read_bytes()
    listing[arch] = set(x.strip() for x in b.decode("utf-16" if b[:2] == b"\xff\xfe" else "utf-8-sig").splitlines() if x.strip())
    for x in listing[arch]:
        m = re.match(r"(\d+)(?:_\d+)?\.(\w+)$", x)
        if m:
            files_by_id[int(m.group(1))].append(m.group(2))


def extract(names):
    found = {}
    for arch in ("DATA_0.pak", "initial_0.pak", "patch_0.pak"):
        sel = [n for n in names if n in listing[arch]]
        d = inp / arch
        for start in range(0, len(sel), 40):
            todo = [n for n in sel[start:start + 40] if not (d / n).exists()]
            if todo:
                subprocess.run([str(g / "modding/pakfileunpacker.exe"), str(g / "data" / arch), "unpack", str(d), *todo], cwd=g / "modding", capture_output=True, timeout=280)
        for n in sel:
            if (d / n).exists():
                found[n] = d / n
    return found


def qmul(a, b):
    x1, y1, z1, w1 = a; x2, y2, z2, w2 = b
    return (w1*x2+x1*w2+y1*z2-z1*y2, w1*y2-x1*z2+y1*w2+z1*x2, w1*z2+x1*y2-y1*x2+z1*w2, w1*w2-x1*x2-y1*y2-z1*z2)
def conj(q): return (-q[0], -q[1], -q[2], q[3])
def rot(q, v): return qmul(qmul(q, (v[0], v[1], v[2], 0.0)), conj(q))[:3]


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
    best = []
    for start in range(0, len(fb) - 52):  # Records are not always 4-byte aligned.
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


def decode_best(tid):
    names = [f"{tid}.dds"] + [f"{tid}_{k}.dds" for k in range(6)]
    files = extract(names)
    best = None
    for name in names:
        if name not in files:
            continue
        data = files[name].read_bytes()
        if data[16:20] != b"KEEN" or data[29] not in (1, 5):
            continue
        w, h, fmt, mips = *struct.unpack_from("<HH", data, 20), data[29], struct.unpack_from("<H", data, 35)[0]
        at, block = 38, 8 if fmt == 1 else 16
        for _ in range(mips):
            size = ((w + 3) // 4) * ((h + 3) // 4) * block
            if at + size > len(data):
                break
            if max(w, h) <= TEXTURE_LIMIT:
                if best is None or w > best[0]:
                    best = (w, h, bytes(keen_texture.decode_blocks(data[at:at + size], w, h, fmt)))
                break
            at += size
            w, h = max(1, w // 2), max(1, h // 2)
    return best


def material_refs(mid):
    files = extract([f"{mid}.mat_bxml"])
    refs = []
    if files:
        d = next(iter(files.values())).read_bytes()
        for i in range(0, len(d) - 3, 4):
            v = struct.unpack_from("<I", d, i)[0]
            name = syms["texture"].get(str(v))
            if name and v not in [r[0] for r in refs]:
                refs.append((v, name))
    return refs


texture_cache = {}
def material_texture(mid):
    if mid in texture_cache:
        return texture_cache[mid]
    refs = material_refs(mid)
    order = [r for r in refs if r[1].lower().endswith("_d") and "par_color" not in r[1]] or [r for r in refs if not r[1].lower().endswith(("_n", "_s", "_g", "_a"))]
    alpha = next((r[0] for r in refs if r[1].lower().endswith("_a")), None)
    result = None
    if not any(r[1].lower().endswith("_d") for r in refs) and alpha:
        # Hair and beards carry only a shape mask; the game tints them at runtime. Neutral brown is an authored stand-in.
        mask = decode_best(alpha)
        if mask:
            mw, mh, mr = mask
            o = bytearray(b"\x3a\x28\x1c\xff" * (mw * mh))
            o[3::4] = mr[0::4]
            result = (mw, mh, bytes(o), "tinted mask")
            texture_cache[mid] = result
            return result
    for tid, name in order:
        best = decode_best(tid)
        if best:
            w, h, rgba = best
            o = bytearray(rgba)
            o[3::4] = b"\xff" * (w * h)
            mask = decode_best(alpha) if alpha else None
            if mask:
                mw, mh, mr = mask
                for y in range(h):
                    for x in range(w):
                        o[(y * w + x) * 4 + 3] = mr[((y * mh // h) * mw + x * mw // w) * 4]
            result = (w, h, bytes(o), name)
            break
    texture_cache[mid] = result
    return result


def bake(cid, skel_path):
    extract([f"{cid}.anm_bxml"])
    target = wc / f"baked/{cid}_{Path(skel_path).stem}.bin"
    if not target.exists():
        r = subprocess.run([str(BIN), str(g / "koa.exe"), str(skel_path), str(inp / f"initial_0.pak/{cid}.anm_bxml"), str(target)], capture_output=True, text=True)
        if r.returncode:
            raise SystemExit(f"bake {cid}: {r.returncode} {r.stderr}")
    b = target.read_bytes()
    j, frames, fps = struct.unpack_from("<IIf", b)
    rows = bytearray()
    for i in range(frames * j):
        v = struct.unpack_from("<7f", b, 12 + i * 48)
        rows += struct.pack("<7f", *conj(v[:4]), *v[4:7])
    return frames, fps, bytes(rows)


def anim_id(name):
    return next(int(k) for k, v in syms["animation"].items() if v == name)


def pick_clip(patterns, joints):
    """First looping named clip with a matching joint count, in preference order."""
    for pattern in patterns:
        names = sorted((v, int(k)) for k, v in syms["animation"].items() if re.fullmatch(pattern, v, re.I))
        got = extract([f"{i}.anm_bxml" for _, i in names])
        for v, i in names:
            q = got.get(f"{i}.anm_bxml")
            if q and q.stat().st_size > 400:
                b = q.read_bytes()
                if struct.unpack_from("<H", b, 8 + 0xe)[0] == joints and struct.unpack_from("<f", b, 12)[0] > .6:
                    print("clip", v, i, "seconds", round(struct.unpack_from("<f", b, 12)[0], 2))
                    return i
    raise SystemExit("no idle clip for %d joints" % joints)


SKELS = {}
skel_files = extract(["467100.fab_bxml", "611642.fab_bxml"])
for key, fid, idle in (("m", 467100, [r"human_idle_01"]), ("f", 611642, [r"human_female_idle_\d+", r"human_npc_female_idle\w*", r"human_npc_idle_?0?1_?f", r"human\w*female\w*idle\w*", r"\w*idle\w*_f", r"human_idle_01"])):
    path = skel_files[f"{fid}.fab_bxml"]
    fb = path.read_bytes()
    J, par, names, world = skeleton(fb)
    SKELS[key] = dict(world=world, path=path, joints=J, parents=par, names=names, index={n: i for i, n in enumerate(names)}, clip=bake(pick_clip(idle, J), path))
    print("skeleton", key, fid, J, "clip frames", SKELS[key]["clip"][0])

# People
gors = [n for n in listing["initial_0.pak"] if n.endswith(".gor_bxml")]
files = extract(gors)
people = []
for n, p in files.items():
    if not re.match(r"citizen_|npc_", n):
        continue
    d = p.read_bytes()
    if len(d) < 80 or struct.unpack_from("<I", d, 8)[0] != SPACE:
        continue
    pos = struct.unpack_from("<3f", d, 24)
    if math.dist(pos[:2], DOOR[:2]) > RADIUS:
        continue
    q = struct.unpack_from("<4f", d, 36)
    sim = next((w for w in struct.unpack_from(f"<{min(30, len(d) // 4)}I", d, 0) if str(w) in syms["simtype"]), None)
    if sim:
        people.append((n[:-9], pos, q, sim))
print("people", [p[0] for p in people])

blob_people = []
report = []
ENEMY_SIM = next(int(k) for k, v in syms["simtype"].items() if v == "human_bandit_swordsman")
COMBAT_CLIPS = [(673754, "combat_idle"), (673863, "combat_walk"), (673928, "combat_run"), (673833, "attack_b"), (1893691, "attack_special"), (673835, "attack_x"), (673903, "react_front"), (1926549, "react_death")]
SWORD_PART = None
people.append(("enemy_bandit", (2600.0, -63500.0, 5170.0), (0.0, 0.0, 0.0, 1.0), ENEMY_SIM))
for name, pos, q, sim in people:
    bd = extract([f"{sim}.bundle"]).get(f"{sim}.bundle")
    if not bd:
        report.append((name, "no bundle")); continue
    d = bd.read_bytes()
    ids = list(dict.fromkeys(struct.unpack_from(f"<{(len(d) - 16) // 4}I", d, 16)))
    ragdolls = [syms["ragdoll"][str(v)] for v in ids if str(v) in syms["ragdoll"]]
    key = "f" if any(r.endswith("_f") for r in ragdolls) else "m"
    sk = SKELS[key]
    fabs = [v for v in ids if "fab_visual_data_streamable_bin" in files_by_id.get(v, []) and v not in (467100, 456813, 611642) and not re.search(r"sword|axe|spear|dagger|mace|hammer|shield|bow|staff|acc_", syms["fab"].get(str(v), ""))]
    parts, textures, tex_index, skipped = [], [], {}, []
    for fid in fabs:
        fs = extract([f"{fid}.fab_bxml", f"{fid}.fab_visual_data_streamable_bin"])
        vis = fs.get(f"{fid}.fab_visual_data_streamable_bin"); fbp = fs.get(f"{fid}.fab_bxml")
        if not vis or not fbp or vis.stat().st_size < 60:
            skipped.append(fid); continue
        fb = fbp.read_bytes()
        try:
            n, fpar, fnames, fworld = skeleton(fb)
            mesh = amalur_mesh.parse_file(vis)
        except Exception as e:
            skipped.append((fid, str(e)[:40])); continue
        pal = palette(fb, n)
        if not pal:
            skipped.append((fid, "no palette")); continue
        raw = vis.read_bytes()
        entries = []
        for idx, inv_t, inv_q in pal:
            cur = idx
            while cur != 0xffff and fnames[cur] not in sk["index"]:
                cur = fpar[cur]
            joint = sk["index"][fnames[cur]] if cur != 0xffff else 1
            wq, wt = fworld[idx]
            iq = conj(wq); it = tuple(-x for x in rot(iq, wt))
            err = max(abs(it[k] - inv_t[k]) for k in range(3))
            entries.append((joint, it, iq) if err < 1 else (joint, tuple(inv_t), conj(tuple(inv_q))))
        # Per-assembly material ids sit unaligned after the skeleton, one for each assembly in order.
        payload_end = struct.unpack_from("<I", fb, 0)[0] + 8
        mats, at = [], payload_end
        while at + 4 <= len(fb):
            v = struct.unpack_from("<I", fb, at)[0]
            if v > 4096 and "mat_bxml" in files_by_id.get(v, []):
                mats.append(v); at += 4
            else:
                at += 1
        for ai, asm in enumerate(mesh["assemblies"]):
            if asm["unknown_u16_at2"]:  # 32768 marks the lower detail copy of the same surface.
                continue
            vb = mesh["vertex_buffers"][asm["vertex_buffer"]]
            ib = mesh["index_buffers"][asm["index_buffer"]]
            st = vb["stride_bytes"]
            if st not in (56, 60, 64):
                skipped.append((fid, f"stride {st}")); continue
            base = vb["data_file_offset"]
            def score(offset):
                s = 0.0
                for i in range(0, vb["vertex_count"], max(1, vb["vertex_count"] // 40)):
                    x = struct.unpack_from("<3h", raw, base + i * st + offset)
                    s += abs(math.sqrt(sum((c / 32767) ** 2 for c in x)) - 1)
                return s
            normal_at = min((o for o in (32, 36, 40, 44) if o + 6 <= st), key=score)
            verts = bytearray()
            for i in range(vb["vertex_count"]):
                a = base + i * st
                p = struct.unpack_from("<3f", raw, a)
                jx = raw[a + 12:a + 16]
                w = [x / 32767.0 for x in struct.unpack_from("<4H", raw, a + 16)]
                # The shader reads three weights and gives the fourth the remainder.
                w[3] = max(0.0, 1.0 - sum(w[:3]))
                uv = struct.unpack_from("<2f", raw, a + 24)
                nn = [x / 32767.0 for x in struct.unpack_from("<3h", raw, a + normal_at)]
                verts += struct.pack("<8f4B4f", *p, *nn, *uv, *jx, *w)
            mid = mats[ai] if ai < len(mats) else (mats[0] if mats else 0)
            if re.search(r"eye_shadow|face_acc|eyelash", syms["material"].get(str(mid), "")):
                continue  # Overlay decals need blending the renderer does not have yet.
            if max(verts[32 + i * 52 + k] for i in range(len(verts) // 52) for k in range(4)) >= len(entries):
                skipped.append((fid, "joint beyond palette")); continue
            tex = material_texture(mid)
            ti = -1
            if tex:
                if mid not in tex_index:
                    tex_index[mid] = len(textures)
                    textures.append(tex)
                ti = tex_index[mid]
            parts.append((verts, ib["indices"], entries, ti, syms["material"].get(str(mid), str(mid)) + ("" if tex else "(notex)"), normal_at, st))
    if not parts or len(parts) > 24 or len(textures) > 16:
        report.append((name, "unusable", len(parts), len(textures), skipped)); continue
    # Skin every part with the first idle frame: nothing should travel far from its bind position.
    frames0, _, rows0 = sk["clip"]
    posed = []
    for i in range(sk["joints"]):
        v0 = struct.unpack_from("<7f", rows0, i * 28)
        if sk["parents"][i] == 0xffff:
            posed.append((v0[:4], v0[4:7]))
        else:
            pq0, pt0 = posed[sk["parents"][i]]
            r0 = rot(pq0, v0[4:7])
            posed.append((qmul(pq0, v0[:4]), tuple(pt0[k] + r0[k] for k in range(3))))
    print("POSE", name, "biggest joint move", max((round(math.dist(posed[i][1], sk["world"][i][1])), str(syms["ragdoll_bone_mappings"].get(str(sk["names"][i]), i))) for i in range(sk["joints"])), "pelvis", [round(x) for x in posed[2][1]], "head", [round(x) for x in posed[21][1]])
    for verts, inds, entries, ti, mname, *_ in parts:
        skins = []
        for joint, it, iq in entries:
            wq, wt = posed[joint]
            skins.append((qmul(wq, iq), tuple(wt[k] + x for k, x in enumerate(rot(wq, it)))))
        worst, worst_joint, moved = 0.0, None, 0
        for i in range(0, len(verts) // 52, 3):
            v = struct.unpack_from("<8f4B4f", verts, i * 52)
            o = [0.0, 0.0, 0.0]
            for b, weight in zip(v[8:12], v[12:16]):
                if weight > 0:
                    q2, t2 = skins[b]
                    r2 = rot(q2, v[:3])
                    for k in range(3):
                        o[k] += weight * (r2[k] + t2[k])
            d = math.dist(o, v[:3])
            if d > 90:
                moved += 1
            if d > worst:
                worst, worst_joint = d, max(zip(v[12:16], v[8:12]))[1]
        if worst > 90:
            e = entries[worst_joint]
            print("SKIN", name, mname, "worst", round(worst), "moved", moved, "of", len(verts) // 156, "entry", worst_joint, "joint", e[0], str(syms["ragdoll_bone_mappings"].get(str(sk["names"][e[0]]), sk["names"][e[0]])), "inv t", [round(x) for x in e[1]], "bind", [round(x) for x in sk["world"][e[0]][1]])
    frames, fps, rows = sk["clip"]
    clip_rows = [(frames, fps, rows)]
    if name == "enemy_bandit":
        clip_rows = [bake(cid, sk["path"]) for cid, _ in COMBAT_CLIPS]
        fid = 1327249
        f2 = extract([f"{fid}.fab_visual_data_streamable_bin"])
        vis2 = f2[f"{fid}.fab_visual_data_streamable_bin"]
        m2 = amalur_mesh.parse_file(vis2); raw2 = vis2.read_bytes()
        asm2 = m2["assemblies"][0]; vb2 = m2["vertex_buffers"][asm2["vertex_buffer"]]
        sv = bytearray()
        for i in range(vb2["vertex_count"]):
            a2 = vb2["data_file_offset"] + i * vb2["stride_bytes"]
            sv += struct.pack("<8f4B4f", *struct.unpack_from("<3f", raw2, a2), *[x / 32767.0 for x in struct.unpack_from("<3h", raw2, a2 + 20)], *struct.unpack_from("<2f", raw2, a2 + 12), 0, 0, 0, 0, 1.0, 0.0, 0.0, 0.0)
        mid2 = next(int(k) for k, v in syms["material"].items() if v == "02_steel_sword_1h")
        tex2 = material_texture(mid2)
        ti2 = -1
        if tex2:
            ti2 = len(textures); textures.append(tex2)
        parts.append((sv, m2["index_buffers"][asm2["index_buffer"]]["indices"], [(55, (0.0, 0.0, 0.0), (0.0, 0.0, 0.0, 1.0))], ti2, "sword", 0, 48))
    c = bytearray(b"OACHAR01") + struct.pack("<IIII", sk["joints"], len(clip_rows), len(parts), len(textures))
    c += struct.pack(f"<{sk['joints']}h", *[(-1 if x == 0xffff else x) for x in sk["parents"]])
    for frames_i, fps_i, rows_i in clip_rows:
        c += struct.pack("<If", frames_i, fps_i) + rows_i
    for w, h, rgba, _ in textures:
        c += struct.pack("<II", w, h) + rgba
    for verts, inds, entries, ti, mname, *_ in parts:
        c += struct.pack("<IIIi", len(verts) // 52, len(inds), len(entries), ti)
        for joint, it, iq in entries:
            c += struct.pack("<I7f", joint, *iq, *it)
        c += bytes(verts) + struct.pack(f"<{len(inds)}I", *inds)
    yaw = 2 * math.atan2(q[2], q[3])
    if name == "enemy_bandit":
        (out / "town_enemy.bin").write_bytes(bytes(c))
        report.append((name, key, "parts", len(parts), "textures", len(textures), [p[4] for p in parts], "skipped", skipped))
        continue
    blob_people.append((name, pos, yaw, bytes(c)))
    report.append((name, key, "parts", len(parts), "textures", len(textures), "mb", round(len(c) / 1e6, 1), [p[4] for p in parts], "skipped", skipped, "normal", sorted({(p[6], p[5]) for p in parts})))
container = bytearray(b"OANPCS01") + struct.pack("<I", len(blob_people))
for name, pos, yaw, c in blob_people:
    container += struct.pack("<4fI", *pos, yaw, len(c)) + c
(out / "town_npcs.bin").write_bytes(container)
for r in report:
    print(r)
print("people packed", len(blob_people), "bytes", len(container))
