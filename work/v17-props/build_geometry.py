"""Windows: verified native world rotations and one explicit actor reference pose.

World matrices are original pure native-function outputs. The new actor's inverse
static bind is a separate reference-pose candidate, not native skeletal proof.
"""
from pathlib import Path
import hashlib,json,math,platform,struct,sys
assert platform.system()=='Windows'
r=Path.home()/'Documents/Opem Amalur';o=r/'outputs/scene-v17'
sys.path[:0]=[str(r/p)for p in ['work/v07-bxml','work/v11-textures','work/v09-textures']]
from amalur_scene import bind_point,transform
from normal_baker import normal_matrix,dot
from material_package import encode,FALLBACK
from keen_texture import decode
sha=lambda b:hashlib.sha256(b).hexdigest()
def inv(a):
 a,b,c,d,e,f,g,h,i=a;det=a*(e*i-f*h)-b*(d*i-f*g)+c*(d*h-e*g);assert abs(det)>1e-10
 return [[(e*i-f*h)/det,(c*h-b*i)/det,(b*f-c*e)/det],[(f*g-d*i)/det,(a*i-c*g)/det,(c*d-a*f)/det],[(d*h-e*g)/det,(b*g-a*h)/det,(a*e-b*d)/det]]
def inverse_affine(m):
 a=inv([m[j*4+k]for j in range(3)for k in range(3)]);p=[m[j*4+3]for j in range(3)];return [x for j in range(3)for x in [*a[j],-dot(a[j],p)]]+[0,0,0,1]
verification=json.loads((o/'native-prop-matrix-verification.json').read_text());assert verification['max_conjugated_error']<.002 and len(verification['rows'])==80
matrices={x['index']:x['native_matrix']for x in verification['rows']}
def world(m,p):return [sum(p[k]*m[k*4+j]for k in range(3))+m[12+j]for j in range(3)]
old=(r/'outputs/scene-v11/scene-normals.bin').read_bytes();scene=bytearray(old);count=struct.unpack_from('<I',old,8)[0]
assert sha(old)=='bf89bfe1a5b7d2ee2955dc7972509a7efb68fd027cb36482d25b24f905a97bc2'
placements=json.loads((r/'outputs/scene-v07/placements.json').read_text());models={m['fab_id']:m for m in placements['baked_scene']['mesh_inputs']};source={p['index']:p for p in placements['placements']};cache={};changed=0
for p in placements['baked_scene']['placements']:
 key=p['fab_id'];model=models[key]
 if key not in cache:
  mb=Path(model['mesh_json']).read_bytes();fb=Path(model['fab_bind']['fab_json']).read_bytes();assert sha(mb)==model['mesh_json_sha256']and sha(fb)==model['fab_bind']['fab_json_sha256'];cache[key]=(json.loads(mb),json.loads(fb))
 mesh,fab=cache[key];cursor=p['first_output_vertex'];original=source[p['placement_index']];matrix=matrices[original['index']]
 for a,d in zip(mesh['assemblies'],fab['mesh_descriptors']):
  vb=mesh['vertex_buffers'][a['vertex_buffer']];indices=mesh['index_buffers'][a['index_buffer']]['indices'];bind=d['static_bind_candidate'];assert bind is not None
  # Correct existing world normals by the rotation delta; retained FAB bind
  # semantics are explicitly unchanged for earlier static prop candidates.
  q=original['quaternion_xyzw'];x,y,z,w=q
  oldR=[[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]]
  oldA=[[oldR[j][k]*original['scale_xyz'][k]for k in range(3)]for j in range(3)];oldInv=inv([x for row in oldA for x in row]);newA=[[matrix[k*4+j]for k in range(3)]for j in range(3)];delta=[[sum(newA[j][l]*oldInv[l][k]for l in range(3))for k in range(3)]for j in range(3)]
  normalInv=inv([x for row in delta for x in row]);nm=[[normalInv[k][j]for k in range(3)]for j in range(3)]
  for idx in indices:
   at=36+cursor*36;local=bind_point(bind,vb['positions'][idx]);assert struct.pack('<3f',*transform(local,original))==old[at:at+12]
   pos=struct.pack('<3f',*world(matrix,local));changed+=pos!=old[at:at+12];scene[at:at+12]=pos
   n=struct.unpack_from('<3f',old,at+12);n=[dot(row,n)for row in nm];length=math.sqrt(dot(n,n));assert length>.01;n=[x/length for x in n];scene[at+12:at+24]=struct.pack('<3f',*n);cursor+=1
  assert cursor<=p['first_output_vertex']+p['output_vertices']
 assert cursor==p['first_output_vertex']+p['output_vertices']
props=placements['baked_scene']['vertices'];assert scene[36+props*36:]==old[36+props*36:]
# Decode the existing authored sidecar to preserve all UV/draw/texture payloads.
side=(r/'outputs/scene-v11/scene_materials.bin').read_bytes();version,vc,dc,tc=struct.unpack_from('<4I',side,8);assert side[:8]==b'OMAT09\0\0'and version==1 and vc==count and side[24:56]==hashlib.sha256(old).digest()
uvs=[struct.unpack_from('<2f',side,56+8*i)for i in range(vc)];at=56+8*vc;draws=[]
for i in range(dc):
 first,n,t,reserved=struct.unpack_from('<4I',side,at);assert not reserved;draws.append(dict(first_vertex=first,vertex_count=n,texture_index=t));at+=16
textures=[]
for i in range(tc):
 w,h,n,reserved=struct.unpack_from('<4I',side,at);at+=16;assert n==w*h*4 and not reserved;textures.append(dict(width=w,height=h,rgba=side[at:at+n]));at+=n
assert at==len(side)
mesh=json.loads((o/'workbench-mesh.json').read_text());fab=json.loads((o/'workbench-fab.json').read_text());raw=(r/'work/v17-inputs/DATA_0.pak/695560.fab_visual_data_streamable_bin').read_bytes();assert sha(raw)==mesh['input_sha256']and mesh['complete_consumption']
matrix=matrices[79];first_workbench=count;workbench_points=[];material_receipts=[]
for a,d in zip(mesh['assemblies'],fab['mesh_descriptors']):
 vb=mesh['vertex_buffers'][a['vertex_buffer']];assert vb['stride_bytes']in [48,56]and not d['remaps'];bind=inverse_affine(d['static_bind_candidate']);point=lambda p:world(matrix,bind_point(bind,p));nm=normal_matrix(point);indices=mesh['index_buffers'][a['index_buffer']]['indices'];mid=struct.unpack_from('<I',bytes.fromhex(d['tail25_hex']))[0];tid={697079:697080,696791:696826}[mid]
 texture=FALLBACK;receipt={};texture_path=None;decode_errors=[]
 for suffix in ['_3.dds','_0.dds']:
  candidate=r/f'work/v17-inputs/DATA_0.pak/{tid}{suffix}'
  if not candidate.exists():continue
  try:rgba,receipt=decode(candidate.read_bytes(),0)
  except ValueError as error:decode_errors.append(str(error));continue
  assert receipt['asset_id']==tid;texture_path=candidate
  if receipt['alpha_min']==255:
   texture=len(textures);textures.append(dict(width=receipt['decoded_width'],height=receipt['decoded_height'],rgba=rgba))
  break
 material_receipts.append(dict(material=mid,texture=tid,texture_index=texture,alpha_min=receipt.get('alpha_min'),texture_sha256=sha(texture_path.read_bytes())if texture_path else None,decode_errors=decode_errors))
 start=count
 for index in indices:
  pos=point(vb['positions'][index]);workbench_points.append(pos);offset=vb['data_file_offset']+index*vb['stride_bytes'];uv=struct.unpack_from('<2f',raw,offset+12);assert all(math.isfinite(x)for x in uv);uvs.append(uv)
  n=[max(-1,x/32767.)for x in struct.unpack_from('<4h',raw,offset+(28 if vb['stride_bytes']==56 else 20))[:3]];n=[dot(row,n)for row in nm];length=math.sqrt(dot(n,n));assert length>.1;n=[x/length for x in n];scene+=struct.pack('<9f',*pos,*n,.55,.45,.3);count+=1
 draws.append(dict(first_vertex=start,vertex_count=count-start,texture_index=texture))
positions=[struct.unpack_from('<3f',scene,36+36*i)for i in range(count)];lo=[min(v[j]for v in positions)for j in range(3)];hi=[max(v[j]for v in positions)for j in range(3)];scene[:36]=b'OMSC07\0\0'+struct.pack('<I6f',count,*lo,*hi)
binary,receipt=encode(bytes(scene),uvs,draws,textures);assert bytes(scene[36+props*36:36+vc*36])==old[36+props*36:]
assert all(scene[36+i*36+24:36+i*36+36]==old[36+i*36+24:36+i*36+36]for i in range(vc))
wb_lo=[min(v[j]for v in workbench_points)for j in range(3)];wb_hi=[max(v[j]for v in workbench_points)for j in range(3)]
receipt.update(source_scene_sha256=sha(old),corrected_static_prop_vertices=props,changed_prop_positions=changed,shell_bytes_preserved=True,existing_colors_uv_topology_preserved=True,native_world_matrix_evidence=str(o/'native-prop-matrix-verification.json'),workbench=dict(source_instance=524875,type=230417,fab=695560,first_vertex=first_workbench,vertices=count-first_workbench,bounds=[wb_lo,wb_hi],bind_scope='Explicit inverse static-bind reference-pose candidate; native FAB skeletal/bind application not verified',materials=material_receipts),limitations=['Native world transform arithmetic verified independently, not full native renderer parity.','Prior FAB static bind candidates retained; new Workbench inverse bind remains a reference-pose candidate.','No Workbench animation, native glass shader, or dynamic object collision is implemented.'])
for p,b in [(o/'scene.bin',bytes(scene)),(o/'scene_materials.bin',binary)]:assert not p.exists();p.write_bytes(b)
(o/'render-scene.json').write_text(json.dumps(receipt,indent=2));header=r/'work/v17-host/workbench_visual.inc';header.write_text('/* Generated reference-pose mesh target; source origin remains separate. */\n#define OA_WORKBENCH_FIRST_VERTEX '+str(first_workbench)+'u\n#define OA_WORKBENCH_VERTEX_COUNT '+str(count-first_workbench)+'u\nstatic const float oa_workbench_spawn_hint[3]={'+','.join(f'{v:.9f}f'for v in [-1412.840576171875,wb_lo[1]-150,-319.9022216796875])+'};\n')
print(json.dumps(dict(scene_sha256=receipt['scene_sha256'],vertices=count,corrected_props=props,workbench=receipt['workbench'])))

# Retain the native static collision bytes and append only this explicitly
# authored visual-mesh proxy; this is not the native actor rigid-body shape.
old_collision=(r/'outputs/scene-v10/collision-confirmed.bin').read_bytes();cn=struct.unpack_from('<I',old_collision,8)[0];triangles=old_collision[36:]+bytes(scene[36+36*first_workbench:]);points=[struct.unpack_from('<3f',triangles,36*i)for i in range(cn+count-first_workbench)];bounds=[min(x[j]for x in points)for j in range(3)]+[max(x[j]for x in points)for j in range(3)];collision=b'OMSC07\0\0'+struct.pack('<I6f',cn+count-first_workbench,*bounds)+triangles
assert not(o/'collision.bin').exists();(o/'collision.bin').write_bytes(collision);(o/'collision-source.json').write_text(json.dumps(dict(output_sha256=sha(collision),base_sha256=sha(old_collision),base_native_layout_corroborated=True,base_vertices=cn,added_vertices=count-first_workbench,added_proxy_kind='Rendered Workbench reference-pose triangle proxy, authored collision; not native object collider',full_collision_native_parity=False),indent=2))
