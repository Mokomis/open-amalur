import collections,json,re
from pathlib import Path
root=Path.home()/"Documents/Opem Amalur"
ext=collections.Counter();size=collections.Counter()
for f in (root/"outputs").glob("*-archive-list.txt"):
    b=f.read_bytes()
    for m in re.finditer(rb"[0-9]+\.([a-z_0-9]+)",b):
        ext[m.group(1).decode()]+=1
print(f"{len(ext)} extensions");print(ext.most_common(70))
s=json.loads((root/"work/v20-inputs/symbols.json").read_text())
print([k for k in s if re.search("fx|effect|particle|emit|vfx|decal|trail",k,re.I)])
for k in s:
    if re.search("fx|effect|particle|emit|vfx",k,re.I):
        v=list(s[k].values());print(k,len(v),[str(x) for x in v[:10]])
