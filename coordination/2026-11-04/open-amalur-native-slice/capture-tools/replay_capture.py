"""Inside native_guest.sh: replay a private frame capture without Wine/FEX.

Example: python3 replay_capture.py /root/oa-native-tools/captures/NAME.gfxr
The reported duration includes loading and pipeline creation, not steady FPS.
"""
import argparse
import json
import os
import platform
import sys
from pathlib import Path
import subprocess
import time

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('capture', type=Path)
p.add_argument('--wsi', choices=['headless', 'xlib'], default='headless')
p.add_argument('--timeout', type=float, default=60)
p.add_argument('--memory-translation', choices=['none','remap','realign','rebind'], default='rebind')
a = p.parse_args()
root = Path('/root/oa-native-tools')
capture = a.capture.resolve(strict=True)
if root / 'captures' not in capture.parents or capture.suffix != '.gfxr':
    raise SystemExit('Expected a capture below /root/oa-native-tools/captures')
os.setgid(10307)
os.setuid(10307)
out = root / 'results' / (capture.stem + '-' + str(time.time_ns()))
out.mkdir(parents=True)
cmd = [str(root / 'gfxrecon-replay'), '--wsi', a.wsi,
       '--screenshot-all', '--screenshot-dir', str(out), '--opcd', '--remove-unsupported']
if a.memory_translation != 'none':
    cmd += ['--memory-translation', a.memory_translation]
cmd.append(str(capture))
start = time.monotonic()
with (out / 'replay.log').open('w') as log:
    try:
        result = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, timeout=a.timeout)
        status = {'exit_code': result.returncode, 'timed_out': False}
    except subprocess.TimeoutExpired:
        status = {'exit_code': None, 'timed_out': True}
status.update(command=cmd, elapsed_including_load_seconds=time.monotonic()-start,
              screenshots=[str(x) for x in out.glob('*.bmp')],
              native_arm64=platform.machine()=='aarch64' and sys.maxsize>2**32,
              architecture=platform.machine(), full_engine=False, steady_fps=None)
(out / 'result.json').write_text(json.dumps(status, indent=2) + '\n')
print(json.dumps({'result_path': str(out / 'result.json'), **status}, indent=2), flush=True)
raise SystemExit(0 if status['exit_code'] == 0 and status['screenshots'] else 1)
