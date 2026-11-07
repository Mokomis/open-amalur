"""Decode skeleton bones, skinned vertex layout, armor FAB tables, clip headers and native tool paths."""
import json, math, re, struct, subprocess, sys
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
g = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning")
inp = root / "work/v20-inputs"
syms = json.loads((inp / "symbols.json").read_text())
anim = {int(k): v for k, v in syms["animation"].items()}

d = (inp / "patch_0.pak/456813.fab_bxml").read_bytes()
BONES, T, P, N = 64, 0x184, 0xd84, 0xe04
names = struct.unpack_from("<64I", d, N)
parents = struct.unpack_from("<64H", d, P)
bone_syms = {}
for k, rows in syms.items():
    for s, v in rows.items():
        bone_syms.setdefault(int(s), (k, v))
def qmul(a, b):
    x1, y1, z1, w1 = a; x2, y2, z2, w2 = b
    return (w1*x2+x1*w2+y1*z2-z1*y2, w1*y2-x1*z2+y1*w2+z1*x2, w1*z2+x1*y2-y1*x2+z1*w2, w1*w2-x1*x2-y1*y2-z1*z2)
def qrot(q, v):
    u = q[:3]; w = q[3]
    t = [2*(u[1]*v[2]-u[2]*v[1]), 2*(u[2]*v[0]-u[0]*v[2]), 2*(u[0]*v[1]-u[1]*v[0])]
    return [v[0]+w*t[0]+u[1]*t[2]-u[2]*t[1], v[1]+w*t[1]+u[2]*t[0]-u[0]*t[2], v[2]+w*t[2]+u[0]*t[1]-u[1]*t[0]]
world = []
print("=== bones: i parent name local_t local_q world_t")
for i in range(BONES):
    t = struct.unpack_from("<4f", d, T + i * 48)
    q = struct.unpack_from("<4f", d, T + i * 48 + 16)
    s = struct.unpack_from("<4f", d, T + i * 48 + 32)
    p = parents[i] if parents[i] != 0xffff else -1
    if p < 0:
        wq, wt = q, list(t[:3])
    else:
        wq = qmul(world[p][0], q)
        rt = qrot(world[p][0], t[:3])
        wt = [world[p][1][k] + rt[k] for k in range(3)]
    world.append((wq, wt))
    print(i, p, names[i], bone_syms.get(names[i], ("", "?"))[1], [round(x, 2) for x in t[:3]], "qn=%.3f" % math.sqrt(sum(x*x for x in q)), "s", round(s[0], 2), "W", [round(x, 1) for x in wt])
print("after names", d[N + 256:N + 300].hex())
print("pre-bones 0x168", struct.unpack_from("<14H", d, 0x168), d[0x40:0x68].hex())
print("bone name symbol kinds", {bone_syms.get(n, ("none",))[0] for n in names})
rb = syms.get("ragdoll_bone_mappings", {})
print("ragdoll_bone sample", list(rb.items())[:8])

print("=== skinned vertex shader inputs")
idx = json.loads((root / "outputs/scene-v19/shader-index.json").read_text())
for name, row in idx.items():
    if row.get("type") == "vs" and "g_skinningbuffer" in row.get("cbuffers", []):
        body = (root / f"outputs/scene-v19/shaders/{name}.asm").read_text(errors="replace")
        sig = body[body.index("// Input signature"):body.index("// Output signature")] if "// Input signature" in body else ""
        print(name, row["lines"]); print(sig[:900])
        code = [l for l in body.splitlines() if not l.startswith("//") and ("cb5" in l or "ishl" in l or "utof" in l or "mul r" in l)][:16]
        print("\n".join(code))
        break

print("=== armor FAB")
sys.path[:0] = [str(root / "work/v07-mesh"), str(root / "work/v07-bxml")]
import amalur_mesh
vis = inp / "DATA_0.pak/1926576.fab_visual_data_streamable_bin"
r = amalur_mesh.parse_file(vis)
print("format", r["format_profile"] if not isinstance(r["format_profile"], dict) else json.dumps(r["format_profile"])[:500])
print("vb", json.dumps(r["vertex_buffers"][0])[:700]); print("asm", json.dumps(r["assemblies"][0])[:500]); print("limits", r["limitations"][:3])
raw = vis.read_bytes()
vb = r["vertex_buffers"][0]
at = vb.get("data_offset", vb.get("offset"))
print("vb keys", list(vb.keys()))
if at is not None:
    for i in (0, 1, 2, 700):
        print(i, raw[at + i * 60:at + (i + 1) * 60].hex())
fb = (inp / "patch_0.pak/1926576.fab_bxml").read_bytes()
print("fab head", struct.unpack_from("<24I", fb, 0))
print(fb[:96].hex())
for k, v in [(fb[i:i+4], i) for i in range(0, 0)]:
    pass
ids = [(i, struct.unpack_from("<I", fb, i)[0]) for i in range(0, len(fb) - 3, 4)]
mat = syms["material"]; tex = syms["texture"]; fabs = syms["fab"]
print("material refs", [(i, v, mat[str(v)]) for i, v in ids if str(v) in mat][:12])
print("texture refs", [(i, v, tex[str(v)]) for i, v in ids if str(v) in tex][:12])
print("fab refs", [(i, v, fabs[str(v)]) for i, v in ids if str(v) in fabs][:12])
print("bone-id hits", [(i, v) for i, v in ids if v in set(names)][:70])

print("=== real clips")
b = (root / "outputs/initial-archive-list.txt").read_bytes()
nor = sorted((v, s) for s, v in anim.items() if re.match(r"player_nor|player_idle|player_wlk|player_walk|player_run", v))
print(len(nor), nor[:110])
want = [f"{s}.anm_bxml" for v, s in nor if re.search(r"^player_nor(idle|walk|wlk|run)(fwd|_01|01|$|_fwd)|^player_(idle|walk|run)", v)][:14]
print("pick", want)
d0 = inp / "initial_0.pak"
subprocess.run([str(g / "modding/pakfileunpacker.exe"), str(g / "data/initial_0.pak"), "unpack", str(d0), *want], cwd=g / "modding", capture_output=True, timeout=200)
for n in want:
    p = d0 / n
    if p.exists():
        c = p.read_bytes()
        a, b_ = struct.unpack_from("<II", c, 0)
        print(n, anim[int(n.split('.')[0])], len(c), "fields", a, b_, c[8:12], "dur %.3f fps %.1f" % struct.unpack_from("<2f", c, 12), "u16", struct.unpack_from("<12H", c, 20), "u32", struct.unpack_from("<12I", c, 44))
print("=== tooling")
print([p.name for p in root.glob("*.cmd")], (root / "rea.cmd").read_text()[:500] if (root / "rea.cmd").exists() else "")
reqs = sorted((root / "work").glob("scene-v19*-requests/*.json"))
print(len(reqs), [p.name for p in reqs[:6]])
if reqs:
    print(reqs[-1].read_text()[:400])
EOF_MARK = None
