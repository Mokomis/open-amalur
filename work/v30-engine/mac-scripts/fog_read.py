import json,re
from pathlib import Path
root=Path.home()/"Documents/Opem Amalur";D=root/"outputs/scene-v19/shaders";idx=json.load(open(root/"outputs/scene-v19/shader-index.json"))
src=(root/"work/v19-lighting/lighting_model.py").read_text();a=src.index("def fog_constants");print(src[a:a+700])
p=json.load(open(root/"outputs/scene-v19/lighting-provenance.json"))
def walk(o):
    if isinstance(o,dict):
        s=json.dumps(o)
        if re.search("fog",s,re.I) and "claim" in o:print("PROV",s[:420])
        else:
            for v in o.values():walk(v)
    elif isinstance(o,list):
        for v in o:walk(v)
walk(p)
fog=[k for k,v in idx.items() if any(re.search("fog",x,re.I) for x in v["vars"])]
print("shaders naming fog",len(fog),[(k,idx[k]["type"],idx[k]["lines"],sorted(idx[k]["cbuffers"])) for k in fog][:14])
print("all fog vars",sorted({x for k in fog for x in idx[k]["vars"] if re.search("fog",x,re.I)}))
t=open(D/"a7fae241e409721f.asm",encoding="latin1").read();print("=== a7fae241 (lit alpha PS, globals + material)");print(t[:3800] if len(t)<9000 else t[:3200]);print("...");b=t[t.find("ps_"):];print(b[:3800])
