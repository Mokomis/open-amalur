import collections,json,re,struct
from pathlib import Path
root=Path.home()/"Documents/Opem Amalur";inp=root/"work/v20-inputs"
s=json.loads((inp/"symbols.json").read_text())
sp=s["simspace"];dal={int(k):str(v) for k,v in sp.items() if re.match(r"out_dal_(north|south|west|tran)_",str(v))}
print("spaces",len(dal),"symbol tables",list(s.keys()))
sim={int(k):str(v) for k,v in s["simtype"].items()}
rows=[]
d=root/"work/v21-ui/live"
for p in d.glob("*.gor_bxml"):
    b=p.read_bytes()
    if len(b)<60:continue
    space=struct.unpack_from("<I",b,8)[0]
    if space not in dal:continue
    found=None
    for o in range(0,min(len(b)-4,160),4):
        v=struct.unpack_from("<I",b,o)[0]
        if v in sim:found=(v,sim[v]);break
    rows.append((p.name[:-9],len(b),found,struct.unpack_from("<3f",b,24),dal[space]))
print("gors",len(rows))
c=collections.Counter(r[2][1] if r[2] else "?" for r in rows)
pre=collections.Counter((r[2][1] if r[2] else "?").split("_")[0] for r in rows)
print(pre.most_common(60))
A=re.compile(r"npc|citizen|human|troll|boggart|antelope|wolf|bolgan|brownie|sprite|spider|ettin|deer|boar|kobold|thrall|tuatha|niskaru|faelin|dokkalfar|ljos|varani|almain|fae|bandit|creature|animal|enc_|encounter|monster",re.I)
act=[r for r in rows if r[2] and A.search(r[2][1]) or A.search(r[0])]
print("actor-like",len(act))
g=collections.Counter(r[2][1] if r[2] else r[0] for r in act)
for k,n in g.most_common(140):print(n,k)
print("name samples",[r[0] for r in rows[:60]])
print("encounters",[str(v) for v in s["encounter"].values() if re.search("(?i)dal",str(v))])
enc=[r for r in rows if "enc" in r[0].lower()]
print("enc-named",len(enc),enc[:20])
print("bytes eg")
for r in act[:3]:
    print(r[0],(d/(r[0]+".gor_bxml")).read_bytes().hex())
