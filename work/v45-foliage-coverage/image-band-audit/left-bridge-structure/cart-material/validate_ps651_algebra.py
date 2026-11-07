from pathlib import Path
import json,re,numpy as np
Q=Path(__file__).resolve().parent
lines=(Q/'module-651.spvasm').read_text().splitlines();ops=[];binding={};location={};storage={};constants={};active=False
for line in lines:
 t=line.strip().split()
 if not t:continue
 if t[0]=='OpDecorate':
  if t[2]=='Binding':binding[t[1]]=int(t[3])
  if t[2]=='Location':location[t[1]]=int(t[3])
 if'='in t:
  rid=t[0];op=t[2];a=t[3:]
  if op=='OpConstant':constants[rid]=float(a[1])
  if op=='OpConstantComposite':constants[rid]=np.array([constants[x]for x in a[1:]],float)
  if op=='OpVariable':storage[rid]=a[1]
  if op=='OpFunction':active=True
  if active:ops.append((rid,op,a))
 elif active:ops.append((None,t[0],t[1:]))
def normalize(x):return x/np.sqrt(np.dot(x,x))
def native(inputs,cb,tex):
 values=dict(constants);memory={k:np.zeros(4)for k in storage};out={}
 for k,s in storage.items():
  if s=='Input':memory[k]=inputs[location[k]]
  elif s=='Uniform':memory[k]=('cb',binding[k])
  elif s=='UniformConstant':memory[k]=('resource',binding[k])
 for rid,op,a in ops:
  val=None
  if op in('OpFunction','OpLabel','OpVariable'):continue
  elif op=='OpFunctionEnd':break
  elif op=='OpLoad':
   p=memory.get(a[1],values.get(a[1]));val=cb[p[1]][p[2]]if isinstance(p,tuple)and p[0]=='element'else p
  elif op=='OpStore':memory[a[0]]=values[a[1]];continue
  elif op=='OpAccessChain':val=('element',binding[a[1]],int(values[a[-1]]))
  elif op=='OpVectorShuffle':val=np.r_[values[a[1]],values[a[2]]][list(map(int,a[3:]))]
  elif op=='OpCompositeConstruct':val=np.r_[tuple(values[x]for x in a[1:])]
  elif op=='OpFMul':val=values[a[1]]*values[a[2]]
  elif op=='OpFAdd':val=values[a[1]]+values[a[2]]
  elif op=='OpFDiv':val=values[a[1]]/values[a[2]]
  elif op=='OpFNegate':val=-values[a[1]]
  elif op=='OpDot':val=np.dot(values[a[1]],values[a[2]])
  elif op=='OpExtInst':
   kind=a[2];v=[values[x]for x in a[3:]]
   if kind=='FClamp':val=np.minimum(np.maximum(v[0],v[1]),v[2])
   elif kind=='FMax':val=np.maximum(v[0],v[1])
   elif kind=='FAbs':val=np.abs(v[0])
   elif kind=='Sqrt':val=np.sqrt(v[0])
   elif kind=='InverseSqrt':val=1/np.sqrt(v[0])
   elif kind=='Log2':val=np.log2(v[0])
   elif kind=='Exp2':val=np.exp2(v[0])
   else:raise ValueError(kind)
  elif op=='OpSampledImage':val=('sample',values[a[1]][1])
  elif op=='OpImageSampleImplicitLod':val=tex(values[a[1]][1],values[a[2]])
  elif op=='OpReturn':continue
  else:raise ValueError(op)
  values[rid]=val
 return np.array([memory[k]for k,s in storage.items()if s=='Output'])
def compact(inputs,cb,tex):
 uv=inputs[2][:2];VC=inputs[1];W=inputs[3][:3];N0,T,B=[inputs[k][:3]for k in(5,6,7)];mat=cb[0];n=tex(35,uv);xy=np.array([n[0]*n[3],n[1]])*2-1;N=normalize(xy[0]*T+xy[1]*B+np.sqrt(np.clip(1-np.dot(xy,xy),0,1))*N0);V=normalize(cb[2][4,:3]-W);fr=1-np.clip(np.exp2(np.log2(max(abs(np.dot(N,V)),1e-5))*mat[3,1])*mat[3,2],0,1);rho=fr*tex(34,uv)[1]*VC[3]*mat[1,3];base=tex(33,uv)[:3]*VC[:3]*(1-rho);spec=tex(36,uv)[1]*mat[0,0];R=2*np.dot(V,N)*N-V;amb=tex(32,N[[0,2,1]])[:3]*base+rho*tex(37,R[[0,2,1]])[:3]*mat[2,:3]*cb[1][6,:3]
 return np.array([np.r_[N*.5+.5,mat[0,1]],np.clip(np.r_[base,spec],0,1),np.r_[np.clip(amb,0,1),np.clip(cb[4][15,3],0,1)]])
rng=np.random.default_rng(651);max_error=0.;cases=512
for case in range(cases):
 cb={0:rng.uniform(0,2,(4,4)),1:rng.uniform(0,2,(7,4)),2:rng.uniform(-50,50,(5,4)),4:rng.uniform(-.2,1.2,(16,4))};cb[0][3,1]=rng.uniform(.1,6);cb[0][0,1]=rng.uniform(0,128)
 inputs={1:rng.uniform(0,1,4),2:rng.uniform(-2,2,4),3:rng.uniform(-50,50,4)}
 for k in(5,6,7):
  tri=np.array([normalize(rng.normal(size=3))for j in range(3)]);weights=rng.dirichlet([1,1,1]);inputs[k]=np.r_[weights@tri,0]
 fixed={b:rng.uniform(0,1,4)for b in(33,34,35,36)}
 def tex(binding,p):
  if binding in fixed:return np.clip(fixed[binding]+np.sin(float(np.sum(p)))*.017,0,1)
  n=normalize(p);coeff=np.array([.13,.19,.11])if binding==32 else np.array([.23,-.17,.31]);rgb=np.clip(.4+n*coeff,0,1);return np.r_[rgb,1]
 a=native(inputs,cb,tex);b=compact(inputs,cb,tex);error=float(np.max(np.abs(a-b)));max_error=max(max_error,error);assert error<1e-10,(case,a,b,error)
result=dict(native_module=651,cases=cases,max_abs_output_error=max_error,verified='Original SPIRV SSA interpreter vs compact material/reflection equations, randomized non-unit interpolated bases, masks,colors,globals,reflectiondirections; float64 algebra comparison.',gpu_validation=False,notes='Shader compile separately checked byglslangValidator. This validates equations and channel/coordinate mappings, not GPUinstruction rounding or texture filtering.')
(Q/'ps651-algebra-validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
