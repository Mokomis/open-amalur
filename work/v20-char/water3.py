import collections,json,re,struct
from pathlib import Path
src=(Path.home()/"Documents/Opem Amalur/work/v20-char/build_npcs.py").read_text()
exec(src[:src.index("SKELS = {}")])
fabs={int(k):str(v) for k,v in syms["fab"].items() if re.search(r"river|waterplane|pond|waterfall",str(v),re.I)}
sp={int(k):str(v) for k,v in syms["simspace"].items() if re.match(r"out_dal_(north|south|west|tran)_",str(v))}
tot=collections.Counter();sam={}
for k,n in sp.items():
    f=extract([f"{k}.space_bxml"]).get(f"{k}.space_bxml")
    if not f:continue
    b=f.read_bytes()
    for o in range(0,len(b)-3):
        v=struct.unpack_from("<I",b,o)[0]
        if v in fabs:
            tot[fabs[v]]+=1;sam.setdefault(fabs[v],(n,o,[round(x) for x in struct.unpack_from("<3f",b,o+4)],b[o-16:o+40].hex()))
print("river fabs in spaces",tot.most_common(30));print(list(sam.items())[:3])
