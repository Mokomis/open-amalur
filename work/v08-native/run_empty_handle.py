"""Bounded Windows launcher for the original empty-token callback experiment."""
import argparse,hashlib,json,platform,subprocess
from pathlib import Path
assert platform.system()=='Windows'
ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
here=Path(__file__).resolve().parent;target=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning\koa.exe')
expected='16a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
before=sha(target);assert before==expected;args.output.mkdir(parents=True,exist_ok=False)
sources=[here/'native_empty_handle_harness.c',here.parent/'v06-compare/native_vm_harness.c',here/'native_empty_handle_harness.exe']
receipt={'target_sha256_before':before,'sources':[{'file':str(p),'sha256':sha(p)} for p in sources],
    'scope':'Original00e43060 callback and read-only00aa0850 helper with eight synthetic frames; no game entry/imports/services.'}
try:
    run=subprocess.run([str(here/'native_empty_handle_harness.exe'),str(target)],capture_output=True,text=True,timeout=30)
    (args.output/'native-results.json').write_text(run.stdout,encoding='utf-8');(args.output/'native-stderr.txt').write_text(run.stderr,encoding='utf-8')
    receipt.update(exit_code=run.returncode,timed_out=False)
    result=json.loads(run.stdout);receipt['case_count']=result['cases_executed'];receipt['failed_cases']=result['failed_cases']
    receipt['passed']=run.returncode==0 and result['cases_executed']==8 and result['failed_cases']==0 and result['original_file_unchanged']
except subprocess.TimeoutExpired as exc:
    (args.output/'native-stdout.partial').write_bytes(exc.stdout or b'');(args.output/'native-stderr.partial').write_bytes(exc.stderr or b'')
    receipt.update(timed_out=True,passed=False)
finally:
    receipt['target_sha256_after']=sha(target);receipt['target_unchanged']=receipt['target_sha256_after']==before
    (args.output/'receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps(receipt,indent=2))
if not receipt.get('passed') or not receipt['target_unchanged']:raise SystemExit(1)
