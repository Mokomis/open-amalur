"""Classify every id in townspeople bundles by which asset files exist for it."""
import collections, json, re, struct, subprocess, sys
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
g = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning")
inp = root / "work/v20-inputs"
syms = json.loads((inp / "symbols.json").read_text())
sys.path[:0] = [str(root / "work/v07-mesh"), str(root / "work/v07-bxml")]
import amalur_mesh
files = collections.defaultdict(list)
for arch, n in (("DATA_0.pak", "DATA"), ("initial_0.pak", "initial"), ("patch_0.pak", "patch")):
    b = (root / f"outputs/{n}-archive-list.txt").read_bytes()
    for x in b.decode("utf-16" if b[:2] == b"\xff\xfe" else "utf-8-sig").splitlines():
        x = x.strip()
        m = re.match(r"(\d+)(?:_\d+)?\.(\w+)$", x)
        if m:
            files[int(m.group(1))].append((arch, x, m.group(2)))
def extract(arch, name):
    d = inp / arch
    if not (d / name).exists():
        subprocess.run([str(g / "modding/pakfileunpacker.exe"), str(g / "data" / arch), "unpack", str(d), name], cwd=g / "modding", capture_output=True, timeout=200)
    return d / name
for pname, sid in (("hercadwold", 1263596), ("citizen_m1", 1407601), ("citizen_f3", 1407602), ("zelda", 1936521)):
    d = (inp / "initial_0.pak" / f"{sid}.bundle").read_bytes()
    ids = list(dict.fromkeys(struct.unpack_from(f"<{(len(d) - 16) // 4}I", d, 16)))
    print("==", pname, syms["simtype"].get(str(sid)), "ids", len(ids), "head", struct.unpack_from("<4I", d, 0), "tail bytes", len(d) % 4)
    kinds = collections.Counter()
    for v in ids:
        ext = {e for _, _, e in files.get(v, [])}
        kinds[tuple(sorted(ext))] += 1
        if ext & {"fab_visual_data_streamable_bin", "fab_bxml", "mat_bxml", "simtype_visual_data_bundle", "bin", "batch", "visualbundle"}:
            name = syms["fab"].get(str(v)) or syms["material"].get(str(v)) or "?"
            line = [v, name, sorted(ext)]
            vis = [x for x in files[v] if x[2] == "fab_visual_data_streamable_bin"]
            if vis:
                p = extract(vis[-1][0], vis[-1][1])
                if p.stat().st_size > 60:
                    try:
                        s = amalur_mesh.parse_file(p)["summary"]
                        line += [s["vertices"], s["strides"], round(s["bounds"]["minimum"][2]), round(s["bounds"]["maximum"][2])]
                    except Exception as e:
                        line.append(str(e)[:50])
            print("  ", line)
    print("  kinds", kinds.most_common(10))
print("female anim", [(k, v) for k, v in syms["animation"].items() if v.lower() in ("human_female_idle_01", "human_female_walk_01", "human_npc_idle_01", "human_npc_idle01", "human_idle_01", "human_walk_01") or "human_npc_f_idle" in v.lower()])
print("female skel fab", (inp / "patch_0.pak/611642.fab_bxml").exists(), [x for x in files.get(611642, [])])
