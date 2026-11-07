"""On-demand Task Scheduler owner keeps Strata alive independently of SSH."""
from pathlib import Path
import json
import os
import subprocess
import time

BASE=Path(__file__).resolve().parents[1]
STOP=BASE/'stop-runtime'


def status(**data):
    (BASE/'runtime-status.json').write_text(json.dumps({'owner_pid':os.getpid(),'time_unix':time.time(),**data},indent=2)+'\n')


def main():
    env=os.environ.copy();env['STRATA_DATA_DIR']=str(BASE/'strata')
    runtime=str(BASE/'strata/terminal/current/bin/strata.cmd')
    arguments=['cmd.exe','/d','/c',runtime,'launch','--family','qwen36','--model','UD-Q4_K_XL',
               '--context','16k','--vision','off','--parallel','1','--set','expert-vram=3.5','--tune','skip','--access','local',
               '--port','18180','--data-dir',str(BASE/'models'),'--yes','--no-tui','--output','json']
    status(state='starting',arguments=arguments)
    with (BASE/'runtime-service.log').open('a',encoding='utf-8') as log:
        try:
            p=subprocess.Popen(arguments,env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,
                               creationflags=subprocess.CREATE_NO_WINDOW)
            while p.poll() is None:
                if STOP.exists():
                    subprocess.run(['cmd.exe','/d','/c',runtime,'launch','--stop','--output','json'],env=env,
                                   stdout=log,stderr=subprocess.STDOUT,timeout=90,creationflags=subprocess.CREATE_NO_WINDOW)
                    p.wait(timeout=90);status(state='stopped');return
                time.sleep(1)
            if p.returncode:
                status(state='failed',launch_exit_code=p.returncode);return
            status(state='running',endpoint='http://127.0.0.1:18180')
            while not STOP.exists():time.sleep(1)
            result=subprocess.run(['cmd.exe','/d','/c',runtime,'launch','--stop','--output','json'],env=env,
                                  stdout=log,stderr=subprocess.STDOUT,timeout=90,creationflags=subprocess.CREATE_NO_WINDOW)
            status(state='stopped',stop_exit_code=result.returncode)
        except BaseException as e:
            status(state='failed',error=f'{type(e).__name__}: {e}')
            raise


if __name__=='__main__':main()
