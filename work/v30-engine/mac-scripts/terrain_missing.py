import collections,pickle,struct,zlib
from pathlib import Path
import numpy as np
root=Path.home()/"Documents/Opem Amalur";wc=root/"work/v20-char"
s=(root/"work/v20-inputs/DATA_0.pak/431658.terrain_streamable_bin").read_bytes()
grids=pickle.load(open(wc/"terrain-grids.pkl","rb"));idx=pickle.load(open(wc/"terrain-index.pkl","rb"))
have={g[0] for g in grids};miss=sorted(set(idx)-have);print(len(miss),miss)
for k in miss[:21]:
    at,comp=idx[k]
    try:
        d=zlib.decompress(s[at:at+comp])
    except Exception as e:
        print(k,at,comp,"zlib",repr(e)[:60],"head",s[at:at+16].hex());continue
    w=np.frombuffer(d[:len(d)//4*4],"<u4");c=collections.Counter(w[w<70000].tolist())
    print(k,"comp",comp,"raw",len(d),"head",d[:24].hex(),"marker361",int((w==361).sum()),"top small words",c.most_common(4))
ok=sorted(have)[100];at,comp=idx[ok];d=zlib.decompress(s[at:at+comp]);print("normal",ok,comp,len(d),d[:32].hex())
print("sizes of normal",np.percentile([idx[k][1] for k in have],[1,50,99]).round())
print("terrain-grids builder",[p.name for p in wc.glob("terrain_*.py") if b"terrain-grids.pkl" in p.read_bytes()])
