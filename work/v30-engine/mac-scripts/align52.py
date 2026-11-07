import json,struct
from pathlib import Path
import numpy as np
src=(Path.home()/"Documents/Opem Amalur/work/v20-char/build_npcs.py").read_text()
exec(src[:src.index("SKELS = {}")])
A={str(v):int(k) for k,v in syms["animation"].items()};mapn=syms.get("ragdoll_bone_mappings",{});nm=lambda v:str(mapn.get(str(v),v))
fb=(inp/"patch_0.pak/456813.fab_bxml").read_bytes();J=struct.unpack_from("<H",fb,4+0x10)[0];pose=4+0x18+struct.unpack_from("<i",fb,4+0x18)[0];par=struct.unpack_from(f"<{J}H",fb,4+0x1c+struct.unpack_from("<I",fb,4+0x1c)[0]);names=struct.unpack_from(f"<{J}I",fb,4+0x20+struct.unpack_from("<I",fb,4+0x20)[0])
R=np.array([struct.unpack_from("<12f",fb,pose+i*48)[4:7] for i in range(J)])
def rows(n):
    i=A[n];p=wc/f"baked/{i}.bin";b=p.read_bytes();j,fr,fps=struct.unpack_from("<IIf",b);a=np.frombuffer(b,"<f4",fr*j*12,12).reshape(fr,j,12);cj=struct.unpack_from("<H",(inp/f"initial_0.pak/{i}.anm_bxml").read_bytes(),8+0xe)[0];return a,cj
for n in ("human_sword_attack_x_01","human_sword_attack_xxx_01","human_sword_attack_xxxx_01"):
    a,cj=rows(n);T=a[:,:cj,4:7]
    fixed=T.std(0).max(1);M=T.mean(0)
    # Order-preserving alignment of the clip's joints onto the rig's.
    INF=1e18;D=np.full((cj+1,J+1),INF);D[0,:]=0;B={}
    for c in range(1,cj+1):
        for r in range(c,J+1):
            s=D[c,r-1];d=D[c-1,r-1]+float(np.linalg.norm(M[c-1]-R[r-1])) if fixed[c-1]<1 else D[c-1,r-1]
            if d<=s:D[c,r]=d;B[c,r]=1
            else:D[c,r]=s;B[c,r]=0
    c,r=cj,J;m={}
    while c>0:
        if B[c,r]:m[c-1]=r-1;c-=1;r-=1
        else:r-=1
    print(n,"clip joints",cj,"total error",round(float(D[cj,J]),2),"worst",round(max(float(np.linalg.norm(M[k]-R[v])) for k,v in m.items() if fixed[k]<1),2))
    print(" clip->rig",[(k,v) for k,v in m.items()]);print(" rig joints absent",[(i,nm(names[i])) for i in range(J) if i not in m.values()])
