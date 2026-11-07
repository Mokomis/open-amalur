import json,re,struct
from pathlib import Path
src=(Path.home()/"Documents/Opem Amalur/work/v20-char/build_npcs.py").read_text()
exec(src[:src.index("SKELS = {}")])
A={int(k):str(v) for k,v in syms["animation"].items()}
for name in ("Player_Reactions","Player_Weapon_Sword"):
    k=next(int(i) for i,v in syms["motionset"].items() if str(v)==name);n=f"{k}.mtns_bxml";b=extract([n])[n].read_bytes()
    c=[A[w] for o in range(0,len(b)-3) for w in [struct.unpack_from("<I",b,o)[0]] if w in A];print(name,len(b),list(dict.fromkeys(c))[:60])
names=sorted(A.values())
print([x for x in names if re.search(r"^human_(react|death|hit|stagger|flinch|die)|^player_(react|death|die)",x,re.I) and not x.lower().endswith("_f")][:40])
print({n:next((i for i,v in A.items() if v==n),None) for n in ("human_sword_attack_x_01","human_sword_attack_x_02","human_sword_attack_xx_01","human_sword_attack_xx_02","human_sword_attack_xxx_01","human_sword_attack_xxx_02","human_sword_attack_xxxx_01","human_sword_attack_xxxx_02")})
