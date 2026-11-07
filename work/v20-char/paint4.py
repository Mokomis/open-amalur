import struct,collections,json
from pathlib import Path
import numpy as np
from PIL import Image
root=Path.home()/"Documents/Opem Amalur"
for p in (root/"work/v20-inputs").rglob("431658.terrain_bin"):b=p.read_bytes();break
u=np.frombuffer(b[:len(b)//2*2],"<u2")
print(u[11940:11990].tolist());print(u[12454:12500].tolist())
# Score each possible row stride by how often a value equals the one a stride earlier
for st in (257,258,512,513,514,515,516,520,1024):
    print(st,round(float((u[st:]==u[:-st]).mean()),3))
# Where along the file is the lattice strong?
st=514;eq=(u[st:]==u[:-st]);step=20000
print("repeat by position",[round(float(eq[i:i+step].mean()),2) for i in range(0,len(eq),step)])
print("small-value share",[round(float((u[i:i+step]<=1344).mean()),2) for i in range(0,len(u),step)])
