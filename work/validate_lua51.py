"""Compile generated drafts with actual Lua 5.1 on Windows, without running them."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'tools' / 'python-libs'))
from lupa import __version__
from lupa.lua51 import LuaRuntime, LUA_VERSION

assert tuple(LUA_VERSION) == (5, 1)
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('directory', type=Path)
args = parser.parse_args()
lua = LuaRuntime(register_eval=False, register_builtins=False)
check = lua.eval('function(source) local f, err = loadstring(source); return f ~= nil, err end')
records = []
for path in sorted(args.directory.rglob('*.lua')):
    raw = path.read_bytes()
    passed, error = check(raw.decode('utf-8'))
    records.append({'file': path.relative_to(args.directory).as_posix(),
                    'sha256': hashlib.sha256(raw).hexdigest(), 'compiled': passed, 'error': error})
report = {'runtime': lua.eval('_VERSION'), 'lupa': __version__,
          'scope': 'Lua compiler validation only; generated chunks were not invoked by this check',
          'files': len(records), 'passed': sum(r['compiled'] for r in records), 'records': records}
(args.directory / 'lua51-compile-validation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k != 'records'}))
if report['passed'] != report['files']:
    print(json.dumps([r for r in records if not r['compiled']], indent=2))
    raise SystemExit(1)
