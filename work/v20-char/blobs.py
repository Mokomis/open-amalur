import json
from pathlib import Path
import numpy as np
from scipy import ndimage as ni
root=Path.home()/"Documents/Opem Amalur";z=root/"work/v22-stress/zone-dal"
H=np.load(z/"terrain_H.npy");gx,gy=json.loads((z/"terrain_H.json").read_text());ny,nx=H.shape
pos=np.asarray(np.load(z/"zone_pos.npy",mmap_mode="r"))
S=8
g=np.zeros((ny//S+1,nx//S+1),bool)
i=((pos[:,0]-gx)/(100*S)).astype(int);j=((pos[:,1]-gy)/(100*S)).astype(int);k=(i>=0)&(j>=0)&(i<g.shape[1])&(j<g.shape[0]);g[j[k],i[k]]=True
print("cells covered",g.sum(),"of",g.size)
# enclosed holes only: not connected to the outside
lab,n=ni.label(~g);edge=set(lab[0])|set(lab[-1])|set(lab[:,0])|set(lab[:,-1])
sizes=ni.sum(~g,lab,range(1,n+1));print("empty blobs",n)
rows=[]
for l,s in enumerate(sizes,1):
    if l in edge: continue
    ys,xs=np.where(lab==l)
    cx=gx+xs.mean()*800+400;cy=gy+ys.mean()*800+400
    vh=H[(ys*S).clip(0,ny-1),(xs*S).clip(0,nx-1)];vh=vh[vh==vh]
    rows.append((int(s),round(cx),round(cy),round(float(vh.mean())) if len(vh) else None,len(vh)))
rows.sort(reverse=True);print("enclosed",len(rows),"cells",sum(r[0] for r in rows));print(rows[:12])
