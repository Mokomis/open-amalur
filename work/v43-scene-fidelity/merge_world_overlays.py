"""Merge independent source-verified overlays without overwriting another overlay's geometry."""
from pathlib import Path
import struct,json,hashlib,collections
import numpy as np
v=Path(__file__).resolve().parent;r=v.parents[1];base=r/'work/v40-windows-host/assets/world';a=v/'placement-research/barrel02-overlay';b=v/'terrain-research/pack-overlay';light=v/'lighting-overlay';out=v/'integrated-world'
if out.exists():raise SystemExit('Preserve the existing integrated pack; select a new output scope')
sha=lambda data:hashlib.sha256(data).hexdigest();out.mkdir();files={};checks=[]
def save(name,data):
 (out/name).write_bytes(data);old=base/name;files[name]={'sha256':sha(data),'bytes':len(data),'before_sha256':sha(old.read_bytes())if old.exists()else None}
def parse(data):
 assert data[:4]==b'OAWC';nv,ni,nd=struct.unpack_from('<3I',data,4);assert nd<=128 and len(data)==16+nd*12+nv*28+ni*4
 return nv,ni,[data[16+i*12:28+i*12]for i in range(nd)],data[16+nd*12:16+nd*12+nv*28],data[16+nd*12+nv*28:]
def extras(original,rows):
 left=collections.Counter(original);extra=[]
 for row in rows:
  if left[row]:left[row]-=1
  else:extra.append(row)
 assert not any(left.values()),'Original draw record omitted'
 return extra
# All non-cell terrain assets and measured lighting profile can be copied directly.
for source in [b,light]:
 for p in source.iterdir():
  if p.is_file()and p.name!='index.bin'and not(p.name.startswith('c')and p.suffix=='.bin'):save(p.name,p.read_bytes())
index=bytearray((base/'index.bin').read_bytes());nc=struct.unpack_from('<I',index,8)[0];assert len(index)==20+48*nc
idx={(struct.unpack_from('<ii',index,20+i*48)):20+i*48 for i in range(nc)}
newnames=sorted({p.name for folder in [a,b]for p in folder.glob('c*.bin')})
barrel_tris=collections.Counter()
for name in newnames:
 original=(base/name).read_bytes();nv,ni,draws,verts,indices=parse(original);av,ai,ar,va,ia=parse((a/name).read_bytes())if(a/name).exists()else(nv,ni,draws,verts,indices)
 bv,bi,br,vb,ib=parse((b/name).read_bytes())if(b/name).exists()else(nv,ni,draws,verts,indices)
 assert bv==nv and bi==ni and vb==verts and ib==indices
 assert va[:len(verts)]==verts and ia[:len(indices)]==indices
 rows=draws+extras(draws,ar)+extras(draws,br);assert len(rows)<=128
 data=b'OAWC'+struct.pack('<3I',av,ai,len(rows))+b''.join(rows)+va+ia
 assert np.frombuffer(ia,'<u4').max()<av
 for row in rows:
  material,first,count=struct.unpack('<3I',row);assert first+count<=ai
 save(name,data);checks.append({'file':name,'original_vertices_indices_preserved':True,'original_draws_preserved':True,'draws':len(rows)})
 if(a/name).exists():
  x,y,lod=map(int,name[1:-4].split('_'));at=idx[(x,y)];P=np.ndarray((av,3),'<f4',va,0,(28,4));lo=np.minimum(struct.unpack_from('<3f',index,at+8),P.min(0));hi=np.maximum(struct.unpack_from('<3f',index,at+20),P.max(0));struct.pack_into('<6f',index,at+8,*lo,*hi);struct.pack_into('<I',index,at+32+4*lod,ai//3)
  if lod==0:barrel_tris[name]=(np.ndarray((av,3),'<f4',va,0,(28,4))[np.frombuffer(ia,'<u4')[ni:]]).reshape(-1,3,3).copy()
struct.pack_into('<I',index,12,655);save('index.bin',bytes(index))
# Optional static collision for the sixteen newly recovered barrels, using the
# same authored visual-mesh policy already validated for the first251 props.
cellsize=struct.unpack_from('<f',index,4)[0];buckets=collections.defaultdict(list);added=0
for tris in barrel_tris.values():
 area=np.linalg.norm(np.cross(tris[:,1]-tris[:,0],tris[:,2]-tris[:,0]),axis=1);tris=tris[area>=1e-5];added+=len(tris);lo=np.floor(tris[:,:,:2].min(1)/cellsize).astype(int);hi=np.floor(tris[:,:,:2].max(1)/cellsize).astype(int)
 for x in range(int(lo[:,0].min()),int(hi[:,0].max())+1):
  for y in range(int(lo[:,1].min()),int(hi[:,1].max())+1):
   mask=(lo[:,0]<=x)&(hi[:,0]>=x)&(lo[:,1]<=y)&(hi[:,1]>=y)
   if mask.any():buckets[(x,y)].append(tris[mask])
for (x,y),parts in buckets.items():
 name=f'k{x}_{y}.bin';p=base/name;old=p.read_bytes()if p.exists()else struct.pack('<I',0);n=struct.unpack_from('<I',old)[0];new=np.concatenate(parts).astype('<f4');assert len(old)==4+n*36;save(name,struct.pack('<I',n+len(new))+old[4:]+new.tobytes())
peak=0
for x,y in {(x+dx,y+dy)for x,y in buckets for dx in [-1,0,1]for dy in [-1,0,1]}:
 n=0
 for dx in [-1,0,1]:
  for dy in [-1,0,1]:
   name=f'k{x+dx}_{y+dy}.bin';p=out/name if(out/name).exists()else base/name
   if p.exists():
    with p.open('rb')as f:n+=struct.unpack('<I',f.read(4))[0]
 peak=max(peak,n);assert n<=300000
result={'files':files,'cell_integrity':checks,'new_barrels':16,'new_barrel_collision_triangles':added,'collision_peak_affected_neighborhood':peak,'terrain_reference_cells':18,'native_terrain_material_count':5,'material_total':263,'texture_count':655,'source_manifests':['placement-research/barrel02-manifest.json','terrain-research/pack-overlay-report.json','lighting-overlay-manifest.json'],'limits':['Terrain coverage limited to18referencecells; undefinednativeowners retainlegacyground','Staticmeshcollisionisauthored,notnativephysics','Scopedmateriallightingremainsapartialnativeequation']}
(v/'integrated-world-manifest.json').write_text(json.dumps(result,indent=2));print('MERGED',len(checks),'cellLODs,',len(files),'files;',added,'newbarrelcollisiontriangles;peak',peak)
