import json, struct, sys, importlib.util
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
inp = root / "work/v20-inputs"
syms = json.loads((inp / "symbols.json").read_text()); bn = syms["ragdoll_bone_mappings"]
src = (root / "work/v20-char/build_character.py").read_text()
ns = {}
g = dict(struct=struct)
exec(src[src.index("def qmul"):src.index("def extract")], g)
conj, rot = g["conj"], g["rot"]
exec(src[src.index("def skeleton"):src.index("# Skeleton and clips")], g)
skeleton, palette = g["skeleton"], g["palette"]
for fid, arch in ((301406, None), (1930173, None)):
    fbp = next((inp / a / f"{fid}.fab_bxml" for a in ("patch_0.pak", "initial_0.pak", "DATA_0.pak") if (inp / a / f"{fid}.fab_bxml").exists()))
    fb = fbp.read_bytes()
    n, par, names, world = skeleton(fb)
    pal = palette(fb, n)
    print(fid, fbp.parent.name, "joints", n, [str(bn.get(str(x), x))[:14] for x in names][:14])
    for idx, t, q in pal[:6]:
        wq, wt = world[idx]
        print("  pal", idx, str(bn.get(str(names[idx]), names[idx]))[:16], "stored t", [round(x, 1) for x in t], "q", [round(x, 3) for x in q], "world", [round(x, 1) for x in wt], "calc inv t", [round(x, 1) for x in (-v for v in rot(conj(wq), wt))])
    print("  q check", [(round(sum(a*b for a,b in zip(conj(world[i][0]),q)),4), round(sum(a*b for a,b in zip(world[i][0],q)),4)) for i,_,q in pal][:6])
    print("  pal count", len(pal))
    vp = next((inp / a / f"{fid}.fab_visual_data_streamable_bin" for a in ("DATA_0.pak", "initial_0.pak", "patch_0.pak") if (inp / a / f"{fid}.fab_visual_data_streamable_bin").exists()))
    v = vp.read_bytes(); c = struct.unpack_from("<I", v, 20)[0]
    used = {}
    zr = []
    for i in range(c):
        a = 24 + i * 60; b = v[a + 12:a + 16]; w = struct.unpack_from("<4H", v, a + 16)
        for k in range(4):
            if w[k]: used[b[k]] = used.get(b[k], 0) + 1
        zr.append(struct.unpack_from("<3f", v, a))
    print("  verts", c, "indices used", sorted(used.items()), "x", round(min(p[0] for p in zr)), round(max(p[0] for p in zr)), "y", round(min(p[1] for p in zr)), round(max(p[1] for p in zr)), "z", round(min(p[2] for p in zr)), round(max(p[2] for p in zr)))
