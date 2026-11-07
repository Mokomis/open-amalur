import collections,json,os,struct,re
from pathlib import Path
import numpy as np
from PIL import Image
src=(Path.home()/"Documents/Opem Amalur/work/v20-char/build_npcs.py").read_text()
exec(src[:src.index("SKELS = {}")])
z=root/"work/v22-stress/zone-dal";P=np.load(z/"zone_pos.npy",mmap_mode="r");T=np.asarray(np.load(z/"zone_tex.npy",mmap_mode="r"));m=json.loads((z/"zone_materials.json").read_text());M=m["materials"]
for i,mt in enumerate(M):
    d=mt["d"]
    if not isinstance(d,list) and re.search("skyline|backdrop|horizon|vista|distant|matte",str(syms["texture"].get(str(d),"")),re.I):
        q=np.where(T==i)[0];p=np.asarray(P[q[0]*3:(q[-1]+1)*3]).reshape(-1,3,3) if len(q) and q[-1]-q[0]+1==len(q) else np.asarray(P)[np.repeat(q,3)*3+np.tile([0,1,2],len(q))].reshape(-1,3,3)
        c=p.mean(1);e=np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0]);e/=np.linalg.norm(e,axis=1,keepdims=True)+1e-9
        print(i,syms["texture"].get(str(d)),"tris",len(q),"x",round(float(p[:,:,0].min())),round(float(p[:,:,0].max())),"y",round(float(p[:,:,1].min())),round(float(p[:,:,1].max())),"z",round(float(p[:,:,2].min())),round(float(p[:,:,2].max())),"mat",{k:(syms["texture"].get(str(v),v) if k!="terrain" else v) for k,v in mt.items()})
        print("  normal toward zone centre fraction",round(float((((np.array([0,0,0])-c)[:,:2]*e[:,:2]).sum(1)>0).mean()),2),"up mean",round(float(e[:,2].mean()),2))
        o=root/"work/v21-ui/live";os_=syms["texture"].get(str(d));
        os.environ["x"]="1" if False else "1"
        b=decode_best(d)
        if b:
            Image.frombytes("RGBA",(b[0],b[1]),b[2]).convert("RGB").save(o/f"{os_}.png");print("  texture",b[0],b[1])
        a=mt.get("a")
        if a:
            bb=decode_best(a);arr=np.frombuffer(bb[2],'u1').reshape(bb[1],bb[0],4);print("  mask mean",arr.reshape(-1,4).mean(0).round(0))
# Who places it and with what material flags
for name,v in syms["material"].items():
    if re.search("skyline",str(v),re.I):
        f=extract([f"{name}.mat_bxml"]).get(f"{name}.mat_bxml")
        if f:
            b=f.read_bytes();refs=[]
            for o in range(0,len(b)-3,4):
                w=struct.unpack_from("<I",b,o)[0]
                for c,t in syms.items():
                    if isinstance(t,dict) and str(w) in t and w>1000:refs.append(f"{c}:{t[str(w)]}");break
            print("material",v,len(b),refs[:14],"floats",[round(x,2) for x in struct.unpack_from(f"<{min(30,len(b)//4)}f",b,0) if 0<abs(x)<100][:16])
print([str(v) for v in syms["fab"].values() if re.search("skyline",str(v),re.I)][:20])
print([str(v) for v in syms["platform_shader"].values() if re.search("sky|vista|horizon|far|distant|unlit",str(v),re.I)][:16])
print([str(v) for v in syms["shader"].values() if re.search("sky|vista|horizon|far|distant|unlit",str(v),re.I)][:16])
