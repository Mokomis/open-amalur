"""Isolated source-authored root fixture. Writes only this research directory."""
from pathlib import Path
import sys,json,struct,hashlib,collections
import numpy as np
sys.dont_write_bytecode=True
P=Path(r'C:\Users\rwill\Documents\Opem Amalur');O=Path(__file__).resolve().parent;ST=O/'root-staging';ST.mkdir(exist_ok=True);A=P/'work/v40-windows-host/assets/world';sys.path.insert(0,str(P/'work/v07-mesh'));import amalur_mesh
sha=lambda b:hashlib.sha256(b).hexdigest();dt=np.dtype([('v','<f4',(16,)),('rgba','u1',(4,)),('material','<u4'),('flags','<u4')]);assert dt.itemsize==76
src=P/'work/v20-inputs/DATA_0.pak/359268.fab_visual_data_streamable_bin';mesh=amalur_mesh.parse_file(src);raw=src.read_bytes();sp=P/'work/v20-inputs/patch_0.pak/431646.space_bxml';sb=sp.read_bytes();body=sb[8:8+struct.unpack_from('<I',sb)[0]];ptr,n=struct.unpack_from('<II',body,0x160);r=body[ptr-8+211*84:ptr-8+212*84];sphere=np.array(struct.unpack_from('<4f',r));t=np.array(struct.unpack_from('<3f',r,16));q=np.array(struct.unpack_from('<4f',r,32));sc=np.array(struct.unpack_from('<3f',r,48));cq=np.r_[-q[:3],q[3]]
def qr(q,v):
 u=q[:3];z=2*np.cross(u,v);return v+q[3]*z+np.cross(u,z)
cl=qr(q,sphere[:3]-t);linear=qr(cq,np.diag(sc));sourceM=np.eye(4);sourceM[:3,:3]=linear;sourceM[3,:3]=t;shift=t+qr(cq,cl*(1-sc));nativeU=np.frombuffer((O/'root-binding68.bin').read_bytes()[:192],'<f4').reshape(12,4).astype(float)
def source(ai,transform):
 a=mesh['assemblies'][ai];vb=mesh['vertex_buffers'][a['vertex_buffer']];ib=mesh['index_buffers'][a['index_buffer']];n=vb['vertex_count'];stride=vb['stride_bytes'];at=vb['data_file_offset'];xyz=np.array(vb['positions']);world=qr(cq,xyz*sc)+t if transform=='direct' else qr(cq,cl+(xyz-cl)*sc)+t
 frame=[]
 for off in [20,28,36]:
  v=np.ndarray((n,3),'<i2',raw,at+off,(stride,2)).astype(float)/32767.;v=np.maximum(v,-1)/sc;v/=np.maximum(np.linalg.norm(v,axis=1,keepdims=True),1e-20);frame.append(qr(cq,v))
 uv=np.ndarray((n,2),'<f4',raw,at+12,(stride,4));col=np.ndarray((n,4),'u1',raw,at+44,(stride,1));out=np.zeros(n,dt);out['v']=np.concatenate([world,*frame,uv,uv],axis=1).astype('<f4');out['rgba']=col;out['material']=266;out['flags']=3
 return out,np.array(ib['indices'],'<u4').reshape(-1,3),dict(assembly=ai,vertices=n,triangles=ib['triangle_count'],vertex_buffer=a['vertex_buffer'],index_buffer=a['index_buffer'],vertex_sha256=vb['data_sha256'],index_sha256=ib['data_sha256'])
new,ni,newmeta=source(0,'direct');old,oi,oldmeta=source(1,'centered');old2,oi2,old2meta=source(2,'centered')
name='c1_-13_0.bin';b=(A/name).read_bytes();magic,nv,nindex,nd=struct.unpack_from('<4sIII',b);assert magic==b'OAWE';draws=[struct.unpack_from('<III',b,16+k*12) for k in range(nd)];base=16+12*nd;V=np.frombuffer(b,dt,nv,base);I=np.frombuffer(b,'<u4',nindex,base+nv*76);target=next(x for x in draws if x[0]==266);_,first,count=target;used=np.unique(I[first:first+count]);checks={}
# Resolve seams by position+UV first, rather than an arbitrary nearest duplicate.
for label,srcv in [('asm1',old),('asm2',old2)]:
 mapped=[];errs=[]
 for s in srcv:
  ds=np.linalg.norm(V['v'][used,:3].astype(float)-s['v'][:3],axis=1);can=used[ds<.02];assert len(can),(label,'missing source vertex')
  uvdelta=np.linalg.norm(V['v'][can,12:14]-s['v'][12:14],axis=1);can2=can[uvdelta<1e-6];can2=can2 if len(can2) else can;frameerr=np.linalg.norm(V['v'][can2,3:12]-s['v'][3:12],axis=1);k=can2[int(frameerr.argmin())];mapped.append(k);errs.append(float(uvdelta.min()))
 mapped=np.array(mapped);matches=V[mapped];checks[label]=dict(vertices=len(srcv),position_max=float(np.abs(matches['v'][:,:3]-srcv['v'][:,:3]).max()),uv_max=float(np.abs(matches['v'][:,12:16]-srcv['v'][:,12:16]).max()),rgba_exact=int(np.all(matches['rgba']==srcv['rgba'],axis=1).sum()),rgba_max_error=int(np.abs(matches['rgba'].astype(int)-srcv['rgba'].astype(int)).max()),normal_max=float(np.abs(matches['v'][:,3:6]-srcv['v'][:,3:6]).max()),tangent_max=float(np.abs(matches['v'][:,6:9]-srcv['v'][:,6:9]).max()),bitangent_max=float(np.abs(matches['v'][:,9:12]-srcv['v'][:,9:12]).max()))
# Full triangle matching uses position+UV+RGBA, invariant to corner ordering.
def vertexkey(v):return (tuple(np.round(v['v'][:3].astype(float),2)),tuple(map(float,v['v'][12:14])),tuple(map(int,v['rgba'])))
def trikey(v):return tuple(sorted(vertexkey(q) for q in v))
budget=collections.Counter(trikey(old[tri]) for tri in oi);removed=[];old_kept=[]
for at in range(first,first+count,3):
 key=trikey(V[I[at:at+3]])
 if budget[key]:budget[key]-=1;removed.append(at)
 else:old_kept.extend(I[at:at+3])
assert len(removed)==len(oi),(len(removed),len(oi));assert not any(budget.values())
remove=set(removed);newdraws=[];chunks=[];cursor=0
for mid,f,n in draws:
 chunk=np.array([int(x) for z in range(f,f+n,3) if z not in remove for x in I[z:z+3]],'<u4')
 if mid==266:chunk=np.r_[chunk,ni.ravel()+nv].astype('<u4')
 newdraws.append((mid,cursor,len(chunk)));chunks.append(chunk);cursor+=len(chunk)
NV=np.r_[V,new];IX=np.concatenate(chunks);out=b'OAWE'+struct.pack('<III',len(NV),len(IX),len(newdraws))+b''.join(struct.pack('<III',*d) for d in newdraws)+NV.tobytes()+IX.tobytes();ST.joinpath(name).write_bytes(out)
# Standalone root-only fixture, for inspection/merging; not a replacement for a world cell.
rootonly=b'OAWE'+struct.pack('<III',len(new),ni.size,1)+struct.pack('<III',266,0,ni.size)+new.tobytes()+ni.astype('<u4').tobytes();ST.joinpath('root-only.oawe').write_bytes(rootonly);ST.joinpath('root-native.oawt').write_bytes(b'OAWT'+struct.pack('<IIII',1,76,len(new),0)+new.tobytes());ST.joinpath('removed-root-index-offsets.u32').write_bytes(np.array(removed,'<u4').tobytes())
# Compare source-only direct TRS to the independently captured native matrix.
worldNative=np.array(mesh['vertex_buffers'][0]['positions'])@nativeU[:3,:3]+nativeU[3,:3];posnew=new['v'][:,:3].astype(float);nativeFrame=[]
vb=mesh['vertex_buffers'][0];at=vb['data_file_offset'];stride=vb['stride_bytes']
for off in [20,28,36]:
 z=np.ndarray((len(new),3),'<i2',raw,at+off,(stride,2)).astype(float)/32767.;z=np.maximum(z,-1)@nativeU[4:7,:3];z/=np.linalg.norm(z,axis=1)[:,None];nativeFrame.append(z)
samples=[0,1,2];receipt=dict(source_mesh=str(src),source_sha256=sha(raw),source_space=str(sp),source_space_sha256=sha(sb),source_render_slot='0x160',source_render_index=211,source_material353286_row266=True,source_only_direct_matrix=sourceM.tolist(),captured_world_matrix=nativeU[:4].tolist(),matrix_max_abs_error=float(abs(sourceM-nativeU[:4]).max()),centered_translation=shift.tolist(),direct_translation=t.tolist(),centered_minus_direct_translation=(shift-t).tolist(),centered_shift_length=float(np.linalg.norm(shift-t)),native_source_vertex_max_error=float(np.abs(worldNative-posnew).max()),native_frame_max_errors=[float(np.abs(z-new['v'][:,off:off+3]).max()) for z,off in zip(nativeFrame,[3,6,9])],current_attribute_checks=checks,current_selected_source=oldmeta,staged_source=newmeta,other_source_assembly=old2meta,native_vertex_samples=[dict(index=k,local=mesh['vertex_buffers'][0]['positions'][k],native_world=worldNative[k].tolist(),staged_world=new['v'][k,:3].tolist(),source_rgba=new['rgba'][k].tolist(),uv=new['v'][k,12:14].tolist()) for k in samples],input_cell=str(A/name),input_cell_sha256=sha(b),staged_cell_sha256=sha(out),removed_triangles=len(removed),added_triangles=len(ni),before_after_index_counts=[nindex,len(IX)],nonroot_vertices_byte_preserved=NV[:nv].tobytes()==V.tobytes(),nonroot_triangle_order_preserved=True,limits=['One source-authored root fixture only; no global placement or LOD policy inferred.','Source quaternion conjugate rotation and scale produce native matrix within measured error; direct TRS needs no captured save-specific placement.','Staged whole cell changes only matching target root triangles and appends its near assembly; all original vertex bytes remain.','No deployment, core editing or waterfall asset changes.'])
ST.joinpath('receipt.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,indent=2))
