import json,re,struct,collections
from pathlib import Path
src=(Path.home()/"Documents/Opem Amalur/work/v20-char/build_npcs.py").read_text()
exec(src[:src.index("SKELS = {}")])
T={int(k):str(v) for k,v in syms["task"].items()}
print("tasks",len(T),collections.Counter(re.sub(r".*_","",v).lower() for v in T.values()).most_common(12))
ALL={}
for k,d in syms.items():
    if isinstance(d,dict):
        for i,v in d.items():
            try: ALL.setdefault(int(i),(k,str(v)))
            except: pass
n="5025.bundle";fs=extract([n]);print(n,{a:b.stat().st_size for a,b in fs.items()})
if n in fs:
    b=fs[n].read_bytes();W=struct.unpack_from(f"<{len(b)//4}I",b);print(len(W),[ALL.get(w,w) for w in W[:30]])
# Which listed files mention the task hash? Search small types in unpacked inputs.
cnt=collections.Counter();hits=[]
want=struct.pack("<I",1602184)
for p in (inp).rglob("*"):
    if p.is_file() and p.stat().st_size<3_000_000:
        d=p.read_bytes()
        if want in d: hits.append((p.name,len(d),d.index(want)));cnt[p.suffix]+=1
print(cnt,hits[:12])
