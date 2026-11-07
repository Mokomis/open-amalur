"""Raw scans: remaining RTTI names, direct callers of pose functions, function starts near the math module."""
import re, struct, sys
from pathlib import Path
exe = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning\koa.exe").read_bytes()
pe = struct.unpack_from("<I", exe, 0x3c)[0]; base = struct.unpack_from("<I", exe, pe + 52)[0]
n = struct.unpack_from("<H", exe, pe + 6)[0]; o = pe + 24 + struct.unpack_from("<H", exe, pe + 20)[0]
secs = [struct.unpack_from("<8sIIII", exe, o + i * 40) for i in range(n)]
text = next(s for s in secs if s[0].startswith(b".text"))
tb = exe[text[4]:text[4] + text[3]]; tva = base + text[2]
rt = sorted(set(m.group(0).decode() for m in re.finditer(rb"\.\?A[VU][A-Za-z0-9_@$?]*(?:Anim|Clip|Skelet|Pose|Motion|Keyframe|Compress|Rig|Bone|Track|Sampler|Havok|hka|NM|Morpheme)[A-Za-z0-9_@$?]*@@", exe)))
print(len(rt)); print([r[4:-2] for r in rt if not re.search("Event|Chooser", r)])
def callers(target):
    out = []
    for m in re.finditer(rb"\xe8", tb):
        i = m.start()
        if i + 5 <= len(tb) and tva + i + 5 + struct.unpack_from("<i", tb, i + 1)[0] == target:
            out.append(hex(tva + i))
    return out
for t in (0x111aa30,):
    print(hex(t), callers(t)[:20])
print("data refs", [hex(base + s[2] + m.start()) for s in secs for m in re.finditer(re.escape(struct.pack("<I", 0x111aa30)), exe[s[4]:s[4] + s[3]])][:10])
starts = sorted(set(tva + m.start() for m in re.finditer(rb"\x55\x8b\xec", tb) if 0x1100000 <= tva + m.start() < 0x1130000))
print(len(starts), [hex(x) for x in starts][:160])
