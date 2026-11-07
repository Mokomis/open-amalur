import struct,collections,json
from pathlib import Path
import numpy as np
root=Path.home()/"Documents/Opem Amalur"
for p in (root/"work/v20-inputs").rglob("431658.terrain_bin"):b=p.read_bytes();break
u=np.frombuffer(b[:len(b)//2*2],"<u2")
# Find where the grid starts: the first offset from which 257x257 pairs have a second field of 0 or 32 and repeat by rows.
best=None
for off in range(0,30000):
    if off+257*2*40>=len(u):break
    v=u[off:off+257*2*40].reshape(40,-1)
    s=v[:,1::2];good=np.isin(s,(0,16,32,64)).mean()
    if good>.98 and (best is None or good>best[0]):best=(good,off);break
print("first",best)
off=best[1]
# walk back to a row boundary: a row starts where the index column resets
G=None
for start in range(off,off+514):
    if start+257*2*257>len(u):break
    v=u[start:start+257*2*257].reshape(257,514)
    col=v[:,0::2]
    d=np.diff(col,axis=1);score=((d>=0)|(col[:,1:]==0)).mean()
    if G is None or score>G[0]:G=(score,start)
print("row start",G)
v=u[G[1]:G[1]+257*2*257].reshape(257,514);idx=v[:,0::2].astype(int);fl=v[:,1::2]
print("second field",collections.Counter(fl.ravel().tolist()).most_common(8));print("max index",idx.max(),"unique",len(np.unique(idx)))
nz=np.argwhere(idx>0);print("nonzero span rows",nz[:,0].min(),nz[:,0].max(),"cols",nz[:,1].min(),nz[:,1].max());print(idx[100,100:124].tolist());print(idx[100:112,110].tolist())
block=idx[:256,:256].reshape(64,4,64,4).transpose(0,2,1,3);print("blocks uniform",float((block.reshape(64,64,16).max(2)==block.reshape(64,64,16).min(2)).mean()))
np.save(root/"work/v25-fx/dal_paint_index.npy",idx)
# Test against slope
Paint=np.load(root/"work/v25-fx/dal_paint.npy",mmap_mode="r");z=root/"work/v22-stress/zone-dal";H=np.load(z/"terrain_H.npy");gx,gy=json.loads((z/"terrain_H.json").read_text())
ORIGIN=-102425.0;gxi=int(round((gx-ORIGIN)/100));gyi=int(round((gy-ORIGIN)/100));print("grid origin cells",gxi,gyi)
Hf=np.nan_to_num(H,nan=float(np.nanmedian(H)));gy_,gx_=np.gradient(Hf);Sl=np.hypot(gx_,gy_)/100
ops={"id":lambda a:a,"T":lambda a:a.T,"fx":lambda a:a[:,::-1],"fy":lambda a:a[::-1,:],"r180":lambda a:a[::-1,::-1],"Tfx":lambda a:a.T[:,::-1],"Tfy":lambda a:a.T[::-1,:],"Tr":lambda a:a.T[::-1,::-1]}
res={}
for (ax,ay,name) in ((0,0,"(j,i)"),):
  for op,fn in ops.items():
    for off_i in (1,):
      for ch in range(4):
        rs=[]
        for j in range(0,256,4):
            for i in range(0,256,4):
                k=idx[j,i]-off_i
                if k<0 or k>=len(Paint):continue
                # 64 map units are 32 grid samples of 100 units
                x0=i*8-gxi;y0=j*8-gyi
                if x0<0 or y0<0 or x0+33>H.shape[1] or y0+33>H.shape[0]:continue
                W=np.isfinite(H[y0:y0+33,x0:x0+33])
                if W.mean()<.9:continue
                s=Sl[y0:y0+33,x0:x0+33];q=fn(Paint[k,::4,::4,ch].astype(np.float32))
                if q.std()<4 or s.std()<1e-3:continue
                rs.append(np.corrcoef(q.ravel(),s.ravel())[0,1])
        if rs:res[(op,ch)]=(len(rs),round(float(np.mean(rs)),3),round(float(np.mean(np.abs(rs))),3))
for k,v in sorted(res.items(),key=lambda x:-x[1][2])[:14]:print(k,v)
