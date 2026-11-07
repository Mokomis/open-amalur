"""Bind prop UVs to exact existing baked vertices; material-tail association inferred."""
from pathlib import Path
import json,struct,hashlib,math
from material_package import FALLBACK
sha=lambda b:hashlib.sha256(b).hexdigest()
def apply(root,scene,combined,report,profile,bindings,uvs,add_draw,normal_baker=None):
 from amalur_scene import bind_point,transform
 from normal_baker import normal_matrix
 baked=report['baked_scene'];parts=[p for p in combined['inputs'] if p['sha256']==baked['scene_sha256']]
 if len(parts)!=1 or parts[0]['first_output_vertex']!=0 or parts[0]['vertices']!=baked['vertices']:raise ValueError('Prop segment receipt mismatch')
 total=baked['vertices'];raw_geometry=scene[36:36+total*36]
 expected_header=b'OMSC07\0\0'+struct.pack('<I6f',total,*baked['bounds_min'],*baked['bounds_max'])
 if sha(expected_header+raw_geometry)!=baked['scene_sha256']:raise ValueError('Combined prop range does not match original baked scene')
 models={m['fab_id']:m for m in baked['mesh_inputs']};placements={p['index']:p for p in report['placements']};cache={};cursor=0;coverage=[];layouts={(x['header_word0'],x['stride_bytes']):x for x in profile['uv_layouts']}
 for placement in baked['placements']:
  key=placement['fab_id'];original=placements[placement['placement_index']]
  if original['fab_id']!=key or placement['first_output_vertex']!=cursor:raise ValueError('Prop placement order/identity mismatch')
  m=models[key]
  if key not in cache:
   mb=(root/m['mesh_json']).read_bytes();fb=(root/m['fab_bind']['fab_json']).read_bytes()
   if sha(mb)!=m['mesh_json_sha256'] or sha(fb)!=m['fab_bind']['fab_json_sha256']:raise ValueError('Prop report hash changed')
   mesh=json.loads(mb);fab=json.loads(fb);raw=Path(mesh['input_file']).read_bytes()
   if sha(raw)!=m['native_stream_sha256']:raise ValueError('Prop stream identity changed')
   cache[key]=(mesh,fab,raw)
  mesh,fab,raw=cache[key];before=cursor
  for ai,a in enumerate(mesh['assemblies']):
   vb=mesh['vertex_buffers'][a['vertex_buffer']];indices=mesh['index_buffers'][a['index_buffer']]['indices'];d=fab['mesh_descriptors'][ai];matrix=d['static_bind_candidate'];material=struct.unpack_from('<I',bytes.fromhex(d['tail25_hex']))[0];n=len(indices);first=cursor;texture=FALLBACK;layout=layouts.get((vb['header_word0'],vb['stride_bytes']))
   if n%3 or first+n>total or matrix is None:raise ValueError('Prop mesh span/binding invalid')
   if material in bindings and layout is not None:
    if vb['data_file_offset']<0 or vb['data_file_offset']+vb['vertex_count']*vb['stride_bytes']>len(raw):raise ValueError('Prop vertex span')
    nm=normal_matrix(lambda p:transform(bind_point(matrix,p),original)) if normal_baker else None
    for j,index in enumerate(indices):
     if not 0<=index<vb['vertex_count']:raise ValueError('Prop index invalid')
     uv=struct.unpack_from('<2f',raw,vb['data_file_offset']+index*vb['stride_bytes']+layout['uv_offset'])
     if not all(math.isfinite(c) for c in uv):raise ValueError('Prop UV nonfinite')
     point=transform(bind_point(matrix,vb['positions'][index]),original)
     if struct.pack('<3f',*point)!=scene[36+(first+j)*36:48+(first+j)*36]:raise ValueError('Prop UV/index transformed position differs from exact baked scene')
     uvs[first+j]=uv
     if normal_baker:normal_baker.vertex(first+j,raw,vb['data_file_offset']+index*vb['stride_bytes']+20,nm)
    texture=bindings[material]['texture_index']
   add_draw(first,n,texture);cursor+=n;coverage.append(dict(placement_index=placement['placement_index'],fab_id=key,assembly=ai,material_id_candidate=material,vertices=n,texture_index=texture))
  if cursor-before!=placement['output_vertices']:raise ValueError('Prop placement vertex count differs')
 if cursor!=total:raise ValueError('Prop ranges do not cover original segment')
 return coverage,total
