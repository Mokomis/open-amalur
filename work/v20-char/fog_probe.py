import json,re
from pathlib import Path
root=Path.home()/"Documents/Opem Amalur"
idx=json.loads((root/"outputs/scene-v19/shader-index.json").read_text())
sd=root/"outputs/scene-v19/shaders"
vs=[k for k,e in idx.items() if any(re.search("(?i)fog",v) for v in e.get("vars",[]))]
print(len(vs),[v for v in idx[vs[0]]["vars"] if "fog" in v.lower()] if vs else None)
shown=0
for k in vs:
    b=(sd/f"{k}.asm").read_text(errors="replace")
    m=re.findall(r"(?m)^//\s+(?:float\w*)\s+(fog\w*);\s*// Offset:\s+(\d+)",b)
    if m and shown<1 and idx[k]["type"]=="vs":
        print(k,idx[k]["type"],m);shown+=1
        code=[l for l in b.splitlines() if not l.startswith("//") and l.strip()]
        print("\n".join(code)[:1600])
        for off in sorted(set(int(o) for _,o in m)):
            r,c=off//16,(off%16)//4
            for l in code:
                if f"cb1[{r}]" in l: print("USE",off,l.strip()[:120])
