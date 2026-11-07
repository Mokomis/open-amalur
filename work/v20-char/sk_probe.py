import json,re,collections,struct
from pathlib import Path
source=(Path.home()/"Documents/Opem Amalur/work/v20-char/build_npcs.py").read_text()
exec(source[:source.index("SKELS = {}")])
r=json.loads((root/"work/v23-actors/report.json").read_text())
bad=[x for x in r["report"] if x[1]!="ok"]
print(collections.Counter((x[1],x[2] if len(x)>2 else "",x[3] if len(x)>3 else "") for x in bad).most_common(40))
sim={str(v):int(k) for k,v in syms["simtype"].items()}
fab={str(v).lower():int(k) for k,v in syms["fab"].items()}
for n in ("wolf_skel","boggart_skel","troll_skel","bear_skel","sprite_skel"):
    i=fab.get(n);print(n,i)
    if i:
        f=extract([f"{i}.fab_bxml"]).get(f"{i}.fab_bxml")
        if f:
            J,par,names,world=skeleton(f.read_bytes());print(" joints",J,"height",round(max(w[1][2] for w in world)))
for nm in ("giantspider_venomspitter","jottun_warrior"):
    i=sim[nm];d=extract([f"{i}.bundle"])[f"{i}.bundle"].read_bytes();ids=list(dict.fromkeys(struct.unpack_from(f"<{(len(d)-16)//4}I",d,16)))
    print(nm,[("ragdoll",syms["ragdoll"][str(v)]) for v in ids if str(v) in syms["ragdoll"]],[("fab",syms["fab"][str(v)]) for v in ids if str(v) in syms["fab"]],[v for v in ids if "fab_visual_data_streamable_bin" in files_by_id.get(v,[])],[ids_ for ids_ in ids if "bundle" in files_by_id.get(ids_,[])][:6])
print("skel names",[k for k in fab if k.endswith("_skel") or "vvs" in k][:50])
