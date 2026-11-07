import json,re
from pathlib import Path
root=Path.home()/"Documents/Opem Amalur"
ids=[1602184,1602185,1602182,1762,1763,7262896,2148946,448152]
for f in (root/"outputs").glob("*-archive-list.txt"):
    b=f.read_bytes()
    for i in ids:
        for m in re.finditer(rb"(?<![0-9])%d\.[A-Za-z_0-9]+"%i,b):
            print(f.name,m.group(0))
    # non numeric-name extensions
    print(f.name,len(b),[m.decode() for m in set(re.findall(rb"\.[a-z_0-9]*(?:fx|part|emit|ptcl)[a-z_0-9]*",b))][:20])
s=json.loads((root/"work/v20-inputs/symbols.json").read_text())
for i in ids:
    print(i,[k for k in s if str(i) in s[k]][:6],[s[k][str(i)] for k in s if str(i) in s[k]][:3])
print(sorted(s.keys()))
g=Path(r"C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning")
print([p.name for p in (g/"data").iterdir()][:30])
