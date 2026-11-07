import json,struct
from pathlib import Path
import numpy as np
root=Path.home()/"Documents/Opem Amalur";z=root/"work/v22-stress/zone-dal"
H=np.load(z/"terrain_H.npy");gx,gy=json.loads((z/"terrain_H.json").read_text());ny,nx=H.shape
b=(root/"work/v23-actors/index.bin").read_bytes();Ty,N=struct.unpack_from("<II",b,4);o=12+Ty*76
A=np.array([struct.unpack_from("<4f",b,o+i*20)[:3] for i in range(N)])
i=((A[:,0]-gx)/100).astype(int);j=((A[:,1]-gy)/100).astype(int);ok=(i>=0)&(j>=0)&(i<nx)&(j<ny)
d=np.full(N,np.nan);d[ok]=A[ok,2]-H[j[ok],i[ok]]
print("actor z minus terrain pct",np.nanpercentile(d,[1,5,25,50,75,95,99]).round(0).tolist())
near=np.where(np.hypot(A[:,0]-20300,A[:,1]+43211)<3000)[0]
print("near",[(A[k].round(0).tolist(),None if np.isnan(d[k]) else round(float(d[k]))) for k in near][:14])
# Rock undersides: flat downward faces hanging above terrain
pos=np.asarray(np.load(z/"zone_pos.npy",mmap_mode="r")).reshape(-1,3,3);tex=np.asarray(np.load(z/"zone_tex.npy",mmap_mode="r"))
M=json.loads((z/"zone_materials.json").read_text());T=M["terrain"]
n=np.cross(pos[:,1]-pos[:,0],pos[:,2]-pos[:,0]);a=np.linalg.norm(n,axis=1)/2;nz=n[:,2]/(2*a+1e-6)
under=np.where((nz<-.95)&(tex!=T)&(a>10000))[0];c=pos[under].mean(1);i=((c[:,0]-gx)/100).astype(int);j=((c[:,1]-gy)/100).astype(int);ok=(i>=0)&(j>=0)&(i<nx)&(j<ny)
g=c[ok,2]-H[j[ok],i[ok]];aa=a[under][ok]/1e4
print("downward faces over 1 m2",len(under),"height above terrain pct",np.nanpercentile(g,[5,25,50,75,95]).round(0).tolist(),"area above ground >0.2m",round(float(aa[g>20].sum())),"of",round(float(aa.sum())))
# upward near flat at 5466 near here: which way do they face?
k=np.where((tex==2)&(np.abs(pos[:,:,2].mean(1)-5470)<20)&(np.hypot(pos[:,:,0].mean(1)-20000,pos[:,:,1].mean(1)+44000)<2500)&(a>5000))[0]
print("flat slabs here",len(k),"nz",nz[k].round(2).tolist()[:12])
