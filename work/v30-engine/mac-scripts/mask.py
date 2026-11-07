import collections,json,pickle,struct,zlib
from pathlib import Path
import numpy as np
root=Path.home()/"Documents/Opem Amalur";wc=root/"work/v20-char";z=root/"work/v22-stress/zone-dal"
out=open(wc/"mask.txt","w",encoding="utf-8");P=lambda *a:print(*a,file=out,flush=True)
s=(root/"work/v20-inputs/DATA_0.pak/431658.terrain_streamable_bin").read_bytes();idx=pickle.load(open(wc/"terrain-index.pkl","rb"));grids=pickle.load(open(wc/"terrain-grids.pkl","rb"));pos=pickle.load(open(wc/"terrain-abs.pkl","rb"))
M=struct.pack("<I",361)
def parse(key):
    at,comp=idx[key];d=zlib.decompress(s[at:at+comp]);o=0;T=[]
    while True:
        o=d.find(M,o)
        if o<0 or o+730>len(d):break
        if d[o+726:o+730]==M:
            m=d[o+730:o+730+361];nx=d.find(M,o+726+365);T.append((struct.unpack_from("<361H",d,o+4),m,d[o+726+365:nx] if nx>0 else d[o+726+365:o+726+365+64]));o+=726+365
        else:o+=1
    return d,T
fit=json.loads((wc/"terrain-fit.json").read_text())
level=collections.defaultdict(dict)
for n,(x,y,w) in pos.items():level[w][(x,y)]=n
O=-102425.0
def tile(wx,wy):
    ux,uy=(wx-O)/50,(wy-O)/50
    for w in sorted(level):
        px,py=int(ux//w)*w,int(uy//w)*w;n=level[w].get((px,py))
        if n is not None:return n,w,px,py,(ux-px)*16/w+1,(uy-py)*16/w+1
n,w,px,py,fx,fy=tile(-13470,-8939);key,i,_=grids[n];d,T=parse(key);P("spot tile",n,"w",w,"key",key,"index",i,"count in chunk",len(T),"head",struct.unpack_from("<I8Hf",d,0));h,m,x=T[i]
np.set_printoptions(linewidth=170);P("heights z");P(((np.array(h,float)-65536*(np.array(h)>=32768))*fit["k"]+fit["z0"]).reshape(19,19).round().astype(int));P("mask");P(np.frombuffer(m,"u1").reshape(19,19));P("after",len(x),x[:80].hex());P("fx,fy",fx,fy)
# Overall mask values
c=collections.Counter();ks=list(idx)[:80];cc=collections.Counter()
for k in ks:
    _,T=parse(k)
    for _,m,x in T:c.update(m);cc[len(x)]+=1
P("mask value histogram",c.most_common(12));P("trailer sizes",cc.most_common(8))
# Compare actors: below terrain vs on it, the mask under them.
b=(root/"work/v23-actors/index.bin").read_bytes();Ty,Na=struct.unpack_from("<II",b,4);o=12+Ty*76;A=np.array([struct.unpack_from("<4f",b,o+i*20)[:3] for i in range(Na)])
cache={};rows=[]
for p in A:
    t=tile(p[0],p[1])
    if not t:continue
    n,w,px,py,fx,fy=t;key,i,_=grids[n]
    if key not in cache:cache[key]=parse(key)[1]
    Tt=cache[key]
    if i>=len(Tt):continue
    h,m,_=Tt[i];ix,iy=int(fx),int(fy);v=h[iy*19+ix];hv=(v-65536 if v>=32768 else v)*fit["k"]+fit["z0"];rows.append((p[2]-hv,m[iy*19+ix]))
R=np.array(rows);P("actors",len(R));
for lo,hi,lab in ((-1e9,-300,"3m+ below"),(-300,300,"on terrain"),(300,1e9,"above")):
    q=R[(R[:,0]>=lo)&(R[:,0]<hi)];P(lab,len(q),collections.Counter(q[:,1].astype(int).tolist()).most_common(8))
out.close()
