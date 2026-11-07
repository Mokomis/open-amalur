import re,struct,collections
from pathlib import Path
import numpy as np
root=Path.home()/"Documents/Opem Amalur"
t=(root/"work/v19-host/town_live.inc").read_text()
print(t[:300])
nums=re.findall(r"\{([^{}]*)\}",t)
L=np.array([[float(x.rstrip("f")) for x in n.split(",")] for n in nums if n.count(",")==7])
print("lights",L.shape,"end pct",np.percentile(L[:,7],[10,50,90,99,100]).round(0),"start pct",np.percentile(L[:,3],[50,90]).round(0),"rgb max pct",np.percentile(L[:,4:7].max(1),[50,90,100]).round(2))
b=(root/"work/v22-stress/live-pack/index.bin")
print(b.exists())
raw=b.read_bytes();cells=struct.unpack_from("<I",raw,8)[0] if raw[:4]==b"OAWI" else 0
print(raw[:4],cells)
rows=[struct.unpack_from("<ii6f4I",raw,20+i*48) for i in range(cells)]
c=[]
for r in rows:
    lo,hi=np.array(r[2:5]),np.array(r[5:8])
    q=np.clip(L[:,:3],lo,hi);d=np.linalg.norm(q-L[:,:3],axis=1);c.append(int((d<L[:,7]).sum()))
c=np.array(c);print("cells",cells,"lights per cell pct",np.percentile(c,[50,90,99,100]),"cells>12",int((c>12).sum()),"cells>0",int((c>0).sum()))