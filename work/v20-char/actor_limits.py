import struct,sys,collections
from pathlib import Path
d=Path(sys.argv[1]);rows=[]
for p in sorted(d.glob("a*.bin")):
    b=p.read_bytes()
    if b[:8]!=b"OACHAR01":print(p.name,"bad magic");continue
    J,C,P,T=struct.unpack_from("<4I",b,8);at=24+((J+1)//2)*4
    for i in range(C):
        fr,fps=struct.unpack_from("<If",b,at);at+=8+fr*J*28
    for i in range(T):
        w,h=struct.unpack_from("<II",b,at);at+=8+w*h*4
    pal=[]
    for i in range(P):
        v,ix,pc,tx=struct.unpack_from("<IIIi",b,at);pal.append(pc);at+=16+pc*32+v*52+ix*4
    rows.append((p.name,J,C,P,T,max(pal),at==len(b)))
print("models",len(rows),"max joints",max(r[1] for r in rows),"clips",max(r[2] for r in rows),"parts",max(r[3] for r in rows),"textures",max(r[4] for r in rows),"palette",max(r[5] for r in rows),"size ok",all(r[6] for r in rows))
print("over limits",[r for r in rows if r[1]>128 or r[2]>30 or r[3]>24 or r[4]>16 or r[5]>64])
