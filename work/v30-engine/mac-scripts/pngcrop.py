"""Crop a PNG to the top-left region. Usage: pngcrop.py in.png out.png width height [maxwidth]"""
import struct, sys, zlib
d = open(sys.argv[1], "rb").read()
at, idat, w, h, bpp = 8, b"", 0, 0, 0
while at < len(d):
    n, t = struct.unpack(">I4s", d[at:at + 8]); body = d[at + 8:at + 8 + n]; at += 12 + n
    if t == b"IHDR":
        w, h, depth, ctype = struct.unpack(">IIBB", body[:10]); bpp = {2: 3, 6: 4}[ctype]; assert depth == 8
    elif t == b"IDAT":
        idat += body
raw = zlib.decompress(idat); stride = w * bpp
cw, ch = int(sys.argv[3]), int(sys.argv[4])
step = max(1, cw // int(sys.argv[5])) if len(sys.argv) > 5 else 1
prev = bytearray(stride); rows = []
for y in range(min(ch, h)):
    f = raw[y * (stride + 1)]; line = bytearray(raw[y * (stride + 1) + 1:(y + 1) * (stride + 1)])
    for i in range(stride):
        a = line[i - bpp] if i >= bpp else 0; b = prev[i]; c = prev[i - bpp] if i >= bpp else 0
        if f == 1: line[i] = (line[i] + a) & 255
        elif f == 2: line[i] = (line[i] + b) & 255
        elif f == 3: line[i] = (line[i] + (a + b) // 2) & 255
        elif f == 4:
            p = a + b - c; pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
            line[i] = (line[i] + (a if pa <= pb and pa <= pc else b if pb <= pc else c)) & 255
    prev = line
    if y % step == 0:
        rows.append(b"\0" + b"".join(bytes(line[x * bpp:x * bpp + 3]) for x in range(0, cw, step)))
chunk = lambda t, b: struct.pack(">I", len(b)) + t + b + struct.pack(">I", zlib.crc32(t + b))
oh = len(rows); ow = (cw + step - 1) // step
open(sys.argv[2], "wb").write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", ow, oh, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(b"".join(rows), 6)) + chunk(b"IEND", b""))
