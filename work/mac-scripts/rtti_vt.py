"""Locate vtables for classes by name through MSVC RTTI in the x86 exe."""
import struct, sys
from pathlib import Path
exe = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning\koa.exe").read_bytes()
pe = struct.unpack_from("<I", exe, 0x3c)[0]; base = struct.unpack_from("<I", exe, pe + 52)[0]
n = struct.unpack_from("<H", exe, pe + 6)[0]; o = pe + 24 + struct.unpack_from("<H", exe, pe + 20)[0]
secs = [struct.unpack_from("<8sIIII", exe, o + i * 40) for i in range(n)]
def f2v(off):
    for name, vs, rva, size, raw in secs:
        if raw <= off < raw + size: return base + rva + off - raw
def v2f(va):
    for name, vs, rva, size, raw in secs:
        if base + rva <= va < base + rva + size: return va - base - rva + raw
for cls in sys.argv[1:]:
    tag = (".?AV" + cls + "@BHG@@").encode() + b"\0"
    at = exe.find(tag)
    td = f2v(at - 8)
    needle = struct.pack("<I", td)
    i = 0
    print(cls, "typedesc", hex(td))
    while True:
        i = exe.find(needle, i)
        if i < 0: break
        col = f2v(i - 12)
        if struct.unpack_from("<I", exe, i - 12)[0] == 0:
            ptr = struct.pack("<I", col); j = exe.find(ptr)
            while j >= 0:
                vt = f2v(j + 4)
                fns = struct.unpack_from("<14I", exe, j + 4)
                print("  vtable", hex(vt), [hex(x) for x in fns])
                j = exe.find(ptr, j + 4)
        i += 4
