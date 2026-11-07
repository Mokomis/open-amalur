"""Codex-facing SSH dispatcher for the Windows-only local REA worker.

Uses existing SSH public-key authentication. No model endpoint is forwarded.
"""
import argparse
import base64
import json
from pathlib import Path
import re
import subprocess
import sys

WINDOWS_ROOT = r'C:\Users\rwill\oa-worker'
PYTHON = r'C:\Users\rwill\AppData\Local\Programs\Python\Python312\python.exe'


def remote(host, script, arguments):
    payload = base64.b64encode(json.dumps(arguments).encode()).decode()
    ps = ("$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue'; [Console]::OutputEncoding=[Text.UTF8Encoding]::new(); "
          "$workerArgs=@(ConvertFrom-Json ([Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('"+payload+"')))); "
          "& '"+PYTHON+"' '"+WINDOWS_ROOT+'\\scripts\\'+script+"' @workerArgs; exit $LASTEXITCODE")
    encoded = base64.b64encode(ps.encode('utf-16le')).decode()
    return subprocess.call(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=8',host,
                            'powershell.exe','-NoProfile','-NonInteractive','-EncodedCommand',encoded])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host',default='open-rune-windows')
    sub=parser.add_subparsers(dest='command',required=True)
    for name in ['start','stop','status']:
        p=sub.add_parser(name);p.add_argument('--wait',type=int,default=150 if name=='start' else 30 if name=='stop' else 0)
    p=sub.add_parser('submit');p.add_argument('--question',required=True);p.add_argument('--target',default='vulkan-layer');p.add_argument('--max-tools',type=int)
    sub.add_parser('run-next')
    p=sub.add_parser('result');p.add_argument('id');p.add_argument('--json',action='store_true')
    p=sub.add_parser('fetch');p.add_argument('id');p.add_argument('--destination',type=Path,default=Path(__file__).resolve().parent/'results')
    a=parser.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9_.@-]*',a.host):parser.error('Invalid SSH host alias')
    if hasattr(a,'id') and not re.fullmatch(r'[A-Za-z0-9_-]{1,80}',a.id):parser.error('Invalid task ID')
    if a.command=='fetch':
        a.destination.mkdir(parents=True,exist_ok=True)
        return subprocess.call(['scp','-q','-r',a.host+':oa-worker/results/'+a.id,str(a.destination)])
    if a.command in {'start','stop','status'}:
        return remote(a.host,'control.py',[a.command,'--wait',str(a.wait)])
    arguments=[a.command]
    if a.command=='submit':
        arguments += ['--target',a.target,'--question',a.question]
        if a.max_tools is not None:arguments += ['--max-tools',str(a.max_tools)]
    if a.command=='result':
        arguments += [a.id]
        if a.json:arguments+=['--json']
    return remote(a.host,'worker.py',arguments)


if __name__=='__main__':sys.exit(main())
