import struct,collections,json,zlib
from pathlib import Path
import numpy as np
src=(Path.home()/"Documents/Opem Amalur/work/v20-char/build_npcs.py").read_text()
exec(src[:src.index("SKELS = {}")])
TID="431658";name=f"{TID}.terrain_streamable_bin";s=extract([name])[name].read_bytes()
recs=[];i=0
while True:
    i=s.find(b"\x78\x9c",i)
    if i<0:break
    if i>=24:
        raw,total,zero,raw2,comp=struct.unpack_from("<5I",s,i-20)
        if raw==raw2 and zero==0 and comp<=total<=comp+32 and i+comp<=len(s):
            recs.append((i,raw,comp));i+=comp;continue
    i+=1
print("stream bytes",len(s),"records",len(recs),"first at",recs[0][0],"gaps",collections.Counter(recs[k+1][0]-recs[k][0]-recs[k][2] for k in range(len(recs)-1)).most_common(5))
p=next((root/"work/v20-inputs").rglob("431658.terrain_bin"));b=p.read_bytes()
W=np.frombuffer(b[:len(b)//4*4],"<u4")
for shift in (0,20,24,28,32,16):
    Pa=np.array([r[0]-shift for r in recs if r[1]==66568]);Ha=np.array([r[0]-shift for r in recs if r[1]!=66568])
    print("shift",shift,"paint offsets found",int(np.isin(Pa,W).sum()),"height offsets found",int(np.isin(Ha,W).sum()))
# Sizes of terrain_bin values that fall in stream range, by position in the file
inr=(W>0)&(W<len(s));print("in-range share by block",[round(float(inr[i:i+20000].mean()),2) for i in range(0,len(W),20000)])
# Same test with 32-bit values at other byte alignments
for al in (1,2,3):
    w=np.frombuffer(b[al:al+(len(b)-al)//4*4],"<u4");Pa=np.array([r[0]-24 for r in recs if r[1]==66568]);print("align",al,int(np.isin(Pa,w).sum()))
# Order of the paint records against the height chunks' map keys: which chunk key precedes each paint record?
keys=[];last=None;pairs=[]
for at,raw,comp in recs:
    d=zlib.decompress(s[at:at+comp])
    if raw==66568:pairs.append(last)
    else:last=struct.unpack_from("<I8H",d,0)[1:5]
print("paint record preceded by",pairs[:12],len(set(pairs)))
print("paint positions in sequence",[k for k,r in enumerate(recs) if r[1]==66568][:30])
