import collections,json,re,struct
from pathlib import Path
import numpy as np
src=(Path.home()/"Documents/Opem Amalur/work/v20-char/build_npcs.py").read_text()
exec(src[:src.index("SKELS = {}")])
out=open(root/"work/v20-char/water2.txt","w",encoding="utf-8");P=lambda *a:print(*a,file=out,flush=True)
ids={}
for c,mp in syms.items():
    if isinstance(mp,dict):
        for k,nm in mp.items():ids.setdefault(int(k),f"{c}:{nm}")
sh={int(k):str(v) for k,v in syms["shader"].items()}
z=root/"work/v22-stress/zone-dal";M=json.loads((z/"zone_materials.json").read_text())["materials"];T=np.asarray(np.load(z/"zone_tex.npy",mmap_mode="r"));cnt=np.bincount(T,minlength=len(M))
ds={}
for i,m in enumerate(M):
    d=m["d"][0] if isinstance(m["d"],list) else m["d"];ds.setdefault(int(d) if d else 0,[]).append(i)
tn=lambda t:str(syms["texture"].get(str(t),""))
hits=[]
for k,n in syms["material"].items():
    if re.search(r"^(for|gen|fae|dal|riv|water|river|ocean|pond)|water|river|pond|fall",str(n),re.I):
        f=(inp/"initial_0.pak"/f"{k}.mat_bxml")
        if not f.exists():
            f=extract([f"{k}.mat_bxml"]).get(f"{k}.mat_bxml")
        if not f:continue
        b=f.read_bytes()
        if len(b)<40:continue
        s=sh.get(struct.unpack_from("<I",b,24)[0],"")
        if re.search("water|river",s,re.I):
            refs=material_refs(int(k));zm=[i for t,_ in refs for i in ds.get(t,[])]
            hits.append((str(n),s,[r[1] for r in refs],sorted(set(zm)),[int(cnt[i]) for i in sorted(set(zm))]));P(hits[-1])
P("in zone",[h for h in hits if h[3]])
for sn in ("river","rivernopointlights","scrollingwaterfall"):
    k=next(k for k,v in sh.items() if v==sn);b=extract([f"{k}.shader_bxml"])[f"{k}.shader_bxml"].read_bytes();P(sn,len(b),list(dict.fromkeys(ids[v] for o in range(0,len(b)-3,4) for v in [struct.unpack_from("<I",b,o)[0]] if v>1000 and v in ids)))
idx=json.load(open(root/"outputs/scene-v19/shader-index.json"));D=root/"outputs/scene-v19/shaders"
for k,v in idx.items():
    t=open(D/(k+".asm"),encoding="latin1").read();h=t[:t.find("ps_")] if v["type"]=="ps" else t[:t.find("vs_")]
    if re.search(r"Scroll|Tile|Refract|Foam|Murk|Fresnel|FlowMap|_E_\w*Water|Water\w*_sampler",h) and v["type"]=="ps" and re.search(r"River|Water|Scroll|Foam|Murk|Refraction",h):
        mats=re.findall(r"float\d?\s+(\w+);\s+// Offset",h[:h.find('g_globalbuffer') if 'g_globalbuffer' in h else None]);res=re.findall(r"// (\w+)\s+texture|// (g_\w+)\s+sampler",h)
        P(k,v["lines"],sorted(v["cbuffers"]),"mat",mats[:24],"res",[a or b for a,b in res][:8])
out.close()
