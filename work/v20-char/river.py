import collections,json,re,struct
from pathlib import Path
src=(Path.home()/"Documents/Opem Amalur/work/v20-char/build_npcs.py").read_text()
exec(src[:src.index("SKELS = {}")])
out=open(root/"work/v20-char/river.txt","w",encoding="utf-8");P=lambda *a:print(*a,file=out,flush=True)
riv={int(k):str(v) for k,v in syms["fab"].items() if re.search(r"^for_river|waterplane|for_fountain_water|waterfall",str(v),re.I)}
mats={int(k) for k,v in syms["material"].items() if re.search(r"river|pond|waterfall|^water",str(v),re.I)};print(len(riv))
sp=[(int(k),str(v)) for k,v in syms["simspace"].items() if re.match(r"out_dal_(north|south|west|tran)_",str(v))]
agg=collections.Counter()
for sid,n in sp[:8]:
    d=extract([f"{sid}.space_bxml"])[f"{sid}.space_bxml"].read_bytes();pl=struct.unpack_from("<I",d,0)[0];b=d[8:8+pl]
    # pointer slots
    slots=[]
    for s in range(0,0x400,8):
        if s+8>len(b):break
        p,c=struct.unpack_from("<II",b,s)
        if 8<=p<=len(b) and 0<c<2000000:slots.append((s,p,c))
    slots.sort(key=lambda x:x[1])
    hits=collections.Counter();mhits=collections.Counter();where=[]
    for o in range(0,len(b)-3,4):
        v=struct.unpack_from("<I",b,o)[0]
        if v in riv or (v&0xfffffff) in riv or v in mats:
            sl=None
            for s,p,c in slots:
                if p-8<=o:sl=(s,p,c)
                else:break
            key=hex(sl[0]) if sl else "?"
            (mhits if v in mats else hits)[key]+=1
            if len(where)<4:where.append((key,hex(o),hex(v),riv.get(v&0xfffffff) or "mat",(o-(sl[1]-8))/max(1,1) if sl else 0))
    P(n,"fab hits by slot",hits.most_common(6),"mat hits",mhits.most_common(4),where[:3])
    if not agg:
        P("slots",[(hex(s),p,c) for s,p,c in slots][:50])
    agg.update(hits)
# Render record for river materials: material word at +64?
sid,n=sp[0];d=extract([f"{sid}.space_bxml"])[f"{sid}.space_bxml"].read_bytes();pl=struct.unpack_from("<I",d,0)[0];b=d[8:8+pl]
def arr(slot,st):
    p,c=struct.unpack_from("<II",b,slot);return [b[p-8+i*st:p-8+(i+1)*st] for i in range(c)]
r=arr(0x160,84);P("render",len(r));cc=collections.Counter(struct.unpack_from("<I",x,64)[0] for x in r);P("render materials",[(syms["material"].get(str(k),k),v) for k,v in cc.most_common(200) if k in mats][:10]);r2=arr(0x150,84);c2=collections.Counter(struct.unpack_from("<I",x,64)[0] for x in r2);P("placed render materials",[(syms["material"].get(str(k),k),v) for k,v in c2.most_common(300) if k in mats][:10],len(r2))
refs=[struct.unpack("<I",x)[0] for x in arr(0x1b0,4)];P("ref types",collections.Counter(x>>28 for x in refs).most_common());P("riv refs",[(hex(x),riv.get(x&0xfffffff)) for x in refs if (x&0xfffffff) in riv][:10])
out.close()
