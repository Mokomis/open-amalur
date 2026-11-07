"""Follow the space's asset ids to find which file names a terrain."""
import json, struct, subprocess
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
g = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning")
inp = root / "work/v20-inputs"
listing = {}
for arch, n in (("DATA_0.pak", "DATA"), ("initial_0.pak", "initial"), ("patch_0.pak", "patch")):
    b = (root / f"outputs/{n}-archive-list.txt").read_bytes()
    listing[arch] = [x.strip() for x in b.decode("utf-16" if b[:2] == b"\xff\xfe" else "utf-8-sig").splitlines() if x.strip()]
ids = {}
for a in ("DATA_0.pak", "patch_0.pak"):
    for p in (inp / a).glob("*.terrain_bin"):
        if p.stem.isdigit():
            ids[int(p.stem)] = p
d = (inp / "patch_0.pak/431638.space_bxml").read_bytes()
print("head floats", struct.unpack_from("<3f", d, 12), "words", struct.unpack_from("<16I", d, 8))
wanted = ["431608", "485422", "509958", "458617", "431638"]
for arch, names in listing.items():
    for n in names:
        stem = n.split(".")[0].split("_")[0]
        if stem in wanted:
            print(arch, n)
            dest = inp / arch
            if not (dest / n).exists():
                subprocess.run([str(g / "modding/pakfileunpacker.exe"), str(g / "data" / arch), "unpack", str(dest), n], cwd=g / "modding", capture_output=True, timeout=120)
            p = dest / n
            if p.exists() and n != "431638.space_bxml":
                b = p.read_bytes()
                hits = {}
                for i in range(0, len(b) - 3):
                    v = struct.unpack_from("<I", b, i)[0] & 0xfffffff
                    if v in ids:
                        hits[v] = i
                print("   bytes", len(b), "head", b[:40].hex(), "terrain refs", list(hits.items())[:8])
print("terrain 1st bytes with self id check", [(k, hex(struct.unpack_from('<I', p.read_bytes(), 0x18)[0])) for k, p in list(ids.items())[:3]])
