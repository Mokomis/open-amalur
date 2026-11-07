"""Independent CPU source PS352 oracle, not extracted from current C shader."""
from pathlib import Path
import json,hashlib
import numpy as np
OUT=Path(__file__).resolve().parent
f=np.float32
SZ=32
def sha(b):return hashlib.sha256(b).hexdigest()
def normal(v):
 v=np.asarray(v,dtype=np.float32)
 return v/np.sqrt(np.sum(v*v,axis=-1,keepdims=True,dtype=np.float32),dtype=np.float32)
nn=np.array([[0,0,2],[.4,0,3],[0,.5,4]],dtype=np.float32)
tt=np.array([[3,0,.1],[2,.2,0],[4,0,.4]],dtype=np.float32)
bb=np.array([[0,4,.1],[.2,3,0],[0,2,.3]],dtype=np.float32)
y,x=np.mgrid[0:SZ,0:SZ].astype(np.float32)
W=np.stack([(x+f(.5))*f(2/SZ)-f(1),(y+f(.5))*f(2/SZ)-f(1),x*f(0)],axis=-1)
b1=(W[...,0]+f(1))*f(.25);b2=(W[...,1]+f(1))*f(.25);b0=f(1)-b1-b2
def interp(v):return b0[...,None]*v[0]+b1[...,None]*v[1]+b2[...,None]*v[2]
N0,T0,B0=interp(normal(nn)),interp(normal(tt)),interp(normal(bb))
# Active native packed map x=R*A*2-1, y=G*2-1; positive reconstructed Z.
rgba=np.array([204,102,128,255],dtype=np.float32)/f(255)
mx=rgba[0]*rgba[3]*f(2)-f(1);my=rgba[1]*f(2)-f(1)
mz=np.sqrt(np.clip(f(1)-mx*mx-my*my,0,1),dtype=np.float32)
N=normal(T0*mx+B0*my+N0*mz)
wrongN=normal(interp(tt)*mx+interp(bb)*my+interp(nn)*mz)
V=normal(np.array([4,0,-1],dtype=np.float32)-W)
D=np.array([80,120,160],dtype=np.float32)/f(255)
CUBE=np.array([101,173,219],dtype=np.float32)/f(255)
VC=np.array([204,153,230],dtype=np.float32)/f(255)
def unorm(x):return np.rint(np.clip(x,0,1)*f(255)).astype(np.uint8)
cases=[json.loads(l) for l in (OUT/'gpu-cases.jsonl').read_text().splitlines() if l.strip()]
res=[];actuals={}
for c in cases:
 if c['diagnostic_normal']:
  rgb=unorm(N*f(.5)+f(.5));half=None;rim=None;base=None
 else:
  facing=np.clip(np.sum(N*V,axis=-1,dtype=np.float32),f(0),f(1))
  rim=np.clip((f(1.4) if c['fresnel_on'] else f(0))*np.power(f(1)-facing,f(2.4)),f(0),f(1))
  base=(D+f(.15)*rim[...,None])*VC*f(c['alpha'])
  # CharacterAmbientMap * vertexAlpha * RAW base, clamp independently then F16.
  half=np.clip(CUBE*f(c['alpha'])*base,f(0),f(1)).astype(np.float16).astype(np.float32)
  rgb=unorm(half)
 expected=np.concatenate([rgb,np.full((SZ,SZ,1),255,dtype=np.uint8)],axis=-1)
 actual=np.frombuffer((OUT/c['file']).read_bytes(),dtype=np.uint8).reshape(SZ,SZ,4)
 actuals[c['id']]=actual.copy()
 delta=np.abs(actual.astype(np.int16)-expected.astype(np.int16))
 row={**c,'oracle_file':c['file'].replace('.rgba','-oracle.rgba'),'actual_sha256':sha(actual.tobytes()),'oracle_sha256':sha(expected.tobytes()),'oracle_center_rgba':expected[16,16].tolist(),'max_abs_code_delta':int(delta.max()),'mismatched_channels':int(np.count_nonzero(delta)),'channels_over_one_code':int(np.count_nonzero(delta>1)),'compared_channels':int(delta.size),'center_normal':N[16,16].tolist()}
 if half is not None:row.update(center_rim=float(rim[16,16]),center_raw_base=base[16,16].tolist(),center_G2_F16=half[16,16].tolist())
 (OUT/row['oracle_file']).write_bytes(expected.tobytes());res.append(row)
pairs=[];unchanged=True
for c in cases:
 if c['diagnostic_normal'] or c['constant_changed'] or c['generic_ambient_nonzero']:continue
 for o in cases:
  if o['diagnostic_normal'] or o['alpha']!=c['alpha'] or o['fresnel_on']!=c['fresnel_on']:continue
  equal=actuals[c['id']].tobytes()==actuals[o['id']].tobytes()
  unchanged &= equal
  pairs.append({'baseline':c['id'],'comparison':o['id'],'constant_changed':o['constant_changed'],'generic_ambient_nonzero':o['generic_ambient_nonzero'],'all4096bytes_equal':equal})
diags=[c for c in cases if c['diagnostic_normal']]
normal_delta=int(np.max(np.abs(actuals[diags[0]['id']].astype(np.int16)-actuals[diags[1]['id']].astype(np.int16))))
wrongnormal_delta=int(np.max(np.abs(unorm(wrongN*f(.5)+f(.5)).astype(np.int16)-unorm(N*f(.5)+f(.5)).astype(np.int16))))
assert len(cases)==26 and unchanged and normal_delta<=1 and wrongnormal_delta>=2
assert all(c['channels_over_one_code']==0 for c in res)
assert all(np.all(actuals[c['id']][...,:3]==0) for c in cases if not c['diagnostic_normal'] and c['alpha']==0)
summary={'case_count':len(cases),'width':SZ,'height':SZ,'production_material_cases':24,'diagnostic_basis_cases':2,'source_math':'NativePS352: rim=sat(Fx*pow(1-sat(dot(mappedN,V)),Fy));rawBase=(D+ExtraX*rim)*VCrgb*VCa;G2=half(sat(CharacterCube*VCa*rawBase));lights/shadow/sun/fog/AOoff;RGBA8=roundEven(sat(G2)*255). ConstantColor and generic ambient globals intentionally absent from oracle.',
 'comparison_tolerance_codes':1,'tolerance_reason':'CPU source arithmetic and ANGLE highp pow/normalize/interpolation may differ around an 8bit rounding boundary; all exact per-channel differences reported, no ignored samples.',
 'max_abs_code_delta':max(c['max_abs_code_delta'] for c in res),'total_mismatched_channels':sum(c['mismatched_channels'] for c in res),'total_channels':sum(c['compared_channels'] for c in res),
 'constant_and_genericambient_all_pairs_byte_identical':bool(unchanged),'basis_scaled_vs_unit_max_code_delta':normal_delta,'counterfactual_no_vertex_normalization_max_normal_code_delta':wrongnormal_delta,
 'all_alpha_zero_black':True,'tests_passed':True,'cases':res,'invariance_pairs':pairs}
(OUT/'oracle-validation.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k not in ['cases','invariance_pairs']}))
for c in res:print(c['id'],c['center_rgba'],'oracle',c['oracle_center_rgba'],'max',c['max_abs_code_delta'],'mismatch',c['mismatched_channels'])
