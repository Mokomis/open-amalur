"""Build work/v23-actors: every character and creature of Dalentarth, placed from object records and encounter records.
Real: placement objects, encounter spawn points, encounter tables, monster groups, models, textures and clips.
Authored: which group an encounter chooses (first word of each table row taken as a weight), one member per spawn point, all encounters active at once, stats, speeds and strike times."""
import collections, json, math, random, re, struct, sys
from pathlib import Path
source = (Path.home() / "Documents/Opem Amalur/work/v20-char/build_npcs.py").read_text()
exec(source[:source.index("SKELS = {}")])
OUT = Path(__import__("os").environ.get("OA_ACTORS_DIR", str(root / "work/v23-actors"))); OUT.mkdir(parents=True, exist_ok=True)
ZONE = __import__("os").environ.get("OA_ZONE", "dal")
log = lambda *a: print(*a, flush=True)
sim = {int(k): str(v) for k, v in syms["simtype"].items()}
encs = {int(k): str(v) for k, v in syms["encounter"].items()}
groups = {int(k): str(v) for k, v in syms["monstergroup"].items()}
spaces = {int(k): str(v) for k, v in syms["simspace"].items() if re.match(rf"out_{ZONE}_", str(v))}
rng = random.Random(431608)
SKIP_ENC = re.compile(r"obsolet|obsolte|joeonly|^enc_quest|^dlc|^enc_hv|^enc_case|sq\d|ffq|mq\d", re.I)
# Placed characters.
gors = [n for n in listing["initial_0.pak"] if n.endswith(".gor_bxml")]
files = extract(gors)
def bundle_ids(sid):
    bd = extract([f"{sid}.bundle"]).get(f"{sid}.bundle")
    if not bd: return None
    d = bd.read_bytes()
    return list(dict.fromkeys(struct.unpack_from(f"<{(len(d) - 16) // 4}I", d, 16)))
def ragdoll_of(ids):
    found = next((str(syms["ragdoll"][str(v)]) for v in ids if str(v) in syms["ragdoll"]), None)
    if found: return found
    # Some creatures keep their rig in a bundle they depend on.
    for v in ids:
        if "bundle" in files_by_id.get(v, []):
            inner = bundle_ids(v) or []
            found = next((str(syms["ragdoll"][str(w)]) for w in inner if str(w) in syms["ragdoll"]), None)
            if found: return found
    return None
placed = []
for n, p in files.items():
    d = p.read_bytes()
    if len(d) < 80 or struct.unpack_from("<I", d, 8)[0] not in spaces or re.search(r"corpse|^dlc|^obj_|^container|^door", n):
        continue
    sid = parse_gor(d)["record"]["type_id"]
    if sid not in sim: sid = None
    if not sid: continue
    ids = bundle_ids(sid)
    if not ids or not ragdoll_of(ids): continue
    q = parse_gor(d)["record"]["quaternion"]
    placed.append((sid, struct.unpack_from("<3f", d, 24), heading_xy(q), n[:-9]))
log("placed characters", len(placed))
# Encounter spawn points.
def table(eid):
    f = extract([f"{eid}.encounter_bxml"]).get(f"{eid}.encounter_bxml")
    if not f: return []
    b = f.read_bytes(); out = []
    for o in range(0, len(b) - 7, 4):
        w, g2 = struct.unpack_from("<II", b, o)
        if g2 in groups and 0 < w < 100000: out.append((w, g2))
    return out
def members(gid):
    f = extract([f"{gid}.monstergroup_bxml"]).get(f"{gid}.monstergroup_bxml")
    if not f: return []
    b = f.read_bytes(); out = []
    for o in range(4, len(b) - 3, 4):
        v = struct.unpack_from("<I", b, o)[0]
        if v in sim:
            c = struct.unpack_from("<I", b, o - 4)[0]
            out += [v] * (c if 1 <= c <= 8 else 1)
    return out
spawned, enc_used = [], collections.Counter(); seen = set(); skipped_enc = collections.Counter()
for k, n in spaces.items():
    f = extract([f"{k}.space_bxml"]).get(f"{k}.space_bxml")
    if not f: continue
    b = f.read_bytes()
    for o in range(16, len(b) - 48):
        v = struct.unpack_from("<I", b, o)[0]
        if v not in encs: continue
        p1, c1, p2, c2 = struct.unpack_from("<4I", b, o - 16)
        if c1 != c2 or not 0 < c1 < 64 or p1 + c1 * 12 > len(b) or (k, o) in seen: continue
        seen.add((k, o)); name = encs[v]
        if SKIP_ENC.search(name):
            skipped_enc[name] += c1; continue
        rows = table(v)
        if not rows:
            skipped_enc[name] += c1; continue
        gid = rng.choices([r[1] for r in rows], [r[0] for r in rows])[0]
        team = members(gid)
        if not team:
            skipped_enc[name] += c1; continue
        pts = [struct.unpack_from("<3f", b, p1 + i * 12) for i in range(c1)]
        total = min(8, max(len(pts), len(team)))
        for i in range(total):
            base = pts[i % len(pts)]; off = 0 if i < len(pts) else 250
            spawned.append((team[i % len(team)], (base[0] + rng.uniform(-off, off), base[1] + rng.uniform(-off, off), base[2]), rng.uniform(-3.14, 3.14), name, len(enc_used) + 1000 * (o % 997)))
        enc_used[name] += total
log("encounter actors", len(spawned), enc_used.most_common(40)); log("encounters left out", skipped_enc.most_common(30))
wanted = collections.Counter(a[0] for a in placed) + collections.Counter(a[0] for a in spawned)
log("simtypes", len(wanted), [(sim[k], c) for k, c in wanted.most_common(60)])
# Skeletons.
SK = {}
skel_files = extract(["467100.fab_bxml", "611642.fab_bxml"])
def load_skel(key, fid):
    fb = extract([f"{fid}.fab_bxml"])[f"{fid}.fab_bxml"]
    J, par, names, world = skeleton(fb.read_bytes())
    SK[key] = dict(world=world, path=fb, joints=J, parents=par, names=names, index={n: i for i, n in enumerate(names)}, key=key, clips={})
    return SK[key]
load_skel("m", 467100); load_skel("f", 611642)
fab_by_name = {str(v).lower(): int(k) for k, v in syms["fab"].items()}
anim_names = sorted((str(v), int(k)) for k, v in syms["animation"].items())
def find_clip(patterns, joints):
    for pattern in patterns:
        rx = re.compile(pattern, re.I)
        got = [(v, i) for v, i in anim_names if rx.fullmatch(v)]
        fs = extract([f"{i}.anm_bxml" for _, i in got])
        for v, i in got:
            q = fs.get(f"{i}.anm_bxml")
            if q and q.stat().st_size > 400:
                b = q.read_bytes()
                if struct.unpack_from("<H", b, 8 + 0xe)[0] == joints and struct.unpack_from("<f", b, 12)[0] > .25:
                    return i, v
    return None, None
def clip_set(sk, prefix):
    """Idle, walk, run, attack, hit, death; -1 where the creature has none."""
    if prefix in sk["clips"]: return sk["clips"][prefix]
    if prefix == "human":
        f = sk["key"] == "f"
        P = [[r"human_female_idle_01", r"human_idle_01"] if f else [r"human_idle_01"], [r"human_walk_01_f", r"human_female_walk_01"] if f else [r"human_walk_01"], [r"human_run_01_f", r"human_female_run_01"] if f else [r"human_run_01"], [r"Human_NPC_Attack01"], [r"Human_NPC_React\w*Front\w*", r"human\w*react\w*front\w*"], [r"Human_NPC_Death\w*", r"human\w*death\w*"]]
    else:
        p = re.escape(prefix)
        P = [[p + r"_idle(_0?1)?", p + r"_combat_idle(_0?1)?", p + r"_nci_idle(_0?1)?", p + r"\w*idle\w*"], [p + r"_walk(_0?1)?", p + r"_walk\w*", p + r"\w*walk\w*"], [p + r"_run(_f)?(_0?1)?", p + r"_run\w*", p + r"\w*run\w*"],
             [p + r"_attack_(x|swipe|maul|b|melee|bite)\w*", p + r"_attack\w*", p + r"\w*attack\w*"], [p + r"_react_(frt|front|interrupt_front)\w*", p + r"_react\w*", p + r"\w*react\w*"], [p + r"_(react_)?death(_0?1)?", p + r"\w*death\w*"]]
    out = []
    for pats in P:
        i, v = find_clip(pats, sk["joints"]); out.append((i, v))
    log("clips", prefix, sk["key"], [v for _, v in out])
    sk["clips"][prefix] = out
    return out
def skeleton_for(ids, rag):
    """The rig named after the ragdoll when there is one, else the richest rig among the model's own parts; whichever has an idle clip."""
    if rag.startswith("human"):
        return SK["f" if rag.endswith("_f") else "m"], "human"
    key = rag.lower(); stem = re.sub(r"_(skel|vvs)\w*$", "", key); flat = stem.replace("_", "")
    prefixes = list(dict.fromkeys([stem, flat, "giant" + flat, "giant_" + stem, stem.split("_")[0], stem.split("_")[-1], flat.replace("hunter", "")]))
    named = [fab_by_name[n] for n in (key, stem + "_skel", flat + "_skel", "giant_" + stem + "_skel") if n in fab_by_name]
    own = []
    for v in ids:
        if "fab_visual_data_streamable_bin" in files_by_id.get(v, []):
            f = extract([f"{v}.fab_bxml"]).get(f"{v}.fab_bxml")
            if f:
                try:
                    own.append((skeleton(f.read_bytes())[0], v))
                except Exception:
                    pass
    for fid in list(dict.fromkeys(named + [v for _, v in sorted(own, reverse=True)])):
        k = f"rig{fid}"
        if k not in SK:
            try:
                load_skel(k, fid)
            except Exception:
                continue
        sk = SK[k]
        if sk["joints"] > 128: continue
        for pre in prefixes:
            if find_clip([re.escape(pre) + r"_idle(_0?1)?", re.escape(pre) + r"_combat_idle(_0?1)?", re.escape(pre) + r"_nci_idle(_0?1)?", re.escape(pre) + r"\w*idle\w*"], sk["joints"])[0]:
                return sk, pre
    return None, None
def palettes(fb, joints):
    """Every joint table in file order. There is one per surface, lower detail copies included."""
    tables, start = [], 0
    while start < len(fb) - 52:
        chain, at = [], start
        while at + 52 <= len(fb):
            s = struct.unpack_from("<3f", fb, at + 32)
            q = struct.unpack_from("<4f", fb, at + 16)
            count, idx = struct.unpack_from("<II", fb, at + 44)
            if not all(abs(x - 1) < .02 for x in s) or abs(sum(x * x for x in q) - 1) > .02 or idx >= joints or count > 300:
                break
            chain.append((idx, struct.unpack_from("<3f", fb, at), q))
            at += 52
        if chain:
            tables.append(chain); start = at
        else:
            start += 1
    return tables


def model_parts(ids, sk):
    fabs = [v for v in ids if "fab_visual_data_streamable_bin" in files_by_id.get(v, []) and not str(syms["fab"].get(str(v), "")).endswith("_skel") and v not in (467100, 456813, 611642) and not re.search(r"sword|axe|spear|dagger|mace|hammer|shield|bow|staff|acc_", syms["fab"].get(str(v), ""))]
    parts, textures, tex_index, skipped = [], [], {}, []
    for fid in fabs:
        fs = extract([f"{fid}.fab_bxml", f"{fid}.fab_visual_data_streamable_bin"])
        vis = fs.get(f"{fid}.fab_visual_data_streamable_bin"); fbp = fs.get(f"{fid}.fab_bxml")
        if not vis or not fbp or vis.stat().st_size < 60:
            skipped.append(fid); continue
        fb = fbp.read_bytes()
        try:
            n, fpar, fnames, fworld = skeleton(fb); mesh = amalur_mesh.parse_file(vis)
        except Exception as e:
            skipped.append((fid, str(e)[:40])); continue
        tables = palettes(fb, n)
        raw = vis.read_bytes()
        if not tables:
            skipped.append((fid, "no tables")); continue
        payload_end = struct.unpack_from("<I", fb, 0)[0] + 8; mats, at = [], payload_end
        while at + 4 <= len(fb):
            v = struct.unpack_from("<I", fb, at)[0]
            if v > 4096 and "mat_bxml" in files_by_id.get(v, []):
                mats.append(v); at += 4
            else:
                at += 1
        for ai, asm in enumerate(mesh["assemblies"]):
            if asm["unknown_u16_at2"]: continue
            # Stray matches can add tables; then the longest is the one that was meant.
            pal = tables[ai] if len(tables) == len(mesh["assemblies"]) else max(tables, key=len)
            if not pal or len(pal) > 96:
                skipped.append((fid, "palette", len(pal))); continue
            entries = []
            for idx, inv_t, inv_q in pal:
                cur = idx
                while cur != 0xffff and fnames[cur] not in sk["index"]:
                    cur = fpar[cur]
                joint = sk["index"][fnames[cur]] if cur != 0xffff else 1
                wq, wt = sk["world"][joint] if cur != 0xffff else fworld[idx]; iq = conj(wq); it = tuple(-x for x in rot(iq, wt))
                err = max(abs(it[k] - inv_t[k]) for k in range(3))
                entries.append((joint, it, iq) if err < 1 or cur != 0xffff else (joint, tuple(inv_t), conj(tuple(inv_q))))
            vb = mesh["vertex_buffers"][asm["vertex_buffer"]]; ib = mesh["index_buffers"][asm["index_buffer"]]; st = vb["stride_bytes"]
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
                a = base + i * st; p = struct.unpack_from("<3f", raw, a); jx = raw[a + 12:a + 16]
                w = [x / 32767.0 for x in struct.unpack_from("<4H", raw, a + 16)]; w[3] = max(0.0, 1.0 - sum(w[:3]))
                uv = struct.unpack_from("<2f", raw, a + 24); nn = [x / 32767.0 for x in struct.unpack_from("<3h", raw, a + normal_at)]
                verts += struct.pack("<8f4B4f", *p, *nn, *uv, *jx, *w)
            mid = mats[ai] if ai < len(mats) else (mats[0] if mats else 0)
            if re.search(r"eye_shadow|face_acc|eyelash", syms["material"].get(str(mid), "")): continue
            if max(verts[32 + i * 52 + k] for i in range(len(verts) // 52) for k in range(4)) >= len(entries):
                skipped.append((fid, "joint beyond palette")); continue
            tex = material_texture(mid); ti = -1
            if tex:
                if mid not in tex_index:
                    tex_index[mid] = len(textures); textures.append(tex)
                ti = tex_index[mid]
            parts.append((verts, ib["indices"], entries, ti))
    return parts, textures, skipped
def title(name):
    n = re.sub(r"^(npc_dal_\w{3}_|npc_|citizen_gorhart_\w{3}_|citizen_|human_)", "", name).split("_")[0]
    return {"redlegion": "Red Legion", "giantspider": "Giant Spider", "smallspider": "Spider"}.get(n.lower(), n.capitalize())[:23]
types, type_of, report = [], {}, []
HOSTILE = re.compile(r"troll|boggart|wolf|bear|sprite|brownie|spider|ettin|barghest|thresh|kobold|murghan|jottun|faergorta|niskaru|bandit|redlegion|red_legion|legion|tuatha|rat|gorta|dokkalfar", re.I)
ANIMAL = re.compile(r"antelope|deer|boar", re.I)
for sid in [k for k, _ in wanted.most_common()]:
    name = sim[sid]; ids = bundle_ids(sid)
    if not ids:
        report.append((name, "no bundle")); continue
    # The venom spitters carry no rig of their own and use the giant spider's.
    rag = ragdoll_of(ids) or ("giant_spider_skel" if name.startswith("giantspider") else None)
    if not rag:
        report.append((name, "no ragdoll")); continue
    sk, prefix = skeleton_for(ids, rag)
    if not sk:
        report.append((name, "skeleton", rag)); continue
    clips = clip_set(sk, prefix)
    if clips[0][0] is None:
        report.append((name, "no idle", prefix)); continue
    try:
        parts, textures, skipped = model_parts(ids, sk)
    except Exception as e:
        report.append((name, "model failed", repr(e)[:100])); continue
    if not parts or len(parts) > 24 or len(textures) > 16:
        report.append((name, "unusable", len(parts), len(textures), skipped[:4])); continue
    hostile = bool(HOSTILE.search(name)) and not name.startswith(("npc_", "citizen_")); animal = bool(ANIMAL.search(name))
    kind = 1 if animal else 2 if hostile else 0
    order, index = [], {}
    # Oneshot clips must sit at 3 and up. Walk and run stand in for each other when one is missing, so nothing slides.
    move = {1: clips[1][0] or clips[2][0] or clips[0][0], 2: clips[2][0] or clips[1][0] or clips[0][0]}
    baked = [bake(clips[0][0], sk["path"]), bake(move[1], sk["path"]), bake(move[2], sk["path"])]
    extra = [-1, -1, -1]
    if kind == 2:
        for j in range(3, 6):
            if clips[j][0] is not None:
                extra[j - 3] = len(baked); baked.append(bake(clips[j][0], sk["path"]))
    height = max(w[1][2] for w in sk["world"]) or 180.0
    size = min(4.0, max(.35, height / 175.0))
    secs = lambda k: (baked[k][0] - 1) / baked[k][1] if k >= 0 else 1.0
    c = bytearray(b"OACHAR01") + struct.pack("<IIII", sk["joints"], len(baked), len(parts), len(textures))
    c += struct.pack(f"<{sk['joints']}h", *[(-1 if x == 0xffff else x) for x in sk["parents"]]) + (b"\0\0" if sk["joints"] % 2 else b"")
    for fr, fps, rows in baked:
        c += struct.pack("<If", fr, fps) + rows
    for w, h, rgba, _ in textures:
        c += struct.pack("<II", w, h) + rgba
    for verts, inds, entries, ti in parts:
        c += struct.pack("<IIIi", len(verts) // 52, len(inds), len(entries), ti)
        for joint, it, iq in entries:
            c += struct.pack("<I7f", joint, *iq, *it)
        c += bytes(verts) + struct.pack(f"<{len(inds)}I", *inds)
    ti = len(types)
    (OUT / f"a{ti}.bin").write_bytes(bytes(c))
    # Authored stats scaled by body size.
    types.append(dict(name=title(name), kind=kind, walk=150 * size, run=(640 if animal else 420) * size ** .7, radius=35 * size, hp=70 * size ** 1.5, damage=6 * size, aggro=1300 + 300 * size, reach=170 + 45 * size, attack=extra[0], hit=extra[1], death=extra[2], attack_len=secs(extra[0]), hit_len=secs(extra[1]), sim=name))
    type_of[sid] = ti
    report.append((name, "ok", ti, sk["key"], prefix, "kind", kind, "parts", len(parts), "tex", len(textures), "mb", round(len(c) / 1e6, 2), "clips", [v for _, v in clips], "skipped", skipped[:3]))
    log(report[-1])
actors = []
gid_map = {}
for sid, pos, yaw, name in placed:
    if sid in type_of: actors.append((pos, yaw, type_of[sid], 0))
for sid, pos, yaw, name, g in spawned:
    if sid in type_of: actors.append((pos, yaw, type_of[sid], gid_map.setdefault(g, len(gid_map) + 1)))
idx = bytearray(b"OAAI") + struct.pack("<II", len(types), len(actors))
for t in types:
    idx += struct.pack("<9f3iI24s", t["walk"], t["run"], t["radius"], t["hp"], t["damage"], t["aggro"], t["reach"], t["attack_len"], t["hit_len"], t["attack"], t["hit"], t["death"], t["kind"], t["name"].encode()[:23])
for pos, yaw, ti, g in actors:
    idx += struct.pack("<4fHH", *pos, yaw, ti, g & 0xffff)
(OUT / "index.bin").write_bytes(bytes(idx))
(OUT / "report.json").write_text(json.dumps(dict(report=report, types=types, skipped_enc=skipped_enc, enc_used=enc_used), indent=0, default=str))
counts = collections.Counter(types[a[2]]["kind"] for a in actors)
log("DONE types", len(types), "actors", len(actors), "by kind person/animal/hostile", counts, "dropped simtypes", [r[:3] for r in report if r[1] != "ok"], "bytes", sum(p.stat().st_size for p in OUT.glob("a*.bin")))
