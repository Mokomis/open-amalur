import collections,json,struct,sys,zlib,pickle
from pathlib import Path
import numpy as np
src=(Path.home()/"Documents/Opem Amalur/work/v20-char/build_npcs.py").read_text()
exec(src[:src.index("SKELS = {}")])
TID="431658";name=f"{TID}.terrain_streamable_bin";s=extract([name])[name].read_bytes()
recs=[];i=0
while True:
    i=s.find(b"\x78\x9c",i)
    if i<0:break
    if i>=24:
        raw,total,zero,raw2,comp=struct.unpack_from("<5I",s,i-20)
        if raw==raw2 and zero==0 and comp<=total<=comp+32 and i+comp<=len(s):
            recs.append((i,raw,comp));i+=comp;continue
    i+=1
P=[(k,r) for k,r in enumerate(recs) if r[1]==66568];print("first paint index",P[0][0],"last",P[-1][0],"of",len(recs))
Paint=np.stack([np.frombuffer(zlib.decompress(s[r[0]:r[0]+r[2]]),np.uint8,offset=4).reshape(129,129,4) for k,r in P]).astype(np.float32)/255
np.save(root/"work/v25-fx/dal_paint.npy",(Paint*255).astype(np.uint8))
print("channel mean",Paint.mean((0,1,2)).round(3),"std",Paint.std((0,1,2)).round(3),"sum mean",Paint.sum(3).mean().round(3))
z=root/"work/v22-stress/zone-dal";H=np.load(z/"terrain_H.npy");gx,gy=json.loads((z/"terrain_H.json").read_text())
ORIGIN=-102425.0
gxi=(gx-ORIGIN)/100;gyi=(gy-ORIGIN)/100;print("grid start in 100-unit cells",gxi,gyi)
Hf=np.nan_to_num(H,nan=np.nanmedian(H))
gy_,gx_=np.gradient(Hf);Sl=np.hypot(gx_,gy_)/100
ok=np.isfinite(H)
sizes={32:17,64:33,128:65}  # map units: samples of 2 map units each
small=Paint[:,::8,::8,:]  # 17x17
best=[]
for mu,n in sizes.items():
    st=mu//2;step=(n-1)//16
    pos=[];pat=[]
    for iy in range(0,4096//mu):
        for ix in range(0,4096//mu):
            x0=int(ix*st-gxi);y0=int(iy*st-gyi)
            if x0<0 or y0<0 or x0+st+1>H.shape[1] or y0+st+1>H.shape[0]:continue
            if ok[y0:y0+st+1,x0:x0+st+1].mean()<.95:continue
            p=Sl[y0:y0+st+1,x0:x0+st+1][::step,::step];pos.append((ix,iy));pat.append(p.ravel())
    if not pat:continue
    A=np.array(pat);A=(A-A.mean(1,keepdims=True));A/=np.linalg.norm(A,axis=1,keepdims=True)+1e-6
    print("size",mu,"patches",len(pos))
    for op,fn in (("id",lambda a:a),("T",lambda a:a.transpose(0,2,1)),("fx",lambda a:a[:,:,::-1]),("fy",lambda a:a[:,::-1,:]),("r180",lambda a:a[:,::-1,::-1])):
        for ch in range(4):
            B=fn(small[:,:,:,ch]).reshape(len(small),-1);B=B-B.mean(1,keepdims=True);nb=np.linalg.norm(B,axis=1,keepdims=True);keep=nb[:,0]>1.0
            B=B[keep]/nb[keep]
            C=B@A.T;m=np.abs(C).max(1);print(mu,op,ch,"used",int(keep.sum()),"best corr median",round(float(np.median(m)),3),"90%",round(float(np.percentile(m,90)),3),"max",round(float(m.max()),3))
