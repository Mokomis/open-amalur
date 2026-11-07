import struct, itertools
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
d = (root / "work/v20-inputs/patch_0.pak/456813.fab_bxml").read_bytes()
par = struct.unpack_from("<64H", d, 0xd84)
rows = [struct.unpack_from("<12f", d, 0x184 + i * 48) for i in range(64)]
print("first 6 rows"); [print(i, par[i], [round(x, 3) for x in rows[i][:7]]) for i in range(6)]
def qmul(a, b):
    x1, y1, z1, w1 = a; x2, y2, z2, w2 = b
    return (w1*x2+x1*w2+y1*z2-z1*y2, w1*y2-x1*z2+y1*w2+z1*x2, w1*z2+x1*y2-y1*x2+z1*w2, w1*w2-x1*x2-y1*y2-z1*z2)
def conj(q): return (-q[0], -q[1], -q[2], q[3])
def rot(q, v):
    r = qmul(qmul(q, (v[0], v[1], v[2], 0.0)), conj(q))
    return r[:3]
J = {"pelvis": 2, "Lcalf": 4, "Lfoot": 5, "Ltoe": 6, "head": 21, "Lhand": 25, "Rhand": 44}
def solve(order, cj, parent_first):
    out = []
    for i, r in enumerate(rows):
        q = tuple(r[k] for k in order); t = r[4:7]
        if cj: q = conj(q)
        if par[i] == 0xffff: out.append((q, t)); continue
        pq, pt = out[par[i]]
        wq = qmul(pq, q) if parent_first else qmul(q, pq)
        v = rot(pq, t)
        out.append((wq, tuple(pt[k] + v[k] for k in range(3))))
    return out
for order, name in (((0,1,2,3), "xyzw"), ((1,2,3,0), "wxyz")):
    for cj in (False, True):
        for pf in (True, False):
            w = solve(order, cj, pf)
            print(name, "conj" if cj else "plain", "parent*local" if pf else "local*parent", {k: [round(x) for x in w[i][1]] for k, i in J.items()})
