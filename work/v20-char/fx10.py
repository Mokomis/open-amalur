import re,struct,collections,json,sys
from pathlib import Path
root=Path.home()/"Documents/Opem Amalur"
syms=json.loads((root/"work/v20-inputs/symbols.json").read_text())
T={int(k):str(v) for k,v in syms["task"].items()};Mat={int(k):str(v) for k,v in syms["material"].items()}
b=(root/"work/v25-fx/initial_0.pak/batch_1477.task_bxml").read_bytes()
n=struct.unpack_from("<I",b)[0];rec={};o=4+n*8
for i in range(n):
    k,l=struct.unpack_from("<II",b,4+i*8);rec[k]=(o,l);o+=l
ONE=struct.pack("<f",1.0)
def channels(q):
    # A channel starts where bytes +8..15 are zero, +16 is a small count and +24 is 1.0.
    pts=[]
    p=4
    while p+28<=len(q):
        if q[p+8:p+16]==b"\0"*8 and q[p+24:p+28]==ONE and struct.unpack_from("<I",q,p)[0]>0x10000 and struct.unpack_from("<I",q,p+4)[0]>0x10000:
            pts.append(p);p+=28
        else:p+=1
    return pts
Cl=collections.Counter();Pay=collections.defaultdict(collections.Counter);cnt=collections.Counter()
sel=[k for k in rec if re.search(r"(emitter|particle)_task$",T.get(k,""),re.I)]
for k in sel:
    o,l=rec[k];q=b[o:o+l];pts=channels(q);c=struct.unpack_from("<I",q,0)[0];cnt[len(pts)==c]+=1
    for a,e in zip(pts,pts[1:]+[l]):
        cl,nm=struct.unpack_from("<II",q,a);Cl[(hex(cl),hex(nm))]+=1;Pay[(hex(cl),hex(nm))][e-a-28]+=1
print("records",len(sel),"count matches channels",cnt)
for key,c in Cl.most_common(40):print(key,c,Pay[key].most_common(4))
def dump(k):
    o,l=rec[k];q=b[o:o+l];pts=channels(q);print("--",T[k],l,"count",struct.unpack_from("<I",q,0)[0],"found",len(pts))
    for a,e in zip(pts,pts[1:]+[l]):
        cl,nm=struct.unpack_from("<II",q,a);P=q[a+28:e];F=[round(x,3) if abs(x)<1e6 else None for x in struct.unpack_from(f"<{len(P)//4}f",P)];W=struct.unpack_from(f"<{len(P)//4}I",P)
        print(f" {cl:x}/{nm:x} +16={struct.unpack_from('<I',q,a+16)[0]} len {e-a-28}",[Mat.get(w,None) for w in W if w in Mat][:2],W[:6],F[:18])
dump(1602189);dump(1602188)
