"""Compare generated Lua with original x86 VM code in a separate Windows process.

The native process maps original game sections but never calls game entry/TLS.
These are isolated synthetic VM primitive cases, not in-game equivalence tests.
"""
from pathlib import Path
import argparse, hashlib, json, platform, random, struct, subprocess, sys
assert platform.system()=='Windows','run fresh artifact/runtime work on Windows'
ROOT=Path.home()/'Documents'/'Opem Amalur'
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools/python-libs')]
from amalur_script import decode_instruction
from amalur_reconstruct import reconstruct
from lupa.lua51 import LuaRuntime, LUA_VERSION, LuaError
assert tuple(LUA_VERSION)==(5,1)
HERE=Path(__file__).resolve().parent
TARGET=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning\koa.exe')
EXPECTED='16a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314'

def word(op,a=0,b=0,c=0,bx=None):return (op<<25)|a|((((b<<9)|c) if bx is None else bx)<<8)
def jump(pc,target,op=28,a=0):return word(op,a,bx=65535+target-pc-1)
def value(v):
 if v is None:return struct.pack('<II',0,0)
 if isinstance(v,bool):return struct.pack('<II',1,int(v))
 if isinstance(v,int) and -2**31<=v<2**31:return struct.pack('<II',3,v&0xffffffff)
 raise ValueError('primitive fixture value outside admitted domain')
def constant(v):
 if v is None:return {'type':'nil','value':None}
 if isinstance(v,bool):return {'type':'boolean','value':v}
 return {'type':'number','raw_hex':struct.pack('>i',v).hex()}
def body(code,params,stack,constants):
 return {'instructions':[dict(decode_instruction(w,0x100+i*4,i),pc=i,file_offset=0x100+i*4) for i,w in enumerate(code)],
 'constants':[constant(v) for v in constants],'children':[],'parameter_count':params,'maximum_stack_size':stack,'upvalue_count':0,'vararg_flags':0}
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def cases(smoke):
 result=[]
 def add(name,code,args,stack=None,constants=()):
  result.append({'id':len(result),'name':name,'code':code,'arguments':list(args),'stack':stack or max(1,len(args)),'constants':list(constants)})
 add('identity-int',[word(7,a=1,b=0),word(9,a=1,b=2)],[17],2)
 add('add-wrap',[word(34,a=2,b=0,c=1),word(9,a=2,b=2)],[2147483647,1],3)
 if smoke:return result
 rng=random.Random(20261030)
 pairs=[(-2147483648,-1),(-2147483648,1),(-2147483648,-2147483648),(2147483647,2147483647),
        (65537,65537),(-65537,65537),(0,0),(-7,3),(7,-3),(-7,-3),(7,3)]
 pairs += [(rng.randrange(-2**31,2**31),rng.randrange(-2**31,2**31)) for _ in range(48)]
 for op,name in [(34,'add'),(36,'sub'),(38,'mul'),(40,'div'),(42,'mod')]:
  for a,b in pairs:
   if op in (40,42) and (b==0 or (a==-2147483648 and b==-1)):continue
   add(f'{name}:{a}:{b}',[word(op,a=2,b=0,c=1),word(9,a=2,b=2)],[a,b],3)
  add(name+'-constant-B',[word(op+1,a=1,b=0,c=0),word(9,a=1,b=2)],[3],2,[7])
  add(name+'-constant-C',[word(op,a=1,b=0,c=256),word(9,a=1,b=2)],[7],2,[3])
 for a,b in [(0,-1),(2,-1),(-2,-3),(0,0),(123,0),(-2,3),(-2,4),(65537,2),(2147483647,2),(3,31),(2,32),(7,2147483647)]:
  add(f'pow:{a}:{b}',[word(44,a=2,b=0,c=1),word(9,a=2,b=2)],[a,b],3)
 for a in [-2147483648,-2147483647,-1,0,1,2147483647]:
  add(f'unm:{a}',[word(47,a=1,b=0),word(9,a=1,b=2)],[a],2)
 for a in [None,False,True,0,7,-1]:
  add(f'not:{a}',[word(48,a=1,b=0),word(9,a=1,b=2)],[a],2)
  add(f'not-cached:{a}',[word(7,a=1,b=0),word(66,a=2,b=1),word(9,a=2,b=2)],[a],3)
 for op,name in [(4,'eq'),(50,'lt'),(52,'le')]:
  for a,b in [(-2,3),(3,-2),(0,0),(-2147483648,2147483647)]:
   add(f'{name}:{a}:{b}',[word(op,a=1,b=0,c=1),jump(1,3),word(13,a=2,b=0,c=1),word(13,a=2,b=1),word(9,a=2,b=2)],[a,b],3)
 for a in [None,False,True,0,-1]:
  add(f'test:{a}',[word(1,a=0,c=1),jump(1,3),word(13,a=1,b=0,c=1),word(13,a=1,b=1),word(9,a=1,b=2)],[a],2)
  add(f'test-cached:{a}',[word(7,a=1,b=0),word(65,a=1,c=1),jump(2,4),word(13,a=2,b=0,c=1),word(13,a=2,b=1),word(9,a=2,b=2)],[a],3)
 for start,limit,step in [(1,5,1),(5,1,-1),(1,0,1),(0,1,-1),(1,2,3),(2,1,-3),(-5,5,2),(-2147483648,-2147483645,1),(2147483647,2147483645,-1)]:
  add(f'for-sum:{start}:{limit}:{step}',[word(25,a=4,bx=0),jump(1,3,op=56),word(34,a=4,b=4,c=3),jump(3,2,op=57),word(9,a=4,b=2)],[start,limit,step],5,[0])
 return result

def decode_result(v):
 tag=v['tag'];hi=int(v['raw_hi'],16)
 if tag==0:return {'type':'nil','value':None}
 if tag==1:return {'type':'boolean','value':bool(hi)}
 if tag==3:return {'type':'number','value':hi if hi<2**31 else hi-2**32}
 return {'type':'unadmitted-native-tag','tag':tag,'raw_lo':v['raw_lo'],'raw_hi':v['raw_hi']}
def lua_value(v):
 if v is None:return {'type':'nil','value':None}
 if isinstance(v,bool):return {'type':'boolean','value':v}
 if isinstance(v,(int,float)) and -2**31<=v<2**31 and int(v)==v:return {'type':'number','value':int(v)}
 raise ValueError('unexpected generated Lua result '+repr(v))

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--smoke',action='store_true');ap.add_argument('--prepare-only',action='store_true');ap.add_argument('--output',type=Path);ap.add_argument('--real-fixtures',type=Path)
 args=ap.parse_args();out=args.output or ROOT/'outputs/engine-bindings-v06'/('native-vm-smoke' if args.smoke else 'native-vm-primitives')
 out.mkdir(parents=True,exist_ok=False)
 assert digest(TARGET)==EXPECTED
 profile=json.loads((ROOT/'outputs/native-script-profile.json').read_text());data=cases(args.smoke)
 if args.real_fixtures:
  real=json.loads(args.real_fixtures.read_text());data=[]
  for record in real['records']:
   n=record['parameter_count']
   inputs=[[]] if not n else [[1]*n,[-1]*n,[7,3,2][:n],[0]*n,[-2147483648,2147483647,1][:n]]
   for values in inputs:
    data.append({'id':len(data),'name':record['file']+':'+record['function_path']+':'+str(values),'code':record['code'],'arguments':values,'stack':record['stack'],'constants':record['constants'],
                 'real_source':{k:record[k] for k in ('file','input_sha256','function_path','function_signature','instruction_offsets')}})
 payload=bytearray(b'OMVM06\0\0'+struct.pack('<I',0));admitted=[];excluded=[]
 runtime=LuaRuntime(unpack_returned_tuples=True,register_eval=False,register_builtins=False)
 runtime.execute("debug.sethook(function() error('generated fixture instruction limit') end,'',1000000); io=nil;os=nil;python=nil;dofile=nil;loadfile=nil;require=nil;debug=nil")
 pack=runtime.eval("function(f,...) local function p(...) return {n=select('#',...),...} end return p(f(...)) end")
 for item in data:
  fn=body(item['code'],len(item['arguments']),item['stack'],item['constants']);ir,source=reconstruct({'input_sha256':'0'*64,'chunk':{'root_function':fn}},profile)
  assert ir['root_function']['body_emittable'],ir['root_function']['unknowns']
  path=out/f"case-{item['id']:04d}.lua";path.write_text(source,encoding='utf-8');item['generated_source_sha256']=digest(path)
  run=runtime.eval('function(...)\n'+source+'\nend')
  try:r=pack(run,*item['arguments'])
  except LuaError as exc:
   if not args.real_fixtures:raise
   excluded.append({'id':item['id'],'name':item['name'],'real_source':item.get('real_source'),'reason':str(exc),'scope':'generated runtime domain rejected; native case not run'});continue
  admitted.append(item)
  item['generated_results']=[lua_value(r[i]) for i in range(1,r.n+1)]
  payload+=struct.pack('<IIIII',item['id'],len(item['code']),item['stack'],len(item['constants']),len(item['arguments']))
  payload+=struct.pack('<'+'I'*len(item['code']),*item['code'])
  payload+=b''.join(value(v) for v in item['arguments'])+b''.join(value(v) for v in item['constants'])
 data=admitted;struct.pack_into('<I',payload,8,len(data));(out/'excluded-inputs.json').write_text(json.dumps(excluded,indent=2),encoding='utf-8')
 fixture=out/'fixtures.bin';fixture.write_bytes(payload);(out/'cases.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
 if args.prepare_only:print(json.dumps({'prepared':len(data),'directory':str(out)}));return
 harness=HERE/'native_vm_harness.exe';assert harness.exists()
 command=[str(harness),str(TARGET),str(fixture)]
 try:run=subprocess.run(command,capture_output=True,text=True,timeout=45)
 except subprocess.TimeoutExpired as exc:
  (out/'native-process.json').write_text(json.dumps({'command':command,'timeout_seconds':45,'timed_out':True,'target_unchanged':digest(TARGET)==EXPECTED},indent=2),encoding='utf-8')
  (out/'native-stdout.partial').write_bytes(exc.stdout or b'');(out/'native-stderr.partial').write_bytes(exc.stderr or b'')
  raise
 (out/'native-stdout.json').write_text(run.stdout,encoding='utf-8');(out/'native-stderr.txt').write_text(run.stderr,encoding='utf-8')
 (out/'native-process.json').write_text(json.dumps({'command':command,'exit_code':run.returncode,'timed_out':False,'target_unchanged':digest(TARGET)==EXPECTED},indent=2),encoding='utf-8')
 if not run.stdout.strip():
  print(json.dumps({'native_exit_code':run.returncode,'error':run.stderr,'output_directory':str(out)},indent=2));raise SystemExit(1)
 native=json.loads(run.stdout);assert native['target_sha256']==EXPECTED
 by_id={r['id']:r for r in native['cases']};assert len(by_id)==len(data)
 records=[]
 for item in data:
  observed=by_id[item['id']];results=[decode_result(v) for v in observed['results']]
  records.append({'id':item['id'],'name':item['name'],'match':observed['ok'] and results==item['generated_results'],
                  'real_source':item.get('real_source'),'native':results,'generated':item['generated_results'],'native_ok':observed['ok'],'native_exception_code':observed['exception_code'],'native_exception_ip':observed['exception_ip']})
 report={'scope':'Original x86 VM code with standard PE HIGHLOW base relocations executes on Windows CPU with synthetic primitive frames in a separate process. No game entry, TLS callbacks, import resolution, saves, or engine services. This is isolated native-VM parity, not in-game or whole-engine equivalence.',
  'target_sha256':EXPECTED,'target_unchanged':digest(TARGET)==EXPECTED,'harness_sha256':digest(harness),'fixture_sha256':digest(fixture),
  'generated_source_sha256':digest(ROOT/'src/amalur_reconstruct.py'),'profile_sha256':digest(ROOT/'outputs/native-script-profile.json'),
  'mapped_image_base':native['mapped_image_base'],'relocation_delta':native['relocation_delta'],'highlow_relocations':native['highlow_relocations'],
  'excluded_generated_domain_inputs':len(excluded),'cases':len(records),'matched':sum(r['match'] for r in records),'native_exit_code':run.returncode,'records':records}
 (out/'comparison.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 print(json.dumps({k:v for k,v in report.items() if k!='records'},indent=2))
 if run.returncode or report['matched']!=report['cases']:
  print(json.dumps([r for r in records if not r['match']],indent=2));raise SystemExit(1)
if __name__=='__main__':main()
