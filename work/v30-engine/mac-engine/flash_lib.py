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


