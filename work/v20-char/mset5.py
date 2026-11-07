import json,re,struct
from pathlib import Path
src=(Path.home()/"Documents/Opem Amalur/work/v20-char/build_npcs.py").read_text()
exec(src[:src.index("SKELS = {}")])
A={int(k):str(v) for k,v in syms["animation"].items()}
M={int(k):str(v) for k,v in syms["motionset"].items()}
print([v for v in M.values() if v.lower().startswith("player")])
for name in ("Player","Player_Weapon_Sword"):
    k=next(i for i,v in M.items() if v==name);n=f"{k}.mtns_bxml";b=extract([n])[n].read_bytes()
    seen=[]
    for o in range(0,len(b)-3):
        w=struct.unpack_from("<I",b,o)[0]
        if w in A and A[w] not in seen: seen.append(A[w])
    print(name,len(b),len(seen))
    print([x for x in seen if not x.lower().endswith("_f")])
