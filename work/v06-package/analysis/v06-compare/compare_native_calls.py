"""Original VM call-frame/open-list movement with controlled native C callees."""
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
 if isinstance(v,dict):return struct.pack('<II',10,v['callback'])
 if v is None:return struct.pack('<II',0,0)
 if isinstance(v,bool):return struct.pack('<II',1,int(v))
 return struct.pack('<II',3,v&0xffffffff)
def cases():
 data=[]
 def cb(i):return {'callback':i}
 def add(name,code,args,stack):data.append({'id':len(data),'name':name,'code':code,'arguments':args,'stack':stack})
 for op in (2,3):
  for callback in (1,2,3):
   add(f'call{op}-open-cb{callback}',[word(op,b=1,c=0),word(9,b=0)],[cb(callback)],1)
   for results in (0,1,2,4,6):
    add(f'call{op}-fixed{results}-cb{callback}',[word(op,b=1,c=results+1),word(9,b=results+1)],[cb(callback)],max(1,results))
 add('fixed-call-clears-entire-tail',[word(3,b=1,c=2),word(9,b=5)],[cb(2),77,88,99],4)
 for callback in (4,5):
  add(f'fixed-args-retain-nils-cb{callback}',[word(3,b=5,c=0),word(9,b=0)],[cb(callback),None,7,False,None],5)
 for producer in (1,2,3):
  for consumer in (4,5):
   add(f'open-args-cb{producer}-to{consumer}',[word(3,a=1,b=1,c=0),word(3,a=0,b=0,c=0),word(9,b=0)],[cb(consumer),cb(producer)],2)
 for callback in (1,2,3):
  add(f'cached-call-cb{callback}',[word(7,a=1,b=0),word(63,a=1,b=1,c=0),word(9,a=1,b=0)],[cb(callback)],2)
  for op in (22,23):add(f'tail{op}-cb{callback}',[word(op,b=1,c=0),word(9,b=0)],[cb(callback)],1)
  add(f'cached-tail-cb{callback}',[word(7,a=1,b=0),word(62,a=1,b=1,c=0),word(9,a=1,b=0)],[cb(callback)],2)
 add('open-args-into-tail',[word(3,a=1,b=1,c=0),word(22,b=0,c=0),word(9,b=0)],[cb(5),cb(3)],2)
 for address,values in [(0xaa1fa0,[-2147483648]),(0xaa1fd0,[2147395600]),(0xaa20b0,[65537,2]),(0xaa2100,[7,-3,0]),(0xaa2160,[7,-3,0])]:
  add('math-call-'+MATH[address],[word(3,b=1+len(values),c=0),word(9,b=0)],[cb(address)]+values,1+len(values))
 return data

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=ROOT/'outputs/engine-bindings-v06/native-vm-calls');ap.add_argument('--smoke',action='store_true');ap.add_argument('--lua-module',type=Path,default=ROOT/'work/v06-runtime/amalur_native_math.lua');args=ap.parse_args();out=args.output;out.mkdir(parents=True,exist_ok=False)
 assert digest(TARGET)==EXPECTED;profile=json.loads((ROOT/'outputs/native-script-profile.json').read_text());data=cases();data=data[:1] if args.smoke else data
 runtime=LuaRuntime(unpack_returned_tuples=True,register_eval=False,register_builtins=False);runtime.execute("debug.sethook(function() error('call fixture instruction limit') end,'',1000000)")
 math=runtime.execute(args.lua_module.read_text());pack=runtime.eval('function(f,...) local function p(...) return {n=select("#",...),...} end return p(f(...)) end')
 lua_callbacks={k:runtime.eval(v) for k,v in CALLBACKS.items()};lua_callbacks.update({k:math[v] for k,v in MATH.items()})
 payload=bytearray(b'OMCL06\0\0'+struct.pack('<I',len(data)))
 for item in data:
  fn=body(item['code'],len(item['arguments']),item['stack'],[]);ir,source=reconstruct({'input_sha256':'0'*64,'chunk':{'root_function':fn}},profile);assert ir['root_function']['body_emittable'],ir['root_function']['unknowns']
  (out/f"case-{item['id']:04d}.lua").write_text(source,encoding='utf-8')
  run=runtime.eval('function(...)\n'+source+'\nend');values=[lua_callbacks[v['callback']] if isinstance(v,dict) else v for v in item['arguments']];r=pack(run,*values);item['generated_results']=[lua_value(r[i]) for i in range(1,r.n+1)]
  payload+=struct.pack('<IIIII',item['id'],len(item['code']),item['stack'],0,len(item['arguments']))+struct.pack('<'+'I'*len(item['code']),*item['code'])+b''.join(native_value(v) for v in item['arguments'])
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
 report={'scope':'Original VM CALL/TAILCALL opcode dispatch, C-frame setup and result mover execute against controlled authored native callees and five original math callbacks. Synthetic Lua state; no engine globals/allocator/yields/closures. Authored boundary callees are inputs, not native engine implementation claims.',
 'target_sha256':EXPECTED,'target_unchanged':digest(TARGET)==EXPECTED,'harness_sha256':digest(harness),'fixture_sha256':digest(fixture),'generated_source_sha256':digest(ROOT/'src/amalur_reconstruct.py'),'profile_sha256':digest(ROOT/'outputs/native-script-profile.json'),
 'mapped_image_base':native['mapped_image_base'],'relocation_delta':native['relocation_delta'],'highlow_relocations':native['highlow_relocations'],'cases':len(records),'matched':sum(r['match'] for r in records),'native_exit_code':run.returncode,'records':records}
 (out/'comparison.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k!='records'},indent=2))
 if run.returncode or report['matched']!=report['cases']:print(json.dumps([r for r in records if not r['match']],indent=2));raise SystemExit(1)
if __name__=='__main__':main()
