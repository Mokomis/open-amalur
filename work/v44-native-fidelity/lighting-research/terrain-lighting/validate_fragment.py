"""CPU SPIR-V evaluator for ONLY captured straight-line PS792.
Independent from GLSL emitter; supports the exact operations encountered.
Constant sampled textures exercise material arithmetic; records cube direction.
No GPU execution. Never mutates the capture or original files.
"""
from pathlib import Path
import re,json,numpy as np
p=Path(__file__).parent;lines=(p/'module-792.spvasm').read_text().splitlines()
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
  elif op=='OpConstant':val[k]=F(float(a[1])) if types[a[0]]=='f' else int(a[1])
  elif op=='OpConstantComposite':val[k]=F([val[x] for x in a[1:]])
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
   elif op=='OpFMul':val[k]=F(val[a[1]]*val[a[2]])
   elif op=='OpFAdd':val[k]=F(val[a[1]]+val[a[2]])
   elif op=='OpFDiv':val[k]=F(val[a[1]]/val[a[2]])
   elif op=='OpFNegate':val[k]=-val[a[1]]
   elif op=='OpDot':val[k]=F(np.dot(val[a[1]],val[a[2]]))
   elif op=='OpImageSampleImplicitLod':
    binding=val[a[1]];coords.append((binding,val[a[2]].copy()));val[k]=samples[binding]
   elif op=='OpExtInst':
    fn=a[2];v=[val[x] for x in a[3:]]
    if fn=='FMax':val[k]=np.maximum(*v)
    elif fn=='FClamp':val[k]=np.clip(*v)
    elif fn=='Sqrt':val[k]=F(np.sqrt(v[0]))
    elif fn=='InverseSqrt':val[k]=F(1/np.sqrt(v[0]))
    elif fn=='Log2':val[k]=F(np.log2(v[0]))
    elif fn=='Exp2':val[k]=F(np.exp2(v[0]))
    else:raise ValueError(fn)
   else:raise ValueError(op)
 return [val[out[i]] for i in range(3)],coords

def norm(x):return x/np.linalg.norm(x)
rng=np.random.default_rng(792);maxerr=0;maxcube=0
with np.errstate(divide='ignore'):
 for case in range(300):
  paint=rng.uniform(.01,.99,4);ds=rng.uniform(.05,.99,(4,4));ns=rng.uniform(.1,.9,(4,4));levels=rng.uniform(.05,3,4);powers=rng.uniform(1,100,4)
  basis=rng.uniform(-1,1,(3,3));basis[0,2]+=2;I=rng.uniform(-10,10,3);cube=rng.uniform(0,.6,4);sky=rng.uniform(.05,.8,4);sky[3]=1.;height=.2;shift=.1875
  u={0:F([levels,powers]),1:F(np.zeros((82,4))),3:F(np.zeros((4,4))),4:F(np.zeros((16,4)))};u[1][4]=sky;u[1][79,3]=5;u[1][80,0]=.9;u[1][81,3]=height;u[3][2]=[.125,.25,.5,1.];u[4][15,3]=shift
  inputs={1:F([.75,.25,.3,.7]),3:F([*I,0]),5:F([*basis[0],0]),6:F([*basis[1],0]),7:F([*basis[2],0])};samples={32:F(cube),41:F(paint)}
  for j in range(4):samples[33+j]=F(ds[j]);samples[37+j]=F(ns[j])
  actual,coords=run(inputs,u,samples)
  rem=1-paint[0];second=paint[1]*rem;third=paint[2]*(1-paint[1]*rem)*rem;w=np.array([paint[0],second,third,1-np.clip(paint[0]+second+third,0,1)]);h=w*ds[:,3];w=np.maximum(h-(max(h)-height),0);inv=1/sum(w);n=sum(w[j]*ns[j] for j in range(4))*inv;nt=n[:3]*2-1;N=norm(nt[0]*basis[1]+nt[1]*basis[2]+nt[2]*basis[0]);albedo=sum(w[j]*ds[j,:3] for j in range(4))*inv*paint[3];raw=np.dot(levels,w)*inv*n[3];Q=raw*.9;rr=I/np.linalg.norm(I);ref=rr-2*np.dot(rr,N)*N;amb=np.clip(cube[:3]*(1-np.clip(Q,0,1))*albedo+np.clip(ref[2],0,1)**5*sky[:3]*Q,0,1);expected=[np.r_[N*.5+.5,np.dot(powers,w)*inv],np.r_[np.clip(albedo,0,1),np.clip(raw*paint[3],0,1)],np.r_[amb,shift]]
  maxerr=max(maxerr,max(np.max(np.abs(a-b)) for a,b in zip(actual,expected)));cubeDir=next(v for b,v in coords if b==32);maxcube=max(maxcube,np.max(np.abs(cubeDir-N[[0,2,1]])))
report={'cases':300,'maximum_G0_G1_G2_absolute_error':float(maxerr),'maximum_cube_direction_error':float(maxcube),'tolerance':2e-5,'gpu_execution':False,'validation':'Independent CPU evaluation of active SPIR-V vs concise material/ambient formulas; random constant texture samples, weights, normals, specular levels and powers.'};assert maxerr<2e-5 and maxcube<2e-5;print(json.dumps(report,indent=2));(p/'terrain-fragment-validation.json').write_text(json.dumps(report,indent=2)+'\n')
