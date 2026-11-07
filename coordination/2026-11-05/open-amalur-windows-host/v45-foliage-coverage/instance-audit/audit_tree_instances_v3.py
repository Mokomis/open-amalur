"""Read-only tree source/native capture correspondence at the bridge camera."""
from pathlib import Path
import sys,json,struct,hashlib,re,collections,numpy as np
sys.dont_write_bytecode=True
P=Path.home()/'Documents/Opem Amalur';Q=Path(__file__).resolve().parent/'all-source-poses';Q.mkdir(exist_ok=True)
sys.path.insert(0,str(P/'work/v07-mesh'));import amalur_mesh
S=json.loads((P/'work/v20-inputs/symbols.json').read_text())
camera=json.loads((P/'work/v44-native-fidelity/bridge-native-final-r2.json').read_text());vp=np.array(camera['mvp_column_major']).reshape(4,4,order='F');eye=np.array(camera['eye'])
planes=np.stack([vp[3]+vp[i] for i in range(3)]+[vp[3]-vp[i] for i in range(3)])
def find(name):return next((P/'work/v20-inputs'/a/name for a in ['patch_0.pak','initial_0.pak','DATA_0.pak'] if (P/'work/v20-inputs'/a/name).exists()),None)
def qr(q,v):
 u=np.array(q[:3]);t=2*np.cross(u,v);return v+q[3]*t+np.cross(u,t)
def tree_name(name):return name.startswith('for_flora_') and ('tree' in name or 'twist' in name or 'leafcover' in name) or name.startswith('for_skyline_trees')
treeids={int(i):n for i,n in S['fab'].items() if tree_name(n)}
meshes={};asmrows=[];byvb=collections.defaultdict(list);missing_meshes=[]
for fab,name in treeids.items():
 f=find(f'{fab}.fab_visual_data_streamable_bin')
 if not f:missing_meshes.append(dict(fab=fab,name=name));continue
 try:m=amalur_mesh.parse_file(f)
 except Exception as e:missing_meshes.append(dict(fab=fab,name=name,error=str(e)));continue
 raw=f.read_bytes();meshes[fab]=(m,raw)
 for ai,a in enumerate(m['assemblies']):
  v=m['vertex_buffers'][a['vertex_buffer']];ib=m['index_buffers'][a['index_buffer']]
  row=dict(fab=fab,name=name,assembly=ai,vertex_buffer=a['vertex_buffer'],index_buffer=a['index_buffer'],vertex_sha256=v['data_sha256'],index_sha256=ib['data_sha256'],stride=v['stride_bytes'],vertices=v['vertex_count'],triangles=ib['triangle_count'],source=str(f.relative_to(P)))
  asmrows.append(row);byvb[row['vertex_sha256']].append(row)
print('tree source models',len(meshes),'assemblies',len(asmrows),flush=True)
source=[];stats=collections.Counter();center_collisions=[];missing_spaces=[]
spaces=sorted((int(i),n) for i,n in S['simspace'].items() if re.match(r'out_dal_(north|south|west|east|central|tran|[a-z0-9])',n))
for sid,name in spaces:
 f=find(f'{sid}.space_bxml')
 if not f:missing_spaces.append(dict(space=sid,name=name));continue
 raw=f.read_bytes();b=raw[8:8+struct.unpack_from('<I',raw)[0]]
 def arr(slot,stride):
  ptr,n=struct.unpack_from('<II',b,slot);return [b[ptr-8+i*stride:ptr-8+(i+1)*stride] for i in range(n)]
 renders=arr(0x160,84);bc={};collision=collections.defaultdict(list)
 for i,r in enumerate(renders):
  key=tuple(round(x,2) for x in struct.unpack_from('<3f',r));bc[key]=(i,r);collision[key].append(i)
 refs=[struct.unpack('<I',x)[0] for x in arr(0x1b0,4)];centers=[struct.unpack('<3f',x) for x in arr(0x1a8,12)];instances=[]
 for ri,(typed,center) in enumerate(zip(refs,centers)):
  fab=typed&0xfffffff;match=bc.get(tuple(round(x,2) for x in center))
  if match and fab in treeids:
   idx,r=match;instances.append((fab,r,'refs',ri,idx,typed>>28))
   key=tuple(round(x,2) for x in center)
   if len(collision[key])>1:center_collisions.append(dict(space=sid,ref=ri,fab=fab,render_indices=collision[key],chosen=idx))
 for ri,(a,r) in enumerate(zip(arr(0x148,80),arr(0x150,84))):
  fab=struct.unpack_from('<I',a,52)[0]
  if fab in treeids:instances.append((fab,r,'placed',ri,None,None))
 for ga,gb in [(0x138,0x170),(0x140,0x180)]:
  for ri,(a,r) in enumerate(zip(arr(ga,16),arr(gb,84))):
   fab=struct.unpack_from('<I',a,8)[0]
   if fab in treeids:instances.append((fab,r,hex(ga),ri,None,None))
 for fab,r,group,ri,renderindex,typed in instances:
  stats['tree_records']+=1;mat,ai=struct.unpack_from('<II',r,64);matname=S['material'].get(str(mat),'')
  if re.search('shadow|for_temp',matname,re.I):stats['shadow_proxy_skipped']+=1;continue
  if fab not in meshes:stats['missing_tree_mesh']+=1;continue
  m,raw=meshes[fab]
  if ai>=len(m['assemblies']):stats['bad_assembly']+=1;continue
  a=m['assemblies'][ai];v=m['vertex_buffers'][a['vertex_buffer']];ib=m['index_buffers'][a['index_buffer']]
  if v['stride_bytes'] not in [48,56,60]:stats['unsupported_stride']+=1;continue
  sphere=np.array(struct.unpack_from('<4f',r));t=np.array(struct.unpack_from('<3f',r,16));q=np.array(struct.unpack_from('<4f',r,32));sc=np.array(struct.unpack_from('<3f',r,48));cq=np.r_[-q[:3],q[3]];cl=qr(q,(sphere[:3]-t)[None,:])[0];linear=qr(cq,np.diag(sc));shift=t+qr(cq,(cl*(1-sc))[None,:])[0];world=np.array(v['positions'])@linear+shift;ix=np.array(ib['indices'],int).reshape(-1,3)
  reach=float(np.linalg.norm(world[np.unique(ix)]-sphere[:3],axis=1).max()) if len(ix) else 0
  if sphere[3]<=0 or reach>sphere[3]*1.25+60:stats['sphere_rejected']+=1;continue
  stats['emitted_tree_records']+=1
  frustum=bool(np.all(planes[:,:3]@sphere[:3]+planes[:,3]>=-sphere[3]*np.linalg.norm(planes[:,:3],axis=1)))
  xy_distance=max(float(np.linalg.norm(sphere[:2]-eye[:2])-sphere[3]),0)
  if not frustum or xy_distance>=64000:stats['outside_camera_sphere']+=1
  clips=np.c_[world,np.ones(len(world))]@vp.T;ci=clips[ix];reject=np.zeros(len(ix),bool)
  for axis in range(3):reject|=np.all(ci[:,:,axis]<-ci[:,:,3],axis=1)|np.all(ci[:,:,axis]>ci[:,:,3],axis=1)
  viable=int((~reject).sum());stats['frustum_tree_records']+=1
  if viable==0:stats['sphere_only_no_triangles']+=1
  pose=np.r_[t,q,sc].astype('<f4');matrix=np.eye(4);matrix[:3,:3]=linear;matrix[3,:3]=shift
  source.append(dict(source_frustum_candidate=frustum and xy_distance<64000,space=sid,space_name=name,group=group,record=ri,render_index=renderindex,typed_high4=typed,fab=fab,fab_name=treeids[fab],assembly=ai,material=mat,material_name=matname,sphere=sphere.tolist(),translation=t.tolist(),quaternion=q.tolist(),scale=sc.tolist(),ported_matrix_row_major=matrix.ravel().tolist(),naive_translation=t.tolist(),pose_key=str(fab)+':'+pose.tobytes().hex(),triangles=len(ix),frustum_candidate_triangles=viable,source_vertex_sha256=v['data_sha256'],source_index_sha256=ib['data_sha256'],render_record_hex=r.hex(),distance=xy_distance))
print('source records',dict(stats),'frustum records',len(source),flush=True)
bh={x['buffer']:x for x in json.loads((Q.parent/'native-gbuffer-buffer-hashes.json').read_text())};draws=json.loads((Q.parent/'native-gbuffer-draws.json').read_text());native=[];sourceused=collections.Counter()
for d in draws:
 h=d.get('vertex_bind',{}).get('pBuffers',[None])[0];v=bh.get(h);ibh=bh.get(d.get('index_bind',{}).get('buffer'))
 if not v or v['sha256'] not in byvb:continue
 options=byvb[v['sha256']];both=[x for x in options if ibh and x['index_sha256']==ibh['sha256']]
 if both:options=both
 if 'world_matrix_row_major' not in d:continue
 mat=np.array(d['world_matrix_row_major']).reshape(4,4);candidates=[]
 for i,s in enumerate(source):
  if not any(a['fab']==s['fab'] for a in options):continue
  cur=np.array(s['ported_matrix_row_major']).reshape(4,4);basis=float(abs(mat[:3,:3]-cur[:3,:3]).max());shift=float(np.linalg.norm(mat[3,:3]-cur[3,:3]));naive=float(np.linalg.norm(mat[3,:3]-s['translation']));cost=min(shift,naive)+basis*10000;candidates.append((cost,i,basis,shift,naive))
 match=min(candidates) if candidates else None
 row=dict(draw=d['index'],vs=d['vs'],pipeline=d['pipeline'],vertex_buffer=h,index_buffer=d.get('index_bind',{}).get('buffer'),native_vertices_bytes=v['bytes'],native_index_count=d['args']['indexCount'],native_first_index=d['args']['firstIndex'],native_base_vertex=d['args']['vertexOffset'],native_world_matrix=d['world_matrix_row_major'],source_assembly_candidates=options,exact_index_buffer_hash_match=bool(both))
 if match:
  _,i,basis,shift,naive=match;s=source[i];row.update(best_source_index=i,basis_max_error=basis,ported_translation_distance=shift,naive_translation_distance=naive,source_pose=s['pose_key'],source_fab=s['fab'],source_assembly=s['assembly'],source_material=s['material'],source_full_index_count=s['triangles']*3)
  if basis<.001 and min(shift,naive)<1:sourceused[i]+=1;row['pose_matched']=True
  else:row['pose_matched']=False
 else:row['pose_matched']=False
 native.append(row)
duplicates=collections.defaultdict(list)
for i,s in enumerate(source):duplicates[(s['fab'],s['assembly'],s['material'],s['pose_key'])].append(i)
dup=[dict(source_indices=v,fab=k[0],assembly=k[1],material=k[2]) for k,v in duplicates.items() if len(v)>1]
physical=collections.defaultdict(list)
for i,s in enumerate(source):physical[s['pose_key']].append(i)
nativeposes=collections.defaultdict(list)
for i,d in enumerate(native):
 if d['pose_matched']:nativeposes[d['source_pose']].append(i)
summary=dict(camera=camera,scope='SamebridgeVP; sourcefrustum candidates are not occlusion-tested visibility counts. Native actual Gbuffer draw submissions fromcapturedphase97.',cached_tree_models=len(meshes),source_tree_assembly_catalogue=len(asmrows),source_stats=dict(stats),source_frustum_parts=len(source),source_frustum_physical_pose_groups=len(physical),native_tree_draws_matched_to_cached_geometry=len(native),native_draws_with_pose_match=sum(x['pose_matched'] for x in native),native_pose_groups_matched=len(nativeposes),native_unmatched_draws=sum(not x['pose_matched'] for x in native),exact_duplicate_source_assembly_pose_groups=dup,rounded_center_collisions=center_collisions,missing_meshes=missing_meshes,missing_spaces=missing_spaces,source_part_draw_counts=dict(collections.Counter(str(s['fab']) for s in source)),native_part_draw_counts=dict(collections.Counter(str(d.get('source_fab','unmatched')) for d in native)),native_vs_counts=dict(collections.Counter(str(d['vs']) for d in native)))
(Q/'tree-source-assembly-catalogue.json').write_text(json.dumps(asmrows,indent=2));(Q/'tree-source-frustum-records.json').write_text(json.dumps(source,indent=2));(Q/'native-tree-source-correspondence.json').write_text(json.dumps(native,indent=2));(Q/'tree-instance-summary.json').write_text(json.dumps(summary,indent=2));(Q/'source-physical-pose-groups.json').write_text(json.dumps([dict(pose=k,source_indices=v,native_draw_indices=[native[x]['draw'] for x in nativeposes.get(k,[])]) for k,v in physical.items()],indent=2))
print('SUMMARY', {k:v for k,v in summary.items() if k not in ['camera','source_stats','exact_duplicate_source_assembly_pose_groups','rounded_center_collisions','missing_meshes','missing_spaces','source_part_draw_counts','native_part_draw_counts']},flush=True);print('duplicates',len(dup),'center collisions',len(center_collisions),'missing spaces',len(missing_spaces),flush=True)
