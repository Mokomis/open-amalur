"""Windows Lua 5.1 checks of provider bridge, not native game equivalence."""
import hashlib, json, platform, sys
from pathlib import Path
assert platform.system() == 'Windows'
root = Path.home()/'Documents'/'Opem Amalur'
sys.path.insert(0, str(root/'tools/python-libs'))
from lupa.lua51 import LuaRuntime
lua = LuaRuntime(unpack_returned_tuples=True)
work = root/'work/v06-bindings'
bridge = lua.execute((work/'amalur_engine_bindings.lua').read_text())
registry = lua.execute((work/'engine_binding_registry.lua').read_text())
manifest = json.loads((work/'engine-binding-registry.json').read_text())
expected_counts = {'ACTOR':611, 'QUEST':48, 'GAME':165, 'TIME':6, 'WINDOW':232}
assert manifest['target_sha256'] == '16a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314'
assert set(registry.keys()) == set(manifest['namespaces']) == set(expected_counts)
for namespace, expected_count in expected_counts.items():
    rows = manifest['namespaces'][namespace]['methods']
    mapping = {row['name']:row['callback'] for row in rows}
    assert len(rows) == len(mapping) == expected_count
    assert dict(registry[namespace].items()) == mapping
carrier = lua.execute((root/'work/v05-parser/amalur_uint64.lua').read_text())
result = lua.execute((work/'test_engine_bindings.lua').read_text(), bridge, registry, carrier)
report = dict(result.items())
report['registry_counts'] = expected_counts
report['registry_total'] = sum(expected_counts.values())
report['registry_matches_native_descriptor_manifest'] = True
report['artifact_sha256'] = {name:hashlib.sha256((work/name).read_bytes()).hexdigest()
                           for name in ['amalur_engine_bindings.lua', 'engine_binding_registry.lua',
                                        'engine-binding-registry.json', 'test_engine_bindings.lua']}
out = root/'outputs/engine-bindings-v06/adapter-test-report.json'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report, indent=2))
