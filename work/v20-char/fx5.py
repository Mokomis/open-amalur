import re,collections
from pathlib import Path
root=Path.home()/"Documents/Opem Amalur"
for f in sorted((root/"outputs").glob("*-archive-list.txt")):
    b=f.read_bytes()
    ext=collections.Counter(m.decode() for m in re.findall(rb"[A-Za-z0-9_\-]+\.([A-Za-z_0-9]+)",b))
    print(f.name,[e for e in ext.most_common(100)][35:100])
    names=re.findall(rb"[A-Za-z_][A-Za-z0-9_\-]*\.[A-Za-z_0-9]+",b)
    print(" named",len(names),[n.decode() for n in names if re.search(rb"fx|task|partic|emit",n,re.I)][:40])
    print(" sample",[n.decode() for n in names[:30]])
    print(" sizes?",b[:300])
