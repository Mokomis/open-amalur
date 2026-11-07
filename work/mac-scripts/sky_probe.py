"""Read Gorhart's sky asset and everything it references."""
import json, re, struct, subprocess, sys, collections
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
sys.path[:0] = [str(root / "work/v07-mesh"), str(root / "work/v07-bxml")]
import amalur_mesh
g = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning")
inp = root / "work/v20-inputs"
syms = json.loads((inp / "symbols.json").read_text())
have = {}
kinds = collections.defaultdict(set)
for arch, n in (("DATA_0.pak", "DATA"), ("initial_0.pak", "initial"), ("patch_0.pak", "patch")):
    b = (root / f"outputs/{n}-archive-list.txt").read_bytes()
    have[arch] = set(x.strip() for x in b.decode("utf-16" if b[:2] == b"\xff\xfe" else "utf-8-sig").splitlines() if x.strip())
    for x in have[arch]:
        m = re.match(r"(\d+)(?:_\d+)?\.(\w+)$", x)
        if m:
            kinds[int(m.group(1))].add(m.group(2))
def extract(names):
    found = {}
    for arch in ("DATA_0.pak", "initial_0.pak", "patch_0.pak"):
        sel = [n for n in names if n in have[arch]]
        d = inp / arch
        d.mkdir(parents=True, exist_ok=True)
        todo = [n for n in sel if not (d / n).exists()]
        if todo:
            subprocess.run([str(g / "modding/pakfileunpacker.exe"), str(g / "data" / arch), "unpack", str(d), *todo], cwd=g / "modding", capture_output=True, timeout=200)
        for n in sel:
            if (d / n).exists():
                found[n] = d / n
    return found
r = extract(["431608.region_bxml"])["431608.region_bxml"].read_bytes()
print("region sky word", struct.unpack_from("<I", r, 8 + 8)[0], syms["sky"].get(str(struct.unpack_from("<I", r, 8 + 8)[0])))
sid = struct.unpack_from("<I", r, 8 + 8)[0]
f = extract([f"{sid}.sky_bxml", f"{sid}.bundle"])
print(list(f))
d = f[f"{sid}.sky_bxml"].read_bytes()
print("bytes", len(d), "head", struct.unpack_from("<16I", d, 0))
print("floats", [round(x, 3) for x in struct.unpack_from("<40f", d, 8)])
def name(v):
    for t in ("fab", "material", "texture", "shader", "simtype", "cluster"):
        if str(v) in syms[t]:
            return t, syms[t][str(v)]
    return None
refs = []
for i in range(0, len(d) - 3, 4):
    v = struct.unpack_from("<I", d, i)[0]
    n = name(v)
    if n or (v > 2000 and kinds.get(v)):
        refs.append((i, v, n, sorted(kinds.get(v, []))))
print("refs", refs)
if f"{sid}.bundle" in f:
    b = f[f"{sid}.bundle"].read_bytes()
    ids = set(struct.unpack_from(f"<{len(b) // 4}I", b, 0))
    print("bundle", [(v, name(v), sorted(kinds.get(v, []))) for v in ids if name(v) or kinds.get(v)][:40])
fabs = [v for _, v, n, k in refs if "fab_bxml" in k or "fab_visual_data_streamable_bin" in k]
for fid in fabs:
    vf = extract([f"{fid}.fab_visual_data_streamable_bin"]).get(f"{fid}.fab_visual_data_streamable_bin")
    if vf:
        m = amalur_mesh.parse_file(vf)
        print("fab", fid, syms["fab"].get(str(fid)), m["summary"]["vertices"], m["summary"]["strides"], m["summary"]["bounds"], [a["unknown_u16_at2"] for a in m["assemblies"]])
for mname in ("odv_skybase", "odv_skylayer"):
    print(mname, [(k, v) for k, v in syms["texture"].items() if v.startswith(mname)], [(k, v) for k, v in syms["material"].items() if "sky" in v.lower()][:12])
# Size and alpha of sky textures
tid = next(k for k, v in syms["texture"].items() if v == "odv_skybase_d")
print("skybase files", sorted(x for a in have.values() for x in a if x.startswith(f"{tid}_") or x.startswith(f"{tid}.")))
