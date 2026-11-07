"""Link Gorhart's space to terrain, and measure the placements around the shop door."""
import collections, json, math, struct, subprocess, sys
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
sys.path[:0] = [str(root / "work/v07-bxml"), str(root / "work/v07-mesh")]
g = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning")
inp = root / "work/v20-inputs"
syms = json.loads((inp / "symbols.json").read_text())
SPACE, DOOR = 431638, (1575.1, -62759.2, 5152.1)
listing = {}
for arch, n in (("DATA_0.pak", "DATA"), ("initial_0.pak", "initial"), ("patch_0.pak", "patch")):
    b = (root / f"outputs/{n}-archive-list.txt").read_bytes()
    listing[arch] = [x.strip() for x in b.decode("utf-16" if b[:2] == b"\xff\xfe" else "utf-8-sig").splitlines() if x.strip()]


def extract(names):
    out = {}
    for arch, have in listing.items():
        hs = set(have)
        sel = [n for n in names if n in hs]
        d = inp / arch
        d.mkdir(parents=True, exist_ok=True)
        for start in range(0, len(sel), 40):
            todo = [n for n in sel[start:start + 40] if not (d / n).exists()]
            if todo:
                subprocess.run([str(g / "modding/pakfileunpacker.exe"), str(g / "data" / arch), "unpack", str(d), *todo], cwd=g / "modding", capture_output=True, timeout=280)
        for n in sel:
            if (d / n).exists():
                out.setdefault(n, []).append(d / n)
    return out


# Terrain link
terr_names = sorted({x for a in listing.values() for x in a if x.endswith(".terrain_bin")})
files = extract(terr_names)
print("terrain files", len(files))
matches = []
for n, ps in files.items():
    d = ps[-1].read_bytes()
    words = struct.unpack_from(f"<{len(d) // 4}I", d, 0)
    if SPACE in words:
        matches.append((n, ps[-1].parent.name, len(d), words.index(SPACE) * 4))
print("terrain files naming the space id", matches[:10])
space = extract([f"{SPACE}.space_bxml"])[f"{SPACE}.space_bxml"][-1].read_bytes()
payload, fixups = struct.unpack_from("<II", space, 0)
print("space bytes", len(space), "payload", payload, "fixups", fixups, "root u32", struct.unpack_from("<48I", space, 8))
ids = set(int(n.split(".")[0]) for n in terr_names if n.split(".")[0].isdigit())
for sym, rows in syms.items():
    hit = [rows[str(w)] for w in set(struct.unpack_from(f"<{len(space) // 4}I", space, 0)) if str(w) in rows and len(rows[str(w)]) > 2]
    if hit and sym in ("region", "sky", "terrain", "terrainpaletteset", "collisionset", "simspace", "pathset"):
        print("  refs", sym, hit[:8])
print("terrain header samples")
for n in terr_names[:4]:
    d = files[n][-1].read_bytes()
    print(" ", n, len(d), "id-ish", struct.unpack_from("<I", d, 0x50)[0], [round(x, 1) for x in struct.unpack_from("<12f", d, 0x54)], struct.unpack_from("<4I", d, 0x84))

# Placements
payload_bytes = space[8:8 + payload]
stored, count = struct.unpack_from("<II", payload_bytes, 152)
base = stored - 8
print("placements", count, "base", base)
rows = []
for i in range(count):
    at = base + i * 80
    px, py, pz = struct.unpack_from("<3f", payload_bytes, at + 4)
    fab = struct.unpack_from("<I", payload_bytes, at + 52)[0]
    sc = struct.unpack_from("<3f", payload_bytes, at + 36)
    rows.append((math.dist((px, py, pz), DOOR), fab, px, py, pz, sc))
xs = [r[2] for r in rows]; ys = [r[3] for r in rows]; zs = [r[4] for r in rows]
print("extent x", round(min(xs)), round(max(xs)), "y", round(min(ys)), round(max(ys)), "z", round(min(zs)), round(max(zs)))
for radius in (1000, 2000, 4000, 8000, 16000, 1e9):
    near = [r for r in rows if r[0] <= radius]
    print("within", radius, "placements", len(near), "unique fabs", len({r[1] for r in near}))
near = sorted(r for r in rows if r[0] <= 4000)[:30]
print("closest", [(round(r[0]), syms["fab"].get(str(r[1]), r[1]), [round(x) for x in r[2:5]]) for r in near])

# Triangle cost inside radii
want = sorted({r[1] for r in rows if r[0] <= 16000})
print("fabs to size", len(want))
vis = extract([f"{f}.fab_visual_data_streamable_bin" for f in want])
print("have visual", len(vis))
tri = {}
for f in want:
    ps = vis.get(f"{f}.fab_visual_data_streamable_bin")
    if not ps:
        continue
    d = ps[-1].read_bytes()
    if len(d) < 24:
        continue
    a = struct.unpack_from("<I", d, 0)[0]
    tri[f] = len(d)
for radius in (1000, 2000, 4000, 8000, 16000):
    near = [r for r in rows if r[0] <= radius]
    print("within", radius, "visual bytes if unique", sum(tri.get(f, 0) for f in {r[1] for r in near}) // 1024, "KiB; instanced", sum(tri.get(r[1], 0) for r in near) // 1024, "KiB; missing", sum(1 for r in near if r[1] not in tri))
