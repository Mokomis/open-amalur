import collections,json,re,struct
from pathlib import Path
src=(Path.home()/"Documents/Opem Amalur/work/v20-char/build_npcs.py").read_text()
exec(src[:src.index("SKELS = {}")])
out=open(root/"work/v20-char/river2.txt","w",encoding="utf-8");P=lambda *a:print(*a,file=out,flush=True)
sh={int(k):str(v) for k,v in syms["shader"].items()}
sp=[(int(k),str(v)) for k,v in syms["simspace"].items() if re.match(r"out_dal_(north|south|west|tran)_",str(v))]
fabs=collections.Counter();mats=collections.Counter();sample=None;shad=collections.Counter()
for sid,n in sp:
    d=extract([f"{sid}.space_bxml"]).get(f"{sid}.space_bxml")
    if not d:continue
    d=d.read_bytes();pl=struct.unpack_from("<I",d,0)[0];b=d[8:8+pl]
    def arr(slot,st):
        p,c=struct.unpack_from("<II",b,slot);return [b[p-8+i*st:p-8+(i+1)*st] for i in range(c)]
    for ga,gb,gc in ((0x138,0x168,0x170),(0x140,0x178,0x180)):
        A,B,C=arr(ga,16),arr(gb,80),arr(gc,84)
        for x,y,r in zip(A,B,C):
            f=struct.unpack_from("<I",x,8)[0];fy=struct.unpack_from("<I",y,52)[0];m=struct.unpack_from("<I",r,64)[0];fabs[(hex(ga),syms["fab"].get(str(f),f),syms["fab"].get(str(fy),fy))]+=1;mats[(hex(ga),syms["material"].get(str(m),m))]+=1
            if sample is None:sample=(n,x.hex(),y.hex(),r.hex(),struct.unpack_from("<3f",r,16),struct.unpack_from("<4f",r,32),struct.unpack_from("<3f",r,48),struct.unpack_from("<4f",r,0),struct.unpack_from("<II",r,64))
P("sample",sample);P("fabs",fabs.most_common(30));P("mats",mats.most_common(40))
for grp,mn in list(mats):
    if isinstance(mn,str):
        k=next(int(i) for i,v in syms["material"].items() if str(v)==mn);f=extract([f"{k}.mat_bxml"]).get(f"{k}.mat_bxml")
        if f:b=f.read_bytes();shad[sh.get(struct.unpack_from("<I",b,24)[0])]+=mats[(grp,mn)]
P("by shader",shad.most_common())
for mn in ("riverwater","river","for_pond","for_waterfall"):
    k=next(int(i) for i,v in syms["material"].items() if str(v)==mn);b=extract([f"{k}.mat_bxml"])[f"{k}.mat_bxml"].read_bytes();P(mn,len(b),"shader",sh.get(struct.unpack_from("<I",b,24)[0]),b.hex());P("  words",[(i,round(struct.unpack_from('<f',b,i*4)[0],3)) for i in range(len(b)//4) if 1e-3<abs(struct.unpack_from('<f',b,i*4)[0])<1e4]);P("  refs",[r[1] for r in material_refs(k)])
D=root/"outputs/scene-v19/shaders";t=open(D/"709ff8ee6bd08c98.asm",encoding="latin1").read()
a=t.find("cbuffer g_materialbuffer");P(t[a:t.find("cbuffer g_dynamicbuffer") if "cbuffer g_dynamicbuffer" in t else a+900][:900]);i=t.find("Resource Bindings");P(t[i:i+2300]);P(t[t.find("ps_4"):])
out.close()
