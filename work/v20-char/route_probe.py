import json,struct
from pathlib import Path
import numpy as np
root=Path.home()/"Documents/Opem Amalur";z=root/"work/v22-stress/zone-dal";A=root/"work/v23-actors/index.bin"
H=np.load(z/"terrain_H.npy");gx,gy=json.loads((z/"terrain_H.json").read_text())
print("H",H.shape,"origin",gx,gy,"valid",round(float(np.mean(H==H)),3))
col=root/"work/v22-stress/live-pack"
names={p.name for p in col.glob("*.bin")}
print("collision-like files",[n for n in sorted(names) if not n.startswith(("c","g","t"))][:10],len([n for n in names if n.startswith("c")]))
b=A.read_bytes();T,N=struct.unpack_from("<II",b,4);ts=[struct.unpack_from("<9f3iI24s",b,12+i*76) for i in range(T)];o=12+T*76
acts=[(struct.unpack_from("<4f",b,o+i*20),struct.unpack_from("<HH",b,o+i*20+16)[0]) for i in range(N)]
H0=lambda x,y:(lambda i,j:H[j,i] if 0<=j<H.shape[0] and 0<=i<H.shape[1] else np.nan)(int((x-gx)//100),int((y-gy)//100))
xy=np.array([a[0][:3] for a in acts]);kinds=np.array([ts[a[1]][12] for a in acts])
g=np.array([H0(*p[:2]) for p in xy]);print("actors",N,"terrain missing under",int(np.isnan(g).sum()),"home below terrain >1m",int(np.nansum(xy[:,2]<g-100)),"above >3m",int(np.nansum(xy[:,2]>g+300)))
d=xy[:,2]-g;print("home-terrain pct",np.nanpercentile(d,[1,10,50,90,99]).round(0))
# Simulate the route.
door=np.array([1575.,-62759.,5152.]);seen=np.zeros(N,bool);pos=door.copy();host=kinds==2;miss=tot=0;segs=[];under=0
while True:
    seen|=((xy[:,0]-pos[0])**2+(xy[:,1]-pos[1])**2)<3500**2
    c=np.where(host&~seen)[0]
    if not len(c):break
    t=c[np.argmin(((xy[c,:2]-pos[:2])**2).sum(1))];L=np.linalg.norm(xy[t,:2]-pos[:2]);n=max(2,int(L/200))
    for f in np.linspace(0,1,n):
        q=pos*(1-f)+xy[t]*f;h=H0(q[0],q[1]);tot+=1
        if h!=h:miss+=1
        elif q[2]<h-100:under+=1
    segs.append((round(L),));pos=xy[t].copy()
print("route stops",len(segs),"length km",round(sum(s[0] for s in segs)/1e5,1),"samples",tot,"no terrain",miss,"straight line below terrain",under)
