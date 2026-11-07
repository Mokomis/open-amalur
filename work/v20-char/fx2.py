import json,re,struct,collections
from pathlib import Path
src=(Path.home()/"Documents/Opem Amalur/work/v20-char/build_npcs.py").read_text()
exec(src[:src.index("SKELS = {}")])
C={int(k):str(v) for k,v in syms["cluster"].items()}
print(len(C),[v for v in C.values() if re.search("impact|blood|hit|spark|torch|fire",v,re.I)][:50])
tex={int(k):str(v) for k,v in syms["texture"].items()}
mat={int(k):str(v) for k,v in syms["material"].items()}
fab={int(k):str(v) for k,v in syms.get("fab",{}).items()}
names=[v for v in C.values() if re.search("impact",v,re.I)][:3]+[v for v in C.values() if re.search("torch|campfire",v,re.I)][:2]
for nm in names:
    k=next(i for i,v in C.items() if v==nm);n=f"{k}.fxcluster_bxml";fs=extract([n])
    if n not in fs: print(nm,"no file");continue
    b=fs[n].read_bytes();print("==",nm,k,len(b),b[:8])
    W=struct.unpack_from(f"<{len(b)//4}I",b)
    refs=[(i*4,tex.get(w) or mat.get(w)) for i,w in enumerate(W) if w in tex or w in mat]
    print("refs",refs[:14])
    F=struct.unpack_from(f"<{len(b)//4}f",b)
    print("head",[hex(w) for w in W[:24]])
    print("floats",[round(x,3) for x in F[24:90] if 1e-4<abs(x)<1e6][:50])
    st=re.findall(rb"[A-Za-z_][A-Za-z0-9_ ]{4,}",b);print("str",st[:12])
