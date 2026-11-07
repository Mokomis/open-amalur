import collections,json,re,struct,zlib,binascii
from pathlib import Path
src=(Path.home()/"Documents/Opem Amalur/work/v20-char/build_npcs.py").read_text()
exec(src[:src.index("SKELS = {}")])
out=open(root/"work/v20-char/water4.txt","w",encoding="utf-8");P=lambda *a:print(*a,file=out,flush=True)
K={"fog_density_scale":0x1138f27,"fog_distance_scale":0x14401b0,"sky_max":0x2cced2,"bloom_min_lum":0x94fa56}
def tests(s):
    b=s.encode();yield "crc",binascii.crc32(b)
    h=0x811c9dc5
    for c in b:h=(h*16777619)&0xffffffff;h^=c
    yield "fnv1",h
    h=0x811c9dc5
    for c in b:h^=c;h=(h*16777619)&0xffffffff
    yield "fnv1a",h
    h=5381
    for c in b:h=(h*33+c)&0xffffffff
    yield "djb2",h
    h=0
    for c in b:h=(c+(h<<6)+(h<<16)-h)&0xffffffff
    yield "sdbm",h
    h=0
    for c in b:h=(h*31+c)&0xffffffff
    yield "j31",h
    h=0
    for c in b:h=((h<<4)+c)&0xffffffff;g=h&0xf0000000;h=(h^(g>>24))&~g&0xffffffff
    yield "pjw",h
for n,v in K.items():
    P(n,hex(v),[(a,hex(x)) for a,x in tests(n) if (x&0xffffff)==(v&0xffffff) or (x&0x1ffffff)==v or x==v])
for mn in ("riverwater","for_waterfall","for_web_01"):
    k=next(int(i) for i,v in syms["material"].items() if str(v)==mn);b=extract([f"{k}.mat_bxml"])[f"{k}.mat_bxml"].read_bytes();W=struct.unpack_from(f"<{len(b)//4}I",b);F=struct.unpack_from(f"<{len(b)//4}f",b);P(mn,len(b),"shader",syms["shader"].get(str(W[6])))
    P(" head",[hex(x) for x in W[:7]])
    for i in range(7,len(W)-5,6):P("  ",i,hex(W[i]),hex(W[i+1]),hex(W[i+2]),[round(F[i+j],3) for j in range(3,6)],(syms["texture"].get(str(W[i])),))
    P(" all tex",[(i,syms["texture"].get(str(x))) for i,x in enumerate(W) if str(x) in syms["texture"]])
idx=json.load(open(root/"outputs/scene-v19/shader-index.json"));D=root/"outputs/scene-v19/shaders"
vs=[(v["lines"],k) for k,v in idx.items() if v["type"]=="vs" and "DetailNormalScrollSpeed" in v["vars"]];P("river VS",vs[:4])
if vs:
    t=open(D/(vs[0][1]+".asm"),encoding="latin1").read();a=t.find("vs_");P(t[t.find("cbuffer g_materialbuffer"):t.find("cbuffer g_materialbuffer")+560]);P(t[a:a+3400])
for ps in ("db5c4b1329799f28","ca77b6f297c27a99"):
    t=open(D/(ps+".asm"),encoding="latin1").read();i=t.find("Resource Bindings");P("==",ps,t[i:i+900]);a=t.find("ps_");P(t[a:a+5200])
P("cube1",(root/"work/v19-lighting/cube1.py").read_text()[:1200])
P("cube files",[x for L in listing.values() for x in L if x.startswith("743412")][:10])
out.close()
