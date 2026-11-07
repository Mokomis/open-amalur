from pathlib import Path
import json,struct,hashlib,collections
r=Path.home()/'Documents/Opem Amalur';p=json.loads((r/'outputs/scene-v07/placements.json').read_text());b=p['baked_scene'];models=[];materials=set();strides=collections.Counter()
for m in b['mesh_inputs']:
 raw=(r/m['mesh_json']).read_bytes();fr=(r/m['fab_bind']['fab_json']).read_bytes()
 assert hashlib.sha256(raw).hexdigest()==m['mesh_json_sha256'] and hashlib.sha256(fr).hexdigest()==m['fab_bind']['fab_json_sha256']
 mesh=json.loads(raw);fab=json.loads(fr);assemblies=[]
 for a,d in zip(mesh['assemblies'],fab['mesh_descriptors']):
  vb=mesh['vertex_buffers'][a['vertex_buffer']];mid=struct.unpack_from('<I',bytes.fromhex(d['tail25_hex']))[0];materials.add(mid);strides[vb['stride_bytes']]+=1
  assemblies.append(dict(assembly=a['index'],material_id_candidate=mid,stride=vb['stride_bytes'],vertices_out=len(mesh['index_buffers'][a['index_buffer']]['indices'])))
 models.append(dict(fab_id=m['fab_id'],assemblies=assemblies))
o=dict(scope='Descriptor tail+0 material correlation matches172/172 primary records; prop use remains inferred until native consumer traced',models=models,material_ids=sorted(materials),strides=dict(strides),placements=len(b['placements']))
(r/'outputs/scene-v11/prop-inventory.json').write_text(json.dumps(o,indent=2));print(json.dumps(dict(materials=len(materials),strides=dict(strides),models=len(models),placements=len(b['placements'])),indent=2))
(r/'work/v11-textures/material-names.txt').write_text('\n'.join(f'{mid}.mat_bxml' for mid in sorted(materials)))
