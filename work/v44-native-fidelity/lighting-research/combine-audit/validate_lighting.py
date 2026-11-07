"""CPU SPIR-V evaluator for ONLY captured straight-line PS792.
Independent from GLSL emitter; supports the exact operations encountered.
Constant sampled textures exercise material arithmetic; records cube direction.
No GPU execution. Never mutates the capture or original files.
"""
from pathlib import Path
import re,json,numpy as np
p=Path(__file__).parent;lines=(p/'module-1895.spvasm').read_text().splitlines()
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
 return val[out[0]],coords

def norm(x):return F(x/F(np.sqrt(np.dot(x,x))))
def half(x):return np.asarray(x,dtype=np.float16).astype(np.float32)
rng=np.random.default_rng(1895);mem=(p.parent/'../does-not-exist').resolve() if False else Path('/Users/rwillmore/Documents/Codex/2026-11-05/open-amalur-native-camera/memory-52.bin');g=np.frombuffer(mem.read_bytes()[360896:360896+1376],dtype=np.float32).reshape(-1,4);sun=g[2,:3];sunC=g[3,:3];sh=g[5];luma=F([.2126,.7152,.0722]);report={}
with np.errstate(divide='ignore'):
 # Validate native deferred sunlight/ambient/AO reconstruction.
 maxerr=0
 for case in range(250):
  n=norm(F(rng.uniform(-1,1,3)));I=F(rng.uniform(-1,1,3));g0=half(F([*(n*.5+.5),rng.uniform(1,100)]));g1=half(F(rng.uniform(0,1,4)));g2=half(F([*rng.uniform(0,1,3),rng.choice([.0625,.1875,.4375]) ]));local=half(F(rng.uniform(0,2,4)));ao=F([*rng.uniform(0,1,2),0,0]);N=norm(F(g0[:3]*2-1));ii=norm(I);R=F(ii-F(2*np.dot(ii,N))*N);dn=float(np.dot(N,sun));front=min(np.clip(dn,0,1),float(1+sh[3]*(ao[1]-1)));backscale=float(ao[0]*g[80,1]);direct=front+np.clip(-dn,0,1)*backscale;ref=float(np.dot(sun,R));lobes=np.maximum(np.clip([ref,-ref],0,1),.00001)**(float(g0[3])*.25);lobes[0]*=float(dn>=0);sunSpec=lobes[0]*direct+lobes[1]*backscale;localSpec=local[:3]*local[3]/(np.dot(local[:3],luma)+1e-7);expected=((1-front)*sh[:3]*g1[:3]+g2[:3])*ao[0]+(sunC*direct+local[:3])*g1[:3]+(sunC*sunSpec+localSpec)*g1[3];samples={32:lambda uv,g0=g0:g0,33:lambda uv,g1=g1:g1,34:lambda uv,g2=g2:g2,35:lambda uv,local=local:local,37:lambda uv,ao=ao:ao};actual,_=run({1:F([.4,.6,0,0]),2:F([*I,0])},{1:g},samples);assert np.all(np.isfinite(actual));maxerr=max(maxerr,float(np.max(np.abs(actual[:3]-expected))))
 report['deferred1895']={'cases':250,'max_RGB_error':maxerr};assert maxerr<2e-5
 # Validate one native point contribution before F16 additive storage.
 lines=(p/'module-1870.spvasm').read_text().splitlines();view=F(np.zeros((9,4)));view[4,:3]=F([8591.932617,-87036.03125,6493.066406]);view[7,:2]=F([-.03818615898489952,.03818806633353233]);view[8,2:]=F([1/1536,1/864]);maxerr=0
 for case in range(200):
  ray=F(rng.uniform(-1,1,3));d=F(rng.uniform(.99,.9995));z=F(1/F(view[7,0]*d+view[7,1]));W=F(ray*z+view[4,:3]);pos=F(W+F(rng.uniform(-500,500,3)));color=F(rng.uniform(0,2,3));inner=F(100);outer=F(1000);co=F([[*pos,F(-1/(outer-inner))],[*color,F(outer/(outer-inner))]]);n=norm(F(rng.uniform(-1,1,3)));g0=half(F([*(n*.5+.5),rng.uniform(1,100)]));N=norm(F(g0[:3]*2-1));I=norm(ray);delta=F(pos-W);dist=F(np.sqrt(np.dot(delta,delta)));Ld=F(delta/F(dist));at=F(np.clip(F(dist*co[0,3]+co[1,3]),0,1));nl=F(np.clip(np.dot(N,Ld),0,1));R=F(I-F(2*np.dot(I,N))*N);r=F(np.clip(np.dot(R,Ld),0,1));sp=F(np.exp2(F(np.log2(max(r,F(.00001)))*F(g0[3]*.25))));rgb=F(F(nl*color)*at);alpha=F(np.dot(F(F(F(nl*sp)*color)*at),luma));expected=F([*rgb,alpha]);samples={32:lambda uv,g0=g0:g0,34:lambda uv,d=d:F([d,0,0,0])};actual,_=run({'FragCoord':F([400.5,500.5,0,0]),1:F([*ray,0])},{0:co,2:view},samples);assert np.all(np.isfinite(actual));maxerr=max(maxerr,float(np.max(np.abs(actual-expected))))
 report['point1870']={'cases':200,'max_RGBA_error':maxerr};assert maxerr<2e-5
 # Validate source screen fog with zero distortion field.
 lines=(p/'module-1898.spvasm').read_text().splitlines();view=view[:8];maxerr=0
 for case in range(200):
  physical=F(rng.uniform(50,50000));d=F(F(1/physical-view[7,1])/view[7,0]);Z=F(1/F(F(view[7,0]*d)+view[7,1]));ray=F(rng.uniform(-1,1,3));I=norm(ray);scene=F(rng.integers(0,256,4))/255;trans=min(float(np.exp2(F(F(g[1,0]*Z+g[1,1])*F(-1.44269502)))),1);tint=float(max(np.dot(I,sun),0))**float(g[80,3])*float(g[80,2]);fog=F(g[0,:3]+tint*(sunC-g[0,:3]));expected=F(fog+trans*(scene[:3]-fog));actual,_=run({1:F([.4,.6,0,0]),2:F([*ray,0])},{1:g,2:view},{32:lambda uv,scene=scene:scene,33:lambda uv,d=d:F([d,0,0,0]),34:lambda uv:F([0,0,0,0])});assert np.all(np.isfinite(actual));maxerr=max(maxerr,float(np.max(np.abs(actual[:3]-expected))))
 report['fog1898']={'cases':200,'max_RGB_error':maxerr};assert maxerr<2e-5
report['gpu_execution']=False;report['snapshot_sha256']='acf3b3db58f10a2ebe95eea9a055f76d7d748c1d3f7c8c265f0e677fc408c55c';(p/'lighting-validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
