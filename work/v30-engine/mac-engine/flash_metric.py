#!/usr/bin/env python3
"""flash_metric.py <png>...: frame to frame change, ignoring the HUD edges. PNGs must be 8-bit RGB or RGBA, non-interlaced."""
import struct, sys, zlib


def luma(path):
    d = open(path, "rb").read()
    p, idat = 8, b""
    while p < len(d):
        n, t = struct.unpack(">I4s", d[p:p + 8])
        if t == b"IHDR":
            w, h, bits, ctype, _, _, inter = struct.unpack(">IIBBBBB", d[p + 8:p + 21])
        elif t == b"IDAT":
            idat += d[p + 8:p + 8 + n]
        p += 12 + n
    assert bits == 8 and inter == 0 and ctype in (2, 6), (bits, inter, ctype)
    c = 3 if ctype == 2 else 4
    raw, stride = zlib.decompress(idat), w * c
    prev, out, q = bytearray(stride), [], 0
    for _ in range(h):
        f, line = raw[q], bytearray(raw[q + 1:q + 1 + stride])
        q += stride + 1
        for i in range(stride):
            a = line[i - c] if i >= c else 0
            b = prev[i]
            pc = prev[i - c] if i >= c else 0
            if f == 1:
                line[i] = (line[i] + a) & 255
            elif f == 2:
                line[i] = (line[i] + b) & 255
            elif f == 3:
                line[i] = (line[i] + (a + b) // 2) & 255
            elif f == 4:
                e = a + b - pc
                pa, pb, pp = abs(e - a), abs(e - b), abs(e - pc)
                line[i] = (line[i] + (a if pa <= pb and pa <= pp else b if pb <= pp else pc)) & 255
        out.append([(299 * line[i] + 587 * line[i + 1] + 114 * line[i + 2]) // 1000 for i in range(0, stride, c)])
        prev = line
    return w, h, out


args = sys.argv[1:]
crop = None
if args[0] == "--wall":  # right side wall only: no character, HUD or minimap
    crop = True
    args = args[1:]
frames = [luma(p) for p in args]
w, h, _ = frames[0]
x0, x1, y0, y1 = w // 8, w * 7 // 8, h // 6, h * 5 // 6
if crop:
    x0, x1, y0, y1 = w * 62 // 100, w * 92 // 100, h * 40 // 100, h * 85 // 100
area = (x1 - x0) * (y1 - y0)
means, changed = [], []
for k, (_, _, f) in enumerate(frames):
    means.append(sum(sum(r[x0:x1]) for r in f[y0:y1]) / area)
    if k:
        g = frames[k - 1][2]
        changed.append(100 * sum(abs(f[y][x] - g[y][x]) > 16 for y in range(y0, y1) for x in range(x0, x1)) / area)
print("brightness", " ".join(f"{m:.1f}" for m in means))
print("pct_pixels_changed", " ".join(f"{c:.1f}" for c in changed))
print(f"mean_changed {sum(changed) / len(changed):.1f} max_changed {max(changed):.1f} brightness_range {max(means) - min(means):.1f}")
