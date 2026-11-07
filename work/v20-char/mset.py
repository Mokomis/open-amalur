import json,re,struct
from pathlib import Path
src=(Path.home()/"Documents/Opem Amalur/work/v20-char/build_npcs.py").read_text()
exec(src[:src.index("SKELS = {}")])
out=open(root/"work/v20-char/mset.txt","w",encoding="utf-8")
def P(*a):print(*a,file=out,flush=True)
A={int(k):str(v) for k,v in syms["animation"].items()}
for c in (673754,673863,673928,673833,1893691,673835,673903,1926549):P("current clip",c,A.get(c))
for name in ("Player","Player_Weapon_Sword","Player_Shield_None","Player_F"):
    k=next((int(i) for i,v in syms["motionset"].items() if str(v)==name),None);exts=[x for L in listing.values() for x in L if x.startswith(f"{k}.")];P("==",name,k,exts)
    for n in exts:
        f=extract([n]).get(n)
        if not f:continue
        b=f.read_bytes();cl=[A[w] for o in range(0,len(b)-3,4) for w in [struct.unpack_from("<I",b,o)[0]] if w in A]
        P(n,len(b),"clips",len(cl));P([c for c in cl if re.search(r"idle|walk|run|jog|sprint|start|stop|turn|look|head",c,re.I)][:110])
sc=(root/"work/v20-char/build_character.py").read_text().splitlines()
for i,l in enumerate(sc):
    if "HEADS" in l or "PARTS" in l or "character.bin" in l or "majestic" in l:P(i+1,l[:220])
j=next(i for i,l in enumerate(sc) if l.startswith("for hid in HEADS"))
P("\n".join(f"{i+1}: {sc[i][:220]}" for i in range(j-2,j+14)))
out.close()
