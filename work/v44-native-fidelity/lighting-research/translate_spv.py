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
  elif storage=='Uniform':val[k]='c';vtyp[k]='buffer'
  elif storage=='UniformConstant':
   # Samplers and images remain aliases until sample/fetch.
   val[k]='src';vtyp[k]='resource'
  elif storage=='Input':
   vtyp[k]=T(base)
   if k=='%gl_FragCoord':val[k]='nativeFragCoord'
   elif decor.get(k,{}).get('Location')==['1']:val[k]='vec4(0.,0.,nativeUV)'
   elif decor.get(k,{}).get('Location')==['2']:val[k]='passthrough'
   else:raise Exception(('input',k))
  elif storage=='Output':val[k]='o';vtyp[k]=T(base)
 elif inside:
  if op in ['OpLabel','OpReturn']:continue
  if op=='OpAccessChain':
   val[k]=f'c[{V(a[-1])}]';vtyp[k]='vec4';continue
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
   f=args[1];xs=args[2:];f={'FMax':'max','FMin':'min','FClamp':'clamp','InverseSqrt':'inversesqrt','Trunc':'trunc','Log2':'log2','Exp2':'exp2','Floor':'floor','Sin':'sin','Cos':'cos','FAbs':'abs'}.get(f,f);e=f+'('+','.join(V(x) for x in xs)+')'
  elif op=='OpImageFetch':e=f'nativeFetch({V(args[1])},int({V(args[3])}))'
  elif op=='OpImageSampleImplicitLod':e=f'nativeSample({V(args[1])})'
  else:raise Exception((op,l))
  emit(k,t,e)
header='''#version 300 es
// Mechanical translation of the captured active SPIR-V. IDs retained per line.
// Source texture and output FBO use ordinary GL bottom-left storage. Adapters
// restore native top-left pixel coordinates/derivatives. Full-size targets only.
precision highp float;precision highp int;
uniform highp sampler2D src;
uniform vec4 c[8];
uniform vec2 nativeExtent;
uniform vec4 passthrough;
out vec4 o;
vec4 nativeFetch(ivec2 q,int level){ivec2 n=textureSize(src,level);if(any(lessThan(q,ivec2(0)))||any(greaterThanEqual(q,n)))return vec4(0.);q.y=n.y-1-q.y;return texelFetch(src,q,level);}
vec4 nativeSample(vec2 q){return texture(src,vec2(q.x,1.-q.y));}
vec4 nativeDy(vec4 x){return -dFdy(x);}
'''
text=header+'\n'.join(const)+'\nvoid main(){\n vec4 nativeFragCoord=vec4(gl_FragCoord.x,nativeExtent.y-gl_FragCoord.y,gl_FragCoord.z,gl_FragCoord.w);\n vec2 nativeUV=vec2(gl_FragCoord.x/nativeExtent.x,1.-gl_FragCoord.y/nativeExtent.y);\n'+'\n'.join(body)+'\n}\n'
(root/f'native-{m}.frag').write_text(text)
print(m,'lines',len(text.splitlines()))
