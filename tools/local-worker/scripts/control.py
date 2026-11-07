"""Start/stop/status for the isolated, localhost-only Qwen runtime."""
import argparse
import json
from pathlib import Path
import subprocess
import time
import urllib.request

BASE=Path(__file__).resolve().parents[1]
TASK='OpenAmalur-Qwen-Local-20261102'


def status():
    p=BASE/'runtime-status.json'
    result={'service':json.loads(p.read_text()) if p.exists() else None}
    try:
        with urllib.request.urlopen('http://127.0.0.1:18180/v1/models',timeout=3) as f:
            result['models']=json.load(f)
        expected=json.loads((BASE/'config.json').read_text())
        result['ready']=any(m.get('id')==expected['model'] and m.get('meta',{}).get('n_ctx')==expected['context_tokens'] for m in result['models'].get('data',[]))
        if not result['ready']:result['error']='Endpoint model/context differs from worker configuration'
    except Exception as e:result.update(ready=False,error=type(e).__name__+': '+str(e))
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['start','stop','status']);p.add_argument('--wait',type=int,default=0)
    a=p.parse_args()
    invoked=time.time()
    if a.command=='start':
        current=status()
        if current['ready']:print(json.dumps(current,indent=2));return
        (BASE/'stop-runtime').unlink(missing_ok=True)
        subprocess.run(['schtasks','/Run','/TN',TASK],check=True)
    elif a.command=='stop':
        (BASE/'stop-runtime').touch()
    deadline=time.monotonic()+a.wait
    while a.wait and time.monotonic()<deadline:
        current=status()
        service=current.get('service') or {}
        if (a.command=='start' and current['ready']) or (a.command=='stop' and not current['ready'] and service.get('state')=='stopped'):break
        if service.get('state')=='failed' and service.get('time_unix',0)>=invoked:break
        time.sleep(2)
    final=status();print(json.dumps(final,indent=2))
    if a.wait and ((a.command=='start' and not final['ready']) or (a.command=='stop' and (final['ready'] or (final.get('service') or {}).get('state')!='stopped'))):return 1
    return 0


if __name__=='__main__':raise SystemExit(main())
