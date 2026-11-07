import collections,json,re,struct
from pathlib import Path
src=(Path.home()/"Documents/Opem Amalur/work/v20-char/enc_probe.py").read_text()
exec(src[:src.index("encs={")])
encs={int(k):str(v) for k,v in s["encounter"].items()}
mg={int(k):str(v) for k,v in s["monstergroup"].items()}
sp={int(k):str(v) for k,v in s["simspace"].items() if re.match(r"out_dal_(north|south|west|tran)_",str(v))}
def scan(name,b):
    h=collections.Counter()
    for o in range(0,len(b)-3):
        v=struct.unpack_from("<I",b,o)[0]
        if v in encs: h["enc:"+encs[v]]+=1
        elif v in mg: h["mg:"+mg[v]]+=1
    print(name,len(b),h.most_common(14))
print("space files",sorted({x.split(".",1)[1] for S in L.values() for x in S if x.startswith(str(next(iter(sp)))+".")}))
for k,n in list(sp.items())[:6]:
    for e in ("space_bxml",):
        b=get(f"{k}.{e}")
        if b: scan(n+"."+e,b)
for n in ("431608.region_bxml","431608.bundle"):
    b=get(n); 
    if b: scan(n,b)
# which gors reference encounters at any offset
hits=[]
for p in dest.glob("*.gor_bxml"):
    b=p.read_bytes()
    for o in range(0,len(b)-3):
        v=struct.unpack_from("<I",b,o)[0]
        if v in encs or v in mg:
            hits.append((p.name[:-9],encs.get(v) or mg.get(v),round(struct.unpack_from("<f",b,24)[0]),round(struct.unpack_from("<f",b,28)[0]),struct.unpack_from("<I",b,8)[0] in sp));break
print("gors naming encounter/group",len(hits),[h for h in hits if h[4]][:30],hits[:6])
# locationmarker and invisible names in the zone
names=collections.Counter()
for p in dest.glob("*.gor_bxml"):
    b=p.read_bytes()
    if len(b)>=60 and struct.unpack_from("<I",b,8)[0] in sp:
        w=[ids[v][0] for o in range(0,min(len(b)-4,160),4) for v in [struct.unpack_from("<I",b,o)[0]] if v in ids and ids[v][0].startswith("simtype:")]
        if w and re.search("locationmarker|invisible",w[0]): names[re.sub(r"[\d_]+$","",p.name[:-9])]+=1
print(names.most_common(60))
m=get(f"{next(k for k,v in mg.items() if v=='boggarts__a')}.monstergroup_bxml");print("boggarts__a",m.hex() if m else None,[x[2] for x in refs(m)] if m else "")
m=get(f"{next(k for k,v in encs.items() if v=='enc_dal_haxhi')}.encounter_bxml");print("enc",m[:156].hex())
