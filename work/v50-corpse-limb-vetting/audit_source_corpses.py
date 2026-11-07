import sys,json,struct,hashlib,collections
sys.dont_write_bytecode=True
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[2];Q=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'work/v07-mesh'));import amalur_mesh,amalur_fab
A=R/'work/v48-opening/content-audit';W=R/'work/v48-opening/integration/probe-preview-closed-container/world'
S=json.loads((A/'1417252-source-render-records.json').read_text());C=json.loads((A/'first-room-mesh-catalog.json').read_text())
wanted={x['fab']:x for x in C if 'corpse' in x['name'].lower()}
def sha(b):return hashlib.sha256(b).hexdigest()
def qr(q,v):
 u=np.array(q[:3]);t=2*np.cross(u,v);return v+q[3]*t+np.cross(u,t)
files=[];sourcecounts=collections.Counter();usedSources=set();models={}
for fid,cat in wanted.items():
 f=A/'inputs/DATA_0.pak'/f'{fid}.fab_bxml';b=f.read_bytes();m=amalur_fab.parse_bytes(b)
 f2=R/cat['source'];raw=f2.read_bytes();mesh=amalur_mesh.parse_bytes(raw)
 models[fid]=(raw,mesh)
 bones=[dict(index=x['index'],parent=x['parent_index'],q=x['quaternion_xyzw'],t=x['position_xyzw'],scale=x['scale_xyzw'])for x in m['bones']]
 asm=[]
 for i,x in enumerate(mesh['assemblies']):
  vb=mesh['vertex_buffers'][x['vertex_buffer']];ib=mesh['index_buffers'][x['index_buffer']]
  p=np.array(vb['positions'])[np.unique(ib['indices'])]
  d=m['mesh_descriptors'][i]
  asm.append(dict(assembly=i,stride=vb['stride_bytes'],vertices=len(p),triangles=len(ib['indices'])//3,local_bounds=[p.min(0).tolist(),p.max(0).tolist()],local_extent_cm=np.ptp(p,axis=0).tolist(),bone=d['bone_index'],remap_count=len(d['remaps']),descriptor_offset=d['file_offset']))
 cat=dict(cat);cat.update(metadata_sha256=sha(b),bones=bones,all_bones_identity=all(x['q']==[0,0,0,1] and x['t'][:3]==[0,0,0] and x['scale'][:3]==[1,1,1]for x in bones),assemblies=asm)
 files.append(cat)
checks=[];worldfiles=[]
for f in sorted(W.glob('r*.bin')):
 b=f.read_bytes()
 if b[:8]!=b'OARGEO1\0':continue
 nv,ni,nr,vs,rs=struct.unpack_from('<5I',b,8);vp=28+nr*48;ip=vp+nv*76
 V=np.ndarray((nv,19),'<f4',b,vp);I=np.frombuffer(b,'<u4',ni,ip)
 U=np.ndarray((nv,4),'u1',b,vp+64,(76,1))
 used=False
 for j in range(nr):
  d=struct.unpack_from('<4I6fIf',b,28+j*48);src=d[10]
  if src>=len(S):continue
  s=S[src];fid=s['fab']
  if fid not in wanted:continue
  if int(np.frombuffer(b,'<u4',1,vp+int(I[d[1]])*76+68)[0])!=s['material']:continue
  raw,mesh=models[fid];a=mesh['assemblies'][s['assembly']];vb=mesh['vertex_buffers'][a['vertex_buffer']];ib=mesh['index_buffers'][a['index_buffer']]
  ix=np.array(ib['indices'],dtype='u4');p=np.array(vb['positions'],dtype='f8');q=s['quaternion'];cq=[-q[0],-q[1],-q[2],q[3]]
  expected=(qr(cq,p*np.array(s['scale']))+np.array(s['translation'])).astype('<f4')
  actual=I[d[1]:d[1]+d[2]]
  assert len(actual)==len(ix)
  err=float(np.max(abs(V[actual,:3]-expected[ix])))
  uv=np.ndarray((len(p),2),'<f4',raw,vb['data_file_offset']+12,(vb['stride_bytes'],4))
  rgba=np.ndarray((len(p),4),'u1',raw,vb['data_file_offset']+44,(vb['stride_bytes'],1))
  uvok=np.array_equal(V[actual,12:14].copy().view('u4'),uv[ix].copy().view('u4'));cok=np.array_equal(U[actual],rgba[ix])
  assert err==0 and uvok and cok
  assert s['scale']==[1,1,1]
  checks.append(dict(file=f.name,range=j,source_index=src,fab=fid,assembly=s['assembly'],mid=s['material'],source_group=s['group'],triangles=len(ix)//3,position_max_error_cm=err,uv_bit_exact=uvok,rgba_bit_exact=cok,scale=s['scale'],raw_T=s['translation'],range_squared=[d[8],d[9]]))
  sourcecounts[fid]+=1;usedSources.add(src);used=True
 if used:worldfiles.append(dict(file=f.name,sha256=sha(b),bytes=len(b)))
poses={fid:len({(tuple(S[i]['translation']),tuple(S[i]['quaternion']),tuple(S[i]['scale']))for i in usedSources if S[i]['fab']==fid})for fid in wanted}
result=dict(status='PASS source-to-current static corpse geometry identity',models=files,source_records_checked=len(checks),triangle_range_count=sum(x['triangles']for x in checks),physical_pose_count_by_fab=poses,render_records_by_fab=dict(sourcecounts),all_current_source_scales_unit=True,max_position_error_cm=max(x['position_max_error_cm']for x in checks),checks=checks,world_files=worldfiles,limits=['No original opening-room GPU capture was identified; this is exact shipped-source-to-current proof, not native-frame pixel parity.','Pixel picks use current source intervals and no cull or alpha emulation. The foreground picked corpse material is opaque.','The models are static pre-posed corpse piles, not individually animated human limbs. Per-limb anatomical measurements are not inferred from whole-pile bounds.'])
(Q/'source-current-validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items()if k not in ['models','checks']},indent=2))
for x in files:print('MODEL',x['fab'],x['name'],'bones',len(x['bones']),'identity',x['all_bones_identity'],'assemblies',x['assemblies'])
