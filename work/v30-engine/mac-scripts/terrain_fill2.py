"""Recover terrain the first stitch lost: chunks it never read, then tiles it never placed. Position comes from the chunk header; shared edges confirm it."""
import collections,pickle,shutil,struct,zlib
from pathlib import Path
import numpy as np
root=Path.home()/"Documents/Opem Amalur";wc=root/"work/v20-char"
s=(root/"work/v20-inputs/DATA_0.pak/431658.terrain_streamable_bin").read_bytes()
idx=pickle.load(open(wc/"terrain-index.pkl","rb"));grids=pickle.load(open(wc/"terrain-grids.pkl","rb"));pos=pickle.load(open(wc/"terrain-abs.pkl","rb"))
for p in ("terrain-grids.pkl","terrain-abs.pkl"):
    if not (wc/(p+".before-recovery")).exists():shutil.copy(wc/p,wc/(p+".before-recovery"))
M=struct.pack("<I",361)
def tiles(d):
    o=0;out=[]
    while True:
        o=d.find(M,o)
        if o<0 or o+4+722>len(d):break
        if d[o+726:o+730]==M:out.append(struct.unpack_from("<361H",d,o+4));o+=726+365
        else:o+=1
    return out
head={};have={g[0] for g in grids};added=0
for key,(at,comp) in idx.items():
    d=zlib.decompress(s[at:at+comp]);head[key]=struct.unpack_from("<I8H",d,0)
    if key in have:continue
    T=tiles(d);print("read",key,"declares",head[key][0],"found",len(T))
    for i,v in enumerate(T):grids.append((key,i,v));added+=1
print("tiles recovered from unread chunks",added,"total",len(grids))
sg=lambda n:(lambda a:a-65536*(a>=32768))(np.array(grids[n][2],np.int32)).reshape(19,19)
V={n:sg(n) for n in range(len(grids))}
L=collections.defaultdict(dict)
for n,(x,y,w) in pos.items():L[w][(x,y)]=n
def agrees(n,x,y,w):
    """Number of shared edges that match, and number that differ."""
    good=bad=0;g=V[n]
    for (dx,dy,a,b) in ((w,0,lambda q:q[:,16:],lambda q:q[:,:3]),(-w,0,lambda q:q[:,:3],lambda q:q[:,16:]),(0,w,lambda q:q[16:,:],lambda q:q[:3,:]),(0,-w,lambda q:q[:3,:],lambda q:q[16:,:])):
        o=L[w].get((x+dx,y+dy))
        if o is None:continue
        e=np.abs(a(g)-b(V[o])).mean()
        if e<=1.0:good+=1
        else:bad+=1
    return good,bad
un=[n for n in range(len(grids)) if n not in pos]
print("unplaced before",len(un))
rule=check=0
counts=collections.Counter(g[0] for g in grids)
# Full chunks: four across, four down, from the chunk's own corner and width.
for n in list(un):
    key,i,_=grids[n]
    if head[key][0]!=16 or counts[key]!=16:continue
    w=head[key][2]-head[key][1];x,y=key[0]+(i%4)*w,key[1]+(i//4)*w
    if (x,y) in L[w]:continue
    L[w][(x,y)]=n;pos[n]=(x,y,w);un.remove(n);rule+=1
print("placed from chunk header",rule)
# Partial chunks: try every free slot in the chunk's square, keep one whose edges all match.
moved=1;passes=0
while moved:
    moved=0;passes+=1
    for n in list(un):
        key,i,_=grids[n];w=head[key][2]-head[key][1]
        if w<=0:continue
        best=None
        for ty in range(4):
            for tx in range(4):
                x,y=key[0]+tx*w,key[1]+ty*w
                if (x,y) in L[w]:continue
                g,b=agrees(n,x,y,w)
                if b==0 and g>0 and (best is None or g>best[0]):best=(g,x,y)
        if best:
            L[w][(best[1],best[2])]=n;pos[n]=(best[1],best[2],w);un.remove(n);moved+=1
    print("edge pass",passes,"placed",moved,"left",len(un),flush=True)
# Whatever is left in a partial chunk takes its row order: most are sea or empty edges of the map.
for n in list(un):
    key,i,_=grids[n];w=head[key][2]-head[key][1]
    if w<=0:continue
    x,y=key[0]+(i%4)*w,key[1]+(i//4)*w
    if (x,y) not in L[w] and agrees(n,x,y,w)[1]==0:
        L[w][(x,y)]=n;pos[n]=(x,y,w);un.remove(n)
print("left unplaced",len(un),"sample",[grids[n][:2] for n in un[:8]],collections.Counter(int(V[n].max()-V[n].min()<4) for n in un))
errs=collections.Counter()
for w,T in L.items():
    for (x,y),n in T.items():
        for dx,dy,a,b in ((w,0,V[n][:,16:],None),(0,w,V[n][16:,:],None)):
            o=T.get((x+dx,y+dy))
            if o is None:continue
            e=np.abs(a-(V[o][:,:3] if dx else V[o][:3,:])).mean();errs["match" if e<=1 else "mismatch"]+=1
print("all shared edges",errs)
pickle.dump(grids,open(wc/"terrain-grids.pkl","wb"));pickle.dump(pos,open(wc/"terrain-abs.pkl","wb"));print("written",len(grids),len(pos),"zero-ish tiles?",collections.Counter(p[2] for p in pos.values()))
