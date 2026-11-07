import json,re,struct,collections
from pathlib import Path
import numpy as np
src=(Path.home()/"Documents/Opem Amalur/work/v20-char/build_npcs.py").read_text()
exec(src[:src.index("SKELS = {}")])
Sp=sorted((int(k),str(v)) for k,v in syms["simspace"].items() if re.match(r"out_dal_(north|south|west|east|central|tran|[a-z0-9])",str(v)))
print(len(Sp),[n for _,n in Sp if not re.match(r"out_dal_(north|south|tran)",n)])
Tot=collections.Counter();near=[]
target=np.array([20300,-43211])
for sid,sn in Sp:
    f=extract([f"{sid}.space_bxml"]).get(f"{sid}.space_bxml")
    if f is None: continue
    d=f.read_bytes();pl=struct.unpack_from("<I",d,0)[0];b=d[8:8+pl]
    def arr(slot,st):
        p,c=struct.unpack_from("<II",b,slot);return [b[p-8+i*st:p-8+(i+1)*st] for i in range(c)]
    refs=[struct.unpack("<I",r)[0] for r in arr(0x1b0,4)];cen=[struct.unpack("<3f",r) for r in arr(0x1a8,12)]
    rend=arr(0x160,84);bc={tuple(round(x,2) for x in struct.unpack_from("<3f",r)):r for r in rend}
    for t,c in zip(refs,cen):
        k=t>>28;m=bc.get(tuple(round(x,2) for x in c)) is not None
        Tot[(k,m)]+=1
        if np.hypot(c[0]-target[0],c[1]-target[1])<2500:
            near.append((sn,k,m,t&0xfffffff,[round(x) for x in c],syms["fab"].get(str(t&0xfffffff),"?")))
    Tot["renders"]+=len(rend)
    a148=arr(0x148,80);Tot["a148"]+=len(a148);Tot["a150"]+=len(arr(0x150,84))
    if sid==Sp[0][0]:
        print("slots",[(hex(o),)+struct.unpack_from("<II",b,o) for o in range(0x100,0x1f0,8)])
print(Tot)
print(len(near),collections.Counter((n[1],n[2]) for n in near));
for n in sorted(near,key=lambda x:x[1])[:60]:print(n)
