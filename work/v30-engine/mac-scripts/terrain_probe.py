"""Dump terrain 431658: header, tile table and the compressed stream structure."""
import collections, json, struct, subprocess, zlib
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
g = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning")
inp = root / "work/v20-inputs"
T = 431658
for arch, n in (("DATA_0.pak", "DATA"), ("patch_0.pak", "patch")):
    b = (root / f"outputs/{n}-archive-list.txt").read_bytes()
    have = set(x.strip() for x in b.decode("utf-16" if b[:2] == b"\xff\xfe" else "utf-8-sig").splitlines())
    sel = [x for x in (f"{T}.terrain_bin", f"{T}.terrain_streamable_bin", f"{T}.veggie_streamable_bin") if x in have]
    print(arch, sel)
    d = inp / arch
    todo = [x for x in sel if not (d / x).exists()]
    if todo:
        subprocess.run([str(g / "modding/pakfileunpacker.exe"), str(g / "data" / arch), "unpack", str(d), *todo], cwd=g / "modding", capture_output=True, timeout=280)
p = next(q for q in (inp / "patch_0.pak" / f"{T}.terrain_bin", inp / "DATA_0.pak" / f"{T}.terrain_bin") if q.exists())
h = p.read_bytes()
print(p.parent.name, "bin bytes", len(h))
print("u32", struct.unpack_from("<20I", h, 0))
print("f32", [round(x, 2) for x in struct.unpack_from("<20f", h, 0)])
for at in (0x50, 0x54, 0x80, 0xa0, 0xc0, 0x100, 0x200, 0x400):
    print(hex(at), h[at:at + 48].hex(), [round(x, 2) for x in struct.unpack_from("<8f", h, at)])
s = next(q for q in (inp / "patch_0.pak" / f"{T}.terrain_streamable_bin", inp / "DATA_0.pak" / f"{T}.terrain_streamable_bin") if q.exists()).read_bytes()
print(p.parent.name, "stream bytes", len(s), s[:64].hex())
at, blocks, kinds = 0, [], collections.Counter()
raw_total = 0
while at + 24 <= len(s) and len(blocks) < 200000:
    a, rawa, total, zero, raw, comp = struct.unpack_from("<6I", s, at)
    if a not in (1, 0, 2) or total > len(s) - at:
        print("stop at", at, s[at:at + 32].hex()); break
    body = s[at + 24:at + 8 + total + 8]
    blocks.append((at, a, rawa, total, zero, raw, comp))
    kinds[(raw, comp == raw)] += 1
    at += 16 + total if False else 16 + total
print("blocks", len(blocks), "first", blocks[:6], "end", at, "common", kinds.most_common(10))
at0, *_ = blocks[0]
print("first block body", s[at0:at0 + 48].hex())
for off in (at0 + 24, at0 + 16):
    try:
        raw = zlib.decompress(s[off:])
        print("zlib at", off, len(raw), raw[:64].hex())
        break
    except Exception as e:
        print("zlib fail", off, e)
