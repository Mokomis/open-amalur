import json,pickle,struct,collections
from pathlib import Path
import numpy as np
root=Path.home()/"Documents/Opem Amalur";wc=root/"work/v20-char";z=root/"work/v22-stress/zone-dal"
grids=pickle.load(open(wc/"terrain-grids.pkl","rb"));abs_pos=pickle.load(open(wc/"terrain-abs.pkl","rb"));fit=json.loads((wc/"terrain-fit.json").read_text())
print("fit",fit,"grids",len(grids),"abs",len(abs_pos));n0=0;g=grids[n0];print("grid type",type(g),len(g),[type(x).__name__ for x in g],[(len(x) if hasattr(x,'__len__') else x) for x in g]);print(n0,abs_pos.get(n0))
print("level counts",collections.Counter(v[2] for v in abs_pos.values()))
rows=[]
for n,(x,y,w) in abs_pos.items():
    if not 0<=n<len(grids):continue
    v=np.array(grids[n][2],float);rows.append((n,x,y,w,v.min(),v.max(),np.median(v),(v>60000).mean(),len(v)))
R=np.array([r[1:] for r in rows]);print("no grid",len(abs_pos)-len(rows))
for w in sorted(set(R[:,2])):
    q=R[R[:,2]==w];print("w",w,"tiles",len(q),"min pct",np.percentile(q[:,3],[0,10,50,90,100]).round(),"max pct",np.percentile(q[:,4],[0,50,100]).round(),"sentinel frac mean",round(q[:,6].mean(),3),"all-sentinel",int((q[:,6]>.99).sum()))
H=np.load(z/"terrain_H.npy");v=H[H==H];print("H pct",np.percentile(v,[0,1,5,25,50,75,95,99,100]).round());h,e=np.histogram(v,bins=30);print([(round(e[i]),int(h[i])) for i in range(30) if h[i]])
b=(root/"work/v23-actors/index.bin").read_bytes();Ty,N=struct.unpack_from("<II",b,4);o=12+Ty*76;A=np.array([struct.unpack_from("<4f",b,o+i*20)[:3] for i in range(N)])
gx,gy=json.loads((z/"terrain_H.json").read_text());ii=((A[:,0]-gx)//100).astype(int);jj=((A[:,1]-gy)//100).astype(int);g=H[jj,ii];d=A[:,2]-g
bad=np.where(d<-1000)[0];print("far below",len(bad),"sample actor z",A[bad[:8],2].round(),"H",g[bad[:8]].round(),"xy",A[bad[:6],:2].round().tolist())
print("nan",int(np.isnan(g).sum()),"nan sample",A[np.isnan(g)][:5].round().tolist())
# Tiles covering nan points
level=collections.defaultdict(dict)
for n,(x,y,w) in abs_pos.items():level[w][(x,y)]=n
O=-102425.0
for p in list(A[np.isnan(g)][:3])+list(A[bad[:2]]):
    ux,uy=(p[0]-O)/50,(p[1]-O)/50;o2=[]
    for w in sorted(level):
        px,py=int(ux//w)*w,int(uy//w)*w;n=level[w].get((px,py))
        if n is None:o2.append((w,None));continue
        v=np.array(grids[n][2]) if 0<=n<len(grids) else None
        o2.append((w,n,None if v is None else (int(v.min()),int(v.max()),round(float((v>60000).mean()),2))))
    print(p.round(),o2)
print("terrain files",sorted(p.name for p in wc.glob("terrain*")))
