"""Check baked clips and report world-space joints. Usage: check_bake.py baked.bin ..."""
import math, struct, sys
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
d = (root / "work/v20-inputs/patch_0.pak/456813.fab_bxml").read_bytes()
parents = struct.unpack_from("<64H", d, 0xd84)
NAMES = {2: "pelvis", 4: "L_calf", 5: "L_foot", 21: "head", 25: "L_hand", 44: "R_hand", 11: "R_foot"}


def qmul(a, b):
    x1, y1, z1, w1 = a; x2, y2, z2, w2 = b
    return (w1*x2+x1*w2+y1*z2-z1*y2, w1*y2-x1*z2+y1*w2+z1*x2, w1*z2+x1*y2-y1*x2+z1*w2, w1*w2-x1*x2-y1*y2-z1*z2)


def qrot(q, v):
    x, y, z, w = q
    tx, ty, tz = 2*(y*v[2]-z*v[1]), 2*(z*v[0]-x*v[2]), 2*(x*v[1]-y*v[0])
    return (v[0]+w*tx+y*tz-z*ty, v[1]+w*ty+z*tx-x*tz, v[2]+w*tz+x*ty-y*tx)


def world(rows):
    out = []
    for i, row in enumerate(rows):
        q, t = row[:4], row[4:7]
        p = parents[i]
        if p == 0xffff:
            out.append((q, t))
        else:
            r = qrot(out[p][0], t)
            out.append((qmul(out[p][0], q), tuple(out[p][1][k] + r[k] for k in range(3))))
    return out


bind = [struct.unpack_from("<12f", d, 0x184 + i * 48) for i in range(64)]
print("bind", {n: [round(x, 1) for x in world(bind)[i][1]] for i, n in NAMES.items()})
for path in sys.argv[1:]:
    b = Path(path).read_bytes()
    j, f, fps = struct.unpack_from("<IIf", b)
    norms = []
    for fr in sorted({0, f // 2, f - 1}):
        rows = [struct.unpack_from("<12f", b, 12 + (fr * j + i) * 48) for i in range(j)]
        n = [math.sqrt(sum(x * x for x in r[:4])) for r in rows]
        norms.append((min(n), max(n)))
        print(Path(path).stem, "frame", fr, {k: [round(x, 1) for x in world(rows)[i][1]] for i, k in NAMES.items()})
    print("  joints", j, "frames", f, "fps", round(fps, 2), "quat norm range", [(round(a, 4), round(c, 4)) for a, c in norms])
