"""Exercise the worker's target boundary and real cross-process serialization."""
import json
import os
from pathlib import Path
import subprocess
import sys
import winreg

from worker import BASE, check_args, config, sha, task_lock


def main():
    c=config();target=Path(c['targets']['vulkan-layer']['snapshot'])
    rejected=[]
    for tool,arguments in [('execute_command',{'cmd':'echo forbidden'}),
                           ('inspect_native_exports',{'path':str(BASE/'not-the-target.dll')}),
                           ('procedure_pseudo_code',{'procedure':'0x10001000','path':str(target)})]:
        try:check_args(tool,arguments,target)
        except ValueError:rejected.append(tool)
        else:raise AssertionError('Boundary did not reject '+tool)
    with task_lock():
        child=subprocess.run([sys.executable,'-c',
            'from worker import task_lock\nwith task_lock(): print("unexpected-lock-acquisition")'],
            cwd=Path(__file__).parent,capture_output=True,text=True,timeout=10)
    assert child.returncode!=0 and 'Another local investigation owns the worker lock' in child.stderr
    before=json.loads((BASE/'inventory-before.json').read_text())
    hashes={p:sha(p)==expected for p,expected in before['preserved_config_sha256'].items()}
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER,'Environment') as key:
        path=winreg.ExpandEnvironmentStrings(winreg.QueryValueEx(key,'Path')[0])
    sources={name:{'source_sha256_matches':sha(reg['source'])==reg['sha256'],
                   'snapshot_sha256_matches':sha(reg['snapshot'])==reg['sha256']}
             for name,reg in c['targets'].items()}
    assert all(hashes.values()) and path==before['user_path']
    assert all(all(v.values()) for v in sources.values())
    result={'target_tool_boundary_pass':len(rejected)==3,
            'cross_process_lock_pass':True,'existing_codex_config_hashes_unchanged':hashes,
            'user_path_unchanged':True,'sources':sources,
            'limitations':'Checks worker tool boundary and worker-to-worker locking, not an OS sandbox or coordination with unrelated REA clients.'}
    (BASE/'results/boundary-verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
