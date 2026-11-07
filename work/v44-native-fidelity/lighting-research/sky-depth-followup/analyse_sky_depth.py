from pathlib import Path
import numpy as np,struct,json
p=Path(__file__).parent;sky=p.parent/'final-filter-sky'
v=np.asarray(list(struct.iter_unpack('<5f',(sky/'sky-vertices.bin').read_bytes())))[:,:3];v=np.c_[v,np.ones(len(v))];ix=np.array(struct.unpack('<1728H',(sky/'sky-indices.bin').read_bytes()))[:1722].reshape(-1,3)
VP=np.asarray(struct.unpack('<64f',(sky/'constants-phase107-binding68.bin').read_bytes())[:16]).reshape(4,4).T;clip=v@VP.T;screen=clip[:,:2]/clip[:,3,None];zs=clip[:,2]/clip[:,3];points=[]
for px,py in [(650,300),(800,290),(750,390),(480,360),(800,450)]:
 q=np.array([2*(px+.5)/1536-1,1-2*(py+.5)/864]);hits=[]
 for ti,ids in enumerate(ix):
  if min(clip[ids,3])<=0:continue
  a,b,c=screen[ids];mat=np.array([b-a,c-a]).T
  if abs(np.linalg.det(mat))<1e-12:continue
  uv=np.linalg.solve(mat,q-a);w=np.r_[1-sum(uv),uv]
  if min(w)>=-1e-9:
   z=np.dot(w,zs[ids]);hits.append({'triangle':ti,'depthD3D':float(z),'in_clip_range':bool(0<=z<=1)})
 points.append({'pixel_top_left':[px,py],'sky_hits':hits})
(p/'sky-pixel-depths.json').write_text(json.dumps(points,indent=2)+'\n');print(json.dumps(points,indent=2))
