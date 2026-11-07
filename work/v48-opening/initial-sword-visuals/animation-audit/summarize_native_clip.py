from pathlib import Path
import json,struct,hashlib,csv
import numpy as np
O=Path(__file__).resolve().parent;Q=O.parent;R=Q.parents[2]
def sha(b):return hashlib.sha256(b).hexdigest()
def qangle(q,r):
 d=np.abs(np.sum(q*r,axis=-1)/(np.linalg.norm(q,axis=-1)*np.linalg.norm(r,axis=-1)))
 return np.degrees(2*np.arccos(np.clip(d,0,1)))
def matrix(f):
 x,y,z,w=(-float(f[0]),-float(f[1]),-float(f[2]),float(f[3]))
 M=np.eye(4);M[:3,:3]=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])@np.diag(f[8:11]);M[:3,3]=f[4:7];return M
def globalm(local,parents):
 M=[]
 for j,p in enumerate(parents):M.append(matrix(local[j]) if p is None else M[p]@matrix(local[j]))
 return np.array(M)
def main():
 manifest=json.loads((Q/'animation-source-manifest.json').read_text());source=Q/manifest['animation_sources'][0]['file'];raw=source.read_bytes();n=struct.unpack_from('<I',raw,4)[0];a=raw[8:8+n]
 sk=R/'work/v48-opening/initial-sword-audit/inputs/initial_0.pak/1789717.fab_bxml';s=sk.read_bytes();skbase=4;joints=struct.unpack_from('<H',s,skbase+0x10)[0];bo=skbase+0x18+struct.unpack_from('<i',s,skbase+0x18)[0]
 B=np.frombuffer(s,'<f4',joints*12,bo).reshape(joints,12).copy()
 b=(O/'1789841-native-local-trs.bin').read_bytes();J,F,fps=struct.unpack_from('<IIf',b)
 assert (J,F)==(54,101) and J==joints and len(b)==12+F*J*48
 V=np.frombuffer(b,'<f4',offset=12).reshape(F,J,12);assert np.isfinite(V).all()
 md=json.loads((Q/'1789717-fab-metadata.json').read_text());parents=[x['parent_index'] for x in md['bones']]
 assert all(p is None or p<j for j,p in enumerate(parents))
 maps=json.loads((O/'track-mapping-source.json').read_text())
 for c in maps.values():assert len(set(c['indices']))==c['count'] and all(0<=i<J for i in c['indices'])
 channels=[('rotation',slice(0,4)),('translation',slice(4,7)),('scale',slice(8,11))]
 identity=[]
 for name,sl in channels:
  touched=set(maps[name+'_static']['indices'])|set(maps[name+'_dynamic']['indices']);untouched=sorted(set(range(J))-touched)
  assert np.array_equal(V[:,untouched,sl],np.broadcast_to(B[untouched,sl],(F,len(untouched),B[untouched,sl].shape[-1])))
  static=maps[name+'_static']['indices'];assert np.array_equal(V[:,static,sl],np.broadcast_to(V[0,static,sl],V[:,static,sl].shape))
  identity.append(dict(channel=name,untouched_indices=untouched,untouched_bind_byte_identity=True,static_tracks_constant_all_frames=True))
 q=V[:,:,:4].astype('f8');restq=B[:,:4].astype('f8');angles=qangle(q,restq);td=np.linalg.norm(V[:,:,4:7].astype('f8')-B[:,4:7],axis=2);sd=np.max(abs(V[:,:,8:11]-B[:,8:11]),axis=2)
 rows=[]
 for j in range(J):
  rows.append(dict(bone=j,parent=parents[j],name_hash=md['bones'][j]['name_hash_u32'],source_transform_file_offset=bo+j*48,source_parent_file_offset=md['bones'][j]['parent_file_offset'],rest_q=B[j,:4].tolist(),rest_t=B[j,4:8].tolist(),rest_s=B[j,8:12].tolist(),frame0_translation_delta=float(td[0,j]),frame0_rotation_delta_degrees=float(angles[0,j]),end_translation_delta=float(td[-1,j]),end_rotation_delta_degrees=float(angles[-1,j]),clip_max_translation_delta=float(td[:,j].max()),clip_max_rotation_delta_degrees=float(angles[:,j].max())))
 samples=[]
 for f in [0,50,F-1]:
  local=[dict(bone=j,parent=parents[j],name_hash=rows[j]['name_hash'],rotation_xyzw=V[f,j,:4].tolist(),translation_xyzw=V[f,j,4:8].tolist(),scale_xyzw=V[f,j,8:12].tolist()) for j in range(J)]
  gb=globalm(B,parents);gv=globalm(V[f],parents);gd=np.linalg.norm(gv[:,:3,3]-gb[:,:3,3],axis=1)
  rec=dict(frame=f,frame_time_seconds=f/fps,bones=local,derived_global_matrices=gv.reshape(J,16).tolist(),local_rest_max_translation_delta=float(td[f].max()),local_rest_max_translation_bone=int(td[f].argmax()),local_rest_max_rotation_delta_degrees=float(angles[f].max()),local_rest_max_rotation_bone=int(angles[f].argmax()),derived_global_origin_rest_max_delta=float(gd.max()),derived_global_origin_rest_max_bone=int(gd.argmax()))
  (O/f'sample-frame-{f:03}.json').write_text(json.dumps(rec,indent=2)+'\n');samples.append({k:v for k,v in rec.items() if k not in ['bones','derived_global_matrices']})
 (O/'bone-rest-deltas.json').write_text(json.dumps(rows,indent=2)+'\n')
 with (O/'frame-summary.csv').open('w',newline='') as f:
  w=csv.writer(f);w.writerow(['frame','frame_time_seconds','max_local_translation_rest_delta','translation_bone','max_local_rotation_rest_delta_degrees','rotation_bone'])
  for i in range(F):w.writerow([i,i/fps,td[i].max(),td[i].argmax(),angles[i].max(),angles[i].argmax()])
 def ptr(at):return at+struct.unpack_from('<i',a,at)[0]
 ft,dt=ptr(0x3c),ptr(0x38);sets=struct.unpack_from('<H',a,0x12)[0];fs=[]
 for i in range(sets):
  base,count=struct.unpack_from('<2H',a,ft+i*4);off=struct.unpack_from('<I',a,dt+i*8+4)[0];sz=struct.unpack_from('<H',a,dt+i*8+2)[0]
  assert off+sz<=len(a);fs.append(dict(index=i,first_frame=base,count_field=count,payload_offset=off,stored_bytes=sz,payload_sha256=sha(a[off:off+sz])))
 # FAB->motionset and motionset->animation are direct exact ID words.
 fabrefs=[];fabraw=sk.read_bytes()
 needle=struct.pack('<I',1789863);at=fabraw.find(needle)
 while at>=0:fabrefs.append(at);at=fabraw.find(needle,at+1)
 mtn=Q/'inputs/initial_0.pak/1789863.mtns_bxml';mt=mtn.read_bytes();assert struct.unpack_from('<I',mt,40)[0]==1789841 and struct.unpack_from('<I',mt,1060)[0]==1789841
 report=dict(status='Native offline decode PASS; no active initial-state assumption',fab=1789717,motion_set=1789863,animation=1789841,skeleton=dict(file=str(sk.relative_to(R)),sha256=sha(s),bone_count=J,local_transform_offset=bo,parent_indices=parents,FAB_motion_set_word_offsets=fabrefs),clip=dict(file=str(source.relative_to(R)),sha256=sha(raw),container_word0=struct.unpack_from('<I',raw)[0],payload_bytes=n,trailing_bytes=len(raw)-8-n,tag=a[:4].decode(),header_float_at4=struct.unpack_from('<f',a,4)[0],header_float_at4_interpretation='source duration candidate3.333s, agrees outer3333word; no new native duration consumer proved',fps=fps,frame_count=F,clip_joint_count=struct.unpack_from('<H',a,14)[0],frame_set_count=sets,flags_u16_at12=struct.unpack_from('<H',a,12)[0],channel_flags_u16_at38=struct.unpack_from('<H',a,38)[0],frame_sets=fs,frame_table_payload_offset=ft,data_table_payload_offset=dt,motion_set_animation_word_offsets=[40,1060]),output=dict(file='1789841-native-local-trs.bin',bytes=len(b),sha256=sha(b),format='little-endian u32joints,u32frames,f32fps; then frame-major,bone-major12f32 = Qxyzw,Txyzw,Sxyzw; exact native decoder output',quaternion_norm_max_error=float(abs(np.linalg.norm(q,axis=2)-1).max()),finite=True,scale_xyz_max_rest_delta=float(sd.max())),mapping=dict(evidence=['0111bf10 passes source channel index lists to native scatter decoders','01112400/01112990 scatter quaternion to out[index*0x30]','011141e0/011142a0 scatter vector to out[index*0x30+componentoffset]'],tracks=maps,identity_checks=identity,policy='Unanimated channel components initialized byte-exact from this54-bone source skeleton eachframe. No guessed names/remapping/weight changes.'),samples=samples,limits=['Native rest is not frame0: static translation tracks11/19 change source-local T even atframe0. Do not select rest or frame0 as original initial pose without state evidence.','No motion-set node segment/default state interpretation; all101stored clip samples decoded, not an animation state picked.','No animation blending, actor uniform scale override, rootmotion policy, IK/custom-bone handlers or skinning were added.','Output native quaternion floats retained without normalization; angle statistics normalize only the dot product.','Frame100 uses existing helper endpoint logic: last data set index1 count46, requested relative47 clampsidx46,alpha1; set2 is zero-byte sentinel. Last stored endpoint not independently runtime-played.','No original game process/entrypoint/imports/device actions. Standalone helper maps private original PEsections and calls pureEdge0111bf10.'])
 (O/'animation-manifest.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(dict(frames=F,joints=J,first=samples[0],end=samples[-1],untouched_bind_channels_valid=True),indent=2))
if __name__=='__main__':main()
