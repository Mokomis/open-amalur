"""Place terrain patches the first stitch missed, by their overlap with placed neighbours, comparing heights as signed values."""
import collections,pickle,shutil,sys
from pathlib import Path
import numpy as np
wc=Path.home()/"Documents/Opem Amalur/work/v20-char"
grids=pickle.load(open(wc/"terrain-grids.pkl","rb"));pos=pickle.load(open(wc/"terrain-abs.pkl","rb"))
V=np.array([g[2] for g in grids],np.int32);V[V>=32768]-=65536;V=V.reshape(-1,19,19)
print("grids",len(V),"placed",len(pos),"flat",int((V.max((1,2))-V.min((1,2))<2).sum()))
# Is the overlap rule right?  a[r][16+c]==b[r][c] along x, a[16+c][r]==b[c][r] along y.
levels=collections.defaultdict(dict)
for n,(x,y,w) in pos.items():levels[w][(x,y)]=n
tests=collections.defaultdict(list)
for w,L in levels.items():
    for (x,y),n in L.items():
        if (x+w,y) in L:tests[w,"x"].append(np.abs(V[n][:,16:]-V[L[(x+w,y)]][:,:3]).mean())
        if (x,y+w) in L:tests[w,"y"].append(np.abs(V[n][16:,:]-V[L[(x,y+w)]][:3,:]).mean())
for k,v in sorted(tests.items()):print(k,len(v),"overlap err pct",np.percentile(v,[50,90,99]).round(2))
TOL=2.0
un=[n for n in range(len(V)) if n not in pos];print("unplaced",len(un),"duplicates of placed",0)
added=0
for it in range(40):
    moved=0
    for w,L in levels.items():
        keys=list(L);N=np.array([L[k] for k in keys])
        if not len(N):continue
        right,left,up,down=V[N][:,:,16:],V[N][:,:,:3],V[N][:,16:,:],V[N][:,:3,:]
        for n in list(un):
            g=V[n]
            if g.max()-g.min()<4:continue
            for strip,mine,dx,dy in ((right,g[:,:3],w,0),(left,g[:,16:],-w,0),(up,g[:3,:],0,w),(down,g[16:,:],0,-w)):
                e=np.abs(strip-mine).mean((1,2));hits=np.where(e<=TOL)[0]
                for h in hits:
                    slot=(keys[h][0]+dx,keys[h][1]+dy)
                    if slot in L:continue
                    L[slot]=n;pos[n]=(slot[0],slot[1],w);un.remove(n);moved+=1;break
                else:continue
                break
            else:continue
    added+=moved;print("pass",it,"placed",moved,"left",len(un),flush=True)
    if not moved:break
print("added",added,"left",len(un),collections.Counter(pos[n][2] for n in pos))
if len(sys.argv)>1 and sys.argv[1]=="write" and added:
    shutil.copy(wc/"terrain-abs.pkl",wc/"terrain-abs.before-fill.pkl");pickle.dump(pos,open(wc/"terrain-abs.pkl","wb"));print("written")
