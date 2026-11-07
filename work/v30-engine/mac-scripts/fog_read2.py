import json,re,struct,collections
from pathlib import Path
src=(Path.home()/"Documents/Opem Amalur/work/v20-char/build_npcs.py").read_text()
exec(src[:src.index("SKELS = {}")])
D=root/"outputs/scene-v19/shaders";idx=json.load(open(root/"outputs/scene-v19/shader-index.json"))
body=lambda k:(lambda t:t[t.find("ps_" if idx[k]["type"]=="ps" else "vs_"):])(open(D/(k+".asm"),encoding="latin1").read())
print("=== db4503 alpha-test depth PS");print(open(D/"db4503ee162f02b7.asm",encoding="latin1").read()[:900]);print(body("db4503ee162f02b7")[:700])
tint=[k for k,v in idx.items() if "sunlightFogTintAmount" in v["vars"]];print("tint vars in",len(tint))
used=[]
for k,v in idx.items():
    if v["type"]=="ps" and "g_globalbuffer" in v["cbuffers"]:
        t=open(D/(k+".asm"),encoding="latin1").read();m=re.search(r"g_globalbuffer\s+cbuffer\s+NA\s+NA\s+cb(\d+)",t)
        if m:
            c=m.group(1);b=body(k)
            if re.search(rf"cb{c}\[80\]\.[xyzw]|cb{c}\[0\]\.",b):used.append((v["lines"],k,c,bool(re.search(rf"cb{c}\[80\]",b))))
used.sort();print("PS using fogColor",len(used),used[:6],"with tint",[u for u in used if u[3]][:4])
k=next((u for u in used if u[3]),None)
if k:
    b=body(k[1]).split("\n");I=[i for i,l in enumerate(b) if re.search(rf"cb{k[2]}\[(0|80|1)\]",l)]
    for i in I[:6]:print(i,"\n".join(b[max(0,i-3):i+5]));print("--")
vs=[(v["lines"],k) for k,v in idx.items() if v["type"]=="vs" and "worldToFogConstants" in v["vars"]];vs.sort();print("VS",vs[:3]);b=body(vs[0][1]).split("\n");print("\n".join(l for l in b if re.search(r"cb\d\[1\]\.|o\d\.[xyzw]+,? ",l))[:900])
# Alpha reference in materials across dot3alpha, and how it lines up with their masks.
vals=collections.Counter();sid=419915
for mk,mv in list(syms["material"].items()):
    f=(inp/"initial_0.pak"/f"{mk}.mat_bxml")
    if not f.exists():continue
    b=f.read_bytes()
    if len(b)>=48 and struct.unpack_from("<I",b,24)[0]==sid:vals[struct.unpack_from("<I",b,36)[0]]+=1
print("dot3alpha word at +36",vals.most_common(10))
