import collections,json,re,struct,wave
from pathlib import Path
root=Path.home()/"Documents/Opem Amalur"
L=[x.strip() for n in ("initial","patch","DATA") for x in (lambda b:b.decode("utf-16" if b[:2]==b"\xff\xfe" else "utf-8-sig"))((root/f"outputs/{n}-archive-list.txt").read_bytes()).splitlines() if x.strip()]
K=sorted({x for x in L if x.endswith(".ksdf")});B=sorted({x[:-14] for x in L if x.endswith(".koarsoundbank")})
pre=collections.Counter(x.split("__")[0] for x in K)
out=open(root/"work/v20-char/audio4.txt","w",encoding="utf-8");P=lambda *a:print(*a,file=out,flush=True)
P("banks",len(B));P([ (b,pre[b]) for b in B if re.search(r"^ambient|^music|^ui",b)][:90]);P([ (b,pre[b]) for b in B if re.search(r"footstep|bodyfall|weapons|^vocal|player",b)][:60]);P([ (b,pre[b]) for b in B if re.match(r"motion_(wolf|bear|boggart|troll|sprite|brownie|ettin|spider|giant|barghest|thresh|kobold|murghan|jottun|antelope|niskaru|faer|human|player|npc)",b)][:60])
out.close()
