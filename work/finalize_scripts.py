"""Finalize already-validated Windows results and package review artifacts."""
import hashlib
import json
import re
import struct
import sys
import zipfile
from pathlib import Path

root = Path.home() / 'Documents' / 'Opem Amalur'
out = root / 'outputs'
native = out / 'bytecode-reader'
session = native / 'rea-session'
reconstruction = out / 'reconstruction'
assert json.loads((session / 'status.json').read_text())['state'] == 'closed'
integrity = json.loads((session / 'input-integrity.json').read_text())
assert integrity['unchanged']
tests = (reconstruction / 'tests.txt').read_text(encoding='utf-8-sig')
assert re.search(r'Ran 61 tests', tests) and tests.rstrip().endswith('OK')
syntax = json.loads((reconstruction / 'syntax-validation.json').read_text())
assert syntax['files_checked'] == 104 and all(x['syntax'] == 'passed' for x in syntax['results'])

sys.path.insert(0, str(root / 'src'))
from amalur_script import OPCODE_NAMES
table = json.loads((native / 'offline-opcode-table.json').read_text())
assert [row['name'] for row in table['rows']] == OPCODE_NAMES
table_bytes = b''.join(struct.pack('<9I', *(int(w, 16) for w in row['words'])) for row in table['rows'])
record = json.loads((session / 'opcode_metadata_bytes.json').read_text())['structuredContent']
readback = record['normalized_result']
assert readback['requested_bytes'] == readback['returned_bytes'] == 3096
assert bytes.fromhex(readback['bytes_hex']) == table_bytes

for path in session.glob('*_pseudocode.json'):
    result = json.loads(path.read_text())
    assert not result.get('isError')
    evidence = result['structuredContent']
    prefix = ('/* Raw Ghidra pseudocode; types/names may be inferred. Not original source.\n'
              ' * Target SHA-256: ' + integrity['sha256_after'] + '\n'
              ' * Evidence: ' + evidence['evidence_id'] + '\n */\n')
    path.with_suffix('.c').write_text(prefix + evidence['normalized_result'].replace('\r\n', '\n'), encoding='utf-8')

validation = {'execution_host': 'RobMachineX', 'python': sys.version,
              'tests_passed': 61, 'parser_tests': 34, 'reconstruction_tests': 27,
              'test_duration_seconds': 0.028, 'test_exit_code': 0,
              'syntax_files_passed': 104, 'syntax_tool': 'luaparse 0.3.1 / Lua 5.1',
              'opcode_names_matched': 86, 'opcode_memory_matches_original_file_table': True,
              'native_session_closed': True, 'executable_integrity': integrity,
              'game_or_generated_lua_executed': False, 'samples': []}
for label, filename in [('small', '1596600.lua_bxml'), ('sq02', '441939.lua_bxml'), ('third', '1701254.lua_bxml')]:
    ir = json.loads((reconstruction / (label + '.ir.json')).read_text())
    actual = hashlib.sha256((root / 'work' / 'script-samples' / filename).read_bytes()).hexdigest()
    assert actual == ir['input_sha256']
    validation['samples'].append({'file': filename, 'sha256': actual,
                                  'unchanged': True, **ir['summary']})
assert validation['samples'][0]['unresolved_function_bodies'] == 0
(reconstruction / 'validation.json').write_text(json.dumps(validation, indent=2), encoding='utf-8')

source_files = ['src/amalur_script.py', 'src/amalur_reconstruct.py',
                'tests/test_amalur_script.py', 'tests/test_amalur_reconstruct.py',
                'README.md', 'RECONSTRUCTION.md', 'work/export_fragments.py',
                'work/validate_lua.cjs', 'outputs/native-script-profile.json',
                'outputs/native-script-findings.md']
with zipfile.ZipFile(out / 'opem-amalur-script-tools-v0.2.zip', 'w', zipfile.ZIP_DEFLATED) as package:
    for name in source_files:
        package.write(root / name, name)
with zipfile.ZipFile(out / 'opem-amalur-lua-drafts.zip', 'w', zipfile.ZIP_DEFLATED) as package:
    for path in sorted(reconstruction.rglob('*')):
        if path.is_file() and path.name != 'tests-initial.txt':
            package.write(path, path.relative_to(out).as_posix())
with zipfile.ZipFile(out / 'opem-amalur-bytecode-evidence.zip', 'w', zipfile.ZIP_DEFLATED) as package:
    for path in sorted(native.rglob('*')):
        if path.is_file():
            package.write(path, path.relative_to(out).as_posix())
manifest = {}
for name in ['opem-amalur-script-tools-v0.2.zip', 'opem-amalur-lua-drafts.zip', 'opem-amalur-bytecode-evidence.zip']:
    path = out / name
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
    manifest[name] = {'bytes': path.stat().st_size, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
(out / 'script-packages-sha256.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
print(json.dumps({'validation': validation, 'packages': manifest}, indent=2))
