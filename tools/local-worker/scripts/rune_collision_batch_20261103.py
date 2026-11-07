"""Bounded original-engine collision/push REA jobs. No game execution or source editing."""
from pathlib import Path
import argparse,base64,hashlib,json,os,subprocess,sys,time,traceback,uuid
import worker,control
from open_rune_map_audit_20261102 import owned_run
BASE=worker.BASE
OUT=BASE/'results/open-rune-collision-contracts-20261103'
TASK='OpenRune-CollisionContracts-20261103'

def save(path,value):
 path=Path(path);tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8');os.replace(tmp,path)
def status():
 r={}
 for name in ['lifecycle','progress','manifest']:
  p=OUT/(name+'.json')
  if p.exists():
   value=json.loads(p.read_text())
   r[name]=value if name!='manifest' else {'tasks_total':len(value['jobs']),'job_ids':[x['id'] for x in value['jobs']]}
 r['inference_ready']=control.status()['ready'];print(json.dumps(r,indent=2))
def child():
 manifest=json.loads((OUT/'manifest.json').read_text());results=[]
 for job in manifest['jobs']:
  p=BASE/'jobs'/(job['id']+'.json')
  content=json.loads(p.read_text())
  if content['target']!='rune-classic-engine' or content['max_tools']!=2:raise RuntimeError('Job binding changed')
  existing=BASE/'results'/job['id']/'status.json'
  if existing.exists():raise RuntimeError('Refusing duplicate or ambiguous prior job')
  result=worker.run_job(p)
  row={k:result.get(k) for k in ['task_id','status','error','rea_closed','total_task_seconds','report_path']};row['label']=job['label'];results.append(row)
  save(OUT/'progress.json',{'tasks_total':len(manifest['jobs']),'processed':len(results),'completed':sum(x['status']=='completed_pending_codex_review' for x in results),'results':results,'hold_results_until_user_requests':True})
  if result.get('rea_closed') is False:raise RuntimeError('REA cleanup incomplete; not proceeding to another job')
 save(OUT/'index.json',{'results':results,'reviewed_by_codex':False,'hold_results_until_user_requests':True})
 return 0 if all(r['status']=='completed_pending_codex_review' for r in results) else 1

def supervise():
 OUT.mkdir(exist_ok=True,parents=True)
 with worker.task_lock():
  if (OUT/'lifecycle.json').exists():raise RuntimeError('Existing batch; refusing duplicate')
  pending=[p.stem for p in sorted((BASE/'jobs').glob('*.json')) if not (BASE/'results'/p.stem/'status.json').exists()]
  if pending:raise RuntimeError('Existing queue jobs must be preserved: '+repr(pending))
  if control.status()['ready']:raise RuntimeError('Inference already active; refusing runtime ownership')
  if worker.ALLOWED!={'inspect_native_exports','search_procedures','procedure_pseudo_code','procedure_callees','analyze_function'}:raise RuntimeError('Read-only worker tool boundary differs; refusing to start')
  spec=json.loads((OUT/'batch-spec.json').read_text());reg=worker.config()['targets'][spec['target']]
  if len(spec['tasks'])!=4:raise RuntimeError('Expected four narrowly scoped jobs')
  if spec['sha256']!=reg['sha256'] or worker.sha(reg['snapshot'])!=reg['sha256']:raise RuntimeError('Original-engine snapshot identity mismatch')
  jobs=[]
  for task in spec['tasks']:
   ident=time.strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:6]
   job={'id':ident,'target':'rune-classic-engine','max_tools':2,'question':task['question'],'created_unix':time.time()}
   worker.save(BASE/'jobs'/(ident+'.json'),job);jobs.append({'id':ident,'label':task['label'],'body_address':task['body_address']})
  save(OUT/'manifest.json',{'jobs':jobs,'target_sha256':spec['sha256'],'hold_results_until_user_requests':True})
  life={'state':'starting','supervisor_pid':os.getpid(),'started_unix':time.time(),'tasks_total':len(jobs),'child_timeout_seconds':1800,'hold_results_until_user_requests':True,'shutdown_policy':'Always stop inference on completion, startup/child failure or 30-minute child timeout'};save(OUT/'lifecycle.json',life)
  def start():
   r=subprocess.run([sys.executable,str(BASE/'scripts/control.py'),'start','--wait','150'],capture_output=True,text=True,timeout=180)
   (OUT/'runtime-start.log').write_text(r.stdout+r.stderr,encoding='utf-8')
   if r.returncode or not control.status()['ready']:raise RuntimeError('Inference startup failed')
  def run():
   with (OUT/'batch.log').open('a',encoding='utf-8') as log:
    p=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--child'],stdout=log,stderr=log)
    life.update(state='running',child_pid=p.pid);save(OUT/'lifecycle.json',life)
    try:return p.wait(timeout=1800)
    except subprocess.TimeoutExpired:
     subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True,timeout=30)
     p.wait(timeout=15)
     raise RuntimeError('30-minute safety deadline reached; partial evidence retained')
  def stop():
   (BASE/'stop-runtime').touch()
   try:
    r=subprocess.run([sys.executable,str(BASE/'scripts/control.py'),'stop','--wait','30'],capture_output=True,text=True,timeout=45)
    (OUT/'runtime-stop.log').write_text(r.stdout+r.stderr,encoding='utf-8')
   except Exception as e:life['stop_error']=str(e)
   end=control.status();life['runtime_after']=end;life['inference_stopped']=not end['ready'] and (end.get('service') or {}).get('state')=='stopped'
   save(OUT/'lifecycle.json',life)
  try:
   result=owned_run(run,start,stop,control.status);life.update(state='completed_results_held' if result==0 else 'partial_results_held',child_exit_code=result)
  except Exception as e:
   life.update(state='failed_results_held',error=str(e));(OUT/'supervisor-error.txt').write_text(traceback.format_exc(),encoding='utf-8')
  finally:life['finished_unix']=time.time();save(OUT/'lifecycle.json',life)
  return 0 if life['state']=='completed_results_held' and life.get('inference_stopped') else 1

def register_start():
 if (OUT/'lifecycle.json').exists():raise RuntimeError('Batch exists; use --status')
 code=r'''$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue'
$name='OpenRune-CollisionContracts-20261103'
$existing=Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
if($existing -and $existing.State -eq 'Running'){throw 'Batch already running'}
$user=(Get-ScheduledTask -TaskName 'OpenAmalur-Qwen-Local-20261102').Principal.UserId
$principal=New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited
$action=New-ScheduledTaskAction -Execute 'C:\Users\rwill\AppData\Local\Programs\Python\Python312\python.exe' -Argument '"C:\Users\rwill\oa-worker\scripts\rune_collision_batch_20261103.py"' -WorkingDirectory 'C:\Users\rwill\oa-worker'
$settings=New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Hours 1) -MultipleInstances IgnoreNew -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName $name -Action $action -Principal $principal -Settings $settings -Description 'One-shot read-only Rune collision/push contracts. Four bounded jobs; reports held, inference auto-stop; no triggers.' -Force | Out-Null
Start-ScheduledTask -TaskName $name
$t=Get-ScheduledTask -TaskName $name
[pscustomobject]@{State=$t.State.ToString();NonNullTriggers=@($t.Triggers|Where-Object {$null -ne $_}).Count}|ConvertTo-Json
'''
 r=subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',base64.b64encode(code.encode('utf-16le')).decode()],capture_output=True,text=True)
 print(r.stdout);print(r.stderr if r.returncode else '');return r.returncode

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--status',action='store_true');p.add_argument('--child',action='store_true');p.add_argument('--start',action='store_true');p.add_argument('--self-test',action='store_true');a=p.parse_args()
 if a.status:status()
 elif a.child:raise SystemExit(child())
 elif a.start:raise SystemExit(register_start())
 elif a.self_test:
  from open_rune_map_audit_20261102 import self_test
  import contextlib,io
  buf=io.StringIO()
  with contextlib.redirect_stdout(buf):self_test()
  result=json.loads(buf.getvalue());result['tools_exposed_to_model']=sorted(worker.ALLOWED);result['max_tool_calls_per_job']=2
  print(json.dumps(result,indent=2))
 else:raise SystemExit(supervise())
