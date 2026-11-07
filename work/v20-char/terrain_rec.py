import pickle,struct,zlib
from pathlib import Path
root=Path.home()/"Documents/Opem Amalur";wc=root/"work/v20-char"
s=(root/"work/v20-inputs/DATA_0.pak/431658.terrain_streamable_bin").read_bytes();idx=pickle.load(open(wc/"terrain-index.pkl","rb"))
for k in ((2176,2304),(1344,3200),(3072,2176)):
    at,comp=idx[k];d=zlib.decompress(s[at:at+comp]);m=struct.pack("<I",361);o=[];i=0
    while True:
        i=d.find(m,i)
        if i<0:break
        o.append(i);i+=4
    print(k,len(d),"count",struct.unpack_from("<I",d,0)[0],"markers at",o[:20],"gaps",[o[j+1]-o[j] for j in range(min(16,len(o)-1))])
    n=struct.unpack_from("<I",d,0)[0];print(" head after count",struct.unpack_from("<8H",d,4),struct.unpack_from("<f",d,20))
    for j in o[:3]:print(" before marker",d[max(0,j-40):j].hex()," after grid",d[j+4+722:j+4+722+24].hex())