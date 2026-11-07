from pathlib import Path
import json,struct,collections
r=Path.home()/'Documents/Opem Amalur';s=json.loads((r/'outputs/scene-v07/shell-candidate.json').read_text());models={x['fab_id']:x for x in s['model_inputs']};cache={};matches=collections.Counter();samples={};total=0
for rec in s['admitted_records']:
 mid=rec['material_id_candidate'];m=models[rec['fab_id']]
 if rec['fab_id'] not in cache:cache[rec['fab_id']]=(json.loads((r/m['mesh_json']).read_text()),json.loads((r/m['fab_json']).read_text()))
 mesh,fab=cache[rec['fab_id']];a=mesh['assemblies'][rec['assembly']];d=fab['mesh_descriptors'][rec['assembly']];total+=1
 blobs={'assembly':bytes.fromhex(a['raw_hex']),'descriptor_tail':bytes.fromhex(d['tail25_hex'])}
 for label,data in blobs.items():
  for off in range(len(data)-3):
   if struct.unpack_from('<I',data,off)[0]==mid:
    key=f'{label}+{off}';matches[key]+=1;samples.setdefault(key,dict(fab_id=rec['fab_id'],assembly=rec['assembly'],material=mid))
o=dict(scope='correlation only; no native binding proof',records=total,matches=dict(matches),samples=samples);(r/'outputs/scene-v10/material-binding-correlations.json').write_text(json.dumps(o,indent=2));print(json.dumps(o,indent=2))
