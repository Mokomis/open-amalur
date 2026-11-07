import json,re
from pathlib import Path
root=Path.home()/"Documents/Opem Amalur";D=root/"outputs/scene-v19/shaders";idx=json.load(open(root/"outputs/scene-v19/shader-index.json"))
out=open(root/"work/v20-char/fog3.txt","w",encoding="utf-8")
def P(*a):print(*a,file=out)
def load(k):
    t=open(D/(k+".asm"),encoding="latin1").read();m=re.search(r"g_globalbuffer\s+cbuffer\s+NA\s+NA\s+cb(\d+)",t);return t,(m.group(1) if m else None),t[t.find(idx[k]["type"]+"_"):]
hits={"fogcolor":[],"tint":[],"vsfog":[]}
for k,v in idx.items():
    if "g_globalbuffer" not in v["cbuffers"]:continue
    t,c,b=load(k)
    if c is None:continue
    if v["type"]=="vs" and re.search(rf"cb{c}\[1\]\.",b):hits["vsfog"].append((v["lines"],k,c))
    if v["type"]=="ps":
        if re.search(rf"cb{c}\[0\]\.",b):hits["fogcolor"].append((v["lines"],k,c))
        if re.search(rf"cb{c}\[80\]\.[zw]",b):hits["tint"].append((v["lines"],k,c))
for n,L in hits.items():L.sort();P(n,len(L),L[:5])
def show(k,c,pat,before=6,after=8,limit=3):
    b=load(k)[2].split("\n");seen=-99;n=0
    for i,l in enumerate(b):
        if re.search(pat,l) and i>seen+after and n<limit:
            n+=1;seen=i;P("\n".join(f"{j}: {b[j]}" for j in range(max(0,i-before),min(len(b),i+after))));P("--")
for key,pat in (("vsfog",r"cb%s\[1\]\."),("fogcolor",r"cb%s\[0\]\."),("tint",r"cb%s\[80\]\.[zw]")):
    if hits[key]:
        _,k,c=hits[key][0];P("=====",key,k,"type",idx[k]["type"]);show(k,c,pat%c)
if hits["tint"]:
    _,k,c=hits["tint"][0];P("=== full tint shader body");P(load(k)[2][:6500])
out.close()
