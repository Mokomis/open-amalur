"""Original native math callbacks versus guarded Lua binding implementations."""
from pathlib import Path
import argparse,hashlib,json,platform,random,struct,subprocess,sys
assert platform.system()=='Windows'
ROOT=Path.home()/'Documents'/'Opem Amalur';HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools/python-libs'))
from lupa.lua51 import LuaRuntime,LUA_VERSION
assert tuple(LUA_VERSION)==(5,1)
TARGET=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning\koa.exe')
EXPECTED='16a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314'
ADDRESSES={'abs':0xaa1fa0,'sqrt':0xaa1fd0,'pow':0xaa20b0,'min':0xaa2100,'max':0xaa2160}
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--lua-module',type=Path,default=ROOT/'work/v06-runtime/amalur_native_math.lua');ap.add_argument('--output',type=Path,default=ROOT/'outputs/engine-bindings-v06/native-math');ap.add_argument('--prepare-only',action='store_true');args=ap.parse_args()
 out=args.output;out.mkdir(parents=True,exist_ok=False);assert digest(TARGET)==EXPECTED
 data=[]
 def add(name,values):data.append({'id':len(data),'binding':name,'address':hex(ADDRESSES[name]),'arguments':list(values)})
 for n in [-2147483648,-2147483647,-65537,-1,0,1,65537,2147483647]:add('abs',[n])
 for n in [-2147483648,-1,0,1,2,3,4,8,9,15,16,17,24,25,26,255,256,257,65535,65536,65537,2147302920,2147302921,2147302922,2147395599,2147395600,2147395601,2147483646,2147483647]:add('sqrt',[n])
 for a,b in [(0,-1),(2,-1),(-2,-3),(0,0),(123,0),(-2,3),(-2,4),(65537,2),(2147483647,2),(3,31),(2,32),(7,2147483647),(-2147483648,1),(-2147483648,2)]:add('pow',[a,b])
 for name in ('min','max'):
  for values in ([7],[-2147483648],[2147483647],[-2147483648,2147483647],[0,-7,3,0,2147483647,-2147483648],[7,7,7]):add(name,values)
 rng=random.Random(20261030)
 for _ in range(64):
  n=rng.randrange(-2**31,2**31);add('abs',[n]);add('sqrt',[n]);values=[rng.randrange(-2**31,2**31) for _ in range(rng.randrange(1,9))];add('min',values);add('max',values)
 runtime=LuaRuntime(unpack_returned_tuples=True,register_eval=False,register_builtins=False)
 runtime.execute("debug.sethook(function() error('math adapter instruction budget') end,'',1000000)")
 module=runtime.execute(args.lua_module.read_text(encoding='utf-8'))
 payload=bytearray(b'OMCB06\0\0'+struct.pack('<I',len(data)))
 for item in data:
  result=module[item['binding']](*item['arguments']);assert isinstance(result,(int,float)) and not isinstance(result,bool) and int(result)==result and -2**31<=result<2**31
  item['lua_result']=int(result);payload+=struct.pack('<IIIII',item['id'],1,32,0,len(item['arguments']))+struct.pack('<I',int(item['address'],16))
  payload+=b''.join(struct.pack('<II',3,n&0xffffffff) for n in item['arguments'])
 fixture=out/'fixtures.bin';fixture.write_bytes(payload);(out/'cases.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
 if args.prepare_only:print(json.dumps({'prepared':len(data),'directory':str(out)}));return
 harness=HERE/'native_vm_harness.exe';command=[str(harness),str(TARGET),str(fixture)]
 try:run=subprocess.run(command,capture_output=True,text=True,timeout=45)
 except subprocess.TimeoutExpired as e:
  (out/'native-process.json').write_text(json.dumps({'command':command,'timed_out':True,'timeout_seconds':45,'target_unchanged':digest(TARGET)==EXPECTED},indent=2),encoding='utf-8')
  (out/'native-stdout.partial').write_bytes(e.stdout or b'');(out/'native-stderr.partial').write_bytes(e.stderr or b'');raise
 (out/'native-stdout.json').write_text(run.stdout,encoding='utf-8');(out/'native-stderr.txt').write_text(run.stderr,encoding='utf-8');(out/'native-process.json').write_text(json.dumps({'exit_code':run.returncode,'timed_out':False,'command':command,'target_unchanged':digest(TARGET)==EXPECTED},indent=2),encoding='utf-8')
 if not run.stdout.strip():print(run.stderr);raise SystemExit(1)
 native=json.loads(run.stdout);assert native['target_sha256']==EXPECTED;by_id={r['id']:r for r in native['cases']};assert len(by_id)==len(data)
 records=[]
 for item in data:
  r=by_id[item['id']];number=None
  if r['ok'] and len(r['results'])==1 and r['results'][0]['tag']==3:
   v=int(r['results'][0]['raw_hi'],16);number=v if v<2**31 else v-2**32
  records.append({**item,'native_result':number,'native_ok':r['ok'],'native_exception_code':r['exception_code'],'native_exception_ip':r['exception_ip'],'match':number==item['lua_result']})
 report={'scope':'Original native math binding callbacks on WindowsCPU using synthetic Lua states and signed-int32 inputs, compared with guarded Lua adapter. Standard HIGHLOW relocations only; no game entry/TLS/import resolution. Other callback domains and in-game behavior remain unverified.',
 'target_sha256':EXPECTED,'target_unchanged':digest(TARGET)==EXPECTED,'harness_sha256':digest(harness),'fixture_sha256':digest(fixture),'lua_module_sha256':digest(args.lua_module),
 'mapped_image_base':native['mapped_image_base'],'relocation_delta':native['relocation_delta'],'highlow_relocations':native['highlow_relocations'],
 'cases':len(records),'matched':sum(r['match'] for r in records),'native_exit_code':run.returncode,'records':records}
 (out/'comparison.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k!='records'},indent=2))
 if run.returncode or report['matched']!=report['cases']:
  print(json.dumps([r for r in records if not r['match']],indent=2));raise SystemExit(1)
if __name__=='__main__':main()
