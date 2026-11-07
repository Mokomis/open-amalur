import json,struct,re,collections
from pathlib import Path
import numpy as np
from PIL import Image
root=Path.home()/"Documents/Opem Amalur";z=root/"work/v22-stress/zone-dal";out=root/"work/v21-ui/live"
H=np.load(z/"terrain_H.npy");gx,gy=json.loads((z/"terrain_H.json").read_text());ny,nx=H.shape
pos=np.load(z/"zone_pos.npy",mmap_mode="r");tex=np.load(z/"zone_tex.npy",mmap_mode="r");m=json.loads((z/"zone_materials.json").read_text());T=m["terrain"]
terr=np.where(np.asarray(tex)==T)[0];print("visible triangles",len(tex),"terrain",len(terr))
P=np.asarray(pos[terr*3]);PX=np.asarray(pos)[::30]
S=8
def grid(p):
    g=np.zeros((ny//S+1,nx//S+1),bool);i=((p[:,0]-gx)/(100*S)).astype(int);j=((p[:,1]-gy)/(100*S)).astype(int);k=(i>=0)&(j>=0)&(i<g.shape[1])&(j<g.shape[0]);g[j[k],i[k]]=True;return g
Gt=grid(P);Gm=grid(PX);Hv=(H==H)[::S,::S];Hv=Hv[:Gt.shape[0],:Gt.shape[1]]
C=np.load(z/"zone_col.npy",mmap_mode="r");Gc=grid(np.asarray(C)[::20])
print("cells of 8 m: terrain grid valid",int(Hv.sum()),"visible terrain",int(Gt.sum()),"visible anything",int(Gm.sum()),"collision",int(Gc.sum()))
print("visible model but no terrain",int((Gm&~Gt).sum()),"no collision where visible",int((Gm&~Gc).sum()))
b=(root/"work/v23-actors/index.bin").read_bytes();Ty,N=struct.unpack_from("<II",b,4);o=12+Ty*76
A=np.array([struct.unpack_from("<4f",b,o+i*20)[:3] for i in range(N)])
def at(G,a):
    i=((a[:,0]-gx)/(100*S)).astype(int);j=((a[:,1]-gy)/(100*S)).astype(int);ok=(i>=0)&(j>=0)&(i<G.shape[1])&(j<G.shape[0]);r=np.zeros(len(a),bool);r[ok]=G[j[ok],i[ok]];return r,ok
print("actors",N,"inside bounds",int(at(Gt,A)[1].sum()),"on visible terrain",int(at(Gt,A)[0].sum()),"on any visible",int(at(Gm,A)[0].sum()),"on collision",int(at(Gc,A)[0].sum()))
print("actor bounds",A.min(0).round(),A.max(0).round(),"world",gx,gy,gx+nx*100,gy+ny*100)
img=np.zeros((*Gt.shape,3),np.uint8);img[Gm]=(90,90,120);img[Gt]=(60,140,60);img[Gc&~Gt&~Gm]=(150,60,60)
a=((A[:,0]-gx)/(100*S)).astype(int);c=((A[:,1]-gy)/(100*S)).astype(int);k=(a>=0)&(c>=0)&(a<img.shape[1])&(c<img.shape[0]);img[c[k],a[k]]=(255,230,40)
Image.fromarray(img[::-1]).resize((img.shape[1]*3,img.shape[0]*3),Image.NEAREST).save(out/"holes.png")
# Space centres vs terrain
s=json.loads((root/"work/v20-inputs/symbols.json").read_text());sp={int(k):str(v) for k,v in s["simspace"].items() if re.match(r"out_dal_(north|south|west|tran)_",str(v))};print("spaces",len(sp),sorted(sp.values())[:30])
print("terrain table",[ (k,v) for k,v in s["terrain"].items()][:12],len(s["terrain"]))
