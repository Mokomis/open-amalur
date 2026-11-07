import struct
from pathlib import Path
import numpy as np
root=Path.home()/"Documents/Opem Amalur"
b=(root/"work/v20-char/character.bin").read_bytes();J,C,_,_=struct.unpack_from("<IIII",b,8);o=24+J*2
cl=[]
for c in range(C):
    fr,fps=struct.unpack_from("<If",b,o);o+=8;cl.append(np.frombuffer(b,"<f4",fr*J*7,o).reshape(fr,J,7));o+=fr*J*28
np.set_printoptions(precision=1,suppress=True,linewidth=170)
for j in (3,4,5,6,7,8,9,10,11,12,13,14,15,16,33,39):
    print(j,"idle",cl[0][0,j,4:],"run",cl[2][0,j,4:],"x01",cl[3][0,j,4:],"xx01",cl[4][0,j,4:],"xxx01",cl[5][0,j,4:],"x02",cl[12][0,j,4:])
