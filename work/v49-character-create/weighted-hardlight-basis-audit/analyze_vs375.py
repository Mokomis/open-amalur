"""Execute straight-line captured VS375 SPIR-V against independently written equations.
No GPU, native process, RE database or shared source changes."""
from pathlib import Path
import numpy as np,re,json,hashlib
P=Path(__file__).resolve().parent
lines=(P/'module-375.spvasm').read_text().splitlines()
def F(v):return np.asarray(v,dtype=np.float32)
def Vnorm(v):v=F(v);return F(v/np.sqrt(np.sum(v*v,dtype=np.float32)))
def execute(inp,cb,bones):
 val={};mem={};types={};dep={};md={};pointer={};execing=False
 def ld(q):
  if isinstance(q,tuple):
   block,at=q
   return cb[at] if block=='%24' else bones[at]
  return mem.get(q,F([0,0,0,0]))
 def dd(q):
  if isinstance(q,tuple):return {('world' if q[0]=='%24' else 'bone')+'['+str(q[1])+']'}
  return md.get(q,set())
 for idx,l in enumerate(lines,1):
  x=l.strip()
  if not x:continue
  if x.startswith('OpStore '):
   _,ptr,src=x.split();q=pointer.get(ptr,ptr);mem[q]=val[src];md[q]=set(dep.get(src,set()));continue
  m=re.match(r'(%\w+) = (\w+)(?: (.*))?$',x)
  if not m:continue
  dst,op,a=m.groups();a=(a or '').split();d=set();v=None
  if op=='OpTypeInt':types[dst]=np.int32 if a[1]=='1' else np.uint32;continue
  if op=='OpTypeFloat':types[dst]=np.float32;continue
  if op=='OpTypeBool':types[dst]=np.bool_;continue
  if op=='OpTypeVector':types[dst]=types[a[0]];continue
  if op=='OpConstant':v=types[a[0]](a[1])
  elif op=='OpConstantComposite':v=np.array([val[q] for q in a[1:]],dtype=types[a[0]])
  elif op=='OpVariable':
   if a[1]=='Input':mem[dst]=inp[dst];md[dst]={'input'+dst}
   continue
  elif op=='OpFunction':execing=True;continue
  elif not execing:continue
  elif op in ['OpLabel','OpFunctionEnd']:continue
  elif op=='OpAccessChain':
   at=int(val[a[-1]]);pointer[dst]=(a[1],at);dep[dst]=set(dep.get(a[-1],set()));continue
  elif op=='OpLoad':
   q=pointer.get(a[1],a[1]);v=ld(q);d=dd(q)|dep.get(a[1],set())
  elif op=='OpVectorShuffle':
   aa=np.asarray(val[a[1]]).reshape(-1);bb=np.asarray(val[a[2]]).reshape(-1)
   v=np.concatenate([aa,bb])[[int(i) for i in a[3:]]]
   d=dep.get(a[1],set())|dep.get(a[2],set())
  elif op=='OpCompositeConstruct':
   v=np.array([val[q] for q in a[1:]],dtype=types[a[0]])
   d=set().union(*(dep.get(q,set()) for q in a[1:]))
  elif op=='OpCompositeExtract':v=val[a[1]][int(a[2])];d=dep.get(a[1],set())
  elif op=='OpBitcast':
   v=np.asarray(val[a[1]]).view(types[a[0]]);d=dep.get(a[1],set())
  elif op in ['OpIMul','OpIAdd','OpFMul','OpFAdd']:
   av,bv=val[a[1]],val[a[2]]
   v=av*bv if op.endswith('Mul') else av+bv
   v=np.asarray(v,dtype=types[a[0]]);d=dep.get(a[1],set())|dep.get(a[2],set())
  elif op=='OpDot':
   v=np.sum(val[a[1]]*val[a[2]],dtype=np.float32);d=dep.get(a[1],set())|dep.get(a[2],set())
  elif op=='OpExtInst' and a[2]=='InverseSqrt':
   v=F(1)/np.sqrt(val[a[3]]);d=dep.get(a[3],set())
  else:raise RuntimeError((idx,op,a))
  if v is not None:val[dst]=v;dep[dst]=set(d)
 return {n:np.array(mem[n]).copy() for n in ['%gl_Position','%43','%44','%45','%47','%48','%49']},{n:sorted(md[n]) for n in ['%43','%47','%48','%49']}
def equations(inp,cb,bones):
 idx=inp['%33'];w0,w1,w2=inp['%35'][:3]
 wr=np.sum(F([-1,-1,-1,1])*F([w0,w1,w2,1]),dtype=np.float32)
 weights=F([w0,w1,w2,wr])
 def skin(v,point):
  arg=F([*v,1]) if point else F(v)
  terms=[]
  for j in idx:
   mat=bones[3*int(j):3*int(j)+3]
   terms.append(F([np.sum((row if point else row[:3])*arg,dtype=np.float32) for row in mat]))
  z=terms[1]*weights[1]
  for k in [0,2,3]:z=terms[k]*weights[k]+z
  return F(z)
 def affine(v,at,width,translation):
  z=v[1]*cb[at+1,:width];z=v[0]*cb[at,:width]+z;z=v[2]*cb[at+2,:width]+z
  return F(z+cb[at+3,:width]) if translation else F(z)
 ps=skin(inp['%31'][:3],True);ns=skin(inp['%37'][:3],False);ts=skin(inp['%38'][:3],False)
 return {'P_skin':ps,'N_skin':ns,'T_skin':ts,'B_source':inp['%39'][:3],'%gl_Position':affine(ps,8,4,True),'%45':affine(ps,0,3,True),'%47':Vnorm(affine(ns,4,3,False)),'%48':Vnorm(affine(ts,4,3,False)),'%49':Vnorm(affine(inp['%39'][:3],4,3,False))}
rng=np.random.default_rng(375);results=[];largest=0.
for k in range(12):
 cb=F(rng.normal(size=(12,4)));bones=F(rng.normal(size=(234,4)))
 idx=np.array([2,7,1,3],dtype=np.int32)
 w=F([.2,.3,.1,0] if k!=11 else [.50001526,.50001526,0,0])
 inp={'%31':F([.8,-1.2,2.5,1]),'%33':idx,'%35':w,'%36':F([.25,.75,0,1]),'%37':F([.1,.3,.9,0]),'%38':F([.8,.2,.1,0]),'%39':F([-.2,.9,.3,0]),'%40':F([1,.6,.8,.6])}
 got,deps=execute(inp,cb,bones);eq=equations(inp,cb,bones);errors={}
 for name in ['%gl_Position','%45','%47','%48','%49']:
  a=got[name] if name=='%gl_Position' else got[name][:3]
  e=float(np.max(np.abs(a-eq[name])));largest=max(largest,e);errors[name]=e;assert e<5e-5,(name,e)
 # Mutate bones/weights while preserving source B and world rows: outputB stays EXACT.
 bones2=F(rng.normal(size=(234,4)));inp2=dict(inp);inp2['%35']=F([.1,.2,.4,0])
 other,_=execute(inp2,cb,bones2);assert np.array_equal(got['%49'],other['%49'])
 assert not np.allclose(got['%47'],other['%47']) and not np.allclose(got['%48'],other['%48'])
 assert got['%43'].tolist()==inp['%40'].tolist()
 results.append({'case':k,'weight3':float(np.sum(F([-1,-1,-1,1])*F([*w[:3],1]),dtype=np.float32)),'max_abs_error_by_output':errors,'B_unchanged_after_bones_weights_mutation':True,'N_and_T_changed_after_bones_weights_mutation':True,'color_direct_pass':True})
# Dependencies intentionally coarse per vector register: values/equation tests above are exact lane math.
# The B block is also checked textually for absence of all bone69 loads and sourceweights/indices.
bblock='\n'.join(lines[974:1032])
assert '%29 ' not in bblock and '%35' not in bblock and '%33' not in bblock
summary={'shader':'module-375.spvasm','shader_sha256':hashlib.sha256((P/'module-375.spvasm').read_bytes()).hexdigest(),'cases':results,'max_abs_error':largest,'case11_negative_residual_preserved':results[11]['weight3']<0,'Bblock_lines':[975,1032],'Bblock_contains_bone_or_weight_reads':False,'method':'Independent straight-line SPIRV interpreter vs separately written vector equations,12deterministicinputs; noGPU/sourceactorcaptureclaim.'}
(P/'equation-validation.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k!='cases'}))
