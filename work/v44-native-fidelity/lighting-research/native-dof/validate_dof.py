"""CPU SPIR-V evaluator for ONLY captured straight-line PS792.
Independent from GLSL emitter; supports the exact operations encountered.
Constant sampled textures exercise material arithmetic; records cube direction.
No GPU execution. Never mutates the capture or original files.
"""
from pathlib import Path
import re,json,numpy as np
p=Path(__file__).parent;lines=(p/'module-1849.spvasm').read_text().splitlines()
F=lambda x:np.asarray(x,dtype=np.float32)
def run(inputs,uniforms,samples):
 val={};ptr={};decor={};types={};out={};inside=False;coords=[]
 for l in lines:
  s=l.split()
  if not s or s[0]==';':continue
  k=s[0] if len(s)>1 and s[1]=='=' else None;op=s[2] if k else s[0];a=s[3:] if k else s[1:]
  if op=='OpDecorate':decor.setdefault(a[0],{})[a[1]]=a[2:]
  elif op=='OpTypePointer':ptr[k]=(a[0],a[1])
  elif op=='OpTypeFloat':types[k]='f'
  elif op=='OpTypeInt':types[k]='i'
  elif op=='OpTypeVector':types[k]=int(a[1])
  elif op=='OpConstant':val[k]=F(float(a[1])) if types[a[0]]=='f' else np.uint32(a[1])
  elif op=='OpConstantComposite':val[k]=np.asarray([val[x] for x in a[1:]],dtype=np.uint32 if a[0].endswith('uint') else np.float32)
  elif op=='OpFunction':inside=True
  elif op=='OpFunctionEnd':inside=False
  elif op=='OpVariable':
   storage,base=ptr[a[0]]
   if storage=='Uniform':val[k]=uniforms[int(decor[k]['Binding'][0])]
   elif storage=='UniformConstant':val[k]=int(decor[k]['Binding'][0])
   elif storage=='Input':val[k]=inputs[int(decor[k]['Location'][0])]
   elif storage=='Output':val[k]=F([0]*4);out[int(decor[k]['Location'][0])]=k
   elif storage=='Function':val[k]=F([0]*4)
   else:raise ValueError(storage)
  elif inside:
   if op in ['OpLabel','OpReturn']:continue
   if op=='OpAccessChain':val[k]=val[a[1]][int(val[a[-1]])]
   elif op=='OpLoad':val[k]=val[a[1]]
   elif op=='OpStore':val[a[0]]=val[a[1]]
   elif op=='OpSampledImage':val[k]=val[a[1]]
   elif op=='OpVectorShuffle':val[k]=np.concatenate([val[a[1]],val[a[2]]])[[int(i) for i in a[3:]]]
   elif op=='OpCompositeConstruct':val[k]=F([val[x] for x in a[1:]])
   elif op=='OpFOrdLessThan':val[k]=np.less(val[a[1]],val[a[2]])
   elif op=='OpFOrdEqual':val[k]=np.equal(val[a[1]],val[a[2]])
   elif op=='OpBitwiseAnd':val[k]=np.bitwise_and(val[a[1]],val[a[2]])
   elif op=='OpINotEqual':val[k]=np.not_equal(val[a[1]],val[a[2]])
   elif op=='OpSelect':val[k]=np.where(val[a[1]],val[a[2]],val[a[3]])
   elif op=='OpBitcast':val[k]=np.asarray(val[a[1]],dtype=np.uint32).view(np.float32) if a[0].endswith('float') else np.asarray(val[a[1]],dtype=np.float32).view(np.uint32)
   elif op=='OpFMul':val[k]=F(val[a[1]]*val[a[2]])
   elif op=='OpFAdd':val[k]=F(val[a[1]]+val[a[2]])
   elif op=='OpFDiv':val[k]=F(val[a[1]]/val[a[2]])
   elif op=='OpFNegate':val[k]=-val[a[1]]
   elif op=='OpDot':val[k]=F(np.dot(val[a[1]],val[a[2]]))
   elif op=='OpImageSampleImplicitLod':
    binding=val[a[1]];coords.append((binding,val[a[2]].copy()));val[k]=F(samples[binding](val[a[2]]))
   elif op=='OpExtInst':
    fn=a[2];v=[val[x] for x in a[3:]]
    if fn=='FMax':val[k]=np.maximum(*v)
    elif fn=='FMin':val[k]=np.minimum(*v)
    elif fn=='FClamp':val[k]=np.clip(*v)
    elif fn=='Sqrt':val[k]=F(np.sqrt(v[0]))
    elif fn=='InverseSqrt':val[k]=F(1/np.sqrt(v[0]))
    elif fn=='Log2':val[k]=F(np.log2(v[0]))
    elif fn=='Exp2':val[k]=F(np.exp2(v[0]))
    else:raise ValueError(fn)
   else:raise ValueError(op)
 return val[out[0]],coords

def sample(im,uv):
 h,w=im.shape[:2];xy=F(uv)*F([w,h])-F(.5);a=np.floor(xy).astype(int);t=xy-a;lo=np.maximum(0,np.minimum(a,[w-1,h-1]));hi=np.maximum(0,np.minimum(a+1,[w-1,h-1]));u=F(t[0]);v=F(t[1]);top=F(im[lo[1],lo[0]]*(1-u)+im[lo[1],hi[0]]*u);bottom=F(im[hi[1],lo[0]]*(1-u)+im[hi[1],hi[0]]*u);return F(top*(1-v)+bottom*v)
rng=np.random.default_rng(1849);scene=F(rng.integers(0,256,(32,32,4)))/F(255);fuzz=F(rng.integers(0,180,(16,16,4)))/F(255);fuzz[:,:,1]=F(rng.integers(0,40,(16,16)))/F(255);fuzz[:,:,2]=fuzz[:,:,0];samples={32:lambda uv:sample(scene,uv),33:lambda uv:sample(fuzz,uv)}
# Kernel comes independently from the concise shader's literal array.
s=(p/'effect_fs.frag').read_text();kernel=[F([float(a),float(b)]) for a,b in re.findall(r'vec2\(([-.0-9]+),([-.0-9]+)\)',s)];assert len(kernel)==16
scale=F([6/1536,6/864]);maxerr=0;cases=160
for i in range(cases):
 uv=F(rng.uniform(0,1,2));actual,_=run({1:F([*uv,0,0])},{0:F([[*scale,0,0]])},samples);center=sample(fuzz,uv);acc=sample(scene,uv)[:3];weight=F(1);factor=F(.5 if center[2]>0 else 1)
 for tap in kernel:
  q=F(F(center[0]*F(scale*tap))+uv);f=sample(fuzz,q);w=F(f[0]*(factor if f[1]<center[1] else F(1)));acc=F(sample(scene,q)[:3]*w+acc);weight=F(weight+w)
 expected=F([*(acc/weight),center[0]]);assert np.all(np.isfinite(actual)) and np.all(np.isfinite(expected));maxerr=max(maxerr,float(np.max(np.abs(actual-expected))))
# Defaults round-trip to captured normalized constants exactly in float32.
pack=F([F(9974.3115234375)*F(1/524288),F(1)/F(F(20001)*F(1/524288)),.699999988079071,1/524288]);captured=F([.01902448944747448,26.213088989257812,.699999988079071,1/524288]);assert np.array_equal(pack,captured)
report={'cases':cases,'maximum_RGBA_error_vs_active_SPIRV1849':maxerr,'tolerance':1e-6,'default_params_pack_bit_exact':bool(np.array_equal(pack.view(np.uint32),captured.view(np.uint32))),'captured_far_start_world':float(captured[0]/captured[3]),'far_range_world_float32':float(F(1)/F(captured[1]*captured[3])),'full_alpha_reaches_cap_world_double':23975.011475297357,'gpu_execution':False,'independence':'Direct SPIR-V interpreter versus concise kernel, same bilinear samples from random quantizedRGBA8scene/fuzziness; sample coordinates differ if kernel/formula is wrong.'};assert maxerr<1e-6;(p/'dof-kernel-validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

lines=(p/'module-1841.spvasm').read_text().splitlines();fuzzMax=0.;camera=F(np.zeros((8,4)));camera[6,0]=F(1/524288);camera[7,:2]=F([-.03818615898489952,.03818806633353233]);config=F([[0,0,*captured[:2]],[captured[2],0,0,0]])
for d in np.r_[np.linspace(0,1,120,dtype=np.float32),F([.995,.997,.999,1.])]:
 actual,_=run({1:F([.3,.7,0,0])},{0:config,2:camera},{32:lambda uv,d=d:F([d,0,0,0]),33:lambda uv:F([0,0,0,0])});dd=F(1 if d==0 else d);z=F(F(1)/F(F(camera[7,0]*dd)+camera[7,1]));nz=F(z*captured[3]);far=F(min(max(F(F(nz-captured[0])*captured[1]),F(0)),captured[2]));gated=far if nz>captured[0] else F(0);expected=F([gated,nz,gated,gated]);assert np.all(np.isfinite(actual));fuzzMax=max(fuzzMax,float(np.max(np.abs(actual-expected))))
report['far_fuzz_cases_vs_active_SPIRV1841']=124;report['maximum_fuzz_RGBA_error']=fuzzMax;assert fuzzMax==0.;(p/'dof-kernel-validation.json').write_text(json.dumps(report,indent=2)+'\n');print('Fuzz1841 maximum error',fuzzMax)
