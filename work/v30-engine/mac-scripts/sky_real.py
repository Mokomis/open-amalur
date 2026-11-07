import collections,json,re,struct
from pathlib import Path
src=(Path.home()/"Documents/Opem Amalur/work/v20-char/build_npcs.py").read_text()
exec(src[:src.index("SKELS = {}")])
ids={}
for c,mp in syms.items():
    if isinstance(mp,dict):
        for k,nm in mp.items():ids.setdefault(int(k),[]).append(f"{c}:{nm}")
allf=lambda i:[x for L in listing.values() for x in L if x.startswith(f"{i}.") or x.startswith(f"{i}_")]
for t in ("shader","platform_shader"):
    for k,v in syms[t].items():
        if str(v).lower() in ("dot3alpha","dot3","dot3alpha_deferred") or re.fullmatch(r"(4x_)?dot3alpha\w*",str(v),re.I):print(t,k,v,allf(k)[:6])
print("shader exts",collections.Counter(x.split(".")[-1] for L in listing.values() for x in L if re.search("shader|fx|hlsl|cso|fxo|vso|pso",x.split(".")[-1])).most_common(20))
sid=next(int(k) for k,v in syms["shader"].items() if str(v)=="dot3alpha")
for n in allf(sid):
    f=extract([n]).get(n)
    if f:
        b=f.read_bytes();print(n,len(b),b[:64].hex());print(" strings",[x.decode() for x in re.findall(rb"[A-Za-z_][A-Za-z0-9_ ./]{4,}",b)][:50]);print(" refs",[ids[v][0] for o in range(0,len(b)-3,4) for v in [struct.unpack_from("<I",b,o)[0]] if v>1000 and v in ids][:30])
mid=next(int(k) for k,v in syms["material"].items() if str(v)=="for_skyline01");b=extract([f"{mid}.mat_bxml"])[f"{mid}.mat_bxml"].read_bytes();print("mat hex",b.hex())
ref=next(int(k) for k,v in syms["material"].items() if str(v)=="for_rock_cliff" or str(v).startswith("for_rock_cliff"));c=extract([f"{ref}.mat_bxml"]).get(f"{ref}.mat_bxml");print("compare",syms["material"][str(ref)],c.read_bytes().hex() if c else None)
for fn in ("for_skyline_mountain01","for_skyline_trees01"):
    fid=next(int(k) for k,v in syms["fab"].items() if str(v)==fn);fs=extract([f"{fid}.fab_bxml"]);fb=fs[f"{fid}.fab_bxml"].read_bytes();print(fn,fid,len(fb),allf(fid)[:6],"refs",[ids[v][0] for o in range(0,len(fb)-3) for v in [struct.unpack_from("<I",fb,o)[0]] if v>1000 and v in ids][:12]);print(" head",fb[:80].hex())
print("exe strings next: tools",[p.name for p in (root/"work/v19-lighting").glob("*")][:30])
