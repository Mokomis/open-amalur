import re,struct,collections,json
from pathlib import Path
root=Path.home()/"Documents/Opem Amalur"
syms=json.loads((root/"work/v20-inputs/symbols.json").read_text())
ALL={}
for k,d in syms.items():
    if isinstance(d,dict) and k not in("main","main64"):
        for i,v in d.items():
            try: ALL.setdefault(int(i),(k,str(v)))
            except: pass
T={int(k):str(v) for k,v in syms["task"].items()}
tex={int(k):str(v) for k,v in syms["texture"].items()}
b=(root/"work/v25-fx/initial_0.pak/batch_1477.task_bxml").read_bytes()
n=struct.unpack_from("<I",b)[0];rec={};o=4+n*8
for i in range(n):
    k,l=struct.unpack_from("<II",b,4+i*8);rec[k]=(o,l);o+=l
print("records",n,"end",o,len(b))
names=collections.Counter()
for k in rec: names[re.sub(r".*_","",T.get(k,"?")).lower()]+=1
print(names.most_common(10))
def show(k):
    o,l=rec[k];q=b[o:o+l];print("--",k,T.get(k),"len",l)
    W=struct.unpack_from(f"<{l//4}I",q);F=struct.unpack_from(f"<{l//4}f",q)
    out=[]
    for i,(w,f) in enumerate(zip(W,F)):
        if w in tex: s="T:"+tex[w]
        elif w in ALL: s=f"{ALL[w][0]}:{ALL[w][1]}"
        elif w==0: s="0"
        elif 1e-4<abs(f)<1e6 and w>0x1000000: s=f"{f:.3f}"
        else: s=hex(w)
        out.append(s)
    print(" ".join(out)[:1500])
for k in (1602184,1602185,1602182,1602183,1602186,1602187,1602188,1602189):
    if k in rec: show(k)
# size classes of particle and emitter
for tail in ("emitter_task","particle_task"):
    L=collections.Counter(rec[k][1] for k in rec if T.get(k,"").lower().endswith(tail));print(tail,L.most_common(10))
