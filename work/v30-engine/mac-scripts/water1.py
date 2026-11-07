import collections,json,re,struct
from pathlib import Path
import numpy as np
src=(Path.home()/"Documents/Opem Amalur/work/v20-char/build_npcs.py").read_text()
exec(src[:src.index("SKELS = {}")])
out=open(root/"work/v20-char/water1.txt","w",encoding="utf-8");P=lambda *a:print(*a,file=out,flush=True)
sh={int(k):str(v) for k,v in syms["shader"].items()};P("shaders",[v for v in sh.values() if re.search("water|river|ocean|lake|fluid|refract",v,re.I)])
P("platform",[str(v) for v in syms["platform_shader"].values() if re.search("water|river|ocean|lake|fluid",str(v),re.I)][:30])
mats={int(k):str(v) for k,v in syms["material"].items() if re.search("water|river|ocean|lake|pond|stream|falls",str(v),re.I)};P("materials",len(mats),list(mats.values())[:60])
P("fabs",[str(v) for v in syms["fab"].values() if re.search("water|river|ocean|lake|pond|falls",str(v),re.I)][:40])
z=root/"work/v22-stress/zone-dal";M=json.loads((z/"zone_materials.json").read_text())["materials"];T=np.asarray(np.load(z/"zone_tex.npy",mmap_mode="r"));cnt=np.bincount(T,minlength=len(M));Pp=np.load(z/"zone_pos.npy",mmap_mode="r")
tn=lambda t:str(syms["texture"].get(str(t),""))
for i,m in enumerate(M):
    d=m["d"][0] if isinstance(m["d"],list) else m["d"]
    if re.search("water|river|ocean|lake|pond|falls|foam|wet",tn(d),re.I):
        q=np.where(T==i)[0];p=np.asarray(Pp)[np.repeat(q,3)*3+np.tile([0,1,2],len(q))] if len(q)<200000 else None
        P(i,tn(d),"tris",int(cnt[i]),"a",tn(m.get("a")),"n",tn(m.get("n")),"xyz",None if p is None or not len(p) else (p.min(0).round().tolist(),p.max(0).round().tolist()))
# Which zone gors/fabs use water: scan zone build log names
for mid,n in list(mats.items())[:60]:
    f=extract([f"{mid}.mat_bxml"]).get(f"{mid}.mat_bxml")
    if f:
        b=f.read_bytes()
        if len(b)>=40:
            s=sh.get(struct.unpack_from("<I",b,24)[0])
            if s and re.search("water",s,re.I):P("  ",n,s,[r[1] for r in material_refs(mid)][:8])
idx=json.load(open(root/"outputs/scene-v19/shader-index.json"))
w=[(v["lines"],k,v["type"],sorted(v["cbuffers"]),[x for x in v["vars"] if re.search("water|depth|flow|wave|scroll|refract|fres",x,re.I)][:14]) for k,v in idx.items() if any(re.search("water|Refract|flow",x,re.I) for x in v["vars"])]
w.sort();P("shaders naming water",len(w));[P(r) for r in w[:16]]
out.close()
