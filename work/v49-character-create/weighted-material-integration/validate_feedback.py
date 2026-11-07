"""Independent nativeVS375 source equations against actual staged adapter GPU feedback."""
from pathlib import Path
import json,hashlib,struct,numpy as np
R=Path(r'C:\Users\rwill\Documents\Opem Amalur');O=Path(__file__).resolve().parent
b=(R/'work/v49-character-create/vertex-contract-audit/almain-male-attributes.oacat').read_bytes()
parts={};at=64
for k in range(12):
 pi,fab,asm,mid,stride,nv,ni,flags=struct.unpack_from('<8I',b,at);at+=128+nv*64
 raw=b[at:at+nv*stride];at+=nv*stride
 if pi in [1,2,3,5]:
  def ary(dtype,count,off):
   return np.ndarray((nv,count),dtype=dtype,buffer=raw,offset=off,strides=(stride,np.dtype(dtype).itemsize)).copy()
  sn=lambda x:np.maximum(np.float32(-1),x.astype(np.float32)/np.float32(32767))
  parts[pi]={'nv':nv,'stride':stride,'P':ary('<f4',3,0),'j':ary('i1',4,12).astype(np.int32),'w':sn(ary('<i2',4,16)),'UV':ary('<f4',2,24),'N':sn(ary('<i2',3,32)),'T':sn(ary('<i2',3,40)),'B':sn(ary('<i2',3,48)),'VC':ary('u1',4,56).astype(np.float32)/np.float32(255) if stride==60 else np.ones((nv,4),dtype=np.float32)}
assert at==len(b)
def norm(x):return x/np.sqrt(np.sum(x*x,axis=1,dtype=np.float32))[:,None]
cases=[json.loads(l) for l in (O/'pose-cases.jsonl').read_text().splitlines()]
res=[];maxerr={k:0. for k in ['world_position_cm','N','T','B','VC','UV0']};counter_B=0.;vertex_total=0
for c in cases:
 p=parts[c['part']];nv=p['nv'];mat=np.frombuffer((O/f"pose-{c['pose']}-part{c['part']}-bones.bin").read_bytes(),dtype='<f4').reshape(c['palette_count'],3,4)
 w=p['w'].copy();w[:,3]=np.sum(np.column_stack([w[:,:3],np.ones(nv,dtype=np.float32)])*np.array([-1,-1,-1,1],dtype=np.float32),axis=1,dtype=np.float32)
 def skin(v,point=False):
  selected=mat[p['j']];v4=np.column_stack([v,np.ones(nv,dtype=np.float32)]) if point else v
  m=selected if point else selected[:,:,:,:3]
  dots=np.sum(m*v4[:,None,None,:],axis=3,dtype=np.float32)
  r=dots[:,1,:]*w[:,1,None]
  for i in [0,2,3]:r=dots[:,i,:]*w[:,i,None]+r
  return r
 wp=skin(p['P'],True);N=norm(skin(p['N']));T=norm(skin(p['T']))
 # Independently derive entity rotation from the same production root quaternion
 # construction (half-angle), not from the adapter's full-angle sin/cos uniforms.
 half=np.float32(c['facing'])*np.float32(.5);ss=np.sin(half);cc=np.cos(half)
 sn=np.float32(2)*ss*cc;cs=np.float32(1)-np.float32(2)*ss*ss
 B=p['B'].copy();B[:,0]=cs*p['B'][:,0]-sn*p['B'][:,1];B[:,1]=sn*p['B'][:,0]+cs*p['B'][:,1];B=norm(B)
 expected=np.column_stack([wp,N,T,B,p['VC'],p['UV']])
 actual=np.frombuffer((O/f"pose-{c['pose']}-part{c['part']}-feedback.bin").read_bytes(),dtype='<f4').reshape(nv,18)
 assert np.isfinite(actual).all()
 spans={'world_position_cm':(0,3),'N':(3,6),'T':(6,9),'B':(9,12),'VC':(12,16),'UV0':(16,18)}
 err={}
 for k,(lo,hi) in spans.items():
  e=float(np.max(np.abs(actual[:,lo:hi]-expected[:,lo:hi])));err[k]=e;maxerr[k]=max(maxerr[k],e)
 assert err['world_position_cm']<.002 and max(err[k] for k in ['N','T','B'])<5e-6 and err['VC']==0 and err['UV0']==0,err
 # Conventional skin-all-three is NOT nativeVS375; quantify this fixture sensitivity.
 wrong=norm(skin(p['B']));bd=float(np.max(np.abs(actual[:,9:12]-wrong)));counter_B=max(counter_B,bd)
 raster=(O/f"pose-{c['pose']}-part{c['part']}.rgba").read_bytes()
 res.append({**c,'feedback_sha256':hashlib.sha256(actual.tobytes()).hexdigest(),'raster_sha256':hashlib.sha256(raster).hexdigest(),'max_abs_error':err,'wrong_skin_B_max_component_delta':bd,'observed_world_bounds':[actual[:,:3].min(axis=0).tolist(),actual[:,:3].max(axis=0).tolist()]})
 vertex_total+=nv
summary={'status':'PASS','pose_count':4,'part_cases':len(res),'feedback_vertices':vertex_total,'feedback_float_components':vertex_total*18,'max_abs_error':maxerr,'counterfactual_skinned_B_max_component_difference':counter_B,'all_sourceUV0_and_COLOR_exact':maxerr['VC']==maxerr['UV0']==0,'source56_color_provenance':'native_shared_all_ff from existing capture; not authored','source60_color_provenance':'authored exactRGBA','basis_oracle':'Independent native375 equations with actual currentC/OACPLworldbone rows; Bentityrotation derived via production half-angle quaternion; no double facing.','scope':'ProductionCpose and testcamera, not nativeclothingcapture/animation timing match. Raster uses sourceCharacterCube-only ambient and ownsourceD/N/S. No source-original-frame pixel equality claim.','cases':res}
(O/'feedback-validation.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k!='cases'}))
print('covered range',min(x['covered_pixels'] for x in cases),max(x['covered_pixels'] for x in cases))
