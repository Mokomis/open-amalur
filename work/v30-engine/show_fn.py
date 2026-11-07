#!/usr/bin/env python3
"""show_fn.py <decomp dir> <exe> <hex addr>...: pseudocode and entry bytes of functions, for local analysis."""
import glob,re,struct,sys
R,exe=sys.argv[1:3]; want=[a.lower().zfill(8) for a in sys.argv[3:]]
d=open(exe,"rb").read(); pe=struct.unpack_from("<I",d,0x3c)[0]; ns=struct.unpack_from("<H",d,pe+6)[0]; oh=struct.unpack_from("<H",d,pe+20)[0]; o=pe+24
base=struct.unpack_from("<I",d,o+28)[0]; S=[]
for i in range(ns):
    s=o+oh+40*i; vs,va,rs,rp=struct.unpack_from("<IIII",d,s+8); S.append((base+va,vs,rp))
def off(v):
    for a,vs,rp in S:
        if a<=v<a+vs: return v-a+rp
for p in glob.glob(R+"/*.c"):
    t=open(p,errors="replace").read()
    for a in want:
        i=t.find("// "+a+" ")
        if i>=0:
            j=t.find("\n// ",i+5); x=off(int(a,16))
            print(t[i:j if j>0 else None]); print("BYTES",d[x:x+16].hex(" ")); print()
