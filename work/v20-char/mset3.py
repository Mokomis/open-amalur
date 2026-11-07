import json,re,struct
from pathlib import Path
root=Path.home()/"Documents/Opem Amalur";s=json.loads((root/"work/v20-inputs/symbols.json").read_text())
n=sorted(str(v) for v in s["animation"].values())
print([x for x in n if re.match(r"human_sword",x,re.I) and not x.lower().endswith("_f")])
print([x for x in n if re.match(r"human_(unarmed|weapon|combat|1h|melee|armed|idle|draw|sheath)",x,re.I) and not x.lower().endswith("_f")][:50])
print([x for x in n if re.search(r"sheath|unsheath|draw",x,re.I) and re.match("human",x,re.I)][:20])
