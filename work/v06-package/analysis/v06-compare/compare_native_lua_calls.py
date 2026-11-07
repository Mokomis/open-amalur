"""Original VM seeded nonvararg Lua callee frames and nested RETURN movement."""
from pathlib import Path
import argparse,json,platform,struct,subprocess,sys
assert platform.system()=='Windows'
from compare_native_vm import ROOT,HERE,TARGET,EXPECTED,digest,word,body,decode_result,lua_value
sys.path.insert(0,str(ROOT/'tools/python-libs'))
from amalur_reconstruct import reconstruct
from lupa.lua51 import LuaRuntime
CALLBACKS={1:'function() end',2:'function() return nil end',3:'function() return nil,7,false,nil end',4:'function(...) return ... end',5:'function(...) return select("#",...),... end'}
MATH={0xaa1fa0:'abs',0xaa1fd0:'sqrt',0xaa20b0:'pow',0xaa2100:'min',0xaa2160:'max'}
def native_value(v):
 if isinstance(v,dict):return struct.pack('<II',9 if 'prototype' in v else 10,v.get('prototype',v.get('callback')))
 if v is None:return struct.pack('<II',0,0)
 if isinstance(v,bool):return struct.pack('<II',1,int(v))
 return struct.pack('<II',3,v&0xffffffff)
def cases():
 data=[]
 prototypes={
  'identity':{'code':[word(7,a=1,b=0),word(9,a=1,b=2)],'params':1,'stack':2,'constants':[]},
  'empty':{'code':[word(9,b=1)],'params':0,'stack':1,'constants':[]},
  'nil':{'code':[word(26,a=0,b=0),word(9,b=2)],'params':0,'stack':1,'constants':[]},
  'multi':{'code':[word(26,a=0,b=3),word(25,a=1,bx=0),word(13,a=2,b=0),word(9,b=5)],'params':0,'stack':4,'constants':[7]},
  'four':{'code':[word(9,b=5)],'params':4,'stack':4,'constants':[]},
  'c-call':{'code':[word(3,b=1,c=0),word(9,b=0)],'params':1,'stack':1,'constants':[]},
  'c-echo':{'code':[word(3,b=5,c=0),word(9,b=0)],'params':5,'stack':5,'constants':[]},
 }
 def add(name,kind,values,results=None,op=2,rootcode=None,rootstack=None):
  args=[{'prototype':1}]+values
  code=rootcode or [word(op,b=len(args),c=0 if results is None else results+1),word(9,b=0 if results is None else results+1)]
  data.append({'id':len(data),'name':name,'code':code,'arguments':args,'stack':rootstack or max(len(args),results or 1),'prototypes':[prototypes[kind]]})
 add('lua-identity-smoke','identity',[17])
 for kind in ('empty','nil','multi','four'):
  for results in (None,0,1,2,4,6):add(f'lua-{kind}-results{results}',kind,[None,7,False,None] if kind=='four' else [],results)
 for values in ([],[None],[False],[0],[-2147483648],[2147483647],[17,99,False]):add('lua-identity-args'+repr(values),'identity',values)
 for values in ([],[7],[None,False],[7,None,False,None],[1,2,3,4,5,6]):add('lua-missing-extra'+repr(values),'four',values)
 add('lua-cached-call','identity',[17],rootcode=[word(7,a=2,b=0),word(7,a=3,b=1),word(7,a=2,b=0),word(63,a=2,b=2,c=0),word(9,a=2,b=0)],rootstack=4)
 for cb in (1,2,3):
  for results in (None,0,1,4,6):add(f'lua-to-C{cb}-results{results}','c-call',[{'callback':cb}],results)
 for cb in (4,5):add(f'lua-to-C-echo{cb}','c-echo',[{'callback':cb},None,7,False,None])
 return data

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=ROOT/'outputs/engine-bindings-v06/native-vm-lua-calls');ap.add_argument('--smoke',action='store_true');ap.add_argument('--lua-module',type=Path,default=ROOT/'work/v06-runtime/amalur_native_math.lua');args=ap.parse_args();out=args.output;out.mkdir(parents=True,exist_ok=False)
 assert digest(TARGET)==EXPECTED;profile=json.loads((ROOT/'outputs/native-script-profile.json').read_text());data=cases();data=data[:1] if args.smoke else data
 runtime=LuaRuntime(unpack_returned_tuples=True,register_eval=False,register_builtins=False);runtime.execute("debug.sethook(function() error('call fixture instruction limit') end,'',1000000)")
 math=runtime.execute(args.lua_module.read_text());pack=runtime.eval('function(f,...) local function p(...) return {n=select("#",...),...} end return p(f(...)) end')
 lua_callbacks={k:runtime.eval(v) for k,v in CALLBACKS.items()};lua_callbacks.update({k:math[v] for k,v in MATH.items()})
 payload=bytearray(b'OMLU06\0\0'+struct.pack('<I',len(data)))
 for item in data:
  fn=body(item['code'],len(item['arguments']),item['stack'],[]);ir,source=reconstruct({'input_sha256':'0'*64,'chunk':{'root_function':fn}},profile);assert ir['root_function']['body_emittable'],ir['root_function']['unknowns']
  (out/f"case-{item['id']:04d}.lua").write_text(source,encoding='utf-8')
  lua_prototypes=[]
  for index,proto in enumerate(item['prototypes']):
   proto_ir,proto_source=reconstruct({'input_sha256':'0'*64,'chunk':{'root_function':body(proto['code'],proto['params'],proto['stack'],proto['constants'])}},profile);assert proto_ir['root_function']['body_emittable']
   (out/f"case-{item['id']:04d}-prototype-{index+1}.lua").write_text(proto_source,encoding='utf-8');lua_prototypes.append(runtime.eval('function(...)\n'+proto_source+'\nend'))
  run=runtime.eval('function(...)\n'+source+'\nend');values=[(lua_prototypes[v['prototype']-1] if 'prototype' in v else lua_callbacks[v['callback']]) if isinstance(v,dict) else v for v in item['arguments']];r=pack(run,*values);item['generated_results']=[lua_value(r[i]) for i in range(1,r.n+1)]
  payload+=struct.pack('<IIIII',item['id'],len(item['code']),item['stack'],0,len(item['arguments']))+struct.pack('<'+'I'*len(item['code']),*item['code'])+b''.join(native_value(v) for v in item['arguments'])
  payload+=struct.pack('<I',len(item['prototypes']))
  for proto in item['prototypes']:
   payload+=struct.pack('<IIII',len(proto['code']),proto['stack'],proto['params'],len(proto['constants']))+struct.pack('<'+'I'*len(proto['code']),*proto['code'])+b''.join(native_value(v) for v in proto['constants'])
 fixture=out/'fixtures.bin';fixture.write_bytes(payload);(out/'cases.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
 harness=HERE/'native_vm_harness.exe';command=[str(harness),str(TARGET),str(fixture)]
 try:run=subprocess.run(command,capture_output=True,text=True,timeout=45)
 except subprocess.TimeoutExpired as e:
  (out/'native-process.json').write_text(json.dumps({'command':command,'timed_out':True,'timeout_seconds':45,'target_unchanged':digest(TARGET)==EXPECTED},indent=2),encoding='utf-8');(out/'native-stdout.partial').write_bytes(e.stdout or b'');(out/'native-stderr.partial').write_bytes(e.stderr or b'');raise
 (out/'native-stdout.json').write_text(run.stdout,encoding='utf-8');(out/'native-stderr.txt').write_text(run.stderr,encoding='utf-8');(out/'native-process.json').write_text(json.dumps({'command':command,'exit_code':run.returncode,'timed_out':False,'target_unchanged':digest(TARGET)==EXPECTED},indent=2),encoding='utf-8')
 if not run.stdout.strip():print(run.stderr);raise SystemExit(1)
 native=json.loads(run.stdout);by_id={r['id']:r for r in native['cases']};assert len(by_id)==len(data);records=[]
 for item in data:
  r=by_id[item['id']];observed=[decode_result(v) for v in r['results']];records.append({'id':item['id'],'name':item['name'],'native_ok':r['ok'],'native_exception_code':r['exception_code'],'native_exception_ip':r['exception_ip'],'native':observed,'generated':item['generated_results'],'match':r['ok'] and observed==item['generated_results']})
 report={'scope':'Original VM CALL/cachedCALL, Lua frame setup, nested RETURN and mixed Lua/C result movement execute with explicitly seeded nonvararg Lua prototypes and controlled authored C callees. Synthetic Lua state; no engine globals/allocator/yields/capture creation. Seeded callee code is controlled input, not proof of whole-engine equivalence.',
 'target_sha256':EXPECTED,'target_unchanged':digest(TARGET)==EXPECTED,'harness_sha256':digest(harness),'fixture_sha256':digest(fixture),'generated_source_sha256':digest(ROOT/'src/amalur_reconstruct.py'),'profile_sha256':digest(ROOT/'outputs/native-script-profile.json'),
 'mapped_image_base':native['mapped_image_base'],'relocation_delta':native['relocation_delta'],'highlow_relocations':native['highlow_relocations'],'cases':len(records),'matched':sum(r['match'] for r in records),'native_exit_code':run.returncode,'records':records}
 (out/'comparison.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k!='records'},indent=2))
 if run.returncode or report['matched']!=report['cases']:print(json.dumps([r for r in records if not r['match']],indent=2));raise SystemExit(1)
if __name__=='__main__':main()
