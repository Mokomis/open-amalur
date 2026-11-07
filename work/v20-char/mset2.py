import json,re,struct
from pathlib import Path
src=(Path.home()/"Documents/Opem Amalur/work/v20-char/build_npcs.py").read_text()
exec(src[:src.index("SKELS = {}")])
out=open(root/"work/v20-char/mset2.txt","w",encoding="utf-8")
def P(*a):print(*a,file=out,flush=True)
A={int(k):str(v) for k,v in syms["animation"].items()}
def clips(name):
    k=next(int(i) for i,v in syms["motionset"].items() if str(v)==name);n=f"{k}.mtns_bxml";b=extract([n])[n].read_bytes();return b,[A[w] for o in range(0,len(b)-3,4) for w in [struct.unpack_from("<I",b,o)[0]] if w in A]
b,c=clips("Player_Weapon_Sword");P("Player_Weapon_Sword",c);P("strings",[x.decode() for x in re.findall(rb"[A-Za-z_][A-Za-z0-9_]{3,}",b)][:60])
b2,c2=clips("Player");P("Player all",c2)
all_names=sorted(set(A.values()));P("HM",[x for x in all_names if x.startswith("HM_")][:60]);P("Human_OneHand locomotion",[x for x in all_names if re.match(r"Human_OneHand",x) and re.search("idle|walk|run|jog|move|strafe",x,re.I)][:40]);P("1H",[x for x in all_names if re.search("1HSword|Player_.*Sword|Sword.*(Idle|Run|Walk)|weapon.*(idle|run)",x,re.I)][:40])
for tn in ("motiontree",):
    P("trees",[str(v) for v in syms[tn].values() if re.search("player|human",str(v),re.I)][:20])
sc=(root/"work/v20-char/build_character.py").read_text().splitlines()
P("\n".join(f"{i+1}: {sc[i][:200]}" for i in range(196,262)))
out.close()
