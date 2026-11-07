"""CPU SPIR-V evaluator for ONLY captured straight-line PS792.
Independent from GLSL emitter; supports the exact operations encountered.
Constant sampled textures exercise material arithmetic; records cube direction.
No GPU execution. Never mutates the capture or original files.
"""
from pathlib import Path
import re,json,numpy as np
p=Path(__file__).parent;lines=(p/'module-838.spvasm').read_text().splitlines()
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
   elif storage=='Input':val[k]=inputs['FragCoord'] if k=='%gl_FragCoord' else inputs[int(decor[k]['Location'][0])]
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
   elif op=='OpCompositeExtract':val[k]=val[a[1]][int(a[2])]
   elif op=='OpCompositeInsert':
    val[k]=val[a[2]].copy();val[k][int(a[3])]=val[a[1]]
   elif op=='OpCompositeConstruct':val[k]=F([val[x] for x in a[1:]])
   elif op=='OpFOrdGreaterThanEqual':val[k]=np.greater_equal(val[a[1]],val[a[2]])
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
 return {key:val[value] for key,value in out.items()},coords

def norm(a):return F(a/F(np.sqrt(np.dot(a,a))))
rng=np.random.default_rng(838);g=np.frombuffer((p/'native-global1376.bin').read_bytes(),'<f4').reshape(-1,4);view=np.zeros((5,4),np.float32);view[4,:3]=F([15,-9,30]);dyn=np.zeros((16,4),np.float32);dyn[15,3]=F(.4375);maximum=np.zeros(3);cubeError=0.
with np.errstate(divide='ignore',invalid='ignore'):
 for case in range(400):
  cb=np.zeros((3,4),np.float32);cb[0,:]=F([*rng.uniform(0,2,3),1]);cb[1,:2]=F([rng.uniform(0,2),rng.uniform(1,150)]);cb[2,0]=F(rng.uniform(0,3));VC=F(rng.uniform(0,1,4));D=F(rng.uniform(0,1,4));n=F(rng.uniform(0,1,4));s=F(rng.uniform(0,1,4));mask=F(rng.uniform(0,1,4));cube=F([*rng.uniform(0,1,3),1]);basis=F(rng.uniform(-1,1,(3,3)));W=F(rng.uniform(-20,20,3));UV=F([.31,.69,0,0]);xy=F([F(n[0]*n[3]),n[1]])*F(2)-F(1);z=F(np.sqrt(max(F(1-np.dot(xy,xy)),F(0))));N=norm(F(F(basis[1]*xy[0]+basis[2]*xy[1])+basis[0]*z));rawSpec=F(s[1]*cb[1,0]);base=F(F(D[:3]*VC[:3])*VC[3]);q=F(rawSpec*g[80,0]);V=norm(F(view[4,:3]-W));R=F(-V+F(F(2)*np.dot(V,N))*N);lobe=F(np.exp2(F(np.log2(np.clip(R[2],F(0),F(1)))*F(g[4,3]*g[79,3]))));ambient=F(F(F(F(1)-np.clip(q,F(0),F(1)))*cube[:3])*base+F(q*F(lobe*g[4,:3])));E=F(F(F(mask[1]*D[:3])*cb[0,:3])*cb[2,0]);expected=[F([*(N*F(.5)+F(.5)),cb[1,1]]),np.clip(F([*base,F(rawSpec*VC[3])]),F(0),F(1)),F([*np.clip(F(ambient+E),F(0),F(1)),dyn[15,3]])]
  inputs={1:VC,2:UV,4:F([*W,0]),6:F([*basis[0],0]),7:F([*basis[1],0]),8:F([*basis[2],0])};samples={32:lambda uv,c=cube:c,33:lambda uv,c=D:c,34:lambda uv,c=mask:c,35:lambda uv,c=n:c,36:lambda uv,c=s:c};out,coords=run(inputs,{0:cb,1:g,2:view,4:dyn},samples)
  for i in range(3):maximum[i]=max(maximum[i],float(np.max(np.abs(out[i]-expected[i]))));assert np.all(np.isfinite(out[i]))
  coord=next(v for b,v in coords if b==32);cubeError=max(cubeError,float(np.max(np.abs(coord-N[[0,2,1]]))))
assert maximum.max()<2e-5,(maximum,cubeError)
report={'cases':400,'max_G0_G1_G2_error':maximum.tolist(),'max_cube_direction_error':cubeError,'sampled_maps':'constant samples exercise all shader arithmetic; not texture filtering or GPU execution','shader':'captured module838','GPU_execution':False};(p/'emissive-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
