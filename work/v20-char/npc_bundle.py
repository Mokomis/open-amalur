"""Read each townsperson's bundle and name its fabs, materials and animations."""
import collections, json, struct, subprocess, sys
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
g = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning")
inp = root / "work/v20-inputs"
syms = json.loads((inp / "symbols.json").read_text())
sys.path[:0] = [str(root / "work/v07-mesh"), str(root / "work/v07-bxml")]
import amalur_mesh
listing = {}
for arch, n in (("DATA_0.pak", "DATA"), ("initial_0.pak", "initial"), ("patch_0.pak", "patch")):
    b = (root / f"outputs/{n}-archive-list.txt").read_bytes()
    listing[arch] = set(x.strip() for x in b.decode("utf-16" if b[:2] == b"\xff\xfe" else "utf-8-sig").splitlines() if x.strip())
def extract(names):
    found = {}
    for arch in ("DATA_0.pak", "initial_0.pak", "patch_0.pak"):
        sel = [n for n in names if n in listing[arch]]
        d = inp / arch
        for start in range(0, len(sel), 60):
            todo = [n for n in sel[start:start + 60] if not (d / n).exists()]
            if todo:
                subprocess.run([str(g / "modding/pakfileunpacker.exe"), str(g / "data" / arch), "unpack", str(d), *todo], cwd=g / "modding", capture_output=True, timeout=280)
        for n in sel:
            if (d / n).exists():
                found.setdefault(n, []).append(d / n)
    return found
people = {"aewinrathgar": 1277575, "hercadwold": 1263596, "eluvia": 1778518, "citizen_m1": 1407601, "citizen_f3": 1407602, "gizela": 639755, "zelda": 1936521, "var_m": 1784021}
for name, sid in people.items():
    fs = extract([f"{sid}.bundle", f"{sid}.simtype_visual_data_bundle"])
    print("==", name, sid, syms["simtype"].get(str(sid)), {k: [p.parent.name for p in v] for k, v in fs.items()})
    ids = collections.OrderedDict()
    for k, ps in fs.items():
        for p in ps:
            d = p.read_bytes()
            print("  ", k, p.parent.name, len(d), struct.unpack_from("<8I", d, 0) if len(d) >= 32 else d.hex())
            for i in range(0, len(d) - 3, 4):
                ids[struct.unpack_from("<I", d, i)[0]] = 1
    named = collections.defaultdict(list)
    for v in ids:
        for t in ("fab", "material", "motionset", "animation", "motiontree", "texture", "simtype", "ragdoll"):
            if str(v) in syms[t]:
                named[t].append((v, syms[t][str(v)]))
    for t in ("fab", "motiontree", "ragdoll", "motionset"):
        print("  ", t, len(named[t]), named[t][:14])
    print("   simtypes", named["simtype"][:12], "materials", len(named["material"]), "textures", len(named["texture"]), "animations", len(named["animation"]))
    for fid, fname in named["fab"][:10]:
        v = extract([f"{fid}.fab_visual_data_streamable_bin"]).get(f"{fid}.fab_visual_data_streamable_bin")
        if v and v[0].stat().st_size > 50:
            try:
                m = amalur_mesh.parse_file(v[0])
                print("     ", fname, m["summary"]["vertices"], "verts strides", m["summary"]["strides"], "z", round(m["summary"]["bounds"]["minimum"][2]), round(m["summary"]["bounds"]["maximum"][2]))
            except Exception as e:
                print("     ", fname, "parse", str(e)[:70])
