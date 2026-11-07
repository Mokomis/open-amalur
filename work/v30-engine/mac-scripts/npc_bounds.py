"""Read the people pack the way the runtime does and report each part's skinned size at the first frame."""
import math, struct
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
d = (root / "work/v20-town/town_npcs.bin").read_bytes()
def qmul(a, b):
    x1, y1, z1, w1 = a; x2, y2, z2, w2 = b
    return (w1*x2+x1*w2+y1*z2-z1*y2, w1*y2-x1*z2+y1*w2+z1*x2, w1*z2+x1*y2-y1*x2+z1*w2, w1*w2-x1*x2-y1*y2-z1*z2)
def conj(q): return (-q[0], -q[1], -q[2], q[3])
def rot(q, v): return qmul(qmul(q, (v[0], v[1], v[2], 0.0)), conj(q))[:3]
count = struct.unpack_from("<I", d, 8)[0]
at = 12
for n in range(count):
    px, py, pz, yaw, size = struct.unpack_from("<4fI", d, at); at += 20
    c = d[at:at + size]; at += size
    J, C, P, T = struct.unpack_from("<4I", c, 8)
    par = struct.unpack_from(f"<{J}h", c, 24)
    o = 24 + J * 2
    frames, fps = struct.unpack_from("<If", c, o); o += 8
    world = []
    for i in range(J):
        v = struct.unpack_from("<7f", c, o + i * 28)
        if par[i] < 0:
            world.append((v[:4], v[4:7]))
        else:
            pq, pt = world[par[i]]; r = rot(pq, v[4:7])
            world.append((qmul(pq, v[:4]), tuple(pt[k] + r[k] for k in range(3))))
    o += frames * J * 28
    for t in range(T):
        w, h = struct.unpack_from("<II", c, o); o += 8 + w * h * 4
    print("person", n, "yaw", round(yaw, 2), "parts", P)
    for p in range(P):
        vc, ic, pc, tex = struct.unpack_from("<IIIi", c, o); o += 16
        pal = [struct.unpack_from("<I7f", c, o + i * 32) for i in range(pc)]; o += pc * 32
        lo = [1e9] * 3; hi = [-1e9] * 3; blo = [1e9] * 3; bhi = [-1e9] * 3; sums = []
        skins = []
        for e in pal:
            wq, wt = world[e[0]]
            r = rot(wq, e[5:8])
            skins.append((qmul(wq, e[1:5]), tuple(wt[k] + r[k] for k in range(3))))
        for i in range(vc):
            v = struct.unpack_from("<8f4B4f", c, o + i * 52)
            out = [0.0] * 3
            s = sum(v[12:16])
            sums.append(s)
            for b, wgt in zip(v[8:12], v[12:16]):
                if b < pc and wgt:
                    q, t2 = skins[b]; r = rot(q, v[:3])
                    for k in range(3):
                        out[k] += wgt * (r[k] + t2[k])
            for k in range(3):
                lo[k] = min(lo[k], out[k]); hi[k] = max(hi[k], out[k]); blo[k] = min(blo[k], v[k]); bhi[k] = max(bhi[k], v[k])
        o += vc * 52
        idx = struct.unpack_from(f"<{ic}I", c, o); o += ic * 4
        big = max(hi[k] - lo[k] for k in range(2))
        flag = "  <<<<" if big > 130 or min(sums) < .9 or max(sums) > 1.1 else ""
        print("  part", p, "verts", vc, "pal", pc, "skinned", [round(x) for x in lo], [round(x) for x in hi], "bind", [round(x) for x in blo], [round(x) for x in bhi], "weightsum", round(min(sums), 2), round(max(sums), 2), "idxmax", max(idx), flag)
    if n >= 1:
        break
