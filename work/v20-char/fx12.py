import json,re,struct,collections,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from fx_common import *
src=(root/"work/v20-char/build_npcs.py").read_text()
exec(src[:src.index("SKELS = {}")])
C={int(k):str(v) for k,v in syms["cluster"].items()};T={int(k):str(v) for k,v in syms["task"].items()};Mat={int(k):str(v) for k,v in syms["material"].items()}
rec=load_tasks();print("tasks",len(rec))
Sp=sorted((int(k),str(v)) for k,v in syms["simspace"].items() if re.match(r"out_dal_",str(v)))
d=extract([f"{Sp[0][0]}.space_bxml"])[f"{Sp[0][0]}.space_bxml"].read_bytes();pl=struct.unpack_from("<I",d,0)[0];b=d[8:8+pl]
p,c=struct.unpack_from("<II",b,0xd0);print("0xd0",p,c)
for i in range(3):
    r=b[p-8+i*60:p-8+(i+1)*60];print([round(x,2) for x in struct.unpack_from("<13f",r)],struct.unpack_from("<15I",r)[9:],C.get(struct.unpack_from("<I",r,52)[0]))
for nm in ("Fire_Small_01_Torch","Ambient-Godray_Medium_02","Magic_Spore_Volume_Light_White_01","Vil_Lamp_Glow_01","Leaves-Falling01_Green","Waterfall_Mist_01","Ambient_Moth_01"):
    k=next(i for i,v in C.items() if v==nm);n=f"{k}.fxcluster_bxml";q=extract([n])[n].read_bytes();kids,o=cluster(q);print("==",nm,len(q),"tail",[round(x,1) for x in struct.unpack_from(f"<{(len(q)-o)//4}f",q,o)][:8],[(hex(a),T.get(x,x),T.get(y,y)) for a,x,y in kids][:4])
    for a,x,y in kids[:2]:
        if a!=0x6ed2b0:continue
        ch=channels(rec[x]);ph=channels(rec[y]) if y in rec else {}
        print(" emit",{hex(m):[round(v,2) if abs(v)<1e5 else None for v in struct.unpack_from(f"<{min(len(p_)//4,6)}f",p_)] if c_!=0x132c1a2 else struct.unpack_from("<3I",p_) for m,(c_,p_) in ch.items() if c_!=0xb40224})
        for m,(c_,p_) in ph.items():
            W=struct.unpack_from(f"<{len(p_)//4}I",p_)
            if c_==0xcab781:print("  mat",Mat.get(W[0]))
            F=[round(v,3) if abs(v)<1e5 and (abs(v)>1e-4 or v==0) else hex(w) for v,w in zip(struct.unpack_from(f"<{len(p_)//4}f",p_),W)]
            print("  ",hex(c_),hex(m),len(p_),F[:44])
