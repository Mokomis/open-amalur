"""List code that reads RigAnimation-like data pointer +0x10 near known rig code, by function boundaries."""
import re, struct
from pathlib import Path
exe = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning\koa.exe").read_bytes()
pe = struct.unpack_from("<I", exe, 0x3c)[0]; base = struct.unpack_from("<I", exe, pe + 52)[0]
n = struct.unpack_from("<H", exe, pe + 6)[0]; o = pe + 24 + struct.unpack_from("<H", exe, pe + 20)[0]
secs = [struct.unpack_from("<8sIIII", exe, o + i * 40) for i in range(n)]
t = next(s for s in secs if s[0].startswith(b".text")); tb = exe[t[4]:t[4] + t[3]]; tva = base + t[2]
# xmm heavy functions with 0x4000/0x7fff scale constants: look for floats 1/32767 and pi-related quaternion decode constants
for name, val in (("1/32767", 1 / 32767), ("1/32768", 1 / 32768), ("1/65535", 1 / 65535), ("1/255", 1 / 255), ("sqrt2/2", 0.70710678), ("1/1023", 1 / 1023), ("1/2047", 1 / 2047), ("1/4095", 1 / 4095), ("1/511", 1 / 511)):
    b = struct.pack("<f", val)
    addrs = [base + s[2] + m.start() for s in secs if not s[0].startswith(b".text") for m in re.finditer(re.escape(b), exe[s[4]:s[4] + s[3]])][:12]
    print(name, [hex(a) for a in addrs])
    for a in addrs[:6]:
        refs = [hex(tva + m.start()) for m in re.finditer(re.escape(struct.pack("<I", a)), tb)][:10]
        print("   ", hex(a), refs)
