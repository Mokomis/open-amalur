import collections,json,struct,sys
from pathlib import Path
import numpy as np
root=Path.home()/"Documents/Opem Amalur";z=root/"work/v22-stress/zone-dal";s=json.loads((root/"work/v20-inputs/symbols.json").read_text())
P=np.load(z/"zone_pos.npy",mmap_mode="r");T=np.load(z/"zone_tex.npy",mmap_mode="r");m=json.loads((z/"zone_materials.json").read_text());M=m["materials"]
print("pos shape",P.shape,"tex",T.shape,"terrain mat",m["terrain"],"H range")
p=np.asarray(P).reshape(-1,3,3);t=np.asarray(T);c=p.mean(1);size=np.ptp(p,axis=1).max(1)
me=np.array([-7632.,-64285.,5507.])
near=(np.abs(c[:,0]-me[0])<30000)&(np.abs(c[:,1]-me[1])<30000)&(c[:,2]>me[2]+2500)
print("tris overhead",int(near.sum()))
name=lambda i:s["texture"].get(str(M[i]["d"] if not isinstance(M[i]["d"],list) else M[i]["d"][0]),"?")
cnt=collections.Counter(t[near].tolist())
for i,n in cnt.most_common(14):
    q=near&(t==i);print(i,name(i),"tris",n,"z",round(float(c[q,2].min())),round(float(c[q,2].max())),"largest tri m",round(float(size[q].max()/100)),"mean m",round(float(size[q].mean()/100),1),"x",round(float(c[q,0].min())),round(float(c[q,0].max())),"y",round(float(c[q,1].min())),round(float(c[q,1].max())))
big=size>3000;cb=collections.Counter(t[big].tolist());print("large tris (>30 m) whole zone",int(big.sum()),[(i,name(i),n,round(float(size[big&(t==i)].max()/100)),round(float(c[big&(t==i),2].mean()))) for i,n in cb.most_common(14)])
H=np.load(z/"terrain_H.npy");gx,gy=json.loads((z/"terrain_H.json").read_text());j,i=int((me[1]-gy)/100),int((me[0]-gx)/100);w=H[j-300:j+300:50,i-300:i+300:50];np.set_printoptions(linewidth=200,precision=0,suppress=True);print("terrain z around (rows y, cols x, 50 m apart)");print(w)
