"""Read-only Windows audit of source props visible in the reported tablet view."""
from pathlib import Path
import json,csv,math,platform,struct
assert platform.system()=='Windows'
r=Path.home()/'Documents/Opem Amalur';o=r/'outputs/scene-v16'
placements=json.loads((r/'outputs/scene-v07/placements.json').read_text())
symbols=r/'references/ZucchiniZap--AmalurBxmlConverter/bin/Release/net10.0-windows/symbol_tables'
names={}
for p in symbols.glob('*fab*.csv'):
 for row in csv.DictReader(p.open(encoding='utf-8-sig')):
  if 'id'in row and 'value'in row:names[int(row['id'])]=row['value']
raw=(r/'outputs/scene-v11/scene-normals.bin').read_bytes()
camera=(-975.520,2142.936,-166.652);yaw=-.84851
source={x['index']:x for x in placements['placements']};rows=[]
for p in placements['baked_scene']['placements']:
 a=p['first_output_vertex'];n=p['output_vertices'];points=[struct.unpack_from('<3f',raw,36+(a+i)*36)for i in range(n)]
 lo=[min(v[i]for v in points)for i in range(3)];hi=[max(v[i]for v in points)for i in range(3)];center=[(lo[i]+hi[i])/2 for i in range(3)]
 dx,dy=center[0]-camera[0],center[1]-camera[1];forward=dx*math.cos(yaw)+dy*math.sin(yaw);right=dx*math.sin(yaw)-dy*math.cos(yaw)
 if math.hypot(dx,dy)>1100:continue
 src=source[p['placement_index']]
 rows.append(dict(index=p['placement_index'],fab_id=p['fab_id'],name=names.get(p['fab_id']),source_instance_id=src['instance_id'],source_position=src['position_xyz'],q=src['quaternion_xyzw'],scale=src['scale_xyz'],bounds=[lo,hi],center=center,view_forward=forward,view_right=right,vertices=n))
rows.sort(key=lambda x:math.hypot(x['view_forward'],x['view_right']))
(o/'prop-view-audit.json').write_text(json.dumps(dict(camera=camera,yaw=yaw,rows=rows),indent=2))
print(json.dumps(rows[:28],separators=(',',':')))
