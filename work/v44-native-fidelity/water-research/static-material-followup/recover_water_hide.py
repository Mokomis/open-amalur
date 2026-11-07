from pathlib import Path
import json,struct,hashlib,sys,numpy as np,collections
P=Path(r'C:\Users\rwill\Documents\Opem Amalur');Q=Path(__file__).resolve().parent;R=Q.parent;S=json.loads((P/'work/v20-inputs/symbols.json').read_text());sys.path.insert(0,str(P/'work/v07-mesh'));import amalur_mesh
M=json.loads((R/'water-mesh-manifest.json').read_text())['draws'];mapping={404112:62,1423574:63,1436262:64,449423:206};sources={};
def find(n):return next((P/'work/v20-inputs'/a/n for a in ['patch_0.pak','initial_0.pak','DATA_0.pak'] if (P/'work/v20-inputs'/a/n).exists()),None)
def qr(q,v):
 u=np.array(q[:3]);t=2*np.cross(u,v);return v+q[3]*t+np.cross(u,t)
for id,name in S['fab'].items():
 if not name.startswith('for_river'):continue
 f=find(id+'.fab_visual_data_streamable_bin')
 if not f:continue
 mesh=amalur_mesh.parse_file(f);src=f.read_bytes()
 for ai,a in enumerate(mesh['assemblies']):
  vb=mesh['vertex_buffers'][a['vertex_buffer']];ib=mesh['index_buffers'][a['index_buffer']];raw=src[ib['data_file_offset']:ib['data_file_offset']+ib['data_bytes']];sources.setdefault((vb['data_sha256'],hashlib.sha256(raw).hexdigest()),[]).append((int(id),name,ai,mesh,src,str(f.relative_to(P))))
for m in M:
 vb=(R/'resources'/f"buffer-{m['source_vertex_buffer']}.bin").read_bytes();ib=(R/'resources'/f"buffer-{m['source_index_buffer']}.bin").read_bytes();m['source_matches']=sources.get((hashlib.sha256(vb).hexdigest(),hashlib.sha256(ib).hexdigest()),[])
 print(m['draw'],[(x[0],x[1],x[2]) for x in m['source_matches']],flush=True)
instances=[]
for sid,sname in S['simspace'].items():
 if not sname.startswith('out_dal_'):continue
 f=find(sid+'.space_bxml')
 if not f:continue
 src=f.read_bytes();b=src[8:8+struct.unpack_from('<I',src)[0]]
 def arr(slot,stride):
  ptr,n=struct.unpack_from('<II',b,slot);return [b[ptr-8+i*stride:ptr-8+(i+1)*stride] for i in range(n)]
 for ga,gb in [(0x138,0x170),(0x140,0x180)]:
  for i,(a,r) in enumerate(zip(arr(ga,16),arr(gb,84))):
   fab=struct.unpack_from('<I',a,8)[0];mat,ai=struct.unpack_from('<II',r,64);instances.append((int(sid),sname,ga,i,fab,mat,ai,r))
report=[];O=Q/'water-hide';O.mkdir(exist_ok=True)
for m in M:
 candidates=[]
 for sm in m['source_matches']:
  fab,name,ai,mesh,src,path=sm
  for sid,sname,ga,i,f,mat,a,r in instances:
   if f!=fab or mat!=m['material'] or a!=ai:continue
   t=np.array(struct.unpack_from('<3f',r,16));cost=np.linalg.norm(t-np.array(m['world_matrix'][12:15]));candidates.append((cost,sm,(sid,sname,ga,i,r)))
 assert candidates,m['draw'];cost,sm,instance=min(candidates,key=lambda x:x[0]);assert cost<.1,(m['draw'],cost);fab,name,ai,mesh,src,path=sm;sid,sname,ga,ii,r=instance;sphere=np.array(struct.unpack_from('<4f',r));t=np.array(struct.unpack_from('<3f',r,16));q=struct.unpack_from('<4f',r,32);scale=np.array(struct.unpack_from('<3f',r,48));cq=(-q[0],-q[1],-q[2],q[3]);a=mesh['assemblies'][ai];vb=mesh['vertex_buffers'][a['vertex_buffer']];xyz=np.array(vb['positions']);cl=qr(q,(sphere[:3]-t)[None,:])[0];world=qr(cq,cl+(xyz-cl)*scale)+t;ix=np.array(mesh['index_buffers'][a['index_buffer']]['indices']);used=sorted(set(ix.tolist()));native=(R/'meshes'/m['file']).read_bytes();v=np.frombuffer(native,'<f4',m['vertices']*18,32).reshape(-1,18).copy();assert len(used)==len(v);delta=world[used]-v[:,:3];v[:,:3]=world[used];blob=native[:32]+v.astype('<f4').tobytes()+native[32+m['vertices']*72:];fn=f"legacy-hide-{m['draw']}.oawm";(O/fn).write_bytes(blob);report.append(dict(draw=m['draw'],material=m['material'],legacy_material=mapping[m['material']],fab=fab,fab_name=name,assembly=ai,space=sid,space_name=sname,group=hex(ga),source_instance=ii,source_mesh=path,source_vb_sha256=vb['data_sha256'],source_ib_sha256=hashlib.sha256((R/'resources'/f"buffer-{m['source_index_buffer']}.bin").read_bytes()).hexdigest(),serialized_translation_match_error=float(cost),legacy_position_delta_min=delta.min(0).tolist(),legacy_position_delta_max=delta.max(0).tolist(),file=fn,sha256=hashlib.sha256(blob).hexdigest()))
(Q/'legacy-water-hide-provenance.json').write_text(json.dumps(report,indent=2));print([(x['draw'],x['legacy_position_delta_min'],x['legacy_position_delta_max']) for x in report])
