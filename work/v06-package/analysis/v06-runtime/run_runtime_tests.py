"""Windows admission tests; original-code differential records are separate."""
import hashlib, json, platform, sys
from pathlib import Path
assert platform.system() == 'Windows'
root = Path.home() / 'Documents' / 'Opem Amalur'
sys.path.insert(0, str(root / 'tools/python-libs'))
from lupa.lua51 import LuaRuntime, LUA_VERSION
assert tuple(LUA_VERSION) == (5, 1)
here = Path(__file__).resolve().parent
lua = LuaRuntime(unpack_returned_tuples=True, register_eval=False, register_builtins=False)
lua.execute("debug.sethook(function() error('runtime fixture budget') end,'',1000000)")
module = lua.execute((here/'amalur_native_math.lua').read_text())
checks = lua.execute((here/'test_native_math_guards.lua').read_text(), module)
report = {
    'scope': 'Guard admission and native-confirmed boundary regression checks; no engine behavior claim.',
    'passed': len(checks), 'checks': [checks[i] for i in range(1, len(checks)+1)],
    'source_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in
                      [here/'amalur_native_math.lua', here/'test_native_math_guards.lua']},
}
out = root/'outputs/engine-bindings-v06/runtime-admission-validation.json'
out.write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='checks'}, indent=2))
