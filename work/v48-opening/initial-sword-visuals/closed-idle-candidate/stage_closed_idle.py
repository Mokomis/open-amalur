from pathlib import Path
import sys,json,struct,hashlib,math,ast,shutil
import numpy as np
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;Q=O.parent;R=Q.parents[2]
sys.path.insert(0,str(R/'work/v07-mesh'));import amalur_mesh
helper=Q/'stage_visual_geometry.py';tree=ast.parse(helper.read_text())
defs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['sha','box','matrix','transform','writepack']]
exec(compile(ast.Module(body=defs,type_ignores=[]),str(helper),'exec'))
DT=np.dtype([('v','<f4',(16,)),('rgba','u1',(4,)),('mid','<u4'),('flags','<u4')]);assert DT.itemsize==76
def readpack(p):
 b=p.read_bytes();_,nv,ni,nr,vs,rs=struct.unpack_from('<8s5I',b);assert(vs,rs)==(76,48);at=28+nr*48
 return b,np.frombuffer(b,DT,nv,at).copy(),np.frombuffer(b,'<u4',ni,at+nv*76).copy(),[struct.unpack_from('<4I6fIf',b,28+i*48) for i in range(nr)]
def main():
 proof=Q/'initial-state-consumer-audit/close-idle-variant/close-idle-proof.json';P=json.loads(proof.read_text());assert P['native_time_formula']['close_idle']['result']==0
 posep=Q/'initial-state-consumer-audit/close-idle-variant/close-idle-native-local-trs.bin';pb=posep.read_bytes();J,F,fps=struct.unpack_from('<IIf',pb);assert(J,F)==(54,1)
 local=np.frombuffer(pb,'<f4',offset=12).reshape(J,12);assert np.array_equal(local[:,8:11],np.ones((J,3),dtype='<f4'))
 md=json.loads((Q/'1789717-fab-metadata.json').read_text());groups=json.loads((Q/'1789717-groups.json').read_text());B=[]
 for j,b in enumerate(md['bones']):
  par=b['parent_index'];assert par is None or par<j
  M=matrix(local[j,:4],local[j,4:7],local[j,8:11])
  B.append(M if par is None else B[par]@M)
 placement=json.loads((R/'work/v48-opening/initial-sword-audit/initial-sword-source-contract.json').read_text())['gor']['record'];assert placement['scale']==[1,1,1];G=matrix(placement['quaternion'],placement['position'],placement['scale'])
 src=R/'work/v48-opening/initial-sword-audit/inputs/initial_0.pak/1789717.fab_visual_data_streamable_bin';raw=src.read_bytes();mesh=amalur_mesh.parse_file(src);prior=json.loads((Q/'visual-stage-manifest.json').read_text());profiles=prior['profiles'];rows={p['native_material']:p['local_material'] for p in profiles}
 parts=[];withheld=[];provenance=[]
 for a in mesh['assemblies']:
  ai=a['index'];d=md['mesh_descriptors'][ai];e=groups['elements'][ai];vb=mesh['vertex_buffers'][a['vertex_buffer']];ib=mesh['index_buffers'][a['index_buffer']]
  if d['remaps'] or d['bone_index']<0:withheld.append(dict(assembly=ai,triangles=ib['triangle_count'],reason='multibone/remap path withheld'));continue
  if e['native_material_id'] not in rows:withheld.append(dict(assembly=ai,triangles=ib['triangle_count'],reason='HardLight1880463 unsupported inthis4rowbank'));continue
  assert vb['stride_bytes']==60 and a['unknown_u32_at8'][0]==22
  n=vb['vertex_count'];I=np.array(ib['indices'],dtype='<u4');vr=raw[vb['data_file_offset']:vb['data_file_offset']+vb['data_bytes']]
  V=np.zeros(n,DT);V['mid']=e['native_material_id'];V['flags']=3
  for j in range(n):
   at=j*60
   assert struct.unpack_from('<4B',vr,at+12)==(0,0,0,0) and struct.unpack_from('<4h',vr,at+16)==(32767,0,0,0)
   V['v'][j,:3]=struct.unpack_from('<3f',vr,at);V['v'][j,12:14]=struct.unpack_from('<2f',vr,at+24);V['v'][j,14:16]=V['v'][j,12:14]
   for k in range(3):V['v'][j,3+3*k:6+3*k]=np.maximum(-1,np.array(struct.unpack_from('<4h',vr,at+32+8*k)[:3],dtype='f8')/32767)
   V['rgba'][j]=np.frombuffer(vr,'u1',4,at+56)
  BV=transform(V,B[d['bone_index']]);WV=transform(BV,G)
  assert WV['v'][:,12:].tobytes()==V['v'][:,12:].tobytes() and WV['rgba'].tobytes()==V['rgba'].tobytes()
  p=dict(fab=1789717,assembly=ai,native_material=e['native_material_id'],bone=d['bone_index'],distance_min=e['distance_min'],distance_max=e['distance_max'])
  parts.append((p,WV,I));provenance.append(dict(**p,vertices=n,triangles=len(I)//3,source_vb_sha256=vb['data_sha256'],source_ib_sha256=ib['data_sha256'],source_descriptor_file_offset=d['file_offset'],source_vertex_type=22,source_stride=60,source_local_bounds=box(V['v'][:,:3]),frame0_assembled_local_bounds=box(BV['v'][:,:3]),frame0_world_bounds=box(WV['v'][:,:3]),source_bone_global_matrix=B[d['bone_index']].reshape(-1).tolist()))
 assert len(parts)==17 and sum(len(I)//3 for _,_,I in parts)==1370
 W=O/'world';W.mkdir(exist_ok=True);old=Q/'placed-container-rigid-candidate/world';copied=[]
 for f in sorted(old.iterdir()):
  if f.name in ['materials.bin','native-materials.bin'] or (f.name.startswith('t') and f.suffix=='.bin'):
   bb=f.read_bytes();(W/f.name).write_bytes(bb);copied.append(dict(file=f.name,bytes=len(bb),sha256=sha(bb),source=str(f.relative_to(R))))
 anchor=placement['position'];cx,cy=math.floor(anchor[0]/6400),math.floor(anchor[1]/6400);name=f'r{cx}_{cy}.bin'
 rec,V,I=writepack(W/name,parts,rows,anchor);lo,hi=rec['bounds']
 registry=struct.pack('<8sIIfI',b'OARGIDX1',1,len(profiles),1.,0)+struct.pack('<iiII6f',cx,cy,len(I)//3,len(parts),*lo,*hi);(W/'region-index.bin').write_bytes(registry)
 index=b'OAWI'+struct.pack('<fIII',6400.,1,len(prior['textures']),0)+struct.pack('<ii6f4I',cx,cy,*lo,*hi,0,0,0,0);(W/'index.bin').write_bytes(index)
 rb,RV,RI,RR=readpack(old/name);nb,NV,NI,NR=readpack(W/name)
 assert np.array_equal(RI,NI) and len(RV)==len(NV)
 assert RV['v'][:,12:].tobytes()==NV['v'][:,12:].tobytes()
 for field in ['rgba','mid','flags']:assert RV[field].tobytes()==NV[field].tobytes()
 shifts=[]
 for part,r,nr in zip(provenance,RR,NR):
  assert r[:4]==nr[:4] and r[4:7]==nr[4:7] and r[8:]==nr[8:]
  ids=NI[nr[1]:nr[1]+nr[2]];delta=np.linalg.norm(NV['v'][ids,:3].astype('f8')-RV['v'][ids,:3],axis=1);shifts.append(dict(assembly=part['assembly'],bone=part['bone'],max_world_vertex_delta_from_rest=float(delta.max()),mean_world_vertex_delta_from_rest=float(delta.mean())))
 (O/'frame0-global-bone-matrices.json').write_text(json.dumps(dict(source_raw_local_pose=str(posep.relative_to(R)),matrices=[x.reshape(-1).tolist() for x in B],actor_matrix=G.reshape(-1).tolist(),convention='matrix=R(conjugate(rawEdgeQ)); parent*local; noQnormalization; noInverseBind forrigid branch'),indent=2)+'\n')
 report=dict(status='STAGED ordinary-default sourceCloseIdle frame0 candidate; noGPU/currentoriginalactor state validation',fab=1789717,GOR=1790948,instance=1789992,space=1417252,geometry=rec,material_count=len(profiles),texture_count=len(prior['textures']),profiles=profiles,copied_material_texture_files=copied,parts=provenance,withheld=withheld,shifts_from_rest=shifts,source_clip_pose=dict(file=str(posep.relative_to(R)),sha256=sha(pb),joints=J,frames=F,animation=1789841,sample_time=0,chooser_variant=0,motion='Close Idle4514355',proof=str(proof.relative_to(R))),source_mesh=dict(file=str(src.relative_to(R)),sha256=sha(raw)),vertex_contract=dict(evidence='work/v49-character-create/vertex-contract-audit/REPORT.md +evidence/recorded-input-layouts.json',source_type=22,stride=60,fields='Pfloat3@0,jointsUINT8x4@12,weightsSNORM16x4@16,UV0float2@24,N/T/B SNORM16x4@32/40/48,RGBA8@56',scope='Recorded native type22 declaration correspondence; not a captured pipeline for thiscontainer. No length-scoring used.',UV1='No authoredstream1 available; derivedstaticOAWE UV1duplicatesUV0 forreadercompatibility; noneofselectedfamilies useUV1'),transforms='RawEdgeQ conjugatedexactlyonce bymatrix();54bone parent hierarchy; sourceunitS; descriptorbone rigidtransform then provenGOR TRS. NoInverseBind inrigidpath.',validation=dict(triangle_index_occurrence_order_equals_frozen_rest=True,UV_RGBA_nativeMID_flags_byte_identity=True,material_texture_bytes_equal_frozen_rest=True,newpositions_TBN_sourceformula_valid=True,range_material_first_count_flags_anchor_intervals_source_unchanged=True,draw_spheres_and_registry_bounds_recomputed=True,reader_reparse_payload_identity=True),limits=['Ordinary defaultpath, notdeath orMotionSetoverride proof; noinitialstate timer/event executed.','Threeblendedparts18/19/20 withheld318tri,HardLightpart0 withheld610tri; nofallbackmaterial/pose invented.','Fourmaterialprofilebank sameasfrozenrest; family11 stillrequires exactcube505647/currentauthoredEnvironmentTint integration.','RootmustremaplocalbankIDs andreviewbeforemerge. No live/default/source/core edits.','Oldrestcandidate andallpriorclipreceipts untouched.'])
 (O/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(dict(status=report['status'],parts=len(parts),triangles=len(I)//3,bounds=rec['bounds'],largest_rest_shifts=sorted(shifts,key=lambda x:x['max_world_vertex_delta_from_rest'],reverse=True)[:4]),indent=2))
if __name__=='__main__':main()
