"""Find people in Gorhart, the simtype behind each, and what links them to body models."""
import collections, json, math, re, struct, subprocess
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
g = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning")
inp = root / "work/v20-inputs"
syms = json.loads((inp / "symbols.json").read_text())
SPACE, DOOR = 431638, (1575.1, -62759.2, 5152.1)
listing = {}
for arch, n in (("DATA_0.pak", "DATA"), ("initial_0.pak", "initial"), ("patch_0.pak", "patch")):
    b = (root / f"outputs/{n}-archive-list.txt").read_bytes()
    listing[arch] = [x.strip() for x in b.decode("utf-16" if b[:2] == b"\xff\xfe" else "utf-8-sig").splitlines() if x.strip()]


def extract(names):
    found = {}
    for arch in ("DATA_0.pak", "initial_0.pak", "patch_0.pak"):
        have = set(listing[arch])
        sel = [n for n in names if n in have]
        d = inp / arch
        d.mkdir(parents=True, exist_ok=True)
        for start in range(0, len(sel), 60):
            todo = [n for n in sel[start:start + 60] if not (d / n).exists()]
            if todo:
                subprocess.run([str(g / "modding/pakfileunpacker.exe"), str(g / "data" / arch), "unpack", str(d), *todo], cwd=g / "modding", capture_output=True, timeout=280)
        for n in sel:
            if (d / n).exists():
                found[n] = d / n
    return found


gors = [n for n in listing["initial_0.pak"] if n.endswith(".gor_bxml")]
files = extract(gors)
print("gor files", len(gors), "extracted", len(files))
people = []
kinds = collections.Counter()
for n, p in files.items():
    d = p.read_bytes()
    if len(d) < 60 or struct.unpack_from("<I", d, 8)[0] != SPACE:
        continue
    pos = struct.unpack_from("<3f", d, 24)
    q = struct.unpack_from("<4f", d, 36)
    st = struct.unpack_from("<I", d, 72)[0] if len(d) >= 76 else 0
    words = struct.unpack_from(f"<{min(30, len(d) // 4)}I", d, 0)
    sim = [w for w in words if str(w) in syms["simtype"]]
    near = math.dist(pos[:2], DOOR[:2])
    people.append((round(near), n[:-9], [round(x) for x in pos], [syms["simtype"][str(w)] for w in sim][:2], sim[:2]))
    kinds[re.split(r"[_\d]", n)[0]] += 1
people.sort()
print("objects in space", len(people), kinds.most_common(14))
for row in people[:70]:
    print(row)
sample = next(p for n, p in files.items() if n.startswith("citizen_gorhart_alm_male_1"))
d = sample.read_bytes(); print("citizen bytes", len(d), d[:len(d)].hex())
npc_sims = {w for r in people for w in r[4] if re.search("citizen|npc", r[1])}
print("citizen simtypes", [(w, syms["simtype"][str(w)]) for w in sorted(npc_sims)][:30])
print("fab npc names", [v for v in syms["fab"].values() if re.search(r"almain|varani|citizen|peasant|commoner|villager|^npc|human_(m|f)|_m_body|tunic|robe|shirt|cloth", v, re.I)][:80])
print("files per first citizen simtype")
for w in sorted(npc_sims)[:4]:
    for arch, have in listing.items():
        hits = [x for x in have if x.split(".")[0] == str(w)]
        if hits:
            print(" ", w, syms["simtype"][str(w)], arch, hits)
print("types with bundles sample", [x for x in listing["patch_0.pak"] if x.endswith(".simtype_visual_data_bundle")][:6])
cmp = sorted(p.name for p in (root / "work").rglob("compiled_type*.py"))
print(cmp, [str(p.relative_to(root)) for p in (root / "work").rglob("compiled_type.py")])
