from pathlib import Path
import json,struct,hashlib,sys,collections
import numpy as np
sys.dont_write_bytecode=True
R=Path(r'C:\Users\rwill\Documents\Opem Amalur');O=R/'work/v45-foliage-coverage/image-band-audit/foreground-rock'
P=R/'work/v44-native-fidelity/water-research/static-material-followup';W=R/'work/v40-windows-host/assets/world';sys.path.insert(0,str(R/'work/v07-mesh'));import amalur_mesh
sha=lambda b:hashlib.sha256(b).hexdigest()
src=R/'work/v20-inputs/patch_0.pak/424996.fab_visual_data_streamable_bin';raw=src.read_bytes();mesh=amalur_mesh.parse_file(src)
assert sha(raw)=='e7044beb14e61d7d29c9f80a6ab758e96124a86b585d9088023b2329e184d81a'
x=next(x for x in json.loads((P/'source-provenance.json').read_text()) if x['space']==431646 and x['instance']==672 and x['fab']==424996)
record=bytes.fromhex(x['render_record_hex']);T=np.array(struct.unpack_from('<3f',record,16));Q=np.array(struct.unpack_from('<4f',record,32));S=np.array(struct.unpack_from('<3f',record,48));CQ=np.r_[-Q[:3],Q[3]];assert np.array_equal(S,np.ones(3))
sp=R/'work/v20-inputs/patch_0.pak/431646.space_bxml';sb=sp.read_bytes();body=sb[8:8+struct.unpack_from('<I',sb)[0]];ptr,n=struct.unpack_from('<II',body,0x160);assert body[ptr-8+470*84:ptr-8+471*84]==record
NATIVE=np.frombuffer((O/'native-binding68.bin').read_bytes(),'<f4').reshape(16,4).astype(float)
def qr(q,v):
 z=2*np.cross(q[:3],v);return v+q[3]*z+np.cross(q[:3],z)
dt=np.dtype([('v','<f4',(16,)),('rgba','u1',(4,)),('material','<u4'),('flags','<u4')]);assert dt.itemsize==76
M=np.eye(4);M[:3,:3]=qr(CQ,np.diag(S));M[3,:3]=T
def source(ai):
 a=mesh['assemblies'][ai];vb=mesh['vertex_buffers'][a['vertex_buffer']];ib=mesh['index_buffers'][a['index_buffer']];n=vb['vertex_count'];at=vb['data_file_offset'];stride=vb['stride_bytes'];assert stride==48
 pos=np.array(vb['positions']);frame=[];nativeframe=[]
 for off in [20,28,36]:
  z=np.maximum(np.ndarray((n,3),'<i2',raw,at+off,(stride,2)).astype(float)/32767.,-1);zn=z@NATIVE[4:7,:3];zn/=np.linalg.norm(zn,axis=1)[:,None];nativeframe.append(zn);z/=S;z/=np.linalg.norm(z,axis=1)[:,None];frame.append(qr(CQ,z))
 uv=np.ndarray((n,2),'<f4',raw,at+12,(stride,4));col=np.ndarray((n,4),'u1',raw,at+44,(stride,1));out=np.zeros(n,dt);out['v']=np.concatenate([qr(CQ,pos*S)+T,*frame,uv,uv],axis=1).astype('<f4');out['rgba']=col;out['material']=414763;out['flags']=3
 meta={'assembly':ai,'vertices':n,'triangles':ib['triangle_count'],'VB_SHA256':vb['data_sha256'],'IB_SHA256':ib['data_sha256'],'source_vs_native_world_position_max':float(np.max(abs((pos@NATIVE[:3,:3]+NATIVE[3,:3])-(qr(CQ,pos*S)+T)))),'source_vs_native_frame_max':float(np.max(abs(np.concatenate(frame,axis=1)-np.concatenate(nativeframe,axis=1))))}
 return out,np.array(ib['indices'],'<u4').reshape(-1,3),meta
new,NI,nmeta=source(0);old,OI,ometa=source(2)
assert nmeta['VB_SHA256']=='c6775ac0c914b385a424a60afd8a7c7e5044cd0f841dcfb627c54689fa7ba6d5'
assert nmeta['IB_SHA256']=='909d7ccddfe9c133673bb0e787cc540a2953f2e808712e5cbb4bffde2efed7dd'
cell=W/'c1_-14_0.bin';b=cell.read_bytes();assert sha(b)=='3ecc8fd97451db82cdf9409c93f5d353f06d9e6653e461ce90cfd9030371bf15'
magic,nv,ni,nd=struct.unpack_from('<4sIII',b);assert magic==b'OAWE';draws=[struct.unpack_from('<III',b,16+k*12) for k in range(nd)];base=16+nd*12;V=np.frombuffer(b,dt,nv,base);I=np.frombuffer(b,'<u4',ni,base+nv*76)
def tk(v):return tuple(sorted(a.tobytes() for a in v))
budget=collections.Counter(tk(old[t]) for t in OI);remove=[]
for mid,f,n in draws:
 if mid!=270:continue
 for at in range(f,f+n,3):
  key=tk(V[I[at:at+3]])
  if budget[key]:budget[key]-=1;remove.append(at)
assert len(remove)==50 and not any(budget.values()),(len(remove),sum(budget.values()))
remove=set(remove);outdraw=[];chunks=[];cursor=0;keptold=[]
for mid,f,n in draws:
 chunk=np.array([int(k) for at in range(f,f+n,3) if at not in remove for k in I[at:at+3]],'<u4');keptold.extend(chunk.tolist())
 if mid==270:chunk=np.r_[chunk,NI.ravel()+nv].astype('<u4')
 outdraw.append((mid,cursor,len(chunk)));chunks.append(chunk);cursor+=len(chunk)
NV=np.r_[V,new];IX=np.concatenate(chunks);out=b'OAWE'+struct.pack('<III',len(NV),len(IX),nd)+b''.join(struct.pack('<III',*d) for d in outdraw)+NV.tobytes()+IX.tobytes()
C=O/'candidate-cell';C.mkdir(exist_ok=True);(C/cell.name).write_bytes(out)
subset=b'OAWE'+struct.pack('<III',len(new),NI.size,1)+struct.pack('<III',270,0,NI.size)+new.tobytes()+NI.astype('<u4').tobytes();(O/'rock-only.oawe').write_bytes(subset)
(O/'removed-triangle-index-offsets.u32').write_bytes(np.array(sorted(remove),'<u4').tobytes())
_,onv,oni,ond=struct.unpack_from('<4sIII',out);obase=16+ond*12;assert out[obase:obase+nv*76]==b[base:base+nv*76];OX=np.frombuffer(out,'<u4',oni,obase+onv*76)
retained=[int(k) for mid,f,n in outdraw for at in range(f,f+n,3) if int(OX[at])<nv for k in OX[at:at+3]];assert retained==keptold;assert int(OX.max())<onv
lo=V['v'][:,:3].min(axis=0);hi=V['v'][:,:3].max(axis=0);nlo=new['v'][:,:3].min(axis=0);nhi=new['v'][:,:3].max(axis=0);within=bool(np.all(nlo>=lo)&np.all(nhi<=hi));assert within
clips=np.c_[mesh['vertex_buffers'][0]['positions'],np.ones(len(new))]@NATIVE[8:12];positive=clips[:,3]>0;screen=np.c_[(clips[positive,0]/clips[positive,3]+1)*768,(1-clips[positive,1]/clips[positive,3])*432]
receipt={'native_draw':69783,'VS':923,'PS':924,'pipeline':12360,'FAB':424996,'source_name':'for_rock_stone05','material':414763,'material_row':270,'material_family':4,'source_space':431646,'source_render_slot':'0x160','source_render_index':470,'prior_provenance_instance_ordinal':672,'source_render_record_hex':record.hex(),'source_TRS':{'translation':T.tolist(),'quaternion':Q.tolist(),'scale':S.tolist()},'source_stream':str(src),'source_stream_sha256':sha(raw),'source_space_sha256':sha(sb),'source_direct_matrix':M.tolist(),'native_world_matrix':NATIVE[:4].tolist(),'matrix_max_abs_error':float(np.max(abs(M-NATIVE[:4]))),'replacement':nmeta,'removed':ometa,'native_source_VB_and_IB_exact':True,'source_position_UV_RGBA_raw_bytes':True,'all_retained_vertex_bytes_exact':True,'all_retained_triangle_indices_and_order_exact':True,'removed_triangle_count':50,'appended_triangle_count':190,'preserved_triangle_count':(ni-150)//3,'before_counts':{'vertices':nv,'indices':ni,'draws':nd,'triangles':ni//3},'after_counts':{'vertices':onv,'indices':oni,'draws':ond,'triangles':oni//3},'current_input_cell':str(cell),'current_input_sha256':sha(b),'candidate_cell':str(C/cell.name),'candidate_sha256':sha(out),'rock_only_sha256':sha(subset),'cell_bounds_before':[lo.tolist(),hi.tolist()],'replacement_bounds':[nlo.tolist(),nhi.tolist()],'replacement_inside_existing_cell_AABB':within,'replacement_inside_nominal_xy_cell_1_minus14':bool(nlo[0]>=6400 and nhi[0]<=12800 and nlo[1]>=-89600 and nhi[1]<=-83200),'native_visible_positive_w_vertices':int(positive.sum()),'native_projected_bounds_positive_w':[screen.min(axis=0).tolist(),screen.max(axis=0).tolist()],'request_frustum_change':'No expanded cell AABB/request envelope: all new vertices inside existing bounds; same material/draw list; native capture verifies frontmost coverage at both requested pixels. Parent promotes only after checking input SHA.','promotion_performed':False,'no_material_texture_shader_edits':True,'limits':['Native shader/texture filtering and full brightness attribution not claimed resolved by this geometry fixture.','Changes only this requested LOD0 cell instance; no universal dynamic LOD policy or coarse cell changes.']}
index_path=W/'index.bin';index=index_path.read_bytes();nc=struct.unpack_from('<I',index,8)[0];assert len(index)==20+nc*48
for ii in range(nc):
 row=struct.unpack_from('<ii6f4I',index,20+ii*48)
 if row[:2]==(1,-14):
  inside=all(nlo[j]>=row[2+j] and nhi[j]<=row[5+j] for j in range(3));assert inside
  receipt.update(index_bin_sha256=sha(index),index_row_index=ii,actual_index_cell_bounds=[list(row[2:5]),list(row[5:8])],replacement_inside_actual_index_cell_AABB=inside,index_row_triangle_counts_before=list(row[8:]),index_LOD0_triangle_count_after=oni//3)
  break
else:raise AssertionError('target cell absent from index')
(O/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:receipt[k] for k in ['candidate_sha256','matrix_max_abs_error','replacement','before_counts','after_counts','cell_bounds_before','replacement_bounds','replacement_inside_existing_cell_AABB','replacement_inside_nominal_xy_cell_1_minus14']},indent=2))
