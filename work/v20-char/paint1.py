import collections,json,struct,sys,zlib
from pathlib import Path
import numpy as np
src=(Path.home()/"Documents/Opem Amalur/work/v20-char/build_npcs.py").read_text()
exec(src[:src.index("SKELS = {}")])
TID="431658";name=f"{TID}.terrain_streamable_bin";s=extract([name])[name].read_bytes()
recs=[];i=0
while True:
    i=s.find(b"\x78\x9c",i)
    if i<0:break
    if i>=24:
        raw,total,zero,raw2,comp=struct.unpack_from("<5I",s,i-20)
        if raw==raw2 and zero==0 and comp<=total<=comp+32 and i+comp<=len(s):
            recs.append((i,raw,comp));i+=comp;continue
    i+=1
print(len(recs),collections.Counter(r[1] for r in recs).most_common(8))
seq="".join("P" if r[1]==66568 else "h" for r in recs);print(seq[:200])
kinds=collections.Counter()
Heads=[]
for k,(at,raw,comp) in enumerate(recs):
    d=zlib.decompress(s[at:at+comp])
    if raw==66568:
        h=struct.unpack_from("<I",d,0)[0];kinds[h]+=1;Heads.append((k,h,d[4:4+24].hex(),[d[4+i*4:4+i*4+4].hex() for i in (0,1000,8000)]))
    else:
        Heads.append((k,"h",struct.unpack_from("<I8H",d,0)))
print("paint head values",kinds.most_common(8))
for h in Heads[:24]:print(h)
# neighbours in a separate terrain_bin
n2=f"{TID}.terrain_bin";f=extract([n2]).get(n2)
if f:
    b=f.read_bytes();print("terrain_bin",len(b),b[:64].hex());W=struct.unpack_from(f"<{min(len(b)//4,200)}I",b);print(W[:60])
