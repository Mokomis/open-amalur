import re, struct, subprocess, json, collections
from pathlib import Path
root = Path.home() / "Documents/Opem Amalur"
g = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning")
dest=root/"work/v21-ui/simtype/items"; dest.mkdir(parents=True,exist_ok=True)
L={n:(root/f"outputs/{n}-archive-list.txt").read_text(errors="replace").split() for n in("DATA","initial","patch")}
for n,l in L.items():
    print(n,[x for x in l if re.search(r"(^|[^0-9])(252852|264002|125871|501312)([^0-9]|$)|sword1h_common01a|warrior_common01a_torso|alchemypotion_healthrestoration_01",x)][:10], collections.Counter(x.rsplit('.',1)[-1] for x in l if 'simtype' in x).most_common(5))
want=[x for n in ("initial","patch") for x in L[n] if re.fullmatch(r"(sword1h_common01a|warrior_common01a_torso|alchemypotion_healthrestoration_01|parent_sword_1h|weapon_default|item_default)\.bundle|(252852|125871|501312|385257|87275|87211)\..*",x)]
print("want",want)
for pak in ("patch_0","initial_0"):
    subprocess.run([str(g/"modding/pakfileunpacker.exe"),str(g/"data"/f"{pak}.pak"),"unpack",str(dest),*sorted(set(want))],cwd=g/"modding",capture_output=True,timeout=120)
s=json.loads((root/"work/v20-inputs/symbols.json").read_text())
ids={}
for cat,v in s.items():
    if isinstance(v,dict):
        for k,n in v.items(): ids.setdefault(int(k),f"{cat}:{n}")
for p in sorted(dest.iterdir()):
    b=p.read_bytes(); print("##",p.name,len(b),b[:32].hex())
    print("   strings",re.findall(rb"[A-Za-z_][\w. ]{4,}",b)[:16])
    if len(b)<40000:
        hits=[]
        for o in range(0,len(b)-4):
            v=struct.unpack_from("<I",b,o)[0]
            if v in ids and v>1000: hits.append((o,ids[v]))
        print("   ids",hits[:30])
