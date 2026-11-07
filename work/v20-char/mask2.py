import collections,json,pickle,struct,zlib
from pathlib import Path
import numpy as np
root=Path.home()/"Documents/Opem Amalur";wc=root/"work/v20-char"
out=open(wc/"mask2.txt","w",encoding="utf-8");P=lambda *a:print(*a,file=out,flush=True)
s=(root/"work/v20-inputs/DATA_0.pak/431658.terrain_streamable_bin").read_bytes();idx=pickle.load(open(wc/"terrain-index.pkl","rb"));grids=pickle.load(open(wc/"terrain-grids.pkl","rb"));pos=pickle.load(open(wc/"terrain-abs.pkl","rb"))
M=struct.pack("<I",361);by={}
for key,(at,comp) in idx.items():
    d=zlib.decompress(s[at:at+comp]);o=0
    while True:
        o=d.find(M,o)
        if o<0 or o+730+361>len(d):break
        if d[o+726:o+730]==M:by[struct.unpack_from("<361H",d,o+4)]=d[o+730:o+730+361];o+=726+365
        else:o+=1
masks=[by.get(tuple(g[2])) for g in grids];P("grids",len(grids),"matched",sum(m is not None for m in masks))
pickle.dump(masks,open(wc/"terrain-masks.pkl","wb"))
A_=np.array([np.frombuffer(m,"u1") for m in masks if m is not None]);P("values",collections.Counter(A_.reshape(-1).tolist()).most_common(8),"tiles with any 0",int((A_==0).any(1).sum()),"fraction 0",round(float((A_==0).mean()),4))
fit=json.loads((wc/"terrain-fit.json").read_text())
level=collections.defaultdict(dict)
for n,(x,y,w) in pos.items():level[w][(x,y)]=n
O=-102425.0
def look(wx,wy,use_mask):
    ux,uy=(wx-O)/50,(wy-O)/50
    for w in sorted(level):
        px,py=int(ux//w)*w,int(uy//w)*w;n=level[w].get((px,py))
        if n is None:continue
        v=grids[n][2];fx,fy=(ux-px)*16/w+1,(uy-py)*16/w+1;ix,iy=int(fx),int(fy);ids=(iy*19+ix,iy*19+ix+1,(iy+1)*19+ix,(iy+1)*19+ix+1);q=[v[i] for i in ids]
        if 65535 in q:continue
        m=masks[n]
        if use_mask and m is not None and max(m[i] for i in ids)==0:return None,w,"masked"
        q=[x-65536 if x>=32768 else x for x in q];ax,ay=fx-ix,fy-iy;return (q[0]*(1-ax)*(1-ay)+q[1]*ax*(1-ay)+q[2]*(1-ax)*ay+q[3]*ax*ay)*fit["k"]+fit["z0"],w,"ok"
    return None,0,"none"
for c in ((-13470,-8939,4272),(-13121,-9104,4300)):P(c,"plain",look(c[0],c[1],False),"mask",look(c[0],c[1],True))
b=(root/"work/v23-actors/index.bin").read_bytes();Ty,Na=struct.unpack_from("<II",b,4);o=12+Ty*76;A=np.array([struct.unpack_from("<4f",b,o+i*20)[:3] for i in range(Na)])
tab=collections.Counter()
for p in A:
    h,w,st=look(p[0],p[1],False);h2,w2,st2=look(p[0],p[1],True)
    if h is None:tab["no terrain"]+=1;continue
    d=p[2]-h;k="3m+ below" if d<-300 else "3m+ above" if d>300 else "on"
    tab[(k,st2)]+=1
P(sorted(tab.items(),key=str))
out.close()
