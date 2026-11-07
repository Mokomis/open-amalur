from pathlib import Path
import sys,struct,json,hashlib
r=Path.home()/'Documents/Opem Amalur';sys.path.insert(0,str(r/'work/v10-scene'));from collision_set import parse
scene=(r/'outputs/scene-v07/scene.bin').read_bytes();x=parse((r/'work/scene-inputs-v09/DATA_0.pak/524858.collision_set_bin').read_bytes())
positions={tuple(round(c,1) for c in v[:3]) for v in struct.iter_unpack('<9f',scene[36:])};rows=[]
for scale in [1,100]:
 vertices=[tuple(round(c*scale,1) for c in v) for g in x['groups'] for m in g['meshes'] for v in m['vertices']]
 rows.append(dict(scale=scale,vertices=len(vertices),rounded_point_matches=sum(v in positions for v in vertices),unique_points=len(set(vertices))))
o=dict(scope='Geometric corroboration only; native unit-conversion implementation not established',rounding_scene_units=.1,scene_sha256=hashlib.sha256(scene).hexdigest(),collision_sha256=x['source_sha256'],comparisons=rows)
(r/'outputs/scene-v10/collision-alignment.json').write_text(json.dumps(o,indent=2));print(json.dumps(o,indent=2))
