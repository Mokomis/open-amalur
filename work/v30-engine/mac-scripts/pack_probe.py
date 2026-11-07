import json,re
from pathlib import Path
root=Path.home()/"Documents/Opem Amalur"
print((root/"work/v09-textures/material_package.py").read_text()[:2600])
s=json.loads((root/"work/v20-inputs/symbols.json").read_text())
print([v for v in s["texture"].values() if re.search(r"(?i)grass|fern|veg_|foliage|weed|clover|shrub",str(v)) and not re.search(r"_(n|s|g)$",str(v))][:60])
print([v for v in s["material"].values() if re.search(r"(?i)grass|fern|veg_|weed|clover",str(v))][:40])
t=(root/"work/v19-host/package_android.py").read_text()
for l in t.splitlines():
    if re.search(r"town|STRESS|compress|ZIP|zipfile|writestr|aapt|-0",l): print("PKG",l.strip()[:170])
