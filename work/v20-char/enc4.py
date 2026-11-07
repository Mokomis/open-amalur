import collections,json,re,struct
from pathlib import Path
src=(Path.home()/"Documents/Opem Amalur/work/v20-char/enc_probe.py").read_text()
exec(src[:src.index("encs={")])
encs={int(k):str(v) for k,v in s["encounter"].items()}
mg={int(k):str(v) for k,v in s["monstergroup"].items()}
sp={int(k):str(v) for k,v in s["simspace"].items() if re.match(r"out_dal_(north|south|west|tran)_",str(v))}
k=next(k for k,v in sp.items() if v=="out_dal_north_03");b=get(f"{k}.space_bxml")
print("center",struct.unpack_from("<3f",b,12))
o=78124
print("rec words",[hex(x) for x in struct.unpack_from("<15I",b,o-16)])
for base in (0,4,8,12,16):
    p1=struct.unpack_from("<I",b,o-16)[0]+base
    print(base,"at p1",[round(x,1) for x in struct.unpack_from("<12f",b,p1)])
p=struct.unpack_from("<I",b,o-16)[0]
print("raw around",b[p-16:p+80].hex())
# Walk all spaces: every 60-byte record chain with an encounter id.
tot=collections.Counter();out=[]
for k,n in sp.items():
    b=get(f"{k}.space_bxml")
    if not b:continue
    head=struct.unpack_from("<3f",b,12)
    for o in range(16,len(b)-48):
        v=struct.unpack_from("<I",b,o)[0]
        if v in encs:
            p1,c1,p2,c2=struct.unpack_from("<4I",b,o-16)
            if c1!=c2 or not 0<c1<64 or p1>=len(b):continue
            pts=[]
            for i in range(c1):
                pts.append(struct.unpack_from("<3f",b,p1+i*12))
            out.append((n,encs[v],c1,[tuple(round(x) for x in q) for q in pts][:3]));tot[encs[v]]+=c1
print("records",len(out),"pts",sum(tot.values()));print(out[:14]);print(tot.most_common(40))
print("head",[ (n,[round(x) for x in struct.unpack_from('<3f',get(f'{k}.space_bxml'),12)]) for k,n in list(sp.items())[:4]])
