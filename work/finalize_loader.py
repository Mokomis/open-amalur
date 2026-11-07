"""Package existing Windows analysis results; do not execute the target."""
import hashlib
import json
import zipfile
from pathlib import Path

root = Path.home() / 'Documents' / 'Opem Amalur'
out = root / 'outputs'
session = out / 'loader-recovery' / 'rea-session'
assert json.loads((session / 'status.json').read_text())['state'] == 'closed'
integrity = json.loads((session / 'input-integrity.json').read_text())
assert integrity['unchanged']

functions = [
    ('loader_pseudocode', '0x010d5840'),
    ('inner_pseudocode', '0x010d56f0'),
    ('file_reader_pseudocode', '0x010859d0'),
    ('load_core_pseudocode', '0x010d4600'),
    ('compiler_callback_pseudocode', '0x010d4140'),
    ('bytecode_inner_pseudocode', '0x010c6b70'),
]
sections = ['/* Opem Amalur: raw Ghidra 12.1.4 pseudocode via REA 6.8.0.\n'
            ' * Target SHA-256: ' + integrity['sha256_after'] + '\n'
            ' * Static analysis, not original source or a compilable replacement.\n'
            ' * The first two function names are analyst annotations.\n'
            ' * Their void return types are uncorrected Ghidra inference.\n'
            ' * Assembly shows a status returned in EAX; see recovery report.\n */\n']
for label, address in functions:
    result = json.loads((session / (label + '.json')).read_text())
    assert not result.get('isError')
    evidence = result['structuredContent']
    sections.append('/* Address: ' + address + '\n * Evidence: ' + evidence['evidence_id'] + '\n */\n'
                    + evidence['normalized_result'].replace('\r\n', '\n'))
(out / 'loader-recovery' / 'recovered-loader.c').write_text('\n'.join(sections), encoding='utf-8')

sample_files = [('small', '1596600.lua_bxml'), ('sq02', '441939.lua_bxml'), ('third', '1701254.lua_bxml')]
validation = {'execution_host': 'RobMachineX', 'tests_passed': 32,
              'test_duration_seconds': 0.028, 'test_exit_code': 0,
              'test_evidence': 'parser/tests.txt', 'samples': [],
              'executable_integrity': integrity}
test_bytes = (out / 'parser' / 'tests.txt').read_bytes()
test_log = test_bytes.decode('utf-16' if test_bytes.startswith((b'\xff\xfe', b'\xfe\xff')) else 'utf-8-sig')
assert 'Ran 32 tests' in test_log and test_log.rstrip().endswith('OK')
for label, filename in sample_files:
    data = json.loads((out / 'parser' / (label + '.json')).read_text())
    actual = hashlib.sha256((root / 'work' / 'script-samples' / filename).read_bytes()).hexdigest()
    assert actual == data['input_sha256']
    validation['samples'].append({'file': filename, 'sha256': actual,
                                  'bytes': data['input_bytes'], 'coverage': data['coverage'],
                                  'unchanged_since_parse': True})
(out / 'parser' / 'validation.json').write_text(json.dumps(validation, indent=2), encoding='utf-8')

sources = [(root / 'src' / 'amalur_script.py', 'src/amalur_script.py'),
           (root / 'tests' / 'test_amalur_script.py', 'tests/test_amalur_script.py'),
           (root / 'README.md', 'README.md')]
with zipfile.ZipFile(out / 'opem-amalur-parser.zip', 'w', zipfile.ZIP_DEFLATED) as package:
    for path, name in sources:
        package.write(path, name)
with zipfile.ZipFile(out / 'opem-amalur-loader-evidence.zip', 'w', zipfile.ZIP_DEFLATED) as package:
    for path in sorted((out / 'loader-recovery').rglob('*')):
        if path.is_file():
            package.write(path, path.relative_to(out).as_posix())

manifest = {name: hashlib.sha256((out / name).read_bytes()).hexdigest()
            for name in ['opem-amalur-parser.zip', 'opem-amalur-loader-evidence.zip']}
(out / 'package-sha256.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
print(json.dumps({'packages': manifest, 'validation': validation}, indent=2))
