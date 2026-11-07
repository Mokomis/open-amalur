import json,re,collections
from pathlib import Path
root=Path.home()/"Documents/Opem Amalur"
s=json.loads((root/"work/v20-inputs/symbols.json").read_text())
T=[str(v) for v in s["texture"].values()]
print(sorted(v for v in T if re.search(r"terrain",v,re.I) and v.lower().endswith("_d"))[:90])
print(sorted(v for v in T if re.search(r"(grass)",v,re.I) and v.lower().endswith("_d"))[:40])
print({k:str(v) for k,v in s["terrainpaletteset"].items()})
print(sorted({re.match(r"[a-z0-9]+",v.lower()).group(0) for v in T if re.match(r"[a-z0-9]+_",v.lower())})[:60])
