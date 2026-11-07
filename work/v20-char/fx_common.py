"""Reads effect tasks: emitter and particle records from the batch task files, and cluster files. Channel layout worked out from the data."""
import re,struct,collections,json
from pathlib import Path
root=Path.home()/"Documents/Opem Amalur"
ONE=struct.pack("<f",1.0)
def load_tasks():
    rec={}
    for fn in ("batch_1477","batch_1658189","batch_1946058","batch_1966575"):
        b=(root/f"work/v25-fx/initial_0.pak/{fn}.task_bxml").read_bytes()
        n=struct.unpack_from("<I",b)[0];o=4+n*8
        for i in range(n):
            k,l=struct.unpack_from("<II",b,4+i*8)
            rec.setdefault(k,b[o:o+l]);o+=l
    return rec
def channels(q):
    pts=[];p=4
    while p+28<=len(q):
        if q[p+8:p+16]==b"\0"*8 and q[p+24:p+28]==ONE and struct.unpack_from("<I",q,p)[0]>0x10000 and struct.unpack_from("<I",q,p+4)[0]>0x10000 and struct.unpack_from("<I",q,p)[0]!=0x854bf:
            pts.append(p);p+=28
        else:p+=1
    out={}
    for a,e in zip(pts,pts[1:]+[len(q)]):
        cl,nm=struct.unpack_from("<II",q,a);out.setdefault(nm,(cl,q[a+28:e]))
    return out
def cluster(b):
    """List of (kind,a,b) children and the fade distances."""
    n=struct.unpack_from("<I",b)[0];o=4;kids=[]
    for i in range(n):
        if o+4>len(b):break
        k=struct.unpack_from("<I",b,o)[0]
        if k==0x6ed2b0:
            x,y,x2,y2=struct.unpack_from("<4I",b,o+4);kids.append((k,x,y));o+=20
        else:
            x=struct.unpack_from("<I",b,o+4)[0];kids.append((k,x,0));o+=12
    return kids,o
