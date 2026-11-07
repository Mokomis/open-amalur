import re, struct, subprocess, json
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
g = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning")
d = root/"references/mburbea--ModelSwapper/ModelSwapper"
print((d/"SimTypeAsset.cs").read_text(errors="replace")[:2600])
t=(d/"Program.cs").read_text(errors="replace"); i=t.find("simtype_bxml"); print(t[max(0,i-500):i+900])
dest=root/"work/v21-ui/simtype/items"; dest.mkdir(parents=True,exist_ok=True)
names=[f"{i}.simtype_bxml" for i in (252852,264002,125871,206059,501312,87275,385257,87211)]
for pak in ("patch_0","initial_0"):
    subprocess.run([str(g/"modding/pakfileunpacker.exe"),str(g/"data"/f"{pak}.pak"),"unpack",str(dest),*names],cwd=g/"modding",capture_output=True,timeout=120)
for n in names:
    p=dest/n
    if p.exists():
        b=p.read_bytes(); print(n,len(b),b[:96].hex())
