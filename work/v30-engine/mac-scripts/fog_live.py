import json,re,sys
from pathlib import Path
root=Path.home()/"Documents/Opem Amalur";out=open(root/"work/v20-char/fog4.txt","w",encoding="utf-8")
def P(*a):print(*a,file=out)
p=json.load(open(root/"outputs/scene-v19/lighting-provenance.json"))
def walk(o):
    if isinstance(o,dict):
        s=json.dumps(o)
        if "claim" in o and re.search("fog|live|luminance|shift|g_global",s,re.I):P("PROV",s[:600])
        else:
            for v in o.values():walk(v)
    elif isinstance(o,list):
        for v in o:walk(v)
walk(p)
for name in ("lum.py","prov2.py","write_v19.py","fin.py"):
    f=root/"work/v19-lighting"/name;t=f.read_text(errors="replace")
    for m in re.finditer(r".{0,200}(worldToFog|fog_scale|fogScale|density_scale|shift_weight|luminance_shift|0xB8).{0,240}",t):P(name,"::",m.group(0)[:440])
sys.path[:0]=[str(root/"work/v19-lighting"),str(root/"work/v07-bxml")]
import decode_scene_lighting as D
inp=root/"work/v20-inputs"
for pak in ("patch_0.pak","DATA_0.pak"):
    q=inp/pak/"431608.region_bxml"
    if q.exists():
        r=D.decode_region(q.read_bytes());TK=r["environment"]["time_keyed"];P("region from",pak,"keys",list(TK)[:40])
        for k in ("fog_color","fog_start","fog_density"):P(k,json.dumps(TK.get(k))[:700])
        P("non-time env",{k:v for k,v in r["environment"].items() if k!="time_keyed"} if len(str(r["environment"]))<4000 else list(r["environment"].keys()))
        break
print("ok")
for f in (root/"work").rglob("*"):
    if f.is_file() and f.suffix in (".json",".txt",".log") and f.stat().st_size<3000000:
        try:t=f.read_text(errors="ignore")
        except Exception:continue
        if "worldToFogConstants" in t:P("FILE",f,len(t));[P("  ",m.group(0)[:300]) for m in list(re.finditer(r".{0,120}worldToFogConstants.{0,160}",t))[:3]]
for f in (root/"outputs/scene-v19").glob("*.json"):
    t=f.read_text(errors="ignore")
    if re.search("worldToFog|luminance_shift",t) and f.name!="lighting-provenance.json":P("OUTPUT",f.name,len(t));[P("  ",m.group(0)[:300]) for m in list(re.finditer(r".{0,120}(worldToFog|luminance_shift).{0,200}",t))[:4]]
out.close()
