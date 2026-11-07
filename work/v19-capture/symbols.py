"""Decode engine symbol tables: u32 count, then (id, start, end) rows, then strings."""
import json, re, struct
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
dest = root / "work/v20-inputs/initial_0.pak"
b = (root / "outputs/initial-archive-list.txt").read_bytes()
names = set(x.strip() for x in b.decode("utf-16" if b[:2] == b"\xff\xfe" else "utf-8-sig").splitlines() if x.strip())
all_syms = {}
for path in sorted(dest.glob("symbol_table_*.bin")):
    key = path.stem[13:]
    if key.startswith("64_"):
        continue
    d = path.read_bytes()
    n = struct.unpack_from("<I", d, 0)[0]
    head = 8 + n * 12
    if head > len(d):
        print("bad", key); continue
    rows = {}
    for i in range(n):
        sym, a, e = struct.unpack_from("<III", d, 4 + i * 12)
        if e - a < 400:
            rows[sym] = d[head + a:head + e].split(b"\0")[0].decode("latin1")
    all_syms[key] = rows
print({k: len(v) for k, v in all_syms.items()})
(root / "work/v20-inputs/symbols.json").write_text(json.dumps(all_syms))
anim = all_syms["animation"]
print("samples", list(anim.items())[:6])
core = re.compile(r"hero_(idle|run|walk|strafe\w*|combatidle|jump|swordattack01a|death)\d*", re.I)
print("hero count", sum(v.lower().startswith("hero_") for v in anim.values()))
print("hero core", [(s, v, f"{s}.anm_bxml" in names) for s, v in anim.items() if core.fullmatch(v)])
print("player anim", [(s, v) for s, v in anim.items() if re.search("^player", v, re.I)][:30])
fab = all_syms["fab"]
print("fab samples", list(fab.items())[:8])
print("fab hero", [(s, v) for s, v in fab.items() if re.search(r"hero|player|^pc|human|male|body|head_|_nude|skin", v, re.I)][:80])
print("motiontree", list(all_syms["motiontree"].items())[:120])
print("ragdoll", list(all_syms["ragdoll"].items())[:30])
print("fabslot", list(all_syms["fabslot"].items())[:40])
st = all_syms["simtype"]
print("simtype player", [(s, v) for s, v in st.items() if re.search(r"^(player|hero|pc_)|player_(human|male|female|race|avatar)|race_", v, re.I)][:50])
