import json, re, struct
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
inp = root / "work/v20-inputs"
syms = json.loads((inp / "symbols.json").read_text())
for sid in (431638, 524859):
    p = next((inp / a / f"{sid}.space_bxml" for a in ("patch_0.pak", "DATA_0.pak") if (inp / a / f"{sid}.space_bxml").exists()), None)
    if p is None:
        p = root / "work/scene-inputs-v07/DATA_0.pak/524859.space_bxml"
    d = p.read_bytes(); pl, fx = struct.unpack_from("<II", d, 0); b = d[8:8 + pl]
    slots = sorted(struct.unpack_from(f"<{fx // 4}I", d, 8 + pl))
    root_slots = [s for s in slots if s < 0x130]
    print("==", sid, syms["simspace"].get(str(sid)), "payload", pl, "root slots", root_slots)
    print(" head", struct.unpack_from("<20I", b, 0)[:20])
    pairs = []
    for s in root_slots:
        ptr, cnt = struct.unpack_from("<II", b, s)
        pairs.append((s, ptr - 8, cnt))
    ends = [x[1] for x in pairs] + [pl]
    for i, (s, ptr, cnt) in enumerate(pairs):
        nxt = min([e for e in ends if e > ptr], default=pl)
        print(f"  slot {s:#x} at {ptr} count {cnt} span {nxt - ptr} stride {(nxt - ptr) / cnt if cnt else 0:.1f}")
    print(" tail", struct.unpack_from("<10I", b, 0x100))
s = (root / "work/v07-bxml/amalur_shell.py").read_text(errors="replace")
print(s[:1500])
