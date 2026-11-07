import json,re,struct
from pathlib import Path
src=(Path.home()/"Documents/Opem Amalur/work/v20-char/build_npcs.py").read_text()
exec(src[:src.index("SKELS = {}")])
out=open(root/"work/v20-char/headtex.txt","w",encoding="utf-8");P=lambda *a:print(*a,file=out,flush=True)
t=(root/"work/v20-char/character.log").read_text(errors="replace");i=t.rfind('"parts"');
m=re.findall(r'"label": "(\w+)",\s*"fab": (\d+).*?"material": "?([^",\n]*)"?,\s*"textures": (\[.*?\]),\s*"chosen": "?([^"\n]*)"?',t,re.S)
for r in m:P(r[0],r[1],r[2],r[3][:120].replace("\n",""),"CHOSEN",r[4][:80])
fid=1362163;fb=extract([f"{fid}.fab_bxml"])[f"{fid}.fab_bxml"].read_bytes()
ordered,at=[],struct.unpack_from("<I",fb,0)[0]+8
while at+4<=len(fb):
    v=struct.unpack_from("<I",fb,at)[0]
    if v>4096 and str(v) in syms["material"]:ordered.append(v);at+=4
    else:at+=1
P("head surfaces",[(v,syms["material"][str(v)]) for v in ordered])
for v in ordered[:5]:
    refs=material_refs(v);P(syms["material"][str(v)],refs);f=extract([f"{v}.mat_bxml"])[f"{v}.mat_bxml"].read_bytes();P(" shader",syms["shader"].get(str(struct.unpack_from("<I",f,24)[0])))
    from PIL import Image
    import numpy as np
    for tid,name in refs:
        b=decode_best(tid)
        if b:
            a=np.frombuffer(b[2],'u1').reshape(b[1],b[0],4);P("  ",name,b[0],b[1],"mean",a.reshape(-1,4).mean(0).round(0).tolist())
            if v==ordered[1] or v==ordered[0]:Image.fromarray(a[:,:,:3]).save(root/f"work/v21-ui/live/{name}.png")
out.close()
