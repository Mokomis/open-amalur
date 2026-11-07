"""Optional authored collision from recovered prop meshes. No original physics parity claim."""
from pathlib import Path
import struct,json,hashlib,collections,math
import numpy as np
w=Path(__file__).resolve().parent;r=w.parents[1];base=r/'work/v40-windows-host/assets/world';src=w/'static-props-overlay';out=w/'visual-collision-overlay'
if out.exists():raise SystemExit('Preserve previous collision output')
manifest=json.loads((w/'static-props-manifest.json').read_text());cellsize=struct.unpack_from('<f',(src/'index.bin').read_bytes(),4)[0];buckets=collections.defaultdict(list);total=0;degenerate=0
for name in manifest['files']:
 if not name.startswith('c')or not name.endswith('_0.bin'):continue
 b=(src/name).read_bytes();old=(w/'before-static-props'/name).read_bytes();nv,ni,nd=struct.unpack_from('<3I',b,4);ov,oi,od=struct.unpack_from('<3I',old,4)
 p=np.ndarray((nv,3),'<f4',b,16+nd*12,(28,4));indices=np.frombuffer(b,'<u4',ni,16+nd*12+nv*28)[oi:];tris=p[indices].reshape(-1,3,3).copy()
 area=np.linalg.norm(np.cross(tris[:,1]-tris[:,0],tris[:,2]-tris[:,0]),axis=1);degenerate+=int((area<1e-5).sum());tris=tris[area>=1e-5];total+=len(tris)
 # A triangle enters every XY cell its bounds touch, matching the reader's 3x3 neighborhood.
 lo=np.floor(tris[:,:,:2].min(1)/cellsize).astype(int);hi=np.floor(tris[:,:,:2].max(1)/cellsize).astype(int)
 assert ((hi-lo)<=2).all()
 for ix in range(int(lo[:,0].min()),int(hi[:,0].max())+1):
  for iy in range(int(lo[:,1].min()),int(hi[:,1].max())+1):
   mask=(lo[:,0]<=ix)&(hi[:,0]>=ix)&(lo[:,1]<=iy)&(hi[:,1]>=iy)
   if mask.any():buckets[(ix,iy)].append(tris[mask])
existing={}
def read_count(name):
 p=base/name
 if not p.exists():return 0
 with p.open('rb')as f:b=f.read(4)
 n=struct.unpack('<I',b)[0];assert p.stat().st_size==4+n*36;return n
for name in base.glob('k*.bin'):existing[name.name]=read_count(name.name)
extra={f'k{x}_{y}.bin':np.concatenate(parts).astype('<f4')for(x,y),parts in buckets.items()}
changed_neighborhoods={(x+dx,y+dy)for x,y in buckets for dx in [-1,0,1]for dy in [-1,0,1]};neighborhoods=[]
for x,y in changed_neighborhoods:
 names=[f'k{x+dx}_{y+dy}.bin'for dx in [-1,0,1]for dy in [-1,0,1]];old=sum(existing.get(n,0)for n in names);new=old+sum(len(extra[n])for n in names if n in extra)
 neighborhoods.append({'x':x,'y':y,'old':old,'new':new});assert new<=300000,('Controller triangle cap exceeded',x,y,old,new)
out.mkdir();files={};sha=lambda b:hashlib.sha256(b).hexdigest()
for name,tri in extra.items():
 p=base/name;old=p.read_bytes()if p.exists()else struct.pack('<I',0);n=struct.unpack_from('<I',old)[0];data=struct.pack('<I',n+len(tri))+old[4:]+tri.tobytes();(out/name).write_bytes(data);assert data[4:4+n*36]==old[4:]
 files[name]={'sha256':sha(data),'before_sha256':sha(old)if p.exists()else None,'bytes':len(data)}
# Two actual 3x3 packs for a controller integration check near recovered crate1390814.
target=next(p for p in manifest['placements']if p['instance_id']==1390814);cx,cy=target['cell']
for mode in ['before','after']:
 parts=[]
 for dx in [-1,0,1]:
  for dy in [-1,0,1]:
   name=f'k{cx+dx}_{cy+dy}.bin';p=(out/name)if mode=='after'and(out/name).exists()else(base/name)
   if p.exists():parts.append(p.read_bytes()[4:])
 data=b''.join(parts);(w/f'controller-{mode}.bin').write_bytes(struct.pack('<I',len(data)//36)+data)
result={'files':files,'source':'static-props-manifest.json','collision_policy':'Authored static triangle collision from recovered visual meshes; no native rigid-body/destruction/loot behavior','unique_added_triangles':total,'degenerate_removed':degenerate,'binned_triangle_copies':sum(len(t)for t in extra.values()),'max_3x3_triangles':max(x['new']for x in neighborhoods),'neighborhoods':neighborhoods,'target':target}
(w/'visual-collision-manifest.json').write_text(json.dumps(result,indent=2));print('Collision overlay',len(files),'cells;',total,'triangles;',result['max_3x3_triangles'],'peak neighborhood')
