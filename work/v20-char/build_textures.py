"""Compress every texture the zone's materials use: ASTC, full mip chains, up to 1024 px.
Writes t<index>.bin and materials.bin into the pack. Usage: build_textures.py <zone dir> <pack dir>"""
import concurrent.futures as cf, json, os, struct, subprocess, sys, tempfile, time
from pathlib import Path
from PIL import Image
root = Path.home() / "Documents/Opem Amalur"
zone, pack = Path(sys.argv[1]), Path(sys.argv[2])
os.environ["OA_TEXTURE_LIMIT"] = "1024"
source = (root / "work/v20-char/build_town.py").read_text()
argv, sys.argv = sys.argv, ["build_town.py", "1", str(zone)]
exec(source[:source.index("# Placed models")])
sys.argv = argv
ASTC = str(root / "tools/astc/bin/astcenc-avx2.exe")
BLOCK = {"d": (6, 6, 0x93B4), "n": (5, 5, 0x93B2), "s": (8, 8, 0x93B7)}
meta = json.loads((zone / "zone_materials.json").read_text())
CUTOFFS = json.loads((zone / "zone_cutoffs.json").read_text())
tex_keys, tex_index = [], {}
def key(tid, alpha, kind):
    if tid is None:
        return 0xffffffff
    k = (int(tid), int(alpha) if alpha else 0, kind)
    if k not in tex_index:
        tex_index[k] = len(tex_keys); tex_keys.append(k)
    return tex_index[k]
rows = []
for m in meta["materials"]:
    if m.get("kind") in ("river", "fall"):
        kinds = ("d", "n", "s", "n", "s", None) if m["kind"] == "river" else ("d", "d", "s", "s", "n", "n")
        rows.append((8 if m["kind"] == "river" else 16, *[key(x, None, k) if k else 0xffffffff for x, k in zip(m["t"], kinds)]))
    elif m.get("kind") == "veil":
        rows.append((32 | CUTOFFS.get(str(len(rows)), 50) << 8, key(m["d"], m.get("a"), "d"), 0xffffffff, 0xffffffff, 0xffffffff, 0xffffffff, 0xffffffff))
    elif m.get("terrain"):
        rows.append((1, key(m["d"][0], None, "d"), key(m["d"][1], None, "d"), key(m["d"][2], None, "d"), key(m["n"][0], None, "n"), key(m["n"][1], None, "n"), key(m["n"][2], None, "n")))
    else:
        # Bits 8 to 15 hold the material's alpha cutoff.
        rows.append(((2 if m.get("a") else 0) | CUTOFFS.get(str(len(rows)), 128) << 8, key(m["d"], m.get("a"), "d"), key(m.get("n"), None, "n"), key(m.get("s"), None, "s"), 0xffffffff, 0xffffffff, 0xffffffff))
print("materials", len(rows), "textures", len(tex_keys), flush=True)
done = {"ok": 0, "missing": 0, "bytes": 0}
decoded = []
for i, (tid, alpha, kind) in enumerate(tex_keys):
    best = decode_best(tid)
    if best is None:
        decoded.append(None); done["missing"] += 1; continue
    w, h, rgba = best
    px = bytearray(rgba)
    if kind == "d":
        px[3::4] = b"\xff" * (w * h)
        # Opacity is the green channel of the 256 px level: masks are gray except the flora atlas, whose red and blue hold other data.
        TEXTURE_LIMIT = 256
        mask = decode_best(alpha) if alpha else None
        TEXTURE_LIMIT = 1024
        if mask:
            mw, mh, mr = mask
            for y in range(h):
                for x in range(w):
                    px[(y * w + x) * 4 + 3] = mr[((y * mh // h) * mw + x * mw // w) * 4 + 1]
    decoded.append((w, h, bytes(px)))
print("decoded", len(decoded), "missing", done["missing"], flush=True)
def compress(i):
    if decoded[i] is None:
        return None
    w, h, px = decoded[i]; kind = tex_keys[i][2]; bx, by, fmt = BLOCK[kind]
    im = Image.frombytes("RGBA", (w, h), px); levels = []
    with tempfile.TemporaryDirectory() as d:
        while True:
            a, b = Path(d) / "i.png", Path(d) / "o.astc"
            im.save(a)
            r = subprocess.run([ASTC, "-cl", str(a), str(b), f"{bx}x{by}", "-fast", "-silent"], capture_output=True)
            if r.returncode:
                raise RuntimeError(r.stderr.decode(errors="replace")[:200])
            levels.append((im.width, im.height, b.read_bytes()[16:]))
            if im.width == 1 and im.height == 1:
                break
            im = im.resize((max(1, im.width // 2), max(1, im.height // 2)), Image.BOX)
    out = b"OATX" + struct.pack("<IIII", fmt, w, h, len(levels))
    for lw, lh, data in levels:
        out += struct.pack("<I", len(data)) + data
    (pack / f"t{i}.bin").write_bytes(out)
    return len(out)
T = time.time()
with cf.ThreadPoolExecutor(12) as pool:
    for n, size in enumerate(pool.map(compress, range(len(tex_keys)))):
        if size:
            done["ok"] += 1; done["bytes"] += size
        if n % 50 == 0:
            print(n, round(time.time() - T), flush=True)
missing = {i for i, x in enumerate(decoded) if x is None}
fix = lambda t: 0xffffffff if t in missing else t
data = struct.pack("<I", len(rows))
for r in rows:
    data += struct.pack("<7I", r[0], *[fix(t) for t in r[1:]])
(pack / "materials.bin").write_bytes(data)
# Parameters of water materials, 11 floats for each material.
extra = struct.pack("<I", len(rows))
for m in meta["materials"]:
    extra += struct.pack("<11f", *((list(m.get("p") or []) + [0.0] * 11)[:11]))
(pack / "water.bin").write_bytes(extra)
print(done, "seconds", round(time.time() - T), flush=True)
