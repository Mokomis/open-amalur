import json,re,struct,collections
from pathlib import Path
import numpy as np
src=(Path.home()/"Documents/Opem Amalur/work/v20-char/build_npcs.py").read_text()
exec(src[:src.index("SKELS = {}")])
C={int(k):str(v) for k,v in syms["cluster"].items()}
carr=np.array(sorted(C),np.uint32)
Sp=sorted((int(k),str(v)) for k,v in syms["simspace"].items() if re.match(r"out_dal_",str(v)))
slots=collections.Counter();names=collections.Counter();ex=[]
for sid,sn in Sp:
    f=extract([f"{sid}.space_bxml"]).get(f"{sid}.space_bxml")
    if f is None: continue
    d=f.read_bytes();pl=struct.unpack_from("<I",d,0)[0];b=d[8:8+pl]
    tab=[(o,)+struct.unpack_from("<II",b,o) for o in range(0,0x400,8)]
    tab=[t for t in tab if 0<t[2]<200000 and 0<t[1]<len(b)]
    tab2=sorted(tab,key=lambda t:t[1])
    w=np.frombuffer(b[:len(b)//4*4],"<u4");hits=np.nonzero(np.isin(w,carr))[0]
    for h in hits:
        p=int(h)*4+8
        slot=None
        for t,nx in zip(tab2,tab2[1:]+[(0,len(b)+8,0)]):
            if t[1]<=p<nx[1]:slot=t;break
        key=(hex(slot[0]),round((nx[1]-slot[1])/max(slot[2],1))) if slot else None
        slots[hex(slot[0]) if slot else "?"]+=1;names[C[int(w[h])]]+=1
        if len(ex)<8:ex.append((sn,hex(slot[0]) if slot else None,(p-slot[1]) if slot else None,slot[2] if slot else None,C[int(w[h])]))
print(slots.most_common(20));print(names.most_common(40));print(ex)
print("spaces",len(Sp))
# gor files
gp=list((inp).rglob("*.gor_bxml"));print("gor unpacked",len(gp))
