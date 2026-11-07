"""Combine two independently inventoried, asset-disjoint scene collections."""
from pathlib import Path
import platform,json,struct,hashlib,math,shutil
assert platform.system()=='Windows'
root=Path.home()/'Documents/Opem Amalur';out=root/'outputs/scene-v07'
prop_report=json.loads((out/'placements.json').read_text())['baked_scene'];shell_report=json.loads((out/'shell-candidate.json').read_text());audit=json.loads((out/'107-scene-collection-audit.json').read_text())
assert audit['summary']['primary_prop_shared_ids']==[]
assert prop_report['source_scene_sha256']==shell_report['source_scene_sha256']==audit['source_sha256']
props=out/'scene-props.bin'
if not props.exists():
 data=(out/'scene.bin').read_bytes();assert hashlib.sha256(data).hexdigest()==prop_report['scene_sha256'];props.write_bytes(data)
parts=[];lo=[math.inf]*3;hi=[-math.inf]*3;total=0;inputs=[]
for path,report in [(props,prop_report),(out/'scene-shell-candidate.bin',shell_report)]:
 data=path.read_bytes();digest=hashlib.sha256(data).hexdigest();assert digest==report['scene_sha256'];assert data[:8]==b'OMSC07\0\0'
 n=struct.unpack_from('<I',data,8)[0];bounds=struct.unpack_from('<6f',data,12);assert n>0 and n%3==0 and len(data)==36+n*36 and n==report['vertices']
 for v in struct.iter_unpack('<9f',data[36:]):
  assert all(math.isfinite(x) for x in v)
  for axis in range(3):
   assert bounds[axis]-.01<=v[axis]<=bounds[axis+3]+.01
   lo[axis]=min(lo[axis],v[axis]);hi[axis]=max(hi[axis],v[axis])
 inputs.append({'file':path.name,'sha256':digest,'vertices':n,'first_output_vertex':total});total+=n;parts.append(data[36:])
assert 36+total*36<=64*1024*1024
binary=b'OMSC07\0\0'+struct.pack('<I6f',total,*lo,*hi)+b''.join(parts);(out/'scene.bin').write_bytes(binary)
report={'scope':'Combined diagnostic real-scene architecture and props; no gameplay or native renderer equivalence claim.',
 'source_scene_sha256':audit['source_sha256'],'inputs':inputs,'vertices':total,'triangles':total//3,'bounds_min':lo,'bounds_max':hi,
 'scene_sha256':hashlib.sha256(binary).hexdigest(),'scene_bytes':len(binary),'primary_static_assemblies':shell_report['primary_records_loaded'],
 'prop_instances':prop_report['geometry_placements_loaded'],'asset_ids_disjoint':True,
 'limitations':['Primary static transforms corroborated by per-assembly sphere measurements; native renderer behavior not verified.',
 'Prop transforms retain external-reference/inferred rotation and FAB binding conventions; not promoted by static-record measurements.',
 'Secondary/LOD sets, two skinned props, original materials/textures, animation, collision and gameplay remain absent.']}
(out/'combined-scene.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
