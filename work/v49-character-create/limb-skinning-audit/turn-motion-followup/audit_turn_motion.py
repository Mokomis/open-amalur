from pathlib import Path
import sys,struct,json,math,hashlib
import numpy as np
sys.dont_write_bytecode=True
P=Path(r'C:\Users\rwill\Documents\Opem Amalur');B=P/'work/v49-character-create/limb-skinning-audit';O=Path(__file__).resolve().parent
sys.path.insert(0,str(B));import audit_skinning as A
base=P/'work/v49-character-create/packs/Almain_Male/character.bin';b=base.read_bytes();J,parents,clips,parts=A.packparts(b)
report=json.loads(base.with_name('character-report.json').read_text())
symbols=json.loads((P/'work/v20-inputs/symbols.json').read_text());names=symbols['ragdoll_bone_mappings'];rig=A.amalur_fab.parse_file(P/'work/v20-inputs/patch_0.pak/456813.fab_bxml')
selected=[0,1,2];out=[]
def yaw(q):
 x,y,z,w=q
 return math.degrees(math.atan2(2*(x*y+w*z),1-2*(y*y+z*z)))
for ci in [17,18,19]:
 clip=clips[ci];n=clip['frames'];rows=np.frombuffer(b,'<f4',n*J*7,clip['offset']).reshape(n,J,7)
 q=np.empty((n,J,4));t=np.empty((n,J,3))
 for f in range(n):
  for j in range(J):
   local=rows[f,j,:4].astype(float);local/=np.linalg.norm(local);v=rows[f,j,4:].astype(float);parent=parents[j]
   if parent<0:q[f,j]=local;t[f,j]=v
   else:
    q[f,j]=A.qm(q[f,parent],local)
    pq=q[f,parent];t[f,j]=t[f,parent]+v+2*np.cross(pq[:3],pq[3]*v+np.cross(pq[:3],v))
 jointrows=[]
 for j in selected:
  delta=[A.qm(q[f,j],A.conj(q[0,j])) for f in range(n)]
  yaws=np.degrees(np.unwrap(np.radians([yaw(d) for d in delta])))
  dq=np.array(delta[-1]);angle=math.degrees(2*math.acos(min(1.,abs(float(dq[3]/np.linalg.norm(dq))))))
  jointrows.append(dict(joint=j,name_hash=rig['bones'][j]['name_hash_u32'],name=names.get(str(rig['bones'][j]['name_hash_u32'])),parent=parents[j],
   world_position_start=t[0,j].tolist(),world_position_last=t[-1,j].tolist(),world_translation_delta_cm=(t[-1,j]-t[0,j]).tolist(),world_translation_distance_cm=float(np.linalg.norm(t[-1,j]-t[0,j])),
   net_world_yaw_degrees=float(yaws[-1]),max_abs_transient_world_yaw_degrees=float(abs(yaws).max()),relative_rotation_angle_start_to_last_degrees=angle,
   local_root_translation_range_cm=(rows[:,j,4:].max(0)-rows[:,j,4:].min(0)).tolist()))
 name=report['clips'][ci][0];aid=next(int(k) for k,v in symbols['animation'].items() if v==name)
 baked=P/f'work/v20-char/baked/{aid}.bin';raw=baked.read_bytes();bj,bf,fps=struct.unpack_from('<IIf',raw)
 assert (bj,bf)==(J,n)
 original=np.ndarray((n,J,12),'<f4',raw,12,(J*48,48,4))
 converted=original[:,:,:7].copy();converted[:,:,:3]*=-1
 assert np.array_equal(converted,rows)
 out.append(dict(clip=ci,name=name,source_animation=aid,frames=n,fps=clip['fps'],period_seconds=(n-1)/clip['fps'],joints=jointrows,
  baked_path=str(baked.relative_to(P)),baked_sha256=A.H(raw),every_frame_all_joint_quat_conjugate_and_translation_copy_exact=True))
receipt=dict(result='PASS',base_pack_sha256=A.H(b),definition='Normalize local clip quaternion as current pose; compose parent/local FK with current algebra, facing0/feet0. World yaw is yaw of Qframe_world*inverse(Qstart_world), about global Z; transient yaw is unwrapped across frames.',
 clips=out,builder_root_motion_stripping='No explicit rotation/translation stripping in builder; per frame it only conjugates every quaternion and copies XYZ translation. Every staged row is byte-value equal to this conversion from retained baked data.',
 baker_limits='clip_bake.cpp initializes bind, invokes retained Edge decoder, writes joint48B output; the separate user output buffer is not persisted. This audit establishes staged skeletal clip motion, not a complete original locomotion/root-motion channel contract.',
 slope_lean='Still explicitly unproven: parser constructs delta from each authored slope/lean pair against their quaternion midpoint; original reference pose/additive application convention not recovered.',
 source_sha256={f:A.H((P/f).read_bytes()) for f in ['work/v19-host/oa_character.c','work/v19-host/android_scene.c','work/v20-char/build_character.py','work/v20-char/clip_bake.cpp']})
(O/'turn-motion-receipt.json').write_text(json.dumps(receipt,indent=2))
for c in out:
 print(c['clip'],c['name'])
 for r in c['joints']:print(r['joint'],r['name'],'yawNet',r['net_world_yaw_degrees'],'transYawMax',r['max_abs_transient_world_yaw_degrees'],'dP',r['world_translation_delta_cm'])
