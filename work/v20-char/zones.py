import collections,json,re,struct
from pathlib import Path
src=(Path.home()/"Documents/Opem Amalur/work/v20-char/build_npcs.py").read_text()
exec(src[:src.index("SKELS = {}")])
out=open(root/"work/v20-char/zones.txt","w",encoding="utf-8");P=lambda *a:print(*a,file=out,flush=True)
sp={int(k):str(v) for k,v in syms["simspace"].items()}
g_=collections.Counter(re.match(r"(out_[a-z]+|int_[a-z]+|dgn_[a-z]+|[a-z]+)",v).group(1) for v in sp.values() if re.match(r"[a-z]",v));P(g_.most_common(40))
terr=[x for L in listing.values() for x in L if x.endswith("terrain_streamable_bin")];P("terrains",len(terr),terr[:30])
d={}
for k,n in sp.items():
    if n.startswith("out_"):
        z=re.match(r"out_([a-z]+)",n).group(1);d.setdefault(z,[]).append((k,n))
P({z:len(v) for z,v in d.items()})
info={}
for z,v in d.items():
    k,n=v[0];f=extract([f"{k}.space_bxml"]).get(f"{k}.space_bxml")
    if not f:continue
    b=f.read_bytes();W=struct.unpack_from(f"<{min(16,len(b)//4)}I",b);region=W[15] if len(W)>15 else None
    rn=syms["region"].get(str(region));tf=None
    rb=extract([f"{region}.bundle"]).get(f"{region}.bundle")
    ter=[]
    if rb:
        q=rb.read_bytes();ids=struct.unpack_from(f"<{len(q)//4}I",q);ter=[i for i in ids if f"{i}.terrain_streamable_bin" in terr]
    sz=[(i,round((inp/"DATA_0.pak"/f"{i}.terrain_streamable_bin").stat().st_size/1e6,1)) if (inp/"DATA_0.pak"/f"{i}.terrain_streamable_bin").exists() else (i,None) for i in ter]
    P(z,"spaces",len(v),"region",region,rn,"terrain",sz)
out.close()
