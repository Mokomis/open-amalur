"""Windows export+Lua5.1 compilation, deduplicating exact wrapped input only."""
from pathlib import Path
import collections,hashlib,json,platform,sys,time
assert platform.system()=='Windows'
root=Path.home()/'Documents'/'Opem Amalur'
sys.path[:0]=[str(root/'src'),str(root/'tools/python-libs')]
from amalur_script import parse_file,iter_bundle_file
from amalur_reconstruct import reconstruct,emit_function
from lupa.lua51 import LuaRuntime,LUA_VERSION
assert tuple(LUA_VERSION)==(5,1)
profile=json.loads((root/'outputs/native-script-profile.json').read_text())
out=root/'outputs/initial-corpus-drafts-v05';out.mkdir(exist_ok=False)
source=root/'work/initial-script-corpus-v04'
lua=LuaRuntime(register_eval=False,register_builtins=False,unpack_returned_tuples=True)
compile=lua.eval('function(s) local f,e=loadstring(s); return f~=nil,e end')
seen={};bindings=[];errors=[];checks=[];counts=collections.defaultdict(collections.Counter)
header='local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable\n'
def write_lua(path,text):
 raw=text.encode('utf-8');path.write_bytes(raw);ok,err=compile(text)
 checks.append({'file':path.relative_to(out).as_posix(),'sha256':hashlib.sha256(raw).hexdigest(),'compiled':ok,'error':err})
def process(parsed,label,group):
 h=parsed['input_sha256']
 if h not in seen:
  ir,text=reconstruct(parsed,profile);directory=out/'scripts'/h;directory.mkdir(parents=True)
  write_lua(directory/'whole-script.lua',text)
  (directory/'ir.json').write_text(json.dumps(ir,separators=(',',':')),encoding='utf-8')
  (directory/'metadata.json').write_text(json.dumps({'input_sha256':h,'payload_sha256':parsed['payload_sha256'],'wrapper':parsed['wrapper'],'first_binding':label,'container':parsed.get('container')},indent=2),encoding='utf-8')
  dest=directory/'functions';dest.mkdir();exported=[]
  def visit(fn):
   if fn['body_emittable']:
    filename='function_'+fn['path'].replace('/','_')+'.lua';body=emit_function(fn);body[0]='return '+body[0]
    text='-- Opem Amalur guarded Lua5.1 draft; not original source or game-ready replacement.\n-- Input '+h+' function '+fn['path']+'\n'+header+'\n'.join(body)+'\n'
    write_lua(dest/filename,text);exported.append({'path':fn['path'],'file':filename,'captures':fn['upvalue_count']})
   for child in fn['children']:visit(child)
  visit(ir['root_function']);assert len(exported)==ir['summary']['emittable_function_bodies']
  seen[h]={'directory':directory.relative_to(out).as_posix(),'summary':ir['summary'],'exports':exported}
 record={'label':label,'group':group,'input_sha256':h,'container':parsed.get('container'),**seen[h]['summary']}
 bindings.append(record);counts[group].update(seen[h]['summary'])
for i,path in enumerate(sorted(source.glob('*.lua_bxml'))):
 try:
  if path.name.startswith('batch'):
   for member in iter_bundle_file(path):process(member,path.name+':'+str(member['container']['index']),'bundle')
  else:process(parse_file(path),path.name,'standalone')
 except Exception as exc:errors.append({'file':path.name,'error':repr(exc)})
 if i%250==0:print(i,len(seen),len(checks),flush=True)
report={'source_files':len(list(source.glob('*.lua_bxml'))),'bindings':bindings,'unique_scripts':seen,'totals_by_group':dict(counts),'errors':errors,
 'unique_totals':dict(sum((collections.Counter(v['summary']) for v in seen.values()),collections.Counter())),
 'scope':'Guarded register-level Lua5.1 reconstruction. Exact wrappers deduplicated, all container bindings preserved. Compilation only, no game execution.'}
(out/'manifest.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
validation={'runtime':'Lua5.1','files':len(checks),'passed':sum(c['compiled'] for c in checks),'checks':checks}
(out/'lua51-compile-validation.json').write_text(json.dumps(validation,indent=2),encoding='utf-8')
print(json.dumps({'unique_scripts':len(seen),'unique_totals':report['unique_totals'],'groups':dict(counts),'errors':errors,'compile_files':len(checks),'compile_passed':validation['passed']},indent=2))
if errors or validation['passed']!=len(checks):raise SystemExit(1)
