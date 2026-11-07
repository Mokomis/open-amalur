import collections,json,re,struct,math
from pathlib import Path
src=(Path.home()/"Documents/Opem Amalur/work/v20-char/build_npcs.py").read_text()
exec(src[:src.index("SKELS = {}")])
out=open(root/"work/v20-char/audio2.txt","w",encoding="utf-8");P=lambda *a:print(*a,file=out,flush=True)
c=collections.Counter(x.rsplit(".",1)[-1] for L in listing.values() for x in L);P("all ext",c.most_common(90))
ks=[(a,x) for a,L in listing.items() for x in L if "ksdf" in x.lower() or "__" in x and "ambient_city_lp" in x];P("ksdf",len(ks),ks[:10])
bk=extract(["ambient_city_lp.koarsoundbank"])["ambient_city_lp.koarsoundbank"].read_bytes();P(len(bk));P(bk[:520].hex());
# Do paks list only named ones? Look for en_us etc lists
P("lists",[p.name for p in (root/"outputs").glob("*archive-list*")])
ids=collections.Counter(x.split(".")[-1] for x in listing["initial_0.pak"] if re.match(r"\d+\.",x))
for o in range(0,len(bk)-3,4):
    v=struct.unpack_from("<I",bk,o)[0]
    if 1000<v<3000000:
        hit=[x for L in listing.values() for x in L if x.startswith(f"{v}.") or x.startswith(f"{v}_")]
        if hit:P("ref",o,v,hit[:3])
g2=g
for pak in ("DATA_0.pak","initial_0.pak","patch_0.pak"):
    pass
P("unpacker help");import subprocess
r=subprocess.run([str(g/"modding/pakfileunpacker.exe")],cwd=g/"modding",capture_output=True,timeout=30);P(r.stdout[:500],r.stderr[:300])
for pak in ("en_us_0.pak",):
    r=subprocess.run([str(g/"modding/pakfileunpacker.exe"),str(g/"data"/pak),"list"],cwd=g/"modding",capture_output=True,timeout=120);t=r.stdout.decode("utf-8","replace");Ls=t.splitlines();P(pak,len(Ls),Ls[:6],collections.Counter(x.rsplit(".",1)[-1].strip() for x in Ls).most_common(12));P([x for x in Ls if "ksdf" in x.lower() or "koar" in x.lower()][:10])
out.close()
