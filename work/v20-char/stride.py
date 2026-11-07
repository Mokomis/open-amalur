import collections,json,re,struct
from pathlib import Path
src=(Path.home()/"Documents/Opem Amalur/work/v20-char/build_npcs.py").read_text()
exec(src[:src.index("SKELS = {}")])
out=open(root/"work/v20-char/stride.txt","w",encoding="utf-8");P=lambda *a:print(*a,file=out,flush=True)
log_=(root/"work/v20-char/rebuild.log").read_text(errors="replace");m=re.findall(r"\{'assemblies'[^}]*\}|Counter\(\{[^}]*\}\)|\{[^{}]*other_stride[^{}]*\}",log_);P("last counters",m[-1][:500] if m else None)
sp=[(int(k),str(v)) for k,v in syms["simspace"].items() if re.match(r"out_dal_(north|south|west|tran)_",str(v))]
inst=collections.Counter();byst=collections.Counter();ex=collections.defaultdict(collections.Counter);sh={int(k):str(v) for k,v in syms["shader"].items()}
for sid,n in sp:
    f=extract([f"{sid}.space_bxml"]).get(f"{sid}.space_bxml")
    if not f:continue
    d=f.read_bytes();pl=struct.unpack_from("<I",d,0)[0];b=d[8:8+pl]
    def arr(slot,st):
        p,c=struct.unpack_from("<II",b,slot);return [b[p-8+i*st:p-8+(i+1)*st] for i in range(c)]
    refs=[struct.unpack("<I",r)[0] for r in arr(0x1b0,4)];cen=[struct.unpack("<3f",r) for r in arr(0x1a8,12)];rend=arr(0x160,84);byc={tuple(round(x,2) for x in struct.unpack_from("<3f",r)):r for r in rend};I=[]
    for t,c in zip(refs,cen):
        r=byc.get(tuple(round(x,2) for x in c))
        if r is not None and t>>28==15:I.append((t&0xfffffff,r))
    for a,r in zip(arr(0x148,80),arr(0x150,84)):
        fb=struct.unpack_from("<I",a,52)[0]
        if str(fb) in syms["fab"]:I.append((fb,r))
    for x,r in I:inst[(x,struct.unpack_from("<I",r,64)[0],struct.unpack_from("<I",r,68)[0])]+=1
P("sample render words",[(k,v) for k,v in list(inst.items())[:3]])
import amalur_mesh
cache={}
for (fb,w1,w2),cnt_ in inst.items():
    if fb not in cache:
        fs=extract([f"{fb}.fab_visual_data_streamable_bin"]).get(f"{fb}.fab_visual_data_streamable_bin")
        try:cache[fb]=amalur_mesh.parse_file(fs) if fs else None
        except Exception:cache[fb]=None
    m=cache[fb]
    if not m:continue
    for a in m["assemblies"]:
        vb=m["vertex_buffers"][a["vertex_buffer"]];byst[vb["stride_bytes"]]+=cnt_*vb["vertex_count"]
        if vb["stride_bytes"] not in (48,56,60):ex[vb["stride_bytes"]][syms["fab"].get(str(fb),fb)]+=cnt_
P("placed vertex count by stride",byst.most_common());
for s,c in ex.items():P(s,len(c),c.most_common(50))
b=cache[next(k for k,v in syms["fab"].items() if False) if False else next(int(k) for k,v in syms["fab"].items() if v=="for_river_straight01")]
P("river",[(a["vertex_buffer"],a["index_buffer"],a["unknown_u16_at2"]) for a in b["assemblies"]],[(v["stride_bytes"],v["vertex_count"]) for v in b["vertex_buffers"]],[k for k in b["vertex_buffers"][0]])
fid=next(int(k) for k,v in syms["fab"].items() if v=="for_river_straight01");raw=extract([f"{fid}.fab_visual_data_streamable_bin"])[f"{fid}.fab_visual_data_streamable_bin"].read_bytes();v=b["vertex_buffers"][0];st=v["stride_bytes"];base=v["data_file_offset"]
for i in (0,1,2):P("vtx",struct.unpack_from(f"<{st//4}f",raw,base+i*st),raw[base+i*st:base+i*st+st].hex())
out.close()
