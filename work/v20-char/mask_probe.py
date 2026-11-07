import json,sys,os,collections
from pathlib import Path
import numpy as np
root=Path.home()/"Documents/Opem Amalur";zone=root/"work/v22-stress/zone-dal"
os.environ["OA_TEXTURE_LIMIT"]="256"
src=(root/"work/v20-char/build_town.py").read_text();sys.argv=["b","1",str(zone)];exec(src[:src.index("# Placed models")])
meta=json.loads((zone/"zone_materials.json").read_text())
ids=sorted({m["a"] for m in meta["materials"] if m.get("a")})
print("masks",len(ids))
c=collections.Counter()
for t in ids:
    b=decode_best(t)
    if not b: c["none"]+=1;continue
    a=np.frombuffer(b[2],'u1').reshape(b[1],b[0],4)
    f=(a.reshape(-1,4)>128).mean(0).round(2)
    bi=[(a[:,:,k]<16).mean()+(a[:,:,k]>240).mean() for k in range(4)]
    c[tuple(int(x>0.05 and x<0.95) for x in f[:3])]+=1
    if len(ids)<400 and sum(c.values())%12==0: print(syms["texture"].get(str(t)) or syms["texture"].get(t),b[0],f,np.round(bi,2))
print(c)