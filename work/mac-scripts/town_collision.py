"""Read Gorhart's collision set with the shop's layout; test whether it covers the ground; plot a height map."""
import math, struct, zlib
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
b = (root / "work/v20-inputs/patch_0.pak/485422.collision_set_bin").read_bytes()
DOOR = (1575.1, -62759.2, 5152.1)
gp, gc = struct.unpack_from("<II", b, 16)
print("bytes", len(b), "groups", gc, "at", gp)
tris = 0; verts = 0; meshes = 0; bad = 0
all_tris = []
for i in range(gc):
    u0, u1, mp, mc = struct.unpack_from("<4I", b, gp + i * 16)
    for j in range(mc):
        tag, vp, vc, tp, tc = struct.unpack_from("<5I", b, mp + j * 20)
        if vp + vc * 12 > len(b) or tp + tc * 16 > len(b):
            bad += 1; continue
        meshes += 1; verts += vc; tris += tc
        V = struct.unpack_from(f"<{vc * 3}f", b, vp)
        for k in range(tc):
            a, bb, c, flag = struct.unpack_from("<4I", b, tp + k * 16)
            if a < vc and bb < vc and c < vc:
                all_tris.append(tuple(V[n * 3 + e] * 100 for n in (a, bb, c) for e in range(3)))
print("meshes", meshes, "bad", bad, "verts", verts, "tris", tris, "kept", len(all_tris))
xs = [t[0] for t in all_tris]; ys = [t[1] for t in all_tris]; zs = [t[2] for t in all_tris]
print("extent x", round(min(xs)), round(max(xs)), "y", round(min(ys)), round(max(ys)), "z", round(min(zs)), round(max(zs)))
R = 6000
near = [t for t in all_tris if abs(t[0] - DOOR[0]) < R and abs(t[1] - DOOR[1]) < R]
print("tris within 60 m box", len(near))
# Height map by rasterising triangles from above, 512 pixels over the box.
N = 512
height = [[None] * N for _ in range(N)]
for t in near:
    ax, ay, az, bx, by, bz, cx, cy, cz = t
    det = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
    if abs(det) < 1e-6:
        continue
    lo = lambda v, o: int((min(v) - o + R) * N / (2 * R))
    x0 = max(0, lo((ax, bx, cx), DOOR[0])); x1 = min(N - 1, int((max(ax, bx, cx) - DOOR[0] + R) * N / (2 * R)) + 1)
    y0 = max(0, lo((ay, by, cy), DOOR[1])); y1 = min(N - 1, int((max(ay, by, cy) - DOOR[1] + R) * N / (2 * R)) + 1)
    for y in range(y0, y1 + 1):
        wy = DOOR[1] - R + y * 2 * R / N
        for x in range(x0, x1 + 1):
            wx = DOOR[0] - R + x * 2 * R / N
            l1 = ((by - cy) * (wx - cx) + (cx - bx) * (wy - cy)) / det
            l2 = ((cy - ay) * (wx - cx) + (ax - cx) * (wy - cy)) / det
            l3 = 1 - l1 - l2
            if l1 >= 0 and l2 >= 0 and l3 >= 0:
                z = l1 * az + l2 * bz + l3 * cz
                if height[y][x] is None or z > height[y][x]:
                    height[y][x] = z
cover = sum(v is not None for r in height for v in r) / N / N
vals = sorted(v for r in height for v in r if v is not None)
print("coverage", round(cover, 3), "z p5/p50/p95", [round(vals[int(len(vals) * q)]) for q in (.05, .5, .95)] if vals else None)
print("door column", height[N // 2][N // 2], "ring", [height[N // 2 + d][N // 2] for d in (-40, -20, 20, 40)])
lo, hi = vals[int(len(vals) * .02)], vals[int(len(vals) * .98)]
rows = bytearray()
for y in range(N - 1, -1, -1):
    rows.append(0)
    for x in range(N):
        v = height[y][x]
        if abs(x - N // 2) < 3 and abs(y - N // 2) < 3:
            rows += bytes((255, 40, 40))
        elif v is None:
            rows += bytes((20, 20, 60))
        else:
            g = max(0, min(255, int((v - lo) / (hi - lo + 1e-3) * 255)))
            rows += bytes((g, g, g))
chunk = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d))
(root / "work/v20-char/town-height.png").write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", N, N, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(bytes(rows))) + chunk(b"IEND", b""))
