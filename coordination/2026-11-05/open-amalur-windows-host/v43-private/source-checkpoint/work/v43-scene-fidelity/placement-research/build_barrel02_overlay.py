"""Build16 barrel02 static visuals into a new isolated overlay; never deploy."""
from pathlib import Path
import sys,struct,json,hashlib,math,collections
import numpy as np
w=Path(__file__).resolve().parent;r=w.parents[2]
v42=r/'work/v42-object-visuals';baseline=v42/'static-props-overlay';fallback=r/'work/v40-windows-host/assets/world';out=w/'barrel02-overlay'
if out.exists():raise SystemExit('Preserve existing overlay; choose a new output scope before rebuilding')
sys.path[:0]=[str(r/'work/v07-mesh')]
import amalur_mesh,amalur_fab
sha=lambda b:hashlib.sha256(b).hexdigest()
def source(name):
 p=baseline/name
 if not p.exists():p=fallback/name
 return p
manifest42=json.loads((v42/'static-props-manifest.json').read_text())
materials=(baseline/'materials.bin').read_bytes();nm=struct.unpack_from('<I',materials)[0]
assert len(materials)==4+nm*28 and manifest42['material_ids']==[299790,301326,1377236]
material_index=nm-len(manifest42['material_ids'])+manifest42['material_ids'].index(299790)
assert material_index==255
assert (fallback/'materials.bin').read_bytes()==materials,'Current material table differs from v42 baseline'
placements=[x for x in json.loads((v42/'direct-rendering-catalog.json').read_text())['instances']if x['type_name']=='smashable_barrel_02']
assert len(placements)==16 and len({x['instance_id']for x in placements})==16
assert all(x['type_id']==360769 and len(x['rendering'])==1 and x['rendering'][0]['primary_fab']==1425589 for x in placements)
inputs=r/'work/v20-inputs/initial_0.pak';fb=inputs/'1425589.fab_bxml';vis=inputs/'1425589.fab_visual_data_streamable_bin'
f=amalur_fab.parse_file(fb);m=amalur_mesh.parse_file(vis);proof=json.loads((w/'barrel-native-pose-result.json').read_text())
assert sha(fb.read_bytes())==proof['input_fab_sha256']=='b51f2dfc5980dfc025ce5364ab36d9a9bb15ab018bf3db472f6a8738b4da2a39'
assert f['mesh_count']==len(m['assemblies'])==1 and f['mesh_descriptors'][0]['bone_index']==2 and not f['mesh_descriptors'][0]['remaps']
assert struct.unpack('<I',bytes.fromhex(f['mesh_descriptors'][0]['tail25_hex'])[:4])[0]==299790
assert f['mesh_descriptors'][0]['unknown_two_floats'][0]==1
native=proof['rows'][2];assert native['parent']==0 and native['conjugated_rotation_max_error']<1e-6 and native['direct_max_error']>.5
local=np.array(native['native_matrix_column_vector'],np.float64).reshape(4,4)
assert np.max(np.abs(local[:3,3]))==0 and np.max(np.abs(local[3]-[0,0,0,1]))==0
assert np.max(np.abs(local[:3,:3].T@local[:3,:3]-np.eye(3)))<1e-6
asm=m['assemblies'][0];vb=m['vertex_buffers'][asm['vertex_buffer']];ib=np.array(m['index_buffers'][asm['index_buffer']]['indices'],dtype='<u4')
assert vb['stride_bytes']==48 and asm['unknown_u16_at2']==0
raw=vis.read_bytes();P=np.array(vb['positions'],np.float64)
N=np.ndarray((len(P),3),'<i2',raw,vb['data_file_offset']+20,(48,2)).astype(np.float64)/32767
UV=np.ndarray((len(P),2),'<f4',raw,vb['data_file_offset']+12,(48,4)).copy()
assert len(ib)%3==0 and int(ib.max())<len(P)
P=P@local[:3,:3].T;N=N@local[:3,:3].T
index=bytearray(source('index.bin').read_bytes());cellsize,nc=struct.unpack_from('<fI',index,4);assert len(index)==20+nc*48
dtype=np.dtype([('p','<f4',3),('n','<i2',4),('uv','<f4',2)]);assert dtype.itemsize==28
buckets=collections.defaultdict(list);receipts=[]
def qrot(q,v):
 u=np.array(q[:3]);t=2*np.cross(u,v);return v+q[3]*t+np.cross(u,t)
for obj in placements:
 assert all(abs(s-1)<1e-6 for s in obj['scale'])
 q=obj['quaternion'];q=[-q[0],-q[1],-q[2],q[3]]
 wp=qrot(q,P)+obj['position'];wn=qrot(q,N);wn/=np.linalg.norm(wn,axis=1,keepdims=True)
 assert np.isfinite(wp).all() and np.isfinite(wn).all()
 verts=np.zeros(len(P),dtype=dtype);verts['p']=wp;verts['n'][:,:3]=np.round(wn*32767).astype('<i2');verts['n'][:,3]=32767;verts['uv']=UV
 key=tuple(math.floor(p/cellsize)for p in obj['position'][:2]);buckets[key].append(verts)
 receipts.append(dict(instance_id=obj['instance_id'],type_id=obj['type_id'],fab_id=1425589,triangles=len(ib)//3,position=obj['position'],quaternion=obj['quaternion'],cell=key,bounds=[wp.min(0).tolist(),wp.max(0).tolist()],local_bind_bone=2))
out.mkdir();files={};validation=[]
def save(name,b):
 (out/name).write_bytes(b);p=source(name);before=p.read_bytes();files[name]=dict(bytes=len(b),sha256=sha(b),before_path=str(p),before_sha256=sha(before))
for key,parts in buckets.items():
 matches=[i for i in range(nc)if struct.unpack_from('<ii',index,20+i*48)==key];assert len(matches)==1;row=20+matches[0]*48
 new_v=np.concatenate(parts);new_i=np.concatenate([ib+i*len(P)for i in range(len(parts))])
 for lod in range(3):
  name=f'c{key[0]}_{key[1]}_{lod}.bin';b=source(name).read_bytes();assert b[:4]==b'OAWC';nv,ni,nd=struct.unpack_from('<3I',b,4)
  assert nd<128 and len(b)==16+nd*12+nv*28+ni*4
  olddraw=b[16:16+nd*12];oldv=b[16+nd*12:16+nd*12+nv*28];oldi=b[16+nd*12+nv*28:]
  draws=olddraw+struct.pack('<3I',material_index,ni,len(new_i));vertices=oldv+new_v.tobytes();indices=oldi+(new_i+nv).astype('<u4').tobytes()
  result=b'OAWC'+struct.pack('<3I',nv+len(new_v),ni+len(new_i),nd+1)+draws+vertices+indices
  # Validate original blocks byte-for-byte at their relocated offsets.
  nv2,ni2,nd2=struct.unpack_from('<3I',result,4);vstart=16+nd2*12;istart=vstart+nv2*28
  assert result[16:16+nd*12]==olddraw and result[vstart:vstart+nv*28]==oldv and result[istart:istart+ni*4]==oldi
  assert len(result)==16+nd2*12+nv2*28+ni2*4
  assert int(np.frombuffer(result,dtype='<u4',offset=istart).max())<nv2
  for d in range(nd2):
   mi,first,count=struct.unpack_from('<3I',result,16+d*12);assert mi<nm and first+count<=ni2 and count%3==0
  save(name,result);struct.pack_into('<I',index,row+32+lod*4,ni2//3)
  validation.append(dict(file=name,old_vertices=nv,old_indices=ni,old_draws=nd,new_vertices=nv2,new_indices=ni2,new_draws=nd2,original_draws_vertices_indices_preserved=True,added_instances=len(parts),added_triangles=len(new_i)//3))
 lo=np.minimum(np.array(struct.unpack_from('<3f',index,row+8)),new_v['p'].min(0));hi=np.maximum(np.array(struct.unpack_from('<3f',index,row+20)),new_v['p'].max(0));struct.pack_into('<6f',index,row+8,*lo,*hi)
 assert np.all(new_v['p'].min(0)>=lo-1e-3)and np.all(new_v['p'].max(0)<=hi+1e-3)
save('index.bin',bytes(index))
manifest=dict(type_ids=[360769],fab_ids=[1425589],material_ids=[299790],material_index=material_index,placements=receipts,files=files,inputs=[dict(path=str(p),sha256=sha(p.read_bytes()))for p in [fb,vis]],baseline_static_props_manifest_sha256=sha((v42/'static-props-manifest.json').read_bytes()),native_proof_sha256=sha((w/'barrel-native-pose-result.json').read_bytes()),local_bind_column_vector_matrix=local.reshape(-1).tolist(),added_triangles_lod0=sum(x['triangles']for x in receipts),material_table_sha256=sha(materials),limits=['Static unskinned barrel02 visual only; no destroyed state, destruction, loot, collision or animation','Existing material299790 index255 reused unchanged; all3LODs retain source barrel mesh','No deployment or live file edits; native proof is standalone pose arithmetic and static composition evidence, not observed original draw'])
(w/'barrel02-manifest.json').write_text(json.dumps(manifest,indent=2))
(w/'barrel02-validation.json').write_text(json.dumps(dict(placements=len(receipts),cells=len(buckets),files=len(files),rows=validation,all_original_geometry_materials_preserved=True,material_table_unchanged=True,all_bounds_contain_added_vertices=True),indent=2))
print('Built',len(receipts),'barrel02 visuals in',len(buckets),'cells;',len(files),'files;',manifest['added_triangles_lod0'],'triangles per LOD; material255 unchanged')
