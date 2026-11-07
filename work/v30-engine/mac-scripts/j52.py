import json,re,struct,collections
from pathlib import Path
src=(Path.home()/"Documents/Opem Amalur/work/v20-char/build_npcs.py").read_text()
exec(src[:src.index("SKELS = {}")])
out=open(root/"work/v20-char/j52.txt","w",encoding="utf-8");P=lambda *a:print(*a,file=out,flush=True)
A={str(v):int(k) for k,v in syms["animation"].items()}
J=lambda n:(lambda f:struct.unpack_from("<H",f.read_bytes(),8+0xe)[0] if f else None)(extract([f"{A[n]}.anm_bxml"]).get(f"{A[n]}.anm_bxml"))
names=["human_idle_01","human_walk_01","human_run_01","human_sword_idle_01","human_sword_attack_x_01","human_sword_attack_x_02","human_sword_attack_xx_01","human_sword_attack_xx_02","human_sword_attack_xxx_01","human_sword_attack_xxx_02","human_sword_attack_xxxx_01","human_sword_attack_xxxx_02","human_norreacfrt","human_Death_01","human_sword_attack_special","human_sword_attack_dash","human_sword_putaway_01"]
P({n:J(n) for n in names})
# every fab with an '_skel' name: joints
fabs={str(v).lower():int(k) for k,v in syms["fab"].items()}
rows=[]
for n,k in fabs.items():
    if "skel" in n:
        f=extract([f"{k}.fab_bxml"]).get(f"{k}.fab_bxml")
        if f:
            try:rows.append((n,k,skeleton(f.read_bytes())[0]))
            except Exception as e:rows.append((n,k,"err"))
P(rows)
# Which simtype/fab uses player; bundle of 'player' simtype
mapn=syms.get("ragdoll_bone_mappings",{});nm=lambda v:str(mapn.get(str(v),v))
_,par,nmz,_w=skeleton((inp/"patch_0.pak/456813.fab_bxml").read_bytes());P("rig",[(i,nm(n)) for i,n in enumerate(nmz)])
print("ok")
sim=[(k,v) for k,v in syms["simtype"].items() if re.fullmatch(r"player\w*",str(v),re.I)][:8];P("player simtypes",sim)
for k,v in sim[:3]:
    b=extract([f"{k}.bundle"]).get(f"{k}.bundle")
    if b:
        d=b.read_bytes();ids=list(dict.fromkeys(struct.unpack_from(f"<{(len(d)-16)//4}I",d,16)));P(v,"fabs",[(i,syms["fab"].get(str(i))) for i in ids if str(i) in syms["fab"]][:14],"rag",[syms["ragdoll"][str(i)] for i in ids if str(i) in syms["ragdoll"]])
out.close()
