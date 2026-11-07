"""Bounded source/current palette+weights audit. All outputs private, no pack mutation."""
from pathlib import Path
import sys,struct,json,hashlib,collections,math,re
import numpy as np
sys.dont_write_bytecode=True
P=Path(r'C:\Users\rwill\Documents\Opem Amalur');O=Path(__file__).resolve().parent
sys.path.insert(0,str(P/'work/v07-mesh'));import amalur_fab
H=lambda b:hashlib.sha256(b).hexdigest()
def dump(n,x):(O/n).write_text(json.dumps(x,indent=2))
def qm(a,b):
 x,y,z,w=a;X,Y,Z,W=b
 return np.array([w*X+x*W+y*Z-z*Y,w*Y-x*Z+y*W+z*X,w*Z+x*Y-y*X+z*W,w*W-x*X-y*Y-z*Z])
def conj(q):return np.array([-q[0],-q[1],-q[2],q[3]])
def qr(q,v):return qm(qm(q,np.array([v[0],v[1],v[2],0.])),conj(q))[:3]
def rotmat(q):
 x,y,z,w=q
 return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
def skeleton(f):
 w=[]
 for b in f['bones']:
  q=conj(np.array(b['quaternion_xyzw']));t=np.array(b['position_xyzw'][:3]);parent=b['parent_index']
  if parent is not None:q,t=qm(w[parent][0],q),w[parent][1]+qr(w[parent][0],t)
  w.append((q,t))
 return w
def packparts(b):
 J,C,N,T=struct.unpack_from('<4I',b,8);a=24+((J+1)//2)*4;parents=struct.unpack_from('<'+'h'*J,b,24);clips=[]
 for ci in range(C):
  nf,fps=struct.unpack_from('<If',b,a);a+=8;clips.append(dict(frames=nf,fps=fps,offset=a));a+=nf*J*28
 for _ in range(T):
  w,h=struct.unpack_from('<II',b,a);a+=8+w*h*4
 parts=[]
 for i in range(N):
  nv,ni,pc,ti=struct.unpack_from('<IIIi',b,a);a+=16;pa=a;a+=pc*32;va=a;a+=nv*52;ia=a;a+=ni*4
  parts.append(dict(part=i,nv=nv,ni=ni,pc=pc,palette_offset=pa,vertex_offset=va,index_offset=ia))
 assert a==len(b)
 return J,parents,clips,parts
def native_evidence():
 rows=[]
 for q in sorted((P/'outputs/scene-v19/shaders').glob('*.asm')):
  s=q.read_text()
  if 'BONEWEIGHT' not in s or 'vs_4_0' not in s:continue
  lines=s.splitlines();hits=[dict(line=i+1,text=l) for i,l in enumerate(lines) if 'dcl_input v2.xyz' in l or 'dp4 r0.x, l(-1.000000, -1.000000, -1.000000, 1.000000)' in l]
  assert len(hits)==2 and not re.search(r'v2\.w',s)
  rows.append(dict(file=str(q.relative_to(P)),sha256=H(q.read_bytes()),instructions=hits))
 assert len(rows)==31
 for name in ['065c48e28029429a.asm','28350f22853a5bbe.asm']:
  (O/name).write_bytes((P/'outputs/scene-v19/shaders'/name).read_bytes())
 dump('native-weight-contract.json',dict(shaders=rows,equation='w=(SNORM16.xyz,1-dot(SNORM16.xyz,1)); Pskin=sum4(w_i*M[boneindex_i]*vec4(P,1)); palette is three float4 rows per index. No clamp on reconstructed fourth.',
  active_permutation_limit='31 retained original weightedVS agree; exact Almain male active pipeline not captured here. No stored fourth component is consumed.'))
def main():
 # Native weight proof reused from sealed Almain audit; no shader rescans.
 M=json.loads((O/'source-join-manifest.json').read_text());b=(P/M['pack']).read_bytes();assert H(b)==M['pack_sha256']
 J,parents,clips,parts=packparts(b);rigpath=P/'work/v20-inputs/patch_0.pak/456813.fab_bxml';rig=amalur_fab.parse_file(rigpath);rw=skeleton(rig);rh={r['name_hash_u32']:i for i,r in enumerate(rig['bones'])};bn=json.loads((P/'work/v20-inputs/symbols.json').read_text())['ragdoll_bone_mappings']
 header=b'OACPL01\0'+struct.pack('<6I',1,len(parts),2,128,32,0)+bytes.fromhex(H(b));assert len(header)==64
 side=bytearray(header);rows=[];corrections=[]
 for r in M['parts']:
  p=parts[r['part']];raw=(P/r['source_mesh']).read_bytes();nv=p['nv'];stride=r['source_stride'];base=r['source_vb_data_file_offset']
  sw=np.ndarray((nv,4),'<i2',raw,base+16,(stride,2)).astype(np.float64)/32767.
  sj=np.ndarray((nv,4),'u1',raw,base+12,(stride,1))
  ow=np.ndarray((nv,4),'<f4',b,p['vertex_offset']+36,(52,4)).astype(np.float64)
  oj=np.ndarray((nv,4),'u1',b,p['vertex_offset']+32,(52,1))
  assert np.array_equal(sj,oj) and sw.min()>=0 and sw.max()<=1
  nw=np.column_stack([sw[:,:3],1-sw[:,:3].sum(1)])
  bw=np.column_stack([sw[:,:3],np.maximum(0,nw[:,3])])
  assert abs(ow-bw).max()<3e-8
  f=amalur_fab.parse_file(P/r['source_fab']);d=f['mesh_descriptors'][r['assembly']]
  op=b[p['palette_offset']:p['palette_offset']+p['pc']*32];new=bytearray();mappings=[];mismatch=0
  for si,rem in enumerate(d['remaps']):
   sb=rem['bone_index'];cur=sb;chain=[]
   while cur is not None and f['bones'][cur]['name_hash_u32'] not in rh:
    chain.append(cur);cur=f['bones'][cur]['parent_index']
   assert cur is not None
   j=rh[f['bones'][cur]['name_hash_u32']];iq=conj(rw[j][0]);it=-qr(iq,rw[j][1])
   entry=struct.pack('<I7f',j,*iq,*it);new+=entry
   oldj,=struct.unpack_from('<I',op,si*32) if si<p['pc'] else (0xffffffff,)
   offset=rem['trs']['file_offset'];fb=(P/r['source_fab']).read_bytes()
   source_it=struct.unpack_from('<3f',fb,offset);source_iq=conj(np.array(struct.unpack_from('<4f',fb,offset+16)))
   sh=f['bones'][sb]['name_hash_u32'];dsth=rig['bones'][j]['name_hash_u32'];oldh=rig['bones'][oldj]['name_hash_u32'] if oldj<J else None
   mismatch+=oldj!=j
   mappings.append(dict(slot=si,source_bone_index=sb,source_name_hash=sh,source_name=bn.get(str(sh)),target_rig_joint=j,target_name_hash=dsth,target_name=bn.get(str(dsth)),ancestor_source_chain=chain,exact_hash_join=not chain,
    current_rig_joint=oldj,current_name_hash=oldh,current_name=bn.get(str(oldh)),source_remap_offset=offset,source_remap52_hex=fb[offset:offset+52].hex(),
    source_inverse_t_vs_shared_rig_inverse_t_max_error=max(abs(x-y) for x,y in zip(source_it,it)),
    source_inverse_q_vs_shared_rig_inverse_q_max_error=min(max(abs(x-y) for x,y in zip(source_iq,iq)),max(abs(x+y) for x,y in zip(source_iq,iq))),
    replacement_record32_hex=entry.hex()))
  source_count=len(d['remaps']);positive=sj[nw>0]
  # Tiny negative reconstructed weights are legal native residuals; their indices must also fit.
  active=sj[nw!=0]
  assert int(active.max())<source_count
  rr=dict(part=r['part'],label=r['label'],fab=r['fab'],assembly=r['assembly'],material=r['material_id'],vertices=nv,source_stride=stride,
   current_palette_capacity=p['pc'],source_palette_count=source_count,mapped_slot_disagreements=mismatch,
   source_first3_sum_min=float(sw[:,:3].sum(1).min()),source_first3_sum_max=float(sw[:,:3].sum(1).max()),stored_four_sum_min=float(sw.sum(1).min()),stored_four_sum_max=float(sw.sum(1).max()),
   negative_raw_components=int((sw<0).sum()),native_negative_fourth_vertices=int((nw[:,3]<0).sum()),stored_fourth_differs_from_native_vertices=int((abs(sw[:,3]-nw[:,3])>1e-10).sum()),
   source_stored_fourth_min=float(sw[:,3].min()),source_stored_fourth_max=float(sw[:,3].max()),native_fourth_min=float(nw[:,3].min()),native_fourth_max=float(nw[:,3].max()),
   builder_current_weights_max_error=float(abs(ow-bw).max()),native_vs_builder_weights_max_error=float(abs(ow-nw).max()),
   max_positive_weight_source_index=int(positive.max()),max_nonzero_native_weight_source_index=int(active.max()),palette_mappings=mappings)
  rows.append(rr)
  if mismatch or source_count != p['pc']:
   assert source_count<=p['pc']
   pos=len(side)
   record=struct.pack('<8I',p['part'],r['fab'],r['assembly'],source_count,p['pc'],p['nv'],p['ni'],0)+bytes.fromhex(H(op))+bytes.fromhex(H(new))+bytes.fromhex(r['source_fab_sha256'])
   assert len(record)==128;side+=record+new
   corrections.append(dict(part=p['part'],source_count=source_count,current_capacity=p['pc'],record_offset=pos,replacement_palette_offset=pos+128,replacement_bytes=len(new),old_palette_sha256=H(op),replacement_sha256=H(new),
    all_positive_indices_within_source_count=bool(int(positive.max())<source_count),max_positive_index=int(positive.max()),all_nonzero_native_indices_within_source_count=bool(int(active.max())<source_count),
    source_fab=r['source_fab'],source_fab_sha256=r['source_fab_sha256'],assembly_descriptor_offset=d['file_offset'],source_remap_count=source_count,source_mapping=mappings,
    preserved_trailing_records=p['pc']-source_count,policy='Replace only prefix source_count records; retain existing capacity/header/unused trailing records. Existing current main-rig inverse-rest+ancestor policy unchanged.'))
 dump('weights-and-palettes.json',dict(base_pack=M['pack'],base_pack_sha256=M['pack_sha256'],rig=str(rigpath.relative_to(P)),rig_sha256=H(rigpath.read_bytes()),joint_count=J,parts=rows))
 side[16:20]=struct.pack('<I',len(corrections))
 (O/'varani-male-palette-corrections.oacpl').write_bytes(side)
 dump('palette-correction-manifest.json',dict(base_pack=M['pack'],base_pack_sha256=M['pack_sha256'],base_pack_bytes=len(b),sidecar='varani-male-palette-corrections.oacpl',sidecar_sha256=H(side),sidecar_bytes=len(side),corrections=corrections,
  explicit_limits=['All source-own palette slots joined by bone hash; missing helper/facial bones retain existing ancestor fallback recorded per slot. No new native full-rig claim.',
   'Stored remap52 data is retained at exact descriptor boundaries; amalur_fab generic read_trs labels incorrectly treat first16 bytes as quaternion for these records. We read raw offsets T@0,Q@16,S@32,word44/index48, without trusting those generic labels.',
   'Source own remap association and direct name-hash matches are proven byte joins; full native per-instance palette producer/motion tree not reconstructed.',
   'Current main-rig inverse-rest convention preserved; source inverse-bind comparison is evidence, not automatic replacement authorization.',
   'Weight clamp policy remains unchanged. No current pack/source edit.']))
 print('SEALED PALETTE',len(side),H(side))
 print('TOTAL',sum(r['vertices'] for r in rows),'negativeNative4',sum(r['native_negative_fourth_vertices'] for r in rows))
if __name__=='__main__':main()
