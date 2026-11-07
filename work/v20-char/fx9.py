import re,struct,collections,json
from pathlib import Path
root=Path.home()/"Documents/Opem Amalur"
syms=json.loads((root/"work/v20-inputs/symbols.json").read_text())
T={int(k):str(v) for k,v in syms["task"].items()}
b=(root/"work/v25-fx/initial_0.pak/batch_1477.task_bxml").read_bytes()
n=struct.unpack_from("<I",b)[0];rec={};o=4+n*8
for i in range(n):
    k,l=struct.unpack_from("<II",b,4+i*8);rec[k]=(o,l);o+=l
# Which 32-bit values recur at any byte offset across all emitter and particle records: these are the property and type hashes.
cnt=collections.Counter()
sel=[k for k in rec if T.get(k,"").lower().endswith(("emitter_task","particle_task"))]
for k in sel:
    o,l=rec[k];q=b[o:o+l]
    for i in range(l-3):
        w=struct.unpack_from("<I",q,i)[0]
        if 0x10000<w<0x2000000: cnt[w]+=1
common=[(hex(w),c) for w,c in cnt.most_common(70)]
print(len(sel),common)
com={w for w,c in cnt.items() if c>=len(sel)//8}
def dump(k):
    o,l=rec[k];q=b[o:o+l];print("--",T.get(k),l);i=0;line=[]
    while i<l:
        if i+4<=l and struct.unpack_from("<I",q,i)[0] in com:
            print(" ".join(line));line=[f"[{i}] #{struct.unpack_from('<I',q,i)[0]:x}"];i+=4
        else:
            line.append(f"{q[i]:02x}");i+=1
    print(" ".join(line))
dump(1602189);dump(1602188)
