import json,re,collections
from pathlib import Path
root=Path.home()/"Documents/Opem Amalur"
s=json.loads((root/"work/v20-inputs/symbols.json").read_text())
A={int(k):str(v) for k,v in s["animation"].items()}
H=sorted(v for v in A.values() if re.match(r"human_(?!sword|hammer|staff|dagger|fae|chak|great|long|bow|mage|rog|war|spell)",v,re.I))
print(len(A),len(H))
pat=re.compile(r"start|stop|turn|slope|strafe|pivot|jump|land|fall|sprint|walk|run",re.I)
print([v for v in H if pat.search(v)][:120])
print([v for v in sorted(A.values()) if re.match(r"human_sword",v,re.I) and pat.search(v)][:60])
print([k for k in s if "motion" in k or "anim" in k])
