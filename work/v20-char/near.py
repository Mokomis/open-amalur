import json,collections
from pathlib import Path
import numpy as np
root=Path.home()/"Documents/Opem Amalur";z=root/"work/v22-stress/zone-dal"
s=json.loads((root/"work/v20-inputs/symbols.json").read_text())["texture"]
m=json.loads((z/"zone_materials.json").read_text());M=m["materials"];print("terrain",m["terrain"],"grass",m["grass"])
pos=np.load(z/"zone_pos.npy",mmap_mode="r");tex=np.asarray(np.load(z/"zone_tex.npy",mmap_mode="r"));uv=np.load(z/"zone_uv.npy",mmap_mode="r")
P=np.asarray(pos).reshape(-1,3,3);c=P.mean(1)
k=np.where((np.abs(c[:,0]-20300)<1500)&(np.abs(c[:,1]+43211)<1500))[0];print("tris near",len(k))
Q=P[k];n=np.cross(Q[:,1]-Q[:,0],Q[:,2]-Q[:,0]);area=np.linalg.norm(n,axis=1)/2;nz=np.abs(n[:,2])/(area*2+1e-6)
U=np.asarray(uv).reshape(-1,3,2)[k]
du=np.linalg.norm(np.cross(np.c_[U[:,1]-U[:,0],np.zeros(len(U))],np.c_[U[:,2]-U[:,0],np.zeros(len(U))]),axis=1)/2
A=collections.Counter();B=collections.Counter();D=collections.defaultdict(list)
for t,a,nn,d in zip(tex[k],area,nz,du):
    A[int(t)]+=a/1e4
    if nn<.3:B[int(t)]+=a/1e4;D[int(t)].append(d/(a+1e-6))
nm=lambda t:s.get(str(M[t].get("d")),"?") if t<len(M) else "?"
print("area m2",[(t,nm(t),round(a)) for t,a in A.most_common(14)])
print("steep m2, uv per unit area",[(t,nm(t),round(a),float(np.median(D[t]))) for t,a in B.most_common(14)])
