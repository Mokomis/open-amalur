"""Project-local REA worker. Commands and results remain on the Windows host."""
import hashlib,json,os,queue,re,subprocess,threading,time,traceback
from pathlib import Path
root=Path.home()/'Documents'/'Opem Amalur'
out=root/'outputs'/'scene-v13'/'rea-runtime-cwd'
out.mkdir(parents=True,exist_ok=False)
requests=root/'work'/'scene-v13-runtime-requests'
requests.mkdir(exist_ok=True)
target=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning\koa.exe')
sha=hashlib.sha256(target.read_bytes()).hexdigest()
assert sha=='16a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314'
seed=root/'work'/'scene-v13-runtime-seeds.tsv'
seed.write_text('# Analyst function-entry hypotheses from on-disk disassembly\n0x10d5840\tfunction\tamalur_candidate_script_loadfile\n0x10d56f0\tfunction\tamalur_candidate_script_loadfile_inner\n0x1008b60\tfunction\tworld_chunk_candidate_serializer\n',encoding='utf-8')
env=os.environ.copy()
env.update(GHIDRA_INSTALL_DIR=str(root/'tools'/'ghidra_12.1.4_PUBLIC'),
 JAVA_HOME=str(root/'tools'/'jdk-21.0.13+9'),REA_ANALYSIS_PROVIDER='ghidra',
 REA_GHIDRA_STARTUP_TIMEOUT_MS='900000',REA_GHIDRA_SEED_FILE=str(seed))
rea=root/'tools'/'rea'/'node_modules'/'rea-agents'/'scripts'/'rea.mjs'
err=(out/'server-stderr.log').open('w',encoding='utf-8')
p=subprocess.Popen(['node',str(rea),'mcp'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,text=True,encoding='utf-8',env=env,bufsize=1,cwd=target.parent)
q=queue.Queue()
def read():
 try:
  for line in p.stdout:q.put(json.loads(line))
 except BaseException as e:q.put({'reader_error':str(e)})
 finally:q.put(None)
threading.Thread(target=read,daemon=True).start()
serial=0
def rpc(method,params,notify=False):
 global serial
 serial+=1
 msg={'jsonrpc':'2.0','method':method,'params':params}
 if not notify:msg['id']=serial
 p.stdin.write(json.dumps(msg)+'\n');p.stdin.flush()
 if notify:return
 deadline=time.monotonic()+960
 while True:
  r=q.get(timeout=max(1,deadline-time.monotonic()))
  if r is None or 'reader_error' in r:raise RuntimeError(r)
  if r.get('id')==serial:
   if 'error' in r:raise RuntimeError(r['error'])
   return r['result']
def save(name,data):
 (out/(name+'.json')).write_text(json.dumps(data,indent=2),encoding='utf-8')
def call(name,args,label):
 save('status',{'state':'running','label':label,'tool':name,'time':time.time()})
 r=rpc('tools/call',{'name':name,'arguments':args})
 save(label,r)
 save('status',{'state':'idle','last_label':label,'isError':r.get('isError',False),'time':time.time()})
 return r
opened=False
try:
 save('initialize',rpc('initialize',{'protocolVersion':'2025-06-18','capabilities':{},'clientInfo':{'name':'opem-amalur-native-session','version':'0.2'}}))
 rpc('notifications/initialized',{},True)
 catalog=rpc('tools/list',{})
 save('schemas',{'tools':[{'name':t['name'],'description':t.get('description'),'inputSchema':t['inputSchema']} for t in catalog['tools']]})
 # Target-free Frida worker; preserves the separate warm static session.
 call('list_frida_devices',{},'runtime_devices')
 sid=None
 try:
  r=call('start_frida_session',{'mode':'spawn','device_id':'local','program':str(target)},'spawn')
  if r.get('isError'):raise RuntimeError('Spawn failed')
  data=r['structuredContent'];sid=data['session_id'];save('owned-process',data)
  call('load_frida_script',{'session_id':sid,'source_kind':'file','path':str(root/'work/v13-properties/trace_cwd.js')},'load')
  call('resume_frida_session',{'session_id':sid},'resume')
  time.sleep(48)
  call('frida_session_status',{'session_id':sid,'detail':'complete'},'trace_status')
 finally:
  if sid:call('close_frida_session',{'session_id':sid},'trace_close')
  call('export_evidence_bundle',{'path':str(out/'evidence.json')},'export')
except BaseException:
 (out/'worker-error.txt').write_text(traceback.format_exc(),encoding='utf-8')
 raise
finally:
 try:
  if opened:
   try:call('export_evidence_bundle',{'path':str(out/'evidence.json')},'export')
   finally:call('close_binary',{'snapshot_path':str(out/'analysis.snapshot.json')},'close')
 finally:
  p.stdin.close()
  try:p.wait(timeout=30)
  except subprocess.TimeoutExpired:p.terminate();p.wait(timeout=10)
  err.close()
  after=hashlib.sha256(target.read_bytes()).hexdigest()
  save('input-integrity',{'sha256_before':sha,'sha256_after':after,'unchanged':sha==after})
  save('status',{'state':'closed','time':time.time()})
