import collections,json,re,struct,subprocess,sys
from pathlib import Path
root=Path.home()/"Documents/Opem Amalur";inp=root/"work/v20-inputs"
g=Path(r"C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning")
s=json.loads((inp/"symbols.json").read_text())
ids={}
for c,mp in s.items():
    if isinstance(mp,dict):
        for k,nm in mp.items():
            ids.setdefault(int(k),[]).append(f"{c}:{nm}")
def lst(n):
    b=(root/f"outputs/{n}-archive-list.txt").read_bytes();return set(x.strip() for x in b.decode("utf-16" if b[:2]==b"\xff\xfe" else "utf-8-sig").splitlines() if x.strip())
L={"DATA_0.pak":lst("DATA"),"initial_0.pak":lst("initial"),"patch_0.pak":lst("patch")}
dest=root/"work/v21-ui/live"
def get(n):
    for a,S in L.items():
        if n in S:
            if not (dest/n).exists(): subprocess.run([str(g/"modding/pakfileunpacker.exe"),str(g/"data"/a),"unpack",str(dest),n],cwd=g/"modding",capture_output=True,timeout=120)
            if (dest/n).exists(): return (dest/n).read_bytes()
    return None
def refs(b):
    out=[]
    for o in range(0,len(b)-3):
        v=struct.unpack_from("<I",b,o)[0]
        if v>1000 and v in ids: out.append((o,v,ids[v][0]))
    return out
encs={int(k):str(v) for k,v in s["encounter"].items() if re.search("(?i)^enc_dal",str(v))}
exts=collections.Counter(x.split(".")[-1] for S in L.values() for x in S)
print("exts",[e for e in exts if re.search("enc|monster|vignette|group|spawn",e)])
for i,(k,n) in enumerate(encs.items()):
    b=get(f"{k}.encounter_bxml")
    if b is None: print(n,"missing");continue
    r=refs(b)
    if i<8: print(n,len(b),[x[2] for x in r][:24])
mg={int(k):str(v) for k,v in s["monstergroup"].items()}
print("monstergroups",len(mg),list(mg.values())[:10])
mx=[(k,n) for k,n in mg.items() if re.search("(?i)dal|troll|boggart",n)][:3]
for k,n in mx:
    for e in ("monstergroup_bxml","monster_group_bxml"):
        b=get(f"{k}.{e}")
        if b: print(n,e,len(b),[x[2] for x in refs(b)][:20]);break
    else: print(n,[x for S in L.values() for x in S if x.startswith(str(k)+".")][:4])
# markers
d=dest
rows=[]
for p in d.glob("*.gor_bxml"):
    b=p.read_bytes()
    if len(b)<60:continue
    t=[x[2] for x in refs(b[:160])]
    if re.search("(?i)vignette|marker|spawn|encounter",p.name) or any(re.search("encounter|vignette|monstergroup",x) for x in t):
        rows.append((p.name[:-9],t[:4],[round(v) for v in struct.unpack_from("<3f",b,24)]))
print("markers",len(rows),rows[:25])
print("vignettes",[str(v) for v in s["vignette"].values() if re.search("(?i)dal",str(v))][:12],len(s["vignette"]))
v=[(int(k),str(n)) for k,n in s["vignette"].items() if re.search("(?i)dal",str(n))][:2]
for k,n in v:
    print(n,[x for S in L.values() for x in S if x.startswith(str(k)+".")][:4])
for k in (431658,431608):
    print(k,sorted({x for S in L.values() for x in S if x.startswith(f"{k}.")}))
# simtype bundles and clips
A=s["animation"]
for pre in ("antelope","troll","boggart","wolf","bear","sprite","human_walk","human_run","human_female","human_npc"):
    n=[str(v) for v in A.values() if str(v).lower().startswith(pre)]
    pick=[x for x in n if re.search("(?i)idle|walk|run|attack|death|react|hit|flee",x)]
    print(pre,len(n),pick[:26])
for nm in ("troll_mountain","antelope_a","boggart_plaguebearer_noemerge","wolf_forest","sprite_champion_of_flame","human_bandit_swordsman"):
    sid=next((int(k) for k,v in s["simtype"].items() if v==nm),None)
    b=get(f"{sid}.bundle")
    if not b: print(nm,sid,"no bundle");continue
    w=list(dict.fromkeys(struct.unpack_from(f"<{(len(b)-16)//4}I",b,16)))
    cats=collections.Counter(ids[v][0].split(":")[0] for v in w if v in ids)
    print(nm,sid,len(b),cats.most_common(10))
    print(" fab",[ids[v][0] for v in w if v in ids and ids[v][0].startswith("fab:")][:14])
    print(" ragdoll",[ids[v][0] for v in w if v in ids and ids[v][0].startswith("ragdoll:")][:4],"motion",[ids[v][0] for v in w if v in ids and re.match("motion",ids[v][0])][:6])
    print(" anim",[ids[v][0][10:] for v in w if v in ids and ids[v][0].startswith("animation:")][:30])
