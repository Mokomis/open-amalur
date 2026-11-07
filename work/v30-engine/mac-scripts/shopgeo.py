import struct
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
d = (root / "outputs/scene-v17/collision.bin").read_bytes()
n = struct.unpack_from("<I", d, 8)[0]
print("verts", n, "bounds", [round(x) for x in struct.unpack_from("<6f", d, 12)])
E = (-342.4, -139.6, 0.0)
H = (-350, 380, 0)
import collections
for name, c in (("entrance", E), ("hint", H)):
    zs = collections.Counter()
    for i in range(0, n, 3):
        v = [struct.unpack_from("<3f", d, 36 + (i + k) * 36) for k in range(3)]
        # upward-facing triangles near point
        cx = sum(p[0] for p in v) / 3; cy = sum(p[1] for p in v) / 3
        if abs(cx - c[0]) < 200 and abs(cy - c[1]) < 200:
            ux, uy, uz = v[1][0] - v[0][0], v[1][1] - v[0][1], v[1][2] - v[0][2]
            wx, wy, wz = v[2][0] - v[0][0], v[2][1] - v[0][1], v[2][2] - v[0][2]
            nz = ux * wy - uy * wx
            ln = ((uy * wz - uz * wy) ** 2 + (uz * wx - ux * wz) ** 2 + nz ** 2) ** .5 or 1
            if abs(nz / ln) > .8:
                zs[round(sum(p[2] for p in v) / 3 / 25) * 25] += 1
    print(name, c, sorted(zs.items()))
s = (root / "outputs/scene-v17/scene.bin").read_bytes()
print("scene bounds", [round(x) for x in struct.unpack_from("<6f", s, 12)])
