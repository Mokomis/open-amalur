"""Inspect NPC clothing FABs: assemblies, material links, palette area."""
import collections, json, re, struct, sys
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
sys.path[:0] = [str(root / "work/v07-mesh"), str(root / "work/v07-bxml")]
import amalur_mesh
inp = root / "work/v20-inputs"
syms = json.loads((inp / "symbols.json").read_text())
kinds = collections.defaultdict(set)
for arch, n in (("DATA_0.pak", "DATA"), ("initial_0.pak", "initial"), ("patch_0.pak", "patch")):
    b = (root / f"outputs/{n}-archive-list.txt").read_bytes()
    for x in b.decode("utf-16" if b[:2] == b"\xff\xfe" else "utf-8-sig").splitlines():
        m = re.match(r"(\d+)(?:_\d+)?\.(\w+)$", x.strip())
        if m:
            kinds[int(m.group(1))].add(m.group(2))
def path(name):
    for a in ("patch_0.pak", "initial_0.pak", "DATA_0.pak"):
        if (inp / a / name).exists():
            return inp / a / name
for fid in (632118, 1301785, 666265, 1427730):
    fb = path(f"{fid}.fab_bxml").read_bytes()
    mesh = amalur_mesh.parse_file(path(f"{fid}.fab_visual_data_streamable_bin"))
    print("=====", fid, "fab bytes", len(fb), "tag", fb[4:8], "head", struct.unpack_from("<12I", fb, 4))
    pl = struct.unpack_from("<I", fb, 0)[0]
    n = struct.unpack_from("<H", fb, 4 + 0x10)[0]
    print(" payload", pl, "joints", n, "after", fb[pl + 8:pl + 8 + 80].hex())
    print(" vbs", [(v["vertex_count"], v["stride_bytes"]) for v in mesh["vertex_buffers"]], "ibs", [i["index_count"] for i in mesh["index_buffers"]])
    for a in mesh["assemblies"][:12]:
        print("  asm vb", a["vertex_buffer"], "ib", a["index_buffer"], "words", a["unknown_u32_at8"], "u16", a["unknown_u16_at2"])
    refs = []
    for i in range(0, len(fb) - 3):
        w = struct.unpack_from("<I", fb, i)[0]
        low = w & 0xfffffff
        ext = kinds.get(low, set())
        if ext & {"mat_bxml", "dds"} and low > 1000:
            refs.append((i, hex(w >> 28), low, syms["material"].get(str(low)) or syms["texture"].get(str(low)), sorted(ext)))
    print(" asset refs", refs[:16])
    # Does a records chain exist with looser scale?
    best = 0
    for start in range(0, len(fb) - 52):
        count = 0; at = start
        while at + 52 <= len(fb):
            q = struct.unpack_from("<4f", fb, at + 16)
            if abs(sum(x * x for x in q) - 1) > .02:
                break
            count += 1; at += 52
        if count > best:
            best, where = count, start
    print(" longest quaternion chain", best, where if best else None, fb[where:where + 52].hex() if best else "", "scale", struct.unpack_from("<3f", fb, where + 32) if best else "")
