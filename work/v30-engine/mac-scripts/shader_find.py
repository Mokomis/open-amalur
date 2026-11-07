import json,re,collections,sys
from pathlib import Path
root=Path.home()/"Documents/Opem Amalur";D=root/"outputs/scene-v19/shaders";idx=json.load(open(root/"outputs/scene-v19/shader-index.json"))
print(len(idx),"sample",list(idx.items())[:2])
print([p.name for p in (root/"outputs/scene-v19").iterdir() if "shader" in p.name or "lighting" in p.name or "provenance" in p.name][:12])
keys=collections.Counter(k for v in idx.values() for k in v);print(keys.most_common(12))
print("types",collections.Counter(v["type"] for v in idx.values()))
# Pixel shaders with alpha test that also fog and use the world's lighting buffers.
rows=[]
for k,v in idx.items():
    if v["type"]!="ps":continue
    t=open(D/(k+".asm"),encoding="latin1").read()
    body=t[t.find("ps_"):]
    disc="discard" in body or "clip" in body
    fog="g_globalbuffer" in v["cbuffers"]
    rows.append((k,v["lines"],disc,fog,sorted(v["cbuffers"])[:8],len(re.findall(r"\bsample",body))))
print("ps",len(rows),"with discard",sum(r[2] for r in rows))
for r in sorted([r for r in rows if r[2]],key=lambda r:r[1])[:40]:print(r)
