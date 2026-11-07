"""Prints where the zone's water and webs are, for looking at them."""
import json
from pathlib import Path
import numpy as np
root=Path.home()/"Documents/Opem Amalur";z=root/"work/v22-stress/zone-dal";s=json.loads((root/"work/v20-inputs/symbols.json").read_text())
M=json.loads((z/"zone_materials.json").read_text())["materials"];T=np.asarray(np.load(z/"zone_tex.npy",mmap_mode="r"));P=np.load(z/"zone_pos.npy",mmap_mode="r");P=np.asarray(P).reshape(-1,3,3);H=np.load(z/"terrain_H.npy");gx,gy=json.loads((z/"terrain_H.json").read_text())
for i,m in enumerate(M):
    if m.get("kind"):
        q=np.where(T==i)[0]
        if not len(q):continue
        c=P[q].mean(1);mid=np.median(c,axis=0);k=np.argmin(((c-mid)**2).sum(1));pt=c[k]
        print("WATERSPOT",m["kind"],s["texture"].get(str(m["d"])),"tris",len(q),"at",np.round(pt).tolist(),"p",[round(x,3) for x in (m.get("p") or [])])
