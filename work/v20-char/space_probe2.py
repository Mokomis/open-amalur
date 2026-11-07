import json,re,struct,collections
from pathlib import Path
import numpy as np
src=(Path.home()/"Documents/Opem Amalur/work/v20-char/build_npcs.py").read_text()
exec(src[:src.index("SKELS = {}")])
ALL={}
for k,d in syms.items():
    if isinstance(d,dict) and k not in("main","main64"):
        for i,v in d.items():
            try: ALL.setdefault(int(i),(k,str(v)))
            except: pass
Sp=sorted((int(k),str(v)) for k,v in syms["simspace"].items() if re.match(r"out_dal_(north|south|west|east|central|tran|[a-z0-9])",str(v)))
sam=collections.defaultdict(list);hit=collections.Counter();mat=collections.Counter();rad=collections.defaultdict(list)
for sid,sn in Sp:
    f=extract([f"{sid}.space_bxml"]).get(f"{sid}.space_bxml")
    if f is None: continue
    d=f.read_bytes();pl=struct.unpack_from("<I",d,0)[0];b=d[8:8+pl]
    def arr(slot,st):
        p,c=struct.unpack_from("<II",b,slot);return [b[p-8+i*st:p-8+(i+1)*st] for i in range(c)]
    refs=[struct.unpack("<I",r)[0] for r in arr(0x1b0,4)];cen=[struct.unpack("<3f",r) for r in arr(0x1a8,12)]
    rend=arr(0x160,84);bc={tuple(round(x,2) for x in struct.unpack_from("<3f",r)):r for r in rend}
    for t,c in zip(refs,cen):
        k=t>>28;r=bc[tuple(round(x,2) for x in c)];low=t&0xfffffff
        rad[k].append(struct.unpack_from("<f",r,12)[0])
        if k!=15:
            hit[(k,"full",ALL.get(t,("none",))[0])]+=1;hit[(k,"low",ALL.get(low,("none",))[0])]+=1
            m=struct.unpack_from("<I",r,64)[0];mat[(k,syms["material"].get(str(m),"?"))]+=1
            if len(sam[k])<6:sam[k].append((hex(t),ALL.get(t),ALL.get(low),struct.unpack_from("<II",r,64),[round(x) for x in c],round(struct.unpack_from("<f",r,12)[0])))
print(hit.most_common(20))
for k,v in sam.items():print(k,v)
print({k:(len(v),round(float(np.median(v))),round(float(np.max(v)))) for k,v in rad.items()})
print(mat.most_common(30))
