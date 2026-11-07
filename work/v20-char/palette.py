"""Map vertex bone indices to joints by geometry, and dump FAB part structure and material links."""
import collections, json, math, struct
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
inp = root / "work/v20-inputs"
syms = json.loads((inp / "symbols.json").read_text())
bn = syms["ragdoll_bone_mappings"]; mats = syms["material"]; texs = syms["texture"]
def qmul(a, b):
    x1, y1, z1, w1 = a; x2, y2, z2, w2 = b
    return (w1*x2+x1*w2+y1*z2-z1*y2, w1*y2-x1*z2+y1*w2+z1*x2, w1*z2+x1*y2-y1*x2+z1*w2, w1*w2-x1*x2-y1*y2-z1*z2)
def conj(q): return (-q[0], -q[1], -q[2], q[3])
def rot(q, v): return qmul(qmul(q, (*v, 0.0)), conj(q))[:3]
def skel(fb):
    n = struct.unpack_from("<H", fb, 4 + 0x10)[0]
    basep = 4 + 0x18 + struct.unpack_from("<i", fb, 4 + 0x18)[0]
    table = struct.unpack_from("<I", fb, 4 + 0x1c)[0]
    P = 4 + 0x1c + table
    par = struct.unpack_from(f"<{n}H", fb, P)
    N = 4 + 0x20 + struct.unpack_from("<I", fb, 4 + 0x20)[0]
    names = struct.unpack_from(f"<{n}I", fb, N)
    w = []
    for i in range(n):
        r = struct.unpack_from("<12f", fb, basep + i * 48)
        q = conj(r[:4]); t = r[4:7]
        if par[i] == 0xffff: w.append((q, t))
        else:
            pq, pt = w[par[i]]; v = rot(pq, t)
            w.append((qmul(pq, q), tuple(pt[k] + v[k] for k in range(3))))
    return n, par, names, w, N
for fid in (1926576, 1926575, 1926574, 1923507, 1686788):
    fb = (inp / f"patch_0.pak/{fid}.fab_bxml").read_bytes()
    vis = (inp / f"DATA_0.pak/{fid}.fab_visual_data_streamable_bin").read_bytes()
    n, par, names, w, N = skel(fb)
    print("=====", fid, syms["fab"].get(str(fid)), "fab bytes", len(fb), "tag", fb[4:8], "joints", n, "names", [bn.get(str(x), x) for x in names][:9])
    stride = struct.unpack_from("<I", vis, 12)[0]; count = struct.unpack_from("<I", vis, 20)[0]
    print(" head u32", struct.unpack_from("<10I", vis, 0), "stride", stride)
    if stride < 40 or count == 0: continue
    data = 24
    sums = collections.defaultdict(lambda: [0.0, 0.0, 0.0, 0.0])
    for i in range(count):
        v = vis[data + i * stride:data + (i + 1) * stride]
        p = struct.unpack_from("<3f", v); idx = v[12:16]
        wt = struct.unpack_from("<4H", v, 16)
        k = idx[max(range(4), key=lambda a: wt[a])]
        s = sums[k]
        for c in range(3): s[c] += p[c]
        s[3] += 1
    rows = []
    for k in sorted(sums):
        s = sums[k]; c = [s[i] / s[3] for i in range(3)]
        best = sorted(range(n), key=lambda j: sum((w[j][1][a] - c[a]) ** 2 for a in range(3)))[:3]
        rows.append((k, int(s[3]), [round(x) for x in c], [(str(bn.get(str(names[j]), j))[:14], round(math.dist(w[j][1], c))) for j in best],
                     "same-index:" + (str(bn.get(str(names[k]), "?")) if k < n else "OOR")))
    for r in rows[:24]: print(" ", r)
    payload_end = struct.unpack_from("<I", fb, 0)[0] + 8
    tail = fb[payload_end:]
    print(" after-skel bytes", len(tail), "first u32", struct.unpack_from("<16I", tail, 0))
    ids = [(i, struct.unpack_from("<I", fb, i)[0]) for i in range(payload_end, len(fb) - 3, 4)]
    print(" mats", [(i, mats[str(v)]) for i, v in ids if str(v) in mats], "tex", [(i, texs[str(v)]) for i, v in ids if str(v) in texs][:6])
    # u16/byte runs that look like palettes
    last = (N + n * 4)
    print(" bytes after names", fb[last:last + 60].hex())
