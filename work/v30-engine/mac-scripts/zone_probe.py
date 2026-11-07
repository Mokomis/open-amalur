import json,re,struct,subprocess,collections,pickle
from pathlib import Path
root=Path.home()/"Documents/Opem Amalur"; inp=root/"work/v20-inputs"
g=Path(r"C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning")
s=json.loads((inp/"symbols.json").read_text())
def lst(n):
    b=(root/f"outputs/{n}-archive-list.txt").read_bytes();return set(x.strip() for x in b.decode("utf-16" if b[:2]==b"\xff\xfe" else "utf-8-sig").splitlines() if x.strip())
L={n:lst(n) for n in("DATA","initial","patch")}
terr=sorted(x for x in L["DATA"]|L["initial"]|L["patch"] if x.endswith(".terrain_streamable_bin"))
import os
sizes={}
for n,arch in (("DATA","DATA_0.pak"),("initial","initial_0.pak"),("patch","patch_0.pak")):
    r=subprocess.run([str(g/"modding/pakfileunpacker.exe"),str(g/"data"/arch),"list"],capture_output=True,timeout=280,cwd=g/"modding")
    t=r.stdout.decode("utf-8","replace")
    for m in re.finditer(r"(?m)^(.*?(\d+\.(?:terrain_streamable_bin|veggie_streamable_bin|region_bxml|space_bxml|collision_set_bin)))\s.*$",t):
        pass
    print(n,"list sample",t[:300].replace("\n"," | "))
    break
print("terrain symbols",list(s.get("terrain",{}).items())[:8], "terrain files",len(terr))
print("region sample",[ (k,v) for k,v in list(s["region"].items())[:6]])
sp=s["simspace"]
dal=[(k,v) for k,v in sp.items() if re.search(r"(?i)dal",str(v))]
print("dal spaces",len(dal),dal[:40])
outs=collections.Counter(str(v).split("_")[0]+"_"+str(v).split("_")[1] if "_" in str(v) else str(v) for v in sp.values()); print(outs.most_common(30))
# File sizes on disk of terrain by pak listing via unpack of three candidates is expensive; use the region names instead.
print("region names",[v for v in s["region"].values() if re.search(r"(?i)^out|dal|ala|det|klu|ere|esh",str(v))][:60])
print("colset",[v for v in s["collisionset"].values() if re.search(r"(?i)dal",str(v))][:30], list(s["collisionset"].items())[:4])
for k in ("485422","431638","431608","431658"):
    print(k,[c for c,v in s.items() if isinstance(v,dict) and k in v],[v[k] for c,v in s.items() if isinstance(v,dict) and k in v])
