import json, re, struct, subprocess
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
syms = json.loads((root / "work/v20-inputs/symbols.json").read_text())
print({k: v for k, v in syms["terrainpaletteset"].items() if "odayle" in v or "legacy" in v})
tex = syms["texture"]
hits = sorted(v for v in tex.values() if re.search(r"(^|_)(ter|terrain|grass|dirt|mud|ground|gravel|path|road|soil|moss)", v, re.I) and v.endswith("_d"))
print(len(hits), hits[:90])
