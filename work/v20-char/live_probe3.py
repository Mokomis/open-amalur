import collections,json,pickle,struct,zlib
from pathlib import Path
import numpy as np
root=Path.home()/"Documents/Opem Amalur";inp=root/"work/v20-inputs";wc=root/"work/v20-char"
vb=(inp/"DATA_0.pak/431658.veggie_streamable_bin").read_bytes()
# Block table: chunks are consecutive zlib streams, keep each block separately.
pos=0;blocks=[]
while True:
    i=vb.find(b"\x78\x9c",pos)
    if i<0:break
    try:
        do=zlib.decompressobj();d=do.decompress(vb[i:i+400000]);end=i+min(400000,len(vb)-i)-len(do.unused_data);blocks.append((i,d));pos=end
    except Exception:pos=i+2
print(len(blocks),collections.Counter(len(d) for _,d in blocks).most_common(8))
print("hdr before first",vb[0:blocks[0][0]].hex(),"between",vb[blocks[0][0]+0:0].hex())
_,d=blocks[0]
n=struct.unpack_from("<I",d,0)[0];print("n",n,"len",len(d))
a=np.frombuffer(d,"<f4",n,4);print("grid1 min max",a.min(),a.max())
o=4+n*4;print("after grid hex",d[o:o+64].hex())
m=struct.unpack_from("<I",d,o)[0];print("second count",m)
if m==n:
    raw=d[o+4:o+4+m*4];u=np.frombuffer(raw,"<u4");print("grid2 uniq",len(np.unique(u)),u[:10],"as f",np.frombuffer(raw,"<f4")[:10]);print("bytes uniq per lane",[len(np.unique(np.frombuffer(raw,'u1')[k::4])) for k in range(4)],[np.frombuffer(raw,'u1')[k::4].mean().round(1) for k in range(4)])
    tail=d[o+4+m*4:];print("tail",len(tail),tail[:48].hex())
abs_pos=pickle.load(open(wc/"terrain-abs.pkl","rb"));lv=collections.Counter(w for x,y,w in abs_pos.values());print("terrain levels",sorted(lv.items()))
fit=json.loads((wc/"terrain-fit.json").read_text())
# Try chunk order = terrain order at each level: compare corner heights with the terrain grid.
grids=pickle.load(open(wc/"terrain-grids.pkl","rb"))
for w in sorted(lv):
    items=[(k,v) for k,v in abs_pos.items() if v[2]==w]
    print("level",w,"count",len(items),"first keys",[k for k,_ in items[:4]],[v[:2] for _,v in items[:4]])
# A height match: sample block's corners vs every level-256 terrain chunk's corners.
keys=list(abs_pos.keys())
def grid_z(k): 
    v=np.array(grids[k][2],dtype=float).reshape(19,19);return v*fit["k"]+fit["z0"]
best=collections.Counter()
for bi in (0,1,2,500,1000,1700):
    d=blocks[bi][1];n=struct.unpack_from("<I",d,0)[0]
    if n!=4225:continue
    a=np.frombuffer(d,"<f4",n,4).reshape(65,65)
    samples=a[::16,::16]
    out=[]
    for k in keys:
        x,y,w=abs_pos[k]
        z=grid_z(k)[1:18,1:18]
        if z.max()>30000:continue
        if w in(64,128,256,512):
            err=np.abs(z[::4,::4]-samples).mean()
            out.append((round(float(err),2),w,x,y))
    out.sort();print("block",bi,"z",round(float(a.mean())),"best",out[:3])
