"""Package the exact native-compared generated Lua cases for a portable host."""
import hashlib, json, platform, shutil
from pathlib import Path
assert platform.system() == 'Windows'
root = Path.home()/'Documents'/'Opem Amalur'
source = root/'outputs/engine-bindings-v06/final-real-functions-verified'
target = root/'work/v06-portable/tests'
target.mkdir(parents=True, exist_ok=True)
cases = json.loads((source/'cases.json').read_text())
report = json.loads((source/'comparison.json').read_text())
assert report['cases'] == report['matched'] == 71
native = {r['id']: r for r in report['records']}
def literal(value):
    if value is None: return 'nil'
    if isinstance(value, bool): return 'true' if value else 'false'
    assert isinstance(value, int)
    return str(value)
text = ['-- Generated on Windows from native-compared real function cases.',
        '-- Isolated primitive function coverage only, not whole-game behavior.',
        "local function pack(...) return {n=select('#',...),...} end", 'local passed=0']
provenance = []
for case in cases:
    observation = native[case['id']]
    assert observation['match'] and observation['native_ok']
    path = source/f"case-{case['id']:04d}.lua"
    generated = path.read_text()
    assert hashlib.sha256(path.read_bytes()).hexdigest() == case['generated_source_sha256']
    text += ['do', 'local result=pack((function(...)', generated,
             'end)('+','.join(literal(x) for x in case['arguments'])+'))',
             f"assert(result.n=={len(observation['native'])},'result count case {case['id']}')"]
    for i, value in enumerate(observation['native'], 1):
        text.append(f"assert(result[{i}]=={literal(value['value'])},'result value case {case['id']} slot {i}')")
    text += ['passed=passed+1', 'end']
    provenance.append({'case_id':case['id'], 'real_source':case['real_source'],
                       'generated_source_sha256':case['generated_source_sha256'],
                       'arguments':case['arguments'], 'expected_native_results':observation['native']})
text += ['return passed']
output = target/'native_verified_real_functions.lua'
output.write_text('\n'.join(text)+'\n', encoding='utf-8')
manifest = {'scope':'71 native-compared inputs across19 primitive game function bodies, packaged for portable runtime replay.',
            'target_sha256':report['target_sha256'],'native_harness_sha256':report['harness_sha256'],
            'native_comparison_sha256':hashlib.sha256((source/'comparison.json').read_bytes()).hexdigest(),
            'test_source_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'cases':provenance}
(target/'native_verified_real_functions.json').write_text(json.dumps(manifest, indent=2),encoding='utf-8')
runtime = root/'work/v06-portable/runtime'
runtime.mkdir(exist_ok=True)
for source in [root/'src/amalur_uint64.lua', root/'work/v06-runtime/amalur_native_math.lua',
               root/'work/v06-bindings/engine_binding_registry.lua',root/'work/v06-bindings/amalur_engine_bindings.lua',
               root/'work/v06-handles/amalur_engine_handles.lua']:
    shutil.copy2(source,runtime/source.name)
print(json.dumps({'real_inputs':len(cases),'function_bodies':len({c['real_source']['function_signature'] for c in cases}),
                  'test_source_sha256':manifest['test_source_sha256']}))
