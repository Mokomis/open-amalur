import json,re,struct,collections
from pathlib import Path
import numpy as np
src=(Path.home()/"Documents/Opem Amalur/work/v20-char/build_npcs.py").read_text()
exec(src[:src.index("SKELS = {}")])
A={str(v):int(k) for k,v in syms["animation"].items()};mapn=syms.get("ragdoll_bone_mappings",{});nm=lambda v:str(mapn.get(str(v),v))
fb=(inp/"patch_0.pak/456813.fab_bxml").read_bytes();J,par,names,world=skeleton(fb);rigset=set(names)
J0=lambda n:(lambda f:struct.unpack_from("<H",f.read_bytes(),8+0xe)[0] if f else None)(extract([f"{A[n]}.anm_bxml"]).get(f"{A[n]}.anm_bxml"))
print({n:J0(n) for n in sorted(A) if re.match(r"human_sword_attack_(x|xx|xxx|xxxx)_0[12](_f)?$",n,re.I)})
print("other swings",{n:J0(n) for n in ("HM_OneHand_AttackX_01","HM_OneHand_AttackB_01","Human_OneHand_AttackX_01","Human_OneHand_AttackB_01","human_sword_attack_dash","human_sword_attack_hilt","human_sword_attack_special") if n in A})
a=(inp/f"initial_0.pak/{A['human_sword_attack_x_01']}.anm_bxml").read_bytes();size=struct.unpack_from("<I",a,4)[0];print("anm",len(a),size,a[8:72].hex())
hits=[(o,nm(struct.unpack_from("<I",a,o)[0])) for o in range(0,len(a)-3) if struct.unpack_from("<I",a,o)[0] in rigset];print("name hits",len(hits),hits[:30])
# Any fab with 52 joints: scan human-ish fabs from player bundles and whichever fab_bxml we hold.
rows=[]
for p in list((inp/"patch_0.pak").glob("*.fab_bxml"))+list((inp/"initial_0.pak").glob("*.fab_bxml"))+list((inp/"DATA_0.pak").glob("*.fab_bxml")):
    b=p.read_bytes()
    try:
        n=struct.unpack_from("<H",b,4+0x10)[0]
        if n==52:rows.append(p.name)
    except Exception:pass
print("52-joint fabs held",rows[:20])
sks=[k for k,v in syms["fab"].items() if re.search("skel|rig|human",str(v),re.I)]
ch=[]
for k in sks:
    f=extract([f"{k}.fab_bxml"]).get(f"{k}.fab_bxml")
    if f:
        b=f.read_bytes()
        if struct.unpack_from("<H",b,4+0x10)[0]==52:ch.append((k,syms["fab"][k]))
print("52 named",ch[:20])
# Bone vectors of the clip to identify each joint
i=A['human_sword_attack_x_01'];bb=(wc/f"baked/{i}.bin").read_bytes();j,fr,fps=struct.unpack_from("<IIf",bb);d=np.frombuffer(bb,"<f4",fr*j*12,12).reshape(fr,j,12)[:,:52,4:7]
M=d.mean(0);S=d.std(0).max(1);R=np.array([struct.unpack_from("<12f",fb,4+0x18+struct.unpack_from("<i",fb,4+0x18)[0]+k*48)[4:7] for k in range(J)])
np.set_printoptions(precision=1,suppress=True)
rig=[(k,nm(names[k]),R[k]) for k in range(J)]
for c in range(52):
    best=sorted(range(J),key=lambda r:np.linalg.norm(R[r]-M[c]))[:3];print(c,M[c],"std",round(float(S[c]),1),[(r,nm(names[r]),round(float(np.linalg.norm(R[r]-M[c])),1)) for r in best])
