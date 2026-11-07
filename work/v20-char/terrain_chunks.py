import collections,pickle
from pathlib import Path
import numpy as np
wc=Path.home()/"Documents/Opem Amalur/work/v20-char"
grids=pickle.load(open(wc/"terrain-grids.pkl","rb"));pos=pickle.load(open(wc/"terrain-abs.pkl","rb"))
print("sample grid head",grids[0][:2],grids[5000][:2])
by=collections.defaultdict(list)
for n,g in enumerate(grids):by[g[0]].append((g[1],n))
print("chunks",len(by),"sizes",collections.Counter(len(v) for v in by.values()).most_common(8))
ks=sorted(by);print("chunk key range",ks[0],ks[-1],sorted({k[0] for k in ks})[:20],sorted({k[1] for k in ks})[:20])
for k in ks[200:205]:
    print(k,[(i,pos.get(n)) for i,n in sorted(by[k])][:10])
un=[n for n in range(len(grids)) if n not in pos]
c=collections.Counter(grids[n][0] for n in un);print("chunks with unplaced",len(c),c.most_common(14))
# Per chunk: placed share, level
full=[k for k in by if all(n in pos for _,n in by[k])];print("fully placed chunks",len(full))
rows=[]
for k in full:
    P=[pos[n] for _,n in by[k]];ws=set(p[2] for p in P)
    if len(ws)==1:
        x=min(p[0] for p in P);y=min(p[1] for p in P);rows.append((k[0],k[1],x,y,ws.pop()))
R=np.array(rows);print("single-level chunks",len(R))
for w in sorted(set(R[:,4])):
    q=R[R[:,4]==w];A=np.c_[q[:,:2],np.ones(len(q))];cx=np.linalg.lstsq(A,q[:,2],rcond=None)[0];cy=np.linalg.lstsq(A,q[:,3],rcond=None)[0];print("w",w,len(q),"x fit",cx.round(3),"resid",np.abs(A@cx-q[:,2]).max().round(1),"y fit",cy.round(3),"resid",np.abs(A@cy-q[:,3]).max().round(1),"sample",q[:3].tolist())
idx=pickle.load(open(wc/"terrain-index.pkl","rb"));print("index",len(idx),list(idx.items())[:3],"keys share",len(set(idx)&set(by)))
print("unindexed in grid? ",len(set(by)-set(idx)),"indexed no grids",len(set(idx)-set(by)),list(set(idx)-set(by))[:12])
