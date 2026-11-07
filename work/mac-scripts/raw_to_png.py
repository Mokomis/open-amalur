"""Write an 8-bit staging dump as PNG. Usage: raw_to_png.py <base without extension> <output.png> [step]"""
import json, struct, sys, zlib

base, output = sys.argv[1], sys.argv[2]
step = int(sys.argv[3]) if len(sys.argv) > 3 else 1
meta = json.load(open(base + ".json"))
data = open(base + ".raw", "rb").read()
w, h, pitch, fmt = meta["w"], meta["h"], meta["pitch"], meta["fmt"]
bgra = fmt in (87, 91)
if fmt not in (28, 29, 87, 91):
    raise SystemExit("unsupported format %d" % fmt)
rows = bytearray()
for y in range(0, h, step):
    rows.append(0)
    row = data[y * pitch:y * pitch + w * 4]
    for x in range(0, w, step):
        p = row[x * 4:x * 4 + 3]
        rows += bytes((p[2], p[1], p[0])) if bgra else p


def chunk(tag, body):
    return struct.pack(">I", len(body)) + tag + body + struct.pack(">I", zlib.crc32(tag + body))


size = struct.pack(">IIBBBBB", (w + step - 1) // step, (h + step - 1) // step, 8, 2, 0, 0, 0)
with open(output, "wb") as f:
    f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", size) + chunk(b"IDAT", zlib.compress(bytes(rows), 6)) + chunk(b"IEND", b""))
print(w, h, "fmt", fmt)
