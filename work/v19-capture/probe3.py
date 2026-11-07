"""Skeleton FAB dump, armor mesh decode attempt, and animation references in the Player motion tree."""
import collections, json, re, struct, subprocess, sys
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
g = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning")
inp = root / "work/v20-inputs"
syms = json.loads((inp / "symbols.json").read_text())
anim = {int(k): v for k, v in syms["animation"].items()}
fabs = {int(k): v for k, v in syms["fab"].items()}

def extract(want):
    out = {}
    for arch, listing in (("DATA_0.pak", "DATA"), ("initial_0.pak", "initial"), ("patch_0.pak", "patch")):
        b = (root / f"outputs/{listing}-archive-list.txt").read_bytes()
        names = set(x.strip() for x in b.decode("utf-16" if b[:2] == b"\xff\xfe" else "utf-8-sig").splitlines())
        sel = [n for n in want if n in names]
        if sel:
            d = inp / arch
            d.mkdir(parents=True, exist_ok=True)
            todo = [n for n in sel if not (d / n).exists()]
            if todo:
                subprocess.run([str(g / "modding/pakfileunpacker.exe"), str(g / "data" / arch), "unpack", str(d), *todo], cwd=g / "modding", capture_output=True, timeout=250)
            for n in sel:
                if (d / n).exists():
                    out.setdefault(n, []).append(d / n)
    return out

d = (inp / "patch_0.pak/456813.fab_bxml").read_bytes()
print("=== skeleton FAB", len(d))
print("head u32", struct.unpack_from("<16I", d, 0))
for off in (0x40, 0x168, 0xd64, 0xdd4, 0xde0, 0xed8, 0xedc):
    at = off + 0
    print(hex(off), d[at:at + 48].hex())
    print("   as float", [round(x, 3) for x in struct.unpack_from("<8f", d, at)])
print("tail", d[-64:].hex())

print("=== motion tree anim refs")
t = (inp / "initial_0.pak/100644.mtn_tree_bxml").read_bytes()
hits = collections.Counter()
for i in range(0, len(t) - 3, 4):
    v = struct.unpack_from("<I", t, i)[0]
    if v in anim:
        hits[v] += 1
print("unique anim ids", len(hits))
loco = [(k, anim[k]) for k in hits if re.search(r"idle|walk|run|jog|loco|strafe|turn", anim[k], re.I)]
print("loco count", len(loco), loco[:90])
ms = {int(k): v for k, v in syms["motionset"].items()}
mhits = collections.Counter(struct.unpack_from("<I", t, i)[0] for i in range(0, len(t) - 3, 4))
print("motionset refs", [(k, ms[k]) for k in mhits if k in ms][:60])
mot = {int(k): v for k, v in syms["motion"].items()}
print("motion refs", [(k, mot[k]) for k in mhits if k in mot and re.search("idle|walk|run|move|loco|jog", mot[k], re.I)][:60])
print("anim name families", collections.Counter(re.split(r"[_\d]", v.lower())[0] for v in anim.values()).most_common(40))
print("player/male locomotion names", [(k, v) for k, v in anim.items() if re.search(r"(^|_)(pl|plr|player|pc|hm|hu|human|male|m)_?.*(idle|walk|run|jog)", v, re.I)][:80])

print("=== armor meshes")
sys.path[:0] = [str(root / "work/v07-mesh"), str(root / "work/v07-bxml")]
files = extract([f"{i}.{e}" for i in (1926576, 1926575, 1926574, 1923507, 1378191, 1686788) for e in ("fab_bxml", "fab_visual_data_streamable_bin")])
for n, ps in sorted(files.items()):
    print(n, [(p.parent.name, p.stat().st_size) for p in ps])
try:
    import amalur_mesh
    src = Path(amalur_mesh.__file__).read_text(errors="replace")
    print("mesh module", len(src), [m for m in re.findall(r"^def (\w+)", src, re.M)][:40])
    print("skin words", sorted(set(re.findall(r"\w*(?:bone|weight|skin|joint|blend)\w*", src, re.I)))[:30])
    for key in ("1926576", "1378191"):
        for p in files.get(key + ".fab_visual_data_streamable_bin", []):
            try:
                r = amalur_mesh.parse_file(p)
                print(key, json.dumps(r["summary"])[:1200])
                print(" keys", list(r.keys()))
            except Exception as e:
                print(key, "parse failed", repr(e)[:300])
                print(" head", p.read_bytes()[:96].hex())
except Exception as e:
    print("module failed", repr(e)[:300])
