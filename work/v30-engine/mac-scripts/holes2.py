import collections,json,pickle,struct
from pathlib import Path
import numpy as np
root=Path.home()/"Documents/Opem Amalur";wc=root/"work/v20-char";z=root/"work/v22-stress/zone-dal"
out=open(wc/"holes2.txt","w",encoding="utf-8");P=lambda *a:print(*a,file=out,flush=True)
grids=pickle.load(open(wc/"terrain-grids.pkl","rb"));pos=pickle.load(open(wc/"terrain-abs.pkl","rb"));before=pickle.load(open(wc/"terrain-abs.pkl.before-recovery","rb")) if (wc/"terrain-abs.pkl.before-recovery").exists() else None
level=collections.defaultdict(dict)
for n,(x,y,w) in pos.items():level[w][(x,y)]=n
O=-102425.0
H=np.load(z/"terrain_H.npy");gx,gy=json.loads((z/"terrain_H.json").read_text())
def why(wx,wy):
    ux,uy=(wx-O)/50,(wy-O)/50;r=[]
    for w in sorted(level):
        px,py=int(ux//w)*w,int(uy//w)*w;n=level[w].get((px,py))
        if n is None:r.append((w,"none"));continue
        v=grids[n][2];fx,fy=(ux-px)*16/w+1,(uy-py)*16/w+1;ix,iy=int(fx),int(fy);q=(v[iy*19+ix],v[iy*19+ix+1],v[(iy+1)*19+ix],v[(iy+1)*19+ix+1]);r.append((w,"HOLE" if 65535 in q else "ok",q[0]))
    return r
for c in ((-13470,-8939),(-11000,-8000),(-15000,-7000),(-9000,-10000)):P(c,"H",H[int((c[1]-gy)//100),int((c[0]-gx)//100)],why(*c))
nan=np.isnan(H);P("valid frac",1-nan.mean())
# Causes over all empty cells inside the zone's rough interior.
c=collections.Counter();ex={}
ys,xs=np.where(nan)
rng=np.random.default_rng(1);idx=rng.choice(len(ys),min(40000,len(ys)),replace=False)
for i in idx:
    wx,wy=gx+xs[i]*100,gy+ys[i]*100;r=why(wx,wy);k="tile marked hole" if any(a[1]=="HOLE" for a in r) else "no tile at any level";c[k]+=1
P("empty cells",int(nan.sum()),"sample causes",c.most_common())
g65=sum(1 for g in grids if 65535 in g[2]);P("tiles with 65535",g65,"of",len(grids))
u=[n for n in range(len(grids)) if n not in pos];P("unplaced",len(u))
s=collections.Counter()
for g in grids:
    v=np.array(g[2]);s[round(float((v==65535).mean()),1)]+=1
P("hole fraction per tile",sorted(s.items()))
# Is anything drawn below where the hole is?  Triangles of any material whose centre lies in 60 m around the first spot.
Pp=np.load(z/"zone_pos.npy",mmap_mode="r");T=np.asarray(np.load(z/"zone_tex.npy",mmap_mode="r"));p=np.asarray(Pp).reshape(-1,3,3);cc=p.mean(1);M=json.loads((z/"zone_materials.json").read_text())["materials"];sy=json.loads((root/"work/v20-inputs/symbols.json").read_text())
near=(np.abs(cc[:,0]+13000)<2500)&(np.abs(cc[:,1]+9000)<2500);ct=collections.Counter(T[near].tolist());nm=lambda i:(lambda d:sy["texture"].get(str(d[0] if isinstance(d,list) else d),"?"))(M[i]["d"])
P("near spot",[(nm(i),n,round(float(cc[near&(T==i),2].min())),round(float(cc[near&(T==i),2].max()))) for i,n in ct.most_common(14)])
out.close()
