import json
from pathlib import Path
import numpy as np
from PIL import Image
root=Path.home()/"Documents/Opem Amalur";z=root/"work/v22-stress/zone-dal"
H=np.load(z/"terrain_H.npy");gx,gy=json.loads((z/"terrain_H.json").read_text());ny,nx=H.shape
print("H",H.shape,gx,gy)
dx=np.abs(np.diff(H,axis=1));dy=np.abs(np.diff(H,axis=0))
for t in (100,200,400,800,1600):print("steps over",t,int((dx>t).sum()),int((dy>t).sum()))
cx=int((20300-gx)/100);cy=int((-43211-gy)/100);r=120
W=H[cy-r:cy+r,cx-r:cx+r]
print("near range",np.nanmin(W),np.nanmax(W))
v=np.nan_to_num((W-np.nanmin(W))/(np.nanmax(W)-np.nanmin(W)+1));Image.fromarray((v[::-1]*255).astype(np.uint8)).resize((720,720),Image.NEAREST).save(root/"work/v21-ui/live/steps.png")
print("row",np.round(H[cy,cx-30:cx+30:3]).tolist())
print("col",np.round(H[cy-30:cy+30:3,cx]).tolist())
big=(np.nan_to_num(dx[:-1,:])>150)|(np.nan_to_num(dy[:,:-1])>150)
img=np.zeros(big.shape,np.uint8);img[big]=255;Image.fromarray(img[::-1]).save(root/"work/v21-ui/live/stepsall.png")
