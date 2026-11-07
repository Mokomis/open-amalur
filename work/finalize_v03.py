"""Verify and package completed v0.3 artifacts on Windows; never execute the game."""
import hashlib
import json
import platform
import re
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path

assert platform.system() == 'Windows', 'Run finalization on Windows'
root = Path.home() / 'Documents' / 'Opem Amalur'
out = root / 'outputs'
focus = out / 'reconstruction-v03'
corpus = out / 'corpus-drafts-v03'
evidence = out / 'branch-capture'
expected = '16a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314'

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')

def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

exe = Path(r'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning\koa.exe')
assert digest(exe) == expected
assert read(evidence / 'rea-session' / 'status.json')['state'] == 'closed'
integrity = read(evidence / 'rea-session' / 'input-integrity.json')
assert integrity['unchanged'] and integrity['sha256_before'] == integrity['sha256_after'] == expected
tests = (focus / 'tests.txt').read_text(encoding='utf-8-sig')
assert re.search(r'Ran 115 tests in [\d.]+s', tests)
assert tests.rstrip().endswith('OK') and 'skipped=' not in tests

def check_compile(directory, count):
    report = read(directory / 'lua51-compile-validation.json')
    assert report['runtime'] == 'Lua 5.1'
    assert report['passed'] == report['files'] == len(report['records']) == count
    actual = {p.relative_to(directory).as_posix() for p in directory.rglob('*.lua')}
    assert actual == {r['file'] for r in report['records']}
    for record in report['records']:
        assert record['compiled'] and digest(directory / record['file']) == record['sha256']

check_compile(focus, 121)
check_compile(corpus, 3276)
syntax = read(focus / 'syntax-validation.json')
assert syntax['files_checked'] == len(syntax['results']) == 121
assert all(r['syntax'] == 'passed' and digest(focus / r['file']) == r['sha256'] for r in syntax['results'])
comparison = read(evidence / 'corpus-comparison.json')
assert comparison['totals']['parsed'] == 383
assert comparison['totals']['before_eligible'] == 2248
assert comparison['totals']['after_eligible'] == 2893
assert comparison['totals']['after_unresolved'] == 1460
assert not comparison['coverage_losses']
manifest = read(corpus / 'manifest.json')
assert manifest['selected_scripts'] == 384 and manifest['parsed_scripts'] == 383
assert manifest['function_drafts'] == 2893 and manifest['whole_script_outputs'] == 383
draft_count = 0
for record in manifest['records']:
    if record['status'] != 'exported':
        continue
    assert digest(root / 'work' / 'capture-corpus' / record['file']) == record['input_sha256']
    directory = corpus / Path(record['file']).stem
    ir = read(directory / 'ir.json')
    assert ir['input_sha256'] == record['input_sha256'] and ir['summary'] == record['summary']
    for draft in record['drafts']:
        assert digest(directory / 'functions' / draft['file']) == draft['sha256']
        draft_count += 1
assert draft_count == 2893
samples = {}
for name, filename, folder, eligible, total in [
    ('small', '1596600.lua_bxml', 'script-samples', 2, 2),
    ('sq02', '441939.lua_bxml', 'script-samples', 109, 154),
    ('third', '1701254.lua_bxml', 'script-samples', 4, 5),
    ('ayten', '1378937.lua_bxml', 'capture-corpus', 2, 6),
]:
    ir = read(focus / (name + '.ir.json'))
    assert digest(root / 'work' / folder / filename) == ir['input_sha256']
    assert ir['summary']['emittable_function_bodies'] == eligible
    assert ir['summary']['functions'] == total
    samples[name] = {'file': filename, 'sha256': ir['input_sha256'], **ir['summary']}
profile = read(out / 'native-script-profile.json')
assert len(profile['opcodes']) == 32

# Keep fresh evidence beside the session, without copying original game binaries.
for name in ['capture-handlers.json', 'branch-handlers.json', 'capture-table-handlers.json']:
    shutil.copy2(out / 'bytecode-reader' / name, evidence / name)
reused = evidence / 'reused-evidence'
reused.mkdir(exist_ok=True)
for name in ['vm_a_pseudocode.json', 'vm_a_pseudocode.c', 'vm_a_info.json', 'opcode_metadata_bytes.json']:
    shutil.copy2(out / 'bytecode-reader' / 'rea-session' / name, reused / name)

validation = {
    'version': '0.3', 'execution_host': platform.node(),
    'finalized_utc': datetime.now(timezone.utc).isoformat(),
    'executable_sha256': expected, 'executable_unchanged': True,
    'rea_session_closed': True, 'tests_passed': 115, 'tests_skipped': 0,
    'parser_tests': 37, 'reconstruction_tests': 52, 'runtime_test_methods': 26,
    'focused_syntax_passed': 121, 'focused_lua51_compiled': 121,
    'corpus_lua51_compiled': 3276, 'profile_opcode_mappings': 32,
    'focused_samples': samples,
    'corpus': {'selected': 384, 'parsed': 383, 'functions': 4353, 'before_supported': 2248,
               'supported': 2893, 'unresolved': 1460, 'coverage_losses': 0},
    'input_hashes_rechecked': True, 'generated_artifact_hashes_rechecked': True,
    'generated_lua_executed_with_mock_apis': True,
    'game_launched': False, 'game_patched': False, 'native_runtime_equivalence_verified': False,
    'limitations': ['Supported bodies use explicit runtime domain guards.',
                    'Whole scripts and nested functions may retain unresolved error stubs.',
                    'Compilation does not establish game behavior or whole-game rebuildability.']
}
write(focus / 'validation.json', validation)
write(evidence / 'final-validation.json', validation)

project = read(out / 'project.json')
project['updated'] = datetime.now(timezone.utc).isoformat()
project['next_script_experiment'] = 'Confirm open argument/result lists, nonzero table hints/SETLIST, and numeric/generic loops; retain guarded native integer and custom-value domains'
project['script_parser'].update({
    'status': 'native-correlated structural reader with bounded wrapper metadata strings',
    'package': 'opem-amalur-script-tools-v0.3.zip', 'real_samples': 383,
    'functions': 4353, 'tests_passed': 37, 'complete_payload_consumption': True,
    'limitations': ['Exact observed header only', 'Nonempty debug and prototype sections unsupported',
                    'One of 384 selected wrappers unsupported', 'Metadata-string semantic role unverified'],
})
project['script_parser'].pop('instruction_words', None)
project['script_parser'].pop('constants', None)
project['lua_reconstruction'] = {
    'status': 'guarded branch, shared-capture, cached-call and selected-table reconstruction',
    'profile': 'native-script-profile.json', 'profile_opcode_mappings': 32,
    'source': str(root / 'src' / 'amalur_reconstruct.py'),
    'focused_samples': 4, 'focused_function_bodies': 167, 'focused_supported_bodies': 117,
    'original_baseline_supported_before': 101, 'original_baseline_supported_now': 115,
    'original_baseline_total': 161, 'corpus': validation['corpus'],
    'combined_tests_passed': 115, 'runtime_test_methods': 26,
    'focused_lua51_compiled': 121, 'corpus_lua51_compiled': 3276,
    'runtime_equivalence_verified': False, 'generated_code_executed_with_mocks': True,
    'generated_code_executed_in_game': False,
    'drafts_package': 'opem-amalur-corpus-drafts-v0.3.zip',
    'focused_drafts_package': 'opem-amalur-focused-drafts-v0.3.zip',
    'limitations': ['Explicit PC dispatcher, not recovered high-level structure',
                    'Open argument/result lists, numeric/generic loops, SETLIST and nonzero table hints unresolved',
                    'Native signed-integer arithmetic not emitted',
                    'Comparison/table/call domains guarded; actor/userdata behavior unverified',
                    'Unsupported bodies remain explicit error stubs; supported parents may have unresolved children',
                    'Standalone captures require shared cells and original environment']
}
project['branch_capture'] = {
    'session_closed': True, 'executable_unchanged': True, 'close_helper': '0x01081f30',
    'close_evidence_id': 'ev_1ff04a45181aeac01ce85b671cb59a66d1d10d06e7a778a1992b439d5cd46393',
    'evidence_package': 'opem-amalur-branch-capture-evidence.zip',
    'report': 'branch-capture-findings.md', 'validation': 'reconstruction-v03/validation.json'
}
write(out / 'project.json', project)

def package(filename, paths):
    target = out / filename
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        seen = set()
        for item in paths:
            for path in sorted(item.rglob('*')) if item.is_dir() else [item]:
                if not path.is_file() or '__pycache__' in path.parts or path.name == 'tests-first.txt':
                    continue
                relative = path.relative_to(root).as_posix()
                assert relative not in seen
                assert path.suffix not in ('.exe', '.lua_bxml', '.pak')
                seen.add(relative)
                archive.write(path, relative)
    with zipfile.ZipFile(target) as archive:
        assert archive.testzip() is None
    return {'file': filename, 'bytes': target.stat().st_size, 'sha256': digest(target), 'entries': len(seen)}

workflow = ['export_fragments.py', 'validate_lua.cjs', 'validate_lua51.py',
            'find_capture_samples.py', 'validate_capture_corpus.py', 'export_corpus_v03.py', 'finalize_v03.py']
tools_paths = [root / 'src' / n for n in ['amalur_script.py', 'amalur_reconstruct.py']]
tools_paths += [root / 'tests' / n for n in ['test_amalur_script.py', 'test_amalur_reconstruct.py',
                'test_amalur_lua_runtime.py', 'test_amalur_real_lua_runtime.py', 'test_amalur_table_runtime.py']]
tools_paths += [root / name for name in ['README.md', 'RECONSTRUCTION.md', 'BRANCH_CAPTURE.md']]
tools_paths += [out / name for name in ['native-script-profile.json', 'branch-capture-findings.md', 'project.json']]
tools_paths += [root / 'work' / name for name in workflow]
packages = [package('opem-amalur-script-tools-v0.3.zip', tools_paths),
            package('opem-amalur-focused-drafts-v0.3.zip', [focus]),
            package('opem-amalur-corpus-drafts-v0.3.zip', [corpus]),
            package('opem-amalur-branch-capture-evidence.zip', [evidence])]
write(out / 'v03-package-sha256.json', {'execution_host': platform.node(), 'packages': packages})
print(json.dumps({'validation': validation, 'packages': packages}, indent=2))
