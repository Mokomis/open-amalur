import collections,struct,zlib,json
from pathlib import Path
import numpy as np
root=Path.home()/"Documents/Opem Amalur";inp=root/"work/v20-inputs"
vb=(inp/"DATA_0.pak/431658.veggie_streamable_bin").read_bytes()
pos=0;B=[]
while True:
    i=vb.find(b"\x78\x9c",pos)
    if i<0:break
    try:
        do=zlib.decompressobj();d=do.decompress(vb[i:i+400000]);pos=i+min(400000,len(vb)-i)-len(do.unused_data);B.append((i,d))
    except Exception:pos=i+2
print("pre-header sample",[vb[B[k][0]-24:B[k][0]].hex() for k in (0,1,2)])
for size in (33844,38069,54969,71869,105669):
    i,d=next(x for x in B if len(x[1])==size)
    o=4+4225*4
    print("== size",size,"head",d[o:o+80].hex())
    z,lo,hi,c,a,b=struct.unpack_from("<IffIII",d,o);print(" z",z,"lo",lo,"hi",hi,"c",c,"a",a,"b",b)
    rest=d[o+24:]
    print(" rest",len(rest),"mod 4225",len(rest)%4225,"div",len(rest)/4225,"nonzero frac",round(np.count_nonzero(np.frombuffer(rest,'u1'))/len(rest),3))
    # Show nonzero stretch positions
    arr=np.frombuffer(rest,'u1');nz=np.nonzero(arr)[0]
    if len(nz):
        print(" first nz",nz[:6],"last",nz[-3:],"vals",arr[nz[:16]],"hist",np.bincount(arr)[:6],"max",arr.max())
        # find 4225 marker positions (0x81 0x10)
        m=[k for k in range(0,len(rest)-4) if rest[k:k+4]==b"\x81\x10\x00\x00"][:12];print(" 4225 markers",m,"gaps",np.diff(m))
        for k in m[:3]:print("  before marker",rest[max(0,k-12):k+4].hex())
