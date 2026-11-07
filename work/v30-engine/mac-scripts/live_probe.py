import collections,json,re,struct,subprocess,sys
from pathlib import Path
root=Path.home()/"Documents/Opem Amalur"; inp=root/"work/v20-inputs"
g=Path(r"C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning")
s=json.loads((inp/"symbols.json").read_text())
sys.path[:0]=[str(root/"work/v19-lighting"),str(root/"work/v07-bxml")]
def lst(n):
    b=(root/f"outputs/{n}-archive-list.txt").read_bytes();return set(x.strip() for x in b.decode("utf-16" if b[:2]==b"\xff\xfe" else "utf-8-sig").splitlines() if x.strip())
INI,PAT,DAT=lst("initial"),lst("patch"),lst("DATA")
dest=root/"work/v21-ui/live"; dest.mkdir(parents=True,exist_ok=True)
def unpack(pak,names):
    for i in range(0,len(names),60):
        todo=[n for n in names[i:i+60] if not (dest/n).exists()]
        if todo: subprocess.run([str(g/"modding/pakfileunpacker.exe"),str(g/"data"/pak),"unpack",str(dest),*todo],cwd=g/"modding",capture_output=True,timeout=280)
# 1. Placed objects
gors=sorted(x for x in INI if x.endswith(".gor_bxml"))
unpack("initial_0.pak",gors)
sp=s["simspace"];dal={int(k):str(v) for k,v in sp.items() if re.match(r"out_dal_(north|south|west|tran)_",str(v))}
sim={int(k):str(v) for k,v in s["simtype"].items()}
cnt=collections.Counter();byt=collections.Counter();sample=[];size=collections.Counter()
for n in gors:
    p=dest/n
    if not p.exists(): continue
    b=p.read_bytes()
    if len(b)<40: continue
    space=struct.unpack_from("<I",b,8)[0]
    if space not in dal: continue
    cnt[dal[space]]+=1
    found=None
    for o in range(0,min(len(b)-4,160),4):
        v=struct.unpack_from("<I",b,o)[0]
        if v in sim: found=sim[v];break
    k=(found or "?").split("_")[0];byt[k]+=1
    if len(sample)<6: sample.append((n,len(b),found,struct.unpack_from("<3f",b,24)))
print("gor in dal",sum(cnt.values()),byt.most_common(25));print(sample)
# 2. Lights
import decode_scene_lighting as D
print("lighting fns",[x for x in dir(D) if not x.startswith("_")][:30])
b=(inp/"patch_0.pak/431608.region_bxml") if (inp/"patch_0.pak/431608.region_bxml").exists() else (inp/"DATA_0.pak/431608.region_bxml")
d=b.read_bytes();r=D.decode_region(d)
print("region keys",list(r.keys())[:30]);E=r["environment"];print("env keys",list(E.keys())[:40]);print("time keys",list(E["time_keyed"].keys())[:40])
sd=(inp/"DATA_0.pak/431638.space_bxml").read_bytes() if (inp/"DATA_0.pak/431638.space_bxml").exists() else None
if sd and hasattr(D,"decode_space"):
    q=D.decode_space(sd);print("space keys",list(q.keys()) if isinstance(q,dict) else type(q));print({k:(len(v) if hasattr(v,'__len__') else v) for k,v in q.items()} if isinstance(q,dict) else "")
# 3. Foliage
v=inp/"DATA_0.pak/431658.veggie_streamable_bin"; vb=v.read_bytes() if v.exists() else b""
print("veggie",len(vb),vb[:96].hex())
ids={}
for c,mp in s.items():
    if isinstance(mp,dict):
        for k,nm in mp.items(): ids.setdefault(int(k),f"{c}:{nm}")
hits=collections.Counter()
step=len(vb)//4//400000+1
for o in range(0,len(vb)-4,4*step):
    w=struct.unpack_from("<I",vb,o)[0]
    if w in ids and w>1000: hits[ids[w]]+=1
print("veggie ids",hits.most_common(20))
tb=[n for n in DAT|INI|PAT if n.startswith("431658.")];print(tb)
for n in ("431658.terrain_bin",):
    for a in ("DATA_0.pak","initial_0.pak","patch_0.pak"):
        q=inp/a/n
        if q.exists():
            t=q.read_bytes();print(n,len(t),t[:64].hex());refs=collections.Counter();
            for o in range(0,len(t)-4,4):
                w=struct.unpack_from("<I",t,o)[0]
                if w in ids and w>1000: refs[ids[w]]+=1
            print(" refs",refs.most_common(30))
# 4. Enemy groups
print("encounters",[str(v) for v in s["encounter"].values() if re.search("(?i)dal",str(v))][:8],sum(1 for v in s["encounter"].values() if re.search("(?i)dal",str(v))))
print("fx water",[str(v) for v in s["fab"].values() if re.search("(?i)water|river|ocean|lake",str(v))][:12])
print("cluster/fx simple",len(s["cluster"]))
