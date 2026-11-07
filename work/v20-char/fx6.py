import re,struct,collections,subprocess,json
from pathlib import Path
root=Path.home()/"Documents/Opem Amalur";g=Path(r"C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning")
d=root/"work/v25-fx";d.mkdir(exist_ok=True)
for lst,pak in (("initial","initial_0.pak"),("patch","patch_0.pak"),("DATA","DATA_0.pak")):
    b=(root/f"outputs/{lst}-archive-list.txt").read_text(encoding="utf-8-sig",errors="replace").splitlines()
    tn=[x for x in b if re.match(r"task(_duplicate\d+)?\.bundle$",x) or re.search(r"\.task$",x) or x.startswith("task") and "bundle" in x]
    print(lst,tn[:12],len(tn))
    if tn:
        (d/pak).mkdir(exist_ok=True)
        r=subprocess.run([str(g/"modding/pakfileunpacker.exe"),str(g/"data"/pak),"unpack",str(d/pak),*tn],cwd=g/"modding",capture_output=True,timeout=250)
        print([(p.name,p.stat().st_size) for p in (d/pak).iterdir()][:14])
want=struct.pack("<I",1602184);want2=struct.pack("<I",1602185)
for p in d.rglob("*.bundle"):
    b=p.read_bytes();print(p.name,len(b),b[:32].hex(),"hit",b.find(want),b.find(want2))
    i=b.find(want)
    if i>=0: print(b[i-16:i+96].hex())
