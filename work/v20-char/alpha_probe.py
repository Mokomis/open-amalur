import json,struct,sys,os
from pathlib import Path
import numpy as np
from PIL import Image
root=Path.home()/"Documents/Opem Amalur";zone=root/"work/v22-stress/zone-dal"
os.environ["OA_TEXTURE_LIMIT"]="256"
src=(root/"work/v20-char/build_town.py").read_text();sys.argv=["b","1",str(zone)];exec(src[:src.index("# Placed models")])
meta=json.loads((zone/"zone_materials.json").read_text());g=meta["materials"][meta["grass"]]
out=root/"work/v21-ui/live";
for nm,tid in (("d",g["d"]),("a",g["a"])):
    w,h,p=decode_best(tid);a=np.frombuffer(p,'u1').reshape(h,w,4);print(nm,w,h,"means",a.reshape(-1,4).mean(0).round(1),"per channel frac>128",(a.reshape(-1,4)>128).mean(0).round(3))
    Image.fromarray(a[:,:,:3]).save(out/f"grass_{nm}.png")
