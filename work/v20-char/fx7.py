import re,struct,collections,subprocess,json
from pathlib import Path
root=Path.home()/"Documents/Opem Amalur";g=Path(r"C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning")
d=root/"work/v25-fx/initial_0.pak"
b=(root/"outputs/initial-archive-list.txt").read_text(encoding="utf-8-sig",errors="replace").splitlines()
tn=[x for x in b if x.startswith("batch")]
print(len(tn),collections.Counter(x.split(".")[-1] for x in tn).most_common(30),tn[:10])
fx=[x for x in tn if "fx" in x or "task" in x]
print("fx batches",len(fx),fx[:20])
for i in range(0,min(len(fx),400),40):
    subprocess.run([str(g/"modding/pakfileunpacker.exe"),str(g/"data/initial_0.pak"),"unpack",str(d),*fx[i:i+40]],cwd=g/"modding",capture_output=True,timeout=250)
want=[struct.pack("<I",x) for x in (1602184,1602185,1602182)]
total=0
for n in fx[:400]:
    p=d/n
    if not p.exists(): continue
    q=p.read_bytes();total+=len(q)
    if any(w in q for w in want):
        print("HIT",n,len(q),[q.find(w) for w in want]);print(q[:64].hex())
print("bytes",total)
sizes=sorted(((d/n).stat().st_size,n) for n in fx[:400] if (d/n).exists());print(sizes[-6:])
