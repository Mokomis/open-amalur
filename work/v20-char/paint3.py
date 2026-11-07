import struct,collections
from pathlib import Path
import numpy as np
root=Path.home()/"Documents/Opem Amalur"
for p in (root/"work/v20-inputs").rglob("431658.terrain_bin"):b=p.read_bytes();break
print(len(b),"k",struct.unpack_from("<f",b,96)[0])
N=1344
a=np.frombuffer(b[:len(b)//2*2],"<u2")
ok=a<N;d=np.diff(np.r_[0,ok.astype(np.int8),0]);st=np.where(d==1)[0];en=np.where(d==-1)[0];L=en-st
print("u2 runs",[(int(s)*2,int(l),int(len(np.unique(a[s:e])))) for s,e,l in sorted(zip(st,en,L),key=lambda x:-x[2])[:6]])
# Blocks: repeated structure with 16-unit records. Print the file as words around where the header ends, and find repeats of stride.
W=np.frombuffer(b[:len(b)//4*4],"<u4")
print("after head",W[20:90].tolist())
for stride in (4,8,12,16,20,24,28,32,36,40,48,64,1024,1028,1040):
    if stride%4: continue
    n=stride//4;x=W[:(len(W)//n)*n].reshape(-1,n)
    same=(x[1:]==x[:-1]).mean(0);print(stride,"steady columns",int((same>.9).sum()),"of",n)
# Count of each distinct 2305-ish table
print("2305 at",np.where(W==2305)[0][:10].tolist(),"1344 at",np.where(W==1344)[0][:10].tolist(),"2402 at",np.where(W==2402)[0][:10].tolist(),"4523 at",np.where(W==4523)[0][:10].tolist())
u=np.frombuffer(b[:len(b)//2*2],"<u2");print("u2 1344 at",np.where(u==1344)[0][:10].tolist())
