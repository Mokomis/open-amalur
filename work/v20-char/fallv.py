import json,struct,re,collections
from pathlib import Path
import numpy as np
src=(Path.home()/"Documents/Opem Amalur/work/v20-char/build_npcs.py").read_text()
exec(src[:src.index("SKELS = {}")])
out=open(root/"work/v20-char/fallv.txt","w",encoding="utf-8");P=lambda *a:print(*a,file=out,flush=True)
for name in ("for_river_fallfree02","for_river_fall01","for_river_straight01","for_river_splash"):
    fid=next(int(k) for k,v in syms["fab"].items() if v==name);p=extract([f"{fid}.fab_visual_data_streamable_bin"])[f"{fid}.fab_visual_data_streamable_bin"];m=amalur_mesh.parse_file(p);raw=p.read_bytes()
    for a in m["assemblies"]:
        if a["unknown_u16_at2"]:continue
        v=m["vertex_buffers"][a["vertex_buffer"]];st=v["stride_bytes"];b=v["data_file_offset"];n=v["vertex_count"];P(name,"stride",st,"verts",n,{k:v[k] for k in v if k not in ("positions",)} if False else "")
        arr=np.frombuffer(raw,"u1",n*st,b).reshape(n,st)
        P(" byte columns: distinct/mean per offset",[(o,len(set(arr[:,o].tolist())),int(arr[:,o].mean())) for o in range(12,st)])
        for i in (0,1,n//2):P("  ",arr[i].tobytes().hex())
        break
out.close()
