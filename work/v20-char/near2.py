import json,collections
from pathlib import Path
import numpy as np
root=Path.home()/"Documents/Opem Amalur";z=root/"work/v22-stress/zone-dal"
pos=np.asarray(np.load(z/"zone_pos.npy",mmap_mode="r")).reshape(-1,3,3);tex=np.asarray(np.load(z/"zone_tex.npy",mmap_mode="r"));uv=np.asarray(np.load(z/"zone_uv.npy",mmap_mode="r")).reshape(-1,3,2)
print("total tris",len(pos),"uv range",uv.min(0).min(0),uv.max(0).max(0))
c=pos.mean(1)
k=np.where((tex==2)&(np.abs(c[:,0]-20300)<1500)&(np.abs(c[:,1]+43211)<1500))[0]
P=pos[k];U=uv[k]
n=np.cross(P[:,1]-P[:,0],P[:,2]-P[:,0]);a=np.linalg.norm(n,axis=1)/2;nz=np.abs(n[:,2])/(2*a+1e-6)
print("rock tris",len(k),"z",P[:,:,2].min(),P[:,:,2].max(),"area pct",np.percentile(a/1e4,[10,50,90,100]).round(2),"nz pct",np.percentile(nz,[10,50,90]).round(2))
print("uv pct u",np.percentile(U[:,:,0],[0,50,100]).round(2),"v",np.percentile(U[:,:,1],[0,50,100]).round(2))
# per triangle: world length of each edge against uv change along it
e=[(0,1),(1,2),(2,0)];R=[]
for i,j in e:
    w=np.linalg.norm(P[:,i]-P[:,j],axis=1)/100;d=np.abs(U[:,i]-U[:,j]);R.append(np.c_[w,d])
R=np.concatenate(R);v=R[:,0]>1
print("edges over 1 m",int(v.sum()),"u per m pct",np.percentile(R[v,1]/R[v,0],[10,50,90]).round(3),"v per m pct",np.percentile(R[v,2]/R[v,0],[10,50,90]).round(3))
big=np.argsort(-a)[:8]
for b in big: print(P[b].round(0).tolist(),U[b].round(3).tolist(),round(a[b]/1e4,1),round(nz[b],2))
# All cliff rock in the zone: same statistics
K=np.where(tex==2)[0];print("zone rock tris",len(K))
sets=collections.Counter(np.round(uv[K][:,:,1].max(1)-uv[K][:,:,1].min(1),2).tolist());print("v spans",sets.most_common(5))
