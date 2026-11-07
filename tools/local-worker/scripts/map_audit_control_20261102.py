from pathlib import Path
import argparse,base64,hashlib,json,subprocess,sys
import worker,control
base=worker.BASE;batch=base/'results/open-rune-map-lighting-20261102'
task='OpenRune-MapLightingAudit-20261102'
p=argparse.ArgumentParser();p.add_argument('command',choices=['start','resume','status']);a=p.parse_args()
if a.command in ['start','resume']:
 sha=hashlib.sha256((batch/'map-inputs.json').read_bytes()).hexdigest()
 if sha!='5eb666ecf3661d84d27e19c3a63d70e7a012aa5d1e43813fd0fce4cef2680872':raise RuntimeError('Input manifest changed')
 if (batch/'lifecycle.json').exists():
  previous=json.loads((batch/'lifecycle.json').read_text())
  if a.command!='resume' or previous.get('state') not in ['failed_results_held','partial_results_held'] or control.status()['ready']:raise RuntimeError('Existing active/completed batch; refusing duplicate')
  if not previous.get('inference_stopped'):raise RuntimeError('Previous runtime shutdown not verified')
  import time
  (batch/'lifecycle.json').rename(batch/('lifecycle.previous-'+str(int(time.time()))+'.json'))
 code=r'''$ErrorActionPreference='Stop'
$name='OpenRune-MapLightingAudit-20261102'
$existing=Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
if($existing -and $existing.State -eq 'Running'){throw 'Batch already running'}
$user=(Get-ScheduledTask -TaskName 'OpenAmalur-Qwen-Local-20261102').Principal.UserId
$principal=New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited
$action=New-ScheduledTaskAction -Execute 'C:\Users\rwill\AppData\Local\Programs\Python\Python312\python.exe' -Argument '"C:\Users\rwill\oa-worker\scripts\open_rune_map_audit_20261102.py"' -WorkingDirectory 'C:\Users\rwill\oa-worker'
$settings=New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Hours 4) -MultipleInstances IgnoreNew -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName $name -Action $action -Principal $principal -Settings $settings -Description 'One-shot local Open Rune 94-map lighting triage. Results held. Supervisor always stops inference, 3-hour child deadline. No automatic triggers.' -Force | Out-Null
Start-ScheduledTask -TaskName $name
Get-ScheduledTask -TaskName $name | Select-Object TaskName,State,@{Name='Triggers';Expression={@($_.Triggers).Count}} | ConvertTo-Json
'''
 subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',base64.b64encode(code.encode('utf-16le')).decode()],check=True)
else:
 result={}
 for name in ['lifecycle','progress']:
  path=batch/(name+'.json')
  if path.exists():result[name]=json.loads(path.read_text())
 statuses=[json.loads(p.read_text()) for p in (batch/'maps').glob('*/status.json')]
 result['counts']={key:sum(r.get('state')==key for r in statuses) for key in sorted(set(r.get('state','unknown') for r in statuses))}
 result['model_ready']=control.status()['ready']
 print(json.dumps(result,indent=2))
