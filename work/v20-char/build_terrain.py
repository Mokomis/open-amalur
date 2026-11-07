"""Any zone's terrain: reads every chunk, places tiles from chunk headers and shared edges, keeps masks, and fits height to the zone's spawn points.
Usage: build_terrain.py <terrain id> <zone prefix> <out dir>. Writes terrain-grids.pkl, terrain-abs.pkl, terrain-masks.pkl, terrain-fit.json."""
import collections,json,pickle,re,struct,sys,zlib
from pathlib import Path
import numpy as np
src=(Path.home()/"Documents/Opem Amalur/work/v20-char/build_npcs.py").read_text()
TID,PRE,DIR=sys.argv[1],sys.argv[2],Path(sys.argv[3]);DIR.mkdir(parents=True,exist_ok=True)
exec(src[:src.index("SKELS = {}")])
log=lambda *a:print(*a,flush=True)
name=f"{TID}.terrain_streamable_bin";s=extract([name])[name].read_bytes();log("file MB",round(len(s)/1e6,1))
records=[];i=0
while True:
    i=s.find(b"\x78\x9c",i)
    if i<0:break
    if i>=24:
        raw,total,zero,raw2,comp=struct.unpack_from("<5I",s,i-20)
        if raw==raw2 and zero==0 and comp<=total<=comp+32 and i+comp<=len(s):
            records.append((i,raw,comp));i+=comp;continue
    i+=1
M=struct.pack("<I",361);chunks={}
for at,raw,comp in records:
    if raw==66568:continue
    try:d=zlib.decompress(s[at:at+comp])
    except Exception:continue
    h=struct.unpack_from("<I8H",d,0);T=[];o=0
    while True:
        o=d.find(M,o)
        if o<0 or o+730+361>len(d):break
        if d[o+726:o+730]==M:T.append((struct.unpack_from("<361H",d,o+4),d[o+730:o+1091]));o+=726+365
        else:o+=1
    if T:chunks[(h[1],h[3])]=(h,T)
log("chunks",len(chunks),"tiles",sum(len(v[1]) for v in chunks.values()),"widths",collections.Counter(v[0][2]-v[0][1] for v in chunks.values()).most_common())
grids=[];masks=[];pos={};L=collections.defaultdict(dict);V=[];partial=[]
for key,(h,T) in chunks.items():
    w=h[2]-h[1]
    for i,(v,m) in enumerate(T):
        n=len(grids);grids.append((key,i,v));masks.append(m);a=np.array(v,np.int32);a[a>=32768]-=65536;V.append(a.reshape(19,19))
        if w>=512:continue
        if len(T)==h[0]==16:
            x,y=key[0]+(i%4)*w,key[1]+(i//4)*w
            if (x,y) not in L[w]:L[w][(x,y)]=n;pos[n]=(x,y,w)
        else:partial.append((n,key,w))
def agrees(n,x,y,w):
    good=bad=0;g=V[n]
    for dx,dy,a,b in ((w,0,lambda q:q[:,16:],lambda q:q[:,:3]),(-w,0,lambda q:q[:,:3],lambda q:q[:,16:]),(0,w,lambda q:q[16:,:],lambda q:q[:3,:]),(0,-w,lambda q:q[:3,:],lambda q:q[16:,:])):
        o=L[w].get((x+dx,y+dy))
        if o is None:continue
        if np.abs(a(g)-b(V[o])).mean()<=1:good+=1
        else:bad+=1
    return good,bad
moved=1
while moved:
    moved=0
    for item in list(partial):
        n,key,w=item;best=None
        for ty in range(4):
            for tx in range(4):
                x,y=key[0]+tx*w,key[1]+ty*w
                if (x,y) in L[w]:continue
                g,b=agrees(n,x,y,w)
                if b==0 and g>0 and (best is None or g>best[0]):best=(g,x,y)
        if best:L[w][(best[1],best[2])]=n;pos[n]=(best[1],best[2],w);partial.remove(item);moved+=1
for n,key,w in list(partial):
    i=grids[n][1];x,y=key[0]+(i%4)*w,key[1]+(i//4)*w
    if (x,y) not in L[w] and agrees(n,x,y,w)[1]==0:L[w][(x,y)]=n;pos[n]=(x,y,w);partial.remove((n,key,w))
errs=collections.Counter()
for w,Tl in L.items():
    for (x,y),n in Tl.items():
        for dx,dy in ((w,0),(0,w)):
            o=Tl.get((x+dx,y+dy))
            if o is None:continue
            e=np.abs(V[n][:,16:]-V[o][:,:3]).mean() if dx else np.abs(V[n][16:,:]-V[o][:3,:]).mean();errs["match" if e<=1 else "mismatch"]+=1
log("placed",len(pos),"of",len(grids),"edges",errs,"levels",collections.Counter(p[2] for p in pos.values()))
# Spawn points of the zone against raw heights.
sim={int(k) for k in syms["simtype"]};encs={int(k) for k in syms["encounter"]};pts=[]
sp=[int(k) for k,v in syms["simspace"].items() if re.match(rf"out_{PRE}_",str(v))]
for k in sp:
    f=extract([f"{k}.space_bxml"]).get(f"{k}.space_bxml")
    if not f:continue
    b=f.read_bytes()
    for o in range(16,len(b)-48):
        if struct.unpack_from("<I",b,o)[0] in encs:
            p1,c1,p2,c2=struct.unpack_from("<4I",b,o-16)
            if c1==c2 and 0<c1<64 and p1+c1*12<=len(b):pts+= [struct.unpack_from("<3f",b,p1+i*12) for i in range(c1)]
log("spawn points",len(pts),"x",round(min(p[0] for p in pts)),round(max(p[0] for p in pts)),"y",round(min(p[1] for p in pts)),round(max(p[1] for p in pts)))
ORIGIN=-102425.0
def raw_at(wx,wy):
    ux,uy=(wx-ORIGIN)/50,(wy-ORIGIN)/50
    for w in sorted(L):
        px,py=int(ux//w)*w,int(uy//w)*w;n=L[w].get((px,py))
        if n is None:continue
        fx,fy=(ux-px)*16/w+1,(uy-py)*16/w+1;ix,iy=int(fx),int(fy);g=V[n]
        m=masks[n];ids=(iy*19+ix,iy*19+ix+1,(iy+1)*19+ix,(iy+1)*19+ix+1)
        if max(m[q] for q in ids)==0:return None
        ax,ay=fx-ix,fy-iy;return g[iy,ix]*(1-ax)*(1-ay)+g[iy,ix+1]*ax*(1-ay)+g[iy+1,ix]*(1-ax)*ay+g[iy+1,ix+1]*ax*ay
    return None
X=[];Z=[]
for x,y,z in pts:
    r=raw_at(x,y)
    if r is not None:X.append(r);Z.append(z)
X=np.array(X);Z=np.array(Z);log("usable",len(X))
best=None;rng=np.random.default_rng(1)
for _ in range(4000):
    i,j=rng.integers(0,len(X),2)
    if abs(X[i]-X[j])<500:continue
    k=(Z[i]-Z[j])/(X[i]-X[j]);z0=Z[i]-k*X[i];inl=(np.abs(k*X+z0-Z)<60).sum()
    if best is None or inl>best[0]:best=(inl,k,z0)
inl=np.abs(best[1]*X+best[2]-Z)<60;k,z0=np.polyfit(X[inl],Z[inl],1);res=k*X+z0-Z
log("FIT k",round(float(k),5),"z0",round(float(z0),1),"inliers",int(inl.sum()),"of",len(X),"residual pct",np.percentile(np.abs(res),[50,90,99]).round(1).tolist())
pickle.dump(grids,open(DIR/"terrain-grids.pkl","wb"));pickle.dump(pos,open(DIR/"terrain-abs.pkl","wb"));pickle.dump(masks,open(DIR/"terrain-masks.pkl","wb"));(DIR/"terrain-fit.json").write_text(json.dumps({"k":float(k),"z0":float(z0)}))
log("written",DIR)
