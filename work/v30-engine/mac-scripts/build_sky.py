"""Build work/v20-town/town_sky.bin from sky asset 325844: Noon gradient and two cloud layers."""
import json, struct, subprocess, sys
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
sys.path[:0] = [str(root / "work/v09-textures")]
import keen_texture
g = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning")
inp = root / "work/v20-inputs"
LIMIT = 512
d = next(p for p in (inp / "patch_0.pak/325844.sky_bxml", inp / "initial_0.pak/325844.sky_bxml") if p.exists()).read_bytes()
at, keys = 0, []
for key in range(4):
    count = struct.unpack_from("<I", d, at)[0]
    at += 8
    colors, stops = [], [0.0]
    for i in range(count):
        c = struct.unpack_from("<I", d, at)[0]; at += 4
        colors.append(((c >> 16) & 255, (c >> 8) & 255, c & 255, c >> 24))
        if i + 1 < count:
            stops.append(struct.unpack_from("<f", d, at)[0]); at += 4
    keys.append((colors, stops))
print("keys", [(len(c), [round(s, 3) for s in st]) for c, st in keys], "end", at)
assert at == 272
tints = struct.unpack_from("<32f", d, 272)
lower_ids = struct.unpack_from("<4I", d, 464)
upper_ids = struct.unpack_from("<4I", d, 480)
NOON = 2
colors, stops = keys[NOON]
gradient = bytearray()
for i in range(256):
    t = i / 255.0
    if t <= stops[0]:
        c = colors[0]
    elif t >= stops[-1]:
        c = colors[-1]
    else:
        k = next(j for j in range(len(stops) - 1) if stops[j] <= t <= stops[j + 1])
        a = (t - stops[k]) / max(stops[k + 1] - stops[k], 1e-5)
        c = tuple(round(colors[k][e] + (colors[k + 1][e] - colors[k][e]) * a) for e in range(4))
    gradient += bytes(c)


def texture(tid):
    best = None
    for k in range(5):
        name = f"{tid}_{k}.dds"
        p = None
        for pak in ("patch_0.pak", "initial_0.pak", "DATA_0.pak"):
            q = inp / pak / name
            if not q.exists() and (g / "data" / pak).exists():
                q.parent.mkdir(parents=True, exist_ok=True)
                subprocess.run([str(g / "modding/pakfileunpacker.exe"), str(g / "data" / pak), "unpack", str(inp / pak), name], cwd=g / "modding", capture_output=True, timeout=60)
            if q.exists():
                p = q
                break
        if p is None:
            continue
        data = p.read_bytes()
        w, h, fmt, mips = *struct.unpack_from("<HH", data, 20), data[29], struct.unpack_from("<H", data, 35)[0]
        o, block = 38, 8 if fmt == 1 else 16
        for _ in range(mips):
            size = ((w + 3) // 4) * ((h + 3) // 4) * block
            if max(w, h) <= LIMIT and o + size <= len(data):
                if best is None or w > best[0]:
                    best = (w, h, bytes(keen_texture.decode_blocks(data[o:o + size], w, h, fmt)))
                break
            o += size
            w, h = max(1, w // 2), max(1, h // 2)
    if best is None:
        raise SystemExit(f"sky texture {tid} unavailable")
    n = best[0] * best[1]
    print(tid, best[:2], "mean rgba", [round(sum(best[2][c::4]) / n) for c in range(4)])
    return best


lower, upper = texture(lower_ids[NOON]), texture(upper_ids[NOON])
blob = bytearray(b"OASKY001") + bytes(gradient) + struct.pack("<8f", *tints[NOON * 4:NOON * 4 + 4], *tints[16 + NOON * 4:16 + NOON * 4 + 4])
for w, h, rgba in (lower, upper):
    blob += struct.pack("<II", w, h) + rgba
(root / "work/v20-town/town_sky.bin").write_bytes(blob)
print("gradient samples", [tuple(gradient[i * 4:i * 4 + 4]) for i in (0, 64, 100, 128, 160, 200, 255)], "tints", [round(x, 2) for x in tints[8:12]], [round(x, 2) for x in tints[24:28]], "bytes", len(blob))
