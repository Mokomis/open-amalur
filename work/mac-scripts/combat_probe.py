"""List usable combat clips, candidate enemies and sword attachment data."""
import json, re, struct, subprocess, sys
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
sys.path[:0] = [str(root / "work/v07-mesh"), str(root / "work/v07-bxml")]
import amalur_mesh
g = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning")
inp = root / "work/v20-inputs"
syms = json.loads((inp / "symbols.json").read_text())
anim = {int(k): v for k, v in syms["animation"].items()}
have = {}
for arch, n in (("DATA_0.pak", "DATA"), ("initial_0.pak", "initial"), ("patch_0.pak", "patch")):
    b = (root / f"outputs/{n}-archive-list.txt").read_bytes()
    have[arch] = set(x.strip() for x in b.decode("utf-16" if b[:2] == b"\xff\xfe" else "utf-8-sig").splitlines() if x.strip())


def extract(names):
    found = {}
    for arch in ("DATA_0.pak", "initial_0.pak", "patch_0.pak"):
        sel = [n for n in names if n in have[arch]]
        d = inp / arch
        for s in range(0, len(sel), 60):
            todo = [n for n in sel[s:s + 60] if not (d / n).exists()]
            if todo:
                subprocess.run([str(g / "modding/pakfileunpacker.exe"), str(g / "data" / arch), "unpack", str(d), *todo], cwd=g / "modding", capture_output=True, timeout=280)
        for n in sel:
            if (d / n).exists():
                found[n] = d / n
    return found


pats = {
 "player swings": r"player_swdattkfrt1_0[12]a+b?",
 "sword idle/run": r"player_(swd|sword)\w*(idle|run|walk)\w*|human_sword\w*(idle|run)\w*|humanMale_Sword\w*idle\w*|human_Combat_idle_01|human_Enter_Combat_Idle|human_Exit_Combat_Idle",
 "npc combat": r"HM_OneHand_(Idle01|Combat_Idle01|Combat_Run01|Combat_Walk01|AttackX_01|AttackB_01|React_Front01|React_Front_Light_01|React_Back01|KnockDown_01|GetUp_01)",
 "player react": r"player_\w*(hit|react|death|die)\w*",
 "human death": r"(human|hm)\w*(death|die|dead)\w*",
 "human hit": r"human\w*(hit|react)\w*(front|fwd)\w*",
}
for label, pat in pats.items():
    ids = sorted((v, k) for k, v in anim.items() if re.fullmatch(pat, v, re.I))
    got = extract([f"{i}.anm_bxml" for _, i in ids[:60]])
    rows = []
    for v, i in ids[:60]:
        p = got.get(f"{i}.anm_bxml")
        if p:
            b = p.read_bytes()
            rows.append((v, i, struct.unpack_from("<H", b, 8 + 0xe)[0], round(struct.unpack_from("<f", b, 12)[0], 2), len(b)))
    print(label, len(ids), rows[:30])
print("--- enemies")
st = syms["simtype"]
foes = [(int(k), v) for k, v in st.items() if re.search(r"brigand|bandit|thug|tuatha_|ettin|boggart|^mob_", v, re.I)]
print(len(foes), [v for _, v in foes][:50])
got = extract([f"{k}.bundle" for k, _ in foes[:300]])
rows = []
for k, v in foes[:300]:
    p = got.get(f"{k}.bundle")
    if not p:
        continue
    d = p.read_bytes()
    ids = set(struct.unpack_from(f"<{(len(d) - 16) // 4}I", d, 16))
    rag = [syms["ragdoll"][str(i)] for i in ids if str(i) in syms["ragdoll"]]
    if "human_skel" in rag:
        rows.append((k, v))
print("human male enemies", rows[:40])
print("--- sword")
for fid in (1327249,):
    f = extract([f"{fid}.fab_bxml", f"{fid}.fab_visual_data_streamable_bin"])
    fb = f[f"{fid}.fab_bxml"].read_bytes()
    n = struct.unpack_from("<H", fb, 4 + 0x10)[0]
    print("fab", len(fb), fb[4:8], "joints", n, "payload", struct.unpack_from("<I", fb, 0)[0])
    names = struct.unpack_from(f"<{n}I", fb, 4 + 0x20 + struct.unpack_from("<I", fb, 4 + 0x20)[0])
    print(" names", [syms["ragdoll_bone_mappings"].get(str(x), x) for x in names])
    pose = 4 + 0x18 + struct.unpack_from("<i", fb, 4 + 0x18)[0]
    print(" bind", [[round(x, 2) for x in struct.unpack_from("<7f", fb, pose + i * 48)] for i in range(n)])
    m = amalur_mesh.parse_file(f[f"{fid}.fab_visual_data_streamable_bin"])
    print(" asm", [(a["vertex_buffer"], a["index_buffer"], a["unknown_u16_at2"], a["unknown_u32_at8"][3]) for a in m["assemblies"]], m["summary"]["bounds"], m["summary"]["strides"])
    raw = f[f"{fid}.fab_visual_data_streamable_bin"].read_bytes()
    print(" v0", raw[m["vertex_buffers"][0]["data_file_offset"]:m["vertex_buffers"][0]["data_file_offset"] + 48].hex())
    print(" materials", [syms["material"].get(str(struct.unpack_from("<I", fb, i)[0])) for i in range(struct.unpack_from("<I", fb, 0)[0] + 8, len(fb) - 3) if str(struct.unpack_from("<I", fb, i)[0]) in syms["material"] and struct.unpack_from("<I", fb, i)[0] > 4096])
print("--- sky")
print({k: v for k, v in syms["sky"].items() if "foggy" in v.lower() or v.lower().startswith("out_for")})
print([v for k, v in syms["fab"].items() if re.search(r"sky|dome|cloud|horizon", v, re.I)][:30], "skytex", [v for k, v in syms["texture"].items() if re.search(r"sky", v, re.I)][:30])
sky_files = [x for a in have.values() for x in a if "sky" in x][:20]
print(sky_files)
