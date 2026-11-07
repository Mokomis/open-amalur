import struct,base64
from pathlib import Path
p=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning\koa.exe');d=p.read_bytes();pe=struct.unpack_from('<I',d,0x3c)[0];ns=struct.unpack_from('<H',d,pe+6)[0];oh=struct.unpack_from('<H',d,pe+20)[0];o=pe+24;base=struct.unpack_from('<I',d,o+28)[0]
for i in range(ns):
 s=o+oh+40*i;vs,va,rs,rp=struct.unpack_from('<IIII',d,s+8)
 if base+va<=0xc9dc90<base+va+vs:
  off=0xc9dc90-base-va+rp;print(base64.b64encode(d[off:off+0x380]).decode())
