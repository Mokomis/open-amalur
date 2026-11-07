# Straight-line SPIR-V translator for captured AO1910 and bilateral1926 only.
# Preserves instruction/ID provenance. Not a general SPIR-V implementation.
from pathlib import Path
import re,sys
root=Path(__file__).parent
m=int(sys.argv[1]);lines=(root/f'module-{m}.spvasm').read_text().splitlines();typ={};val={};vtyp={};ptr={};decor={};body=[];const=[];inside=False
name=lambda x:'id'+x.removeprefix('%')
T=lambda x:typ[x]
V=lambda x:val.get(x,name(x))
def emit(k,t,e):
 vtyp[k]=t;val[k]=name(k);body.append(f'  {t} {name(k)} = {e}; // {k}')
def dims(t):return int(t[-1]) if t[-1].isdigit() else 1
def comp(x,i):return V(x) if dims(vtyp[x])==1 else f'{V(x)}[{i}]'
for l in lines:
 s=l.split()
 if not s or s[0]==';':continue
 k=s[0] if len(s)>1 and s[1]=='=' else None;op=s[2] if k else s[0];a=s[3:] if k else s[1:]
 if op=='OpDecorate':decor.setdefault(a[0],{})[a[1]]=a[2:];continue
 if op=='OpTypeFloat':typ[k]='float'
 elif op=='OpTypeInt':typ[k]='int' if a[1]=='1' else 'uint'
 elif op=='OpTypeBool':typ[k]='bool'
 elif op=='OpTypeVector':typ[k]={'float':'vec','int':'ivec','uint':'uvec','bool':'bvec'}[T(a[0])]+a[1]
 elif op=='OpTypePointer':ptr[k]=(a[0],a[1])
 elif op=='OpConstant':
  t=T(a[0]);v=a[1]
  if t=='float' and '.' not in v and 'e' not in v:v+='.'
  if t=='uint':v+='u'
  val[k]=v;vtyp[k]=t
 elif op=='OpConstantComposite':
  t=T(a[0]);val[k]=name(k);vtyp[k]=t;const.append(f'const {t} {name(k)} = {t}('+','.join(V(x) for x in a[1:])+');')
 elif op=='OpFunction':inside=True
 elif op=='OpFunctionEnd':inside=False
 elif op=='OpVariable':
  storage,base=ptr[a[0]]
  if storage=='Function':
   t=T(base);val[k]=name(k);vtyp[k]=t;body.append(f'  {t} {name(k)} = {t}(0); // register {k}')
  elif storage=='Uniform':val[k]={0:'material',1:'g',3:'terrain',4:'dynamic'}[int(decor[k]['Binding'][0])];vtyp[k]='buffer'
  elif storage=='UniformConstant':
   # Samplers and images remain aliases until sample/fetch.
   val[k]=('ambient' if int(decor[k]['Binding'][0])==32 else 'tex'+str(int(decor[k]['Binding'][0])-33)) if int(decor[k]['Binding'][0])>=32 else 'unused_sampler';vtyp[k]='resource'
  elif storage=='Input':
   vtyp[k]=T(base)
   val[k]={1:'uvBlend',3:'cameraRelative',5:'basisN',6:'basisT',7:'basisB'}[int(decor[k]['Location'][0])]
  elif storage=='Output':val[k]={0:'g0',1:'g1',2:'g2'}[int(decor[k]['Location'][0])];vtyp[k]=T(base)
 elif inside:
  if op in ['OpLabel','OpReturn']:continue
  if op=='OpAccessChain':
   val[k]=f'{V(a[1])}[{V(a[-1])}]';vtyp[k]='vec4';continue
  if op=='OpLoad':
   t=a[0]
   if a[1] not in vtyp or vtyp[a[1]]=='resource':val[k]=V(a[1]);vtyp[k]='resource';continue
   emit(k,T(t),V(a[1]));continue
  if op=='OpStore':body.append(f'  {V(a[0])} = {V(a[1])};');continue
  if op=='OpSampledImage':val[k]=V(a[1]);vtyp[k]='resource';continue
  t=T(a[0]);args=a[1:]
  if op=='OpVectorShuffle':
   x,y=args[:2];n=dims(vtyp[x]);e=t+'('+','.join(comp(x,int(i)) if int(i)<n else comp(y,int(i)-n) for i in args[2:])+')'
  elif op=='OpCompositeConstruct':e=t+'('+','.join(V(x) for x in args)+')'
  elif op=='OpCompositeExtract':e=comp(args[0],int(args[1]))
  elif op=='OpCompositeInsert':
   emit(k,t,V(args[1]));body.append(f'  {V(k)}[{args[2]}] = {V(args[0])};');continue
  elif op=='OpBitcast':
   x=args[0];st=vtyp[x]
   if st.startswith(('vec','float')) and t.startswith(('uvec','uint')):e=f'floatBitsToUint({V(x)})'
   elif st.startswith(('vec','float')) and t.startswith(('ivec','int')):e=f'floatBitsToInt({V(x)})'
   elif st.startswith(('uvec','uint')) and t.startswith(('vec','float')):e=f'uintBitsToFloat({V(x)})'
   elif st.startswith(('ivec','int')) and t.startswith(('vec','float')):e=f'intBitsToFloat({V(x)})'
   else:e=t+'('+V(x)+')'
  elif op in ['OpConvertFToS','OpConvertSToF']:e=t+'('+V(args[0])+')'
  elif op in ['OpFAdd','OpFMul','OpFDiv','OpIAdd','OpIMul','OpBitwiseAnd','OpBitwiseXor']:
   o={'OpFAdd':'+','OpFMul':'*','OpFDiv':'/','OpIAdd':'+','OpIMul':'*','OpBitwiseAnd':'&','OpBitwiseXor':'^'}[op];e=f'({V(args[0])} {o} {V(args[1])})'
  elif op=='OpFNegate':e='(-'+V(args[0])+')'
  elif op in ['OpDot','OpDPdx','OpDPdy']:
   f={'OpDot':'dot','OpDPdx':'dFdx','OpDPdy':'nativeDy'}[op];e=f+'('+','.join(V(x) for x in args)+')'
  elif op in ['OpFOrdGreaterThanEqual','OpFOrdLessThan','OpINotEqual']:
   f={'OpFOrdGreaterThanEqual':'greaterThanEqual','OpFOrdLessThan':'lessThan','OpINotEqual':'notEqual'}[op];e=f+'('+','.join(V(x) for x in args)+')'
  elif op=='OpSelect':
   q,x,y=args;e=t+'('+','.join(f'({comp(q,i)} ? {comp(x,i)} : {comp(y,i)})' for i in range(dims(t)))+')'
  elif op=='OpExtInst':
   f=args[1];xs=args[2:];f={'FMax':'max','FMin':'min','FClamp':'clamp','InverseSqrt':'inversesqrt','Trunc':'trunc','Log2':'log2','Exp2':'exp2','Floor':'floor','Sin':'sin','Cos':'cos','FAbs':'abs','Sqrt':'sqrt'}.get(f,f);e=f+'('+','.join(V(x) for x in xs)+')'
  elif op=='OpImageFetch':e=f'nativeFetch({V(args[1])},int({V(args[3])}))'
  elif op=='OpImageSampleImplicitLod':e=f'texture({V(args[0])},{V(args[1])})'
  else:raise Exception((op,l))
  emit(k,t,e)
header="""#version 300 es
// Mechanical translation of ACTIVE PS792. Every SPIR-V ID retained.
precision highp float; precision highp int;
uniform vec4 material[2],g[82],terrain[4],dynamic[16];
uniform highp samplerCube ambient;
"""+''.join('uniform highp sampler2D tex%d;\n'%i for i in range(9))+"""
in vec4 uvBlend,cameraRelative,basisN,basisT,basisB;
layout(location=0)out vec4 g0;
layout(location=1)out vec4 g1;
layout(location=2)out vec4 g2;
"""
text=header+'\n'.join(const)+'\nvoid main(){\n'+'\n'.join(body)+'\n}\n'
(root/f'native-{m}.frag').write_text(text)
print(m,'lines',len(text.splitlines()))
