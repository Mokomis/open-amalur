from pathlib import Path
import sys,json,struct,hashlib,shutil,collections,math
import numpy as np
sys.dont_write_bytecode=True
O=Path(__file__).resolve().parent;R=O.parents[2]
sys.path.insert(0,str(R/'work/v07-mesh'));import amalur_mesh
SOURCE=R/'work/v48-opening/initial-sword-audit/inputs/initial_0.pak'
DT=np.dtype([('v','<f4',(16,)),('rgba','u1',(4,)),('mid','<u4'),('flags','<u4')])
assert DT.itemsize==76
NONE=0xffffffff
def sha(b):return hashlib.sha256(b).hexdigest()
def box(v):return [v.min(0).tolist(),v.max(0).tolist()]
def matrix(q,t,s):
 x,y,z,w=(-q[0],-q[1],-q[2],q[3])
 m=np.eye(4);m[:3,:3]=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])@np.diag(s);m[:3,3]=t;return m
def transform(V,M):
 out=V.copy();out['v'][:,:3]=(V['v'][:,:3].astype('f8')@M[:3,:3].T+M[:3,3]).astype('f4')
 for a in [3,6,9]:out['v'][:,a:a+3]=(V['v'][:,a:a+3].astype('f8')@M[:3,:3].T).astype('f4')
 return out
def writepack(path,parts,rows,anchor,ranges=True):
 allv=[];alli=[];rr=[];nv=0;ni=0
 for p,V,I in parts:
  mid=p['native_material'];allv.append(V);alli.append(I+nv)
  radius=float(np.linalg.norm(V['v'][:,:3].astype('f8')-anchor,axis=1).max())
  rr.append([rows[mid],ni,len(I),0,*anchor,radius,p['distance_min']**2,p['distance_max']**2,p['assembly'],1.0]);nv+=len(V);ni+=len(I)
 V=np.concatenate(allv);I=np.concatenate(alli).astype('<u4')
 b=struct.pack('<8s5I',b'OARGEO1\0',len(V),len(I),len(rr),76,48)+b''.join(struct.pack('<4I6fIf',*r) for r in rr)+V.tobytes()+I.tobytes();path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b)
 # Independently reparse the serialized triangle occurrence order and 76-byte records.
 magic,nvv,nii,nd,vs,rs=struct.unpack_from('<8s5I',b);assert (magic,vs,rs)==(b'OARGEO1\0',76,48)
 VA=28+48*nd;VV=np.frombuffer(b,DT,nvv,VA);II=np.frombuffer(b,'<u4',nii,VA+nvv*76);assert VA+nvv*76+nii*4==len(b)
 for j,(_,pv,pi) in enumerate(parts):
  r=struct.unpack_from('<4I6fIf',b,28+j*48);assert VV[II[r[1]:r[1]+r[2]]].tobytes()==pv[pi].tobytes()
 return dict(file=str(path.relative_to(O)),bytes=len(b),sha256=sha(b),vertices=len(V),triangles=len(I)//3,ranges=len(rr),bounds=box(V['v'][:,:3])),V,I
def main():
 mats=json.loads((O/'material-contracts.json').read_text());allrows={m['material']:i for i,m in enumerate(sorted(mats,key=lambda m:m['material']))}
 placement=json.loads((R/'work/v48-opening/initial-sword-audit/initial-sword-source-contract.json').read_text())['gor']['record'];G=matrix(placement['quaternion'],placement['position'],placement['scale'])
 report=dict(status='STAGED ONLY; no runtime animation/native active pose claim',source_material_rows=allrows,placement=placement,geometry=[],source_parts=[],limits=[])
 eligible=[];withheld=[]
 for fid in [1789717,1880465]:
  src=SOURCE/f'{fid}.fab_visual_data_streamable_bin';raw=src.read_bytes();mesh=amalur_mesh.parse_file(src)
  md=json.loads((O/f'{fid}-fab-metadata.json').read_text());groups=json.loads((O/f'{fid}-groups.json').read_text())
  B=[];pending=set(range(len(md['bones'])))
  while pending:
   progressed=False
   for bi in list(pending):
    b=md['bones'][bi];parent=b['parent_index']
    if parent is not None and parent in pending:continue
    M=matrix(b['quaternion_xyzw'],b['position_xyzw'][:3],b['scale_xyzw'][:3])
    # Single-bone rest-pose candidate only. The active animation state is not recovered.
    if parent is not None:M=B[parent]@M
    while len(B)<=bi:B.append(None)
    B[bi]=M;pending.remove(bi);progressed=True
   assert progressed
  (O/f'{fid}-conjugate-bind-candidate.json').write_text(json.dumps(dict(policy='Source-conjugated quaternion hierarchy, unit-scale here. Candidate only; not active animation or inverse-bind proof.',matrices=[m.reshape(-1).tolist() for m in B]),indent=2)+'\n')
  rawdir=O/'raw-meshes'/str(fid);rawdir.mkdir(parents=True,exist_ok=True)
  local=[];bound=[]
  for asm in mesh['assemblies']:
   a=asm['index'];vb=mesh['vertex_buffers'][asm['vertex_buffer']];ib=mesh['index_buffers'][asm['index_buffer']];stride=vb['stride_bytes'];n=vb['vertex_count'];I=np.array(ib['indices'],dtype='<u4');used=np.unique(I)
   vbraw=raw[vb['data_file_offset']:vb['data_file_offset']+vb['data_bytes']];ibraw=raw[ib['data_file_offset']:ib['data_file_offset']+ib['data_bytes']]
   (rawdir/f'assembly-{a:02}.vb{stride}').write_bytes(vbraw);(rawdir/f'assembly-{a:02}.u16').write_bytes(ibraw)
   uv=24 if stride==60 else 12;normal=32 if stride==60 else 20;rgba=56 if stride==60 else 44
   V=np.zeros(n,DT);V['mid']=groups['elements'][a]['native_material_id'];V['flags']=3
   for vi in range(n):
    at=vi*stride;V['v'][vi,:3]=struct.unpack_from('<3f',vbraw,at);V['v'][vi,12:14]=struct.unpack_from('<2f',vbraw,at+uv);V['v'][vi,14:16]=V['v'][vi,12:14]
    for j in range(3):V['v'][vi,3+3*j:6+3*j]=np.maximum(-1,np.array(struct.unpack_from('<4h',vbraw,at+normal+j*8)[:3],dtype='f8')/32767)
    V['rgba'][vi]=np.frombuffer(vbraw,dtype='u1',count=4,offset=at+rgba)
    assert V['v'][vi,12:14].tobytes()==vbraw[at+uv:at+uv+8];assert V['rgba'][vi].tobytes()==vbraw[at+rgba:at+rgba+4]
   d=md['mesh_descriptors'][a];e=groups['elements'][a]
   rigid=d['bone_index']>=0 and not d['remaps']
   if stride==60:
    for vi in used:
     ii=struct.unpack_from('<4B',vbraw,int(vi)*stride+12);ww=struct.unpack_from('<4H',vbraw,int(vi)*stride+16)
     if rigid:assert ii==(0,0,0,0) and ww==(32767,0,0,0)
   p=dict(fab=fid,assembly=a,native_material=int(V['mid'][0]),vertices=n,triangles=len(I)//3,bone=d['bone_index'],remap_count=len(d['remaps']),remaps=d['remaps'],rigid_single_bone=rigid,distance_min=e['distance_min'],distance_max=e['distance_max'],descriptor_bound_center=e['center'],descriptor_radius=e['radius'],source_local_bounds_all=box(V['v'][:,:3]),source_local_bounds_used=box(V['v'][used,:3]),source_vb_sha256=sha(vbraw),source_ib_sha256=sha(ibraw),assembly52_raw_hex=asm['raw_hex'],source_vb_file_offset=vb['data_file_offset'],source_ib_file_offset=ib['data_file_offset'],raw_vertex_file=str((rawdir/f'assembly-{a:02}.vb{stride}').relative_to(O)),raw_index_file=str((rawdir/f'assembly-{a:02}.u16').relative_to(O)))
   local.append((p,V,I))
   if rigid:
    BV=transform(V,B[d['bone_index']]);bound.append((p,BV,I));p['candidate_bind_bounds']=box(BV['v'][used,:3])
    assert BV['v'][:,12:].tobytes()==V['v'][:,12:].tobytes() and BV['rgba'].tobytes()==V['rgba'].tobytes()
    if fid==1789717:
     if p['native_material']!=1880463:eligible.append((p,transform(BV,G),I))
     else:withheld.append(dict(fab=fid,assembly=a,triangles=p['triangles'],reason='unsupported characterhardlight545212'))
   elif fid==1789717:withheld.append(dict(fab=fid,assembly=a,triangles=p['triangles'],reason='multiple-bone remapping/active skin deformation not proven'))
   report['source_parts'].append(p)
  rec,_,_=writepack(O/'source-local'/f'fab-{fid}.bin',local,allrows,[0,0,0]);rec['meaning']='Exact decoded component-local geometry, not assembled/render-ready whole object.';report['geometry'].append(rec)
  rec,_,_=writepack(O/'source-bind-candidate'/f'fab-{fid}-rigid.bin',bound,allrows,[0,0,0]);rec['meaning']='Single-bone source hierarchy rest-pose candidate; excludes multibone parts; unsupported material rows require implementation.';report['geometry'].append(rec)
 # Four actual supported material contracts, local IDs never touch the opening world.
 tex=json.loads((O/'texture-stage-manifest.json').read_text());texby={x['asset']:x for x in tex['textures']}
 supported=sorted([m for m in mats if m['material']!=1880463],key=lambda m:m['material']);profiles=[];need=set()
 for m in supported:
  par={p['name']:p['values'] for p in m['parameters']};s={x['slot']:x['asset'] for x in m['texture_slots']}
  fam=11 if m['material']==464114 else 1
  assets=[s.get(0),s.get(3),s.get(2),s.get(1) if fam==11 else None,None,None,s.get(1) if m['alpha_test'] else None,None]
  flags=0x10000000|(2 if m['alpha_test'] else 0)|(m['cutoff_byte']<<8)|(0x20000000 if m['alpha_test'] else 0)
  p=dict(local_material=len(profiles),native_material=m['material'],family=fam,flags=flags,source_alpha_test=m['alpha_test'],cutoff_byte=m['cutoff_byte'],source_cull=m['cull'],assets=assets,color=par['TintColor'] if fam==11 else par['ConstantColor'],specular=par['SpecularValues'],uv=[1,1,par['ReflectionInfluence'][0],par['Opacity'][0]] if fam==11 else [1,1,1,1])
  if fam==11:p['probe_asset']=s[21];p['environment_requirement']='Authored current-scene EnvironmentTint and exact cube505647 binding, see family11-integration-contract.json'
  need.update(a for a in assets if a is not None);profiles.append(p)
 tids={a:i for i,a in enumerate(sorted(need))};rows={p['native_material']:p['local_material'] for p in profiles};W=O/'placed-container-rigid-candidate/world';W.mkdir(parents=True,exist_ok=True)
 bank=[];native=[]
 for p in profiles:
  slots=[tids.get(a,NONE) for a in p['assets']];p['texture_slots']=slots;bank.append(struct.pack('<7I',p['flags'],*slots[:6]));native.append(struct.pack('<9I12f',p['family'],*slots,*p['color'],*p['specular'],*p['uv']))
 (W/'materials.bin').write_bytes(struct.pack('<I',len(profiles))+b''.join(bank));(W/'native-materials.bin').write_bytes(struct.pack('<8sI',b'OANM001\0',len(profiles))+b''.join(native))
 for a,ti in tids.items():
  tr=texby[a];b=(O/tr['portable_file']).read_bytes();assert sha(b)==tr['portable_sha256'];(W/f't{ti}.bin').write_bytes(b)
 anchor=placement['position'];cx,cy=math.floor(anchor[0]/6400),math.floor(anchor[1]/6400)
 rec,V,I=writepack(W/f'r{cx}_{cy}.bin',eligible,rows,anchor);report['geometry'].append(rec)
 lo,hi=rec['bounds'];(W/'region-index.bin').write_bytes(struct.pack('<8sIIfI',b'OARGIDX1',1,len(profiles),1.,0)+struct.pack('<iiII6f',cx,cy,len(I)//3,len(eligible),*lo,*hi))
 (W/'index.bin').write_bytes(b'OAWI'+struct.pack('<fIII',6400.,1,len(tids),0)+struct.pack('<ii6f4I',cx,cy,*lo,*hi,0,0,0,0))
 report.update(supported_rigid_assemblies=len(eligible),supported_rigid_triangles=sum(len(i)//3 for _,_,i in eligible),withheld=withheld,profiles=profiles,textures=[dict(local_texture=i,asset=a,source=texby[a]['portable_file'],sha256=texby[a]['portable_sha256']) for a,i in tids.items()],placement_matrix=G.reshape(-1).tolist(),full_container_triangles=2298,sword_triangles=604)
 report['limits']=['Bind candidate uses source-conjugated TQS hierarchy, not an observed animation pose. Do not promote as original active pose proof.','18 rigid container parts source-classified; unsupported sword material removes part0 from placed candidate. Three multibone/remapped parts withheld, not frozen with invented weights.','Sword model has no proven loose-world GOR/socket placement. Source-local and bind candidate remain unplaced; no arbitrary sword spawn.','Current family11 requires separate cube505647 and authored scene EnvironmentTint binding; candidate does not fabricate ambient/environment globals.','Raw source VB/IB retain every bone-index/weight/SNORM fourth component; OAWE76 is a derived static candidate only.','No collision or interaction/animation is added. Motion set1789863 exists but clip/state mapping has not been decoded.']
 (O/'visual-stage-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({k:report[k] for k in ['supported_rigid_assemblies','supported_rigid_triangles','withheld','full_container_triangles','sword_triangles']},indent=2))
if __name__=='__main__':main()
