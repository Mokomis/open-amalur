import json,struct,collections
from pathlib import Path
import numpy as np
from PIL import Image
src=(Path.home()/"Documents/Opem Amalur/work/v20-char/build_npcs.py").read_text()
exec(src[:src.index("SKELS = {}")])
TEXTURE_LIMIT=256
out=open(root/"work/v20-char/white.txt","w",encoding="utf-8");P=lambda *a:print(*a,file=out,flush=True)
z=root/"work/v22-stress/zone-dal";M=json.loads((z/"zone_materials.json").read_text())["materials"]
tn=lambda t:str(syms["texture"].get(str(t)))
tiles=[]
for i,m in enumerate(M):
    if m.get("kind") in ("fall","river"):
        P(i,m["kind"],[tn(t) for t in m["t"]],[round(x,3) for x in m["p"]])
        for t in m["t"][:4]:
            if t:
                b=decode_best(t)
                if b:
                    a=np.frombuffer(b[2],'u1').reshape(b[1],b[0],4);P("   ",tn(t),b[0],b[1],"mean",a.reshape(-1,4).mean(0).round(0).tolist(),"G>128",round(float((a[:,:,1]>128).mean()),2))
                    if m["kind"]=="fall" and len(tiles)<8:tiles.append(Image.fromarray(a[:,:,:3]).resize((256,256)))
if tiles:
    I=Image.new("RGB",(256*len(tiles),256))
    for k,t in enumerate(tiles):I.paste(t,(k*256,0))
    I.save(root/"work/v21-ui/live/falltex.png")
# Sun and the blend of what is drawn there
T=np.asarray(np.load(z/"zone_tex.npy",mmap_mode="r"));p=np.asarray(np.load(z/"zone_pos.npy",mmap_mode="r")).reshape(-1,3,3);c=p.mean(1)
near=(np.abs(c[:,0]+12000)<2500)&(np.abs(c[:,1]+9000)<1500)&(c[:,2]<4700)
area=np.linalg.norm(np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0]),axis=1)/2
P("area by material near white, m2",sorted([(round(float(area[near&(T==i)].sum()/1e4),1),str(tn(M[i]["d"][0] if isinstance(M[i]["d"],list) else M[i]["d"])),M[i].get("kind")) for i in set(T[near].tolist())],reverse=True)[:12])
out.close()
