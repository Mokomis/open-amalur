import json, re, struct, sys, zlib
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
sys.path[:0] = [str(root / "work/v09-textures")]
import keen_texture
inp = root / "work/v20-inputs"
d = next(p for p in (inp / "patch_0.pak/325844.sky_bxml", inp / "initial_0.pak/325844.sky_bxml") if p.exists()).read_bytes()
print(len(d))
for i in range(0, len(d) - 3, 4):
    u = struct.unpack_from("<I", d, i)[0]; f = struct.unpack_from("<f", d, i)[0]
    print(i, hex(u), round(f, 4) if abs(f) < 1e6 and abs(f) > 1e-4 else "", tuple(d[i:i + 4]) if u >> 24 == 0xff else "", sep=" ", end=" | " if (i // 4) % 2 == 0 else "\n")
print()
idx = json.loads((root / "outputs/scene-v19/shader-index.json").read_text())
for n, row in idx.items():
    body = (root / f"outputs/scene-v19/shaders/{n}.asm").read_text(errors="replace")
    names = re.findall(r"^//\s+(\w+)\s+texture\s", body, re.M)
    if any(re.search(r"cloud|sky|star|moon|sun", x, re.I) for x in names):
        code = [l for l in body.splitlines() if not l.startswith("//")]
        print("---", n, row.get("type"), len(code), names)
        if len(code) < 60:
            print("\n".join(l for l in code if not l.startswith(("dcl_sampler", "dcl_temps"))))
        a = body.find("cbuffer")
        print(re.findall(r"float\w* (\w*(?:[Ss]ky|[Cc]loud|[Ss]tar|[Mm]oon|[Ss]un)\w*)", body)[:12])
for tid in (159747, 159748, 710562):
    for k in (2, 1, 0, 3):
        p = inp / "DATA_0.pak" / f"{tid}_{k}.dds"
        if not p.exists():
            import subprocess
            g = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning")
            subprocess.run([str(g / "modding/pakfileunpacker.exe"), str(g / "data/DATA_0.pak"), "unpack", str(inp / "DATA_0.pak"), p.name], cwd=g / "modding", capture_output=True, timeout=60)
        if p.exists():
            b = p.read_bytes()
            w, h, fmt, mips = *struct.unpack_from("<HH", b, 20), b[29], struct.unpack_from("<H", b, 35)[0]
            print(tid, k, len(b), w, h, fmt, mips)
            if w <= 1024:
                size = ((w + 3) // 4) * ((h + 3) // 4) * (8 if fmt == 1 else 16)
                rgba = keen_texture.decode_blocks(b[38:38 + size], w, h, fmt)
                step = max(1, w // 512)
                rows = b"".join(b"\0" + b"".join(bytes(rgba[(y * w + x) * 4:(y * w + x) * 4 + 3]) for x in range(0, w, step)) for y in range(0, h, step))
                c = lambda t, q: struct.pack(">I", len(q)) + t + q + struct.pack(">I", zlib.crc32(t + q))
                (root / f"work/v20-char/sky-{tid}.png").write_bytes(b"\x89PNG\r\n\x1a\n" + c(b"IHDR", struct.pack(">IIBBBBB", w // step, h // step, 8, 2, 0, 0, 0)) + c(b"IDAT", zlib.compress(rows)) + c(b"IEND", b""))
                break
