"""Materialize the supported bodies from the already-bounded Windows corpus."""
import hashlib
import json
import sys
from pathlib import Path

root = Path.home() / 'Documents' / 'Opem Amalur'
sys.path.insert(0, str(root / 'src'))
from amalur_script import parse_file
from amalur_reconstruct import reconstruct, emit_function

out = root / 'outputs' / 'corpus-drafts-v04'
out.mkdir(exist_ok=False)
profile = json.loads((root / 'outputs' / 'native-script-profile.json').read_text())
comparison = json.loads((root / 'outputs' / 'loops-openlists' / 'corpus-comparison.json').read_text())
records = []
drafts = 0
for entry in comparison['records']:
    if 'parse_error' in entry:
        records.append({'file': entry['file'], 'status': 'unsupported_wrapper', 'reason': entry['parse_error']})
        continue
    source = root / 'work' / 'capture-corpus' / entry['file']
    parsed = parse_file(source)
    assert parsed['input_sha256'] == entry['sha256']
    ir, lua = reconstruct(parsed, profile)
    assert ir['summary'] == entry['after']
    directory = out / Path(entry['file']).stem
    directory.mkdir()
    (directory / 'whole-script.lua').write_text(lua, encoding='utf-8')
    (directory / 'ir.json').write_text(json.dumps(ir, indent=2), encoding='utf-8')
    functions_dir = directory / 'functions'
    functions_dir.mkdir()
    exported = []
    def visit(fn):
        if fn['body_emittable']:
            filename = 'function_' + fn['path'].replace('/', '_') + '.lua'
            header = [
                '-- Opem Amalur guarded function draft, not original source or a game-ready replacement.',
                '-- Input SHA-256: ' + ir['input_sha256'],
                '-- Function path: ' + fn['path'],
                '-- Original environment required; captured bodies return factories accepting shared cells.',
                '-- Nested children may remain explicit error stubs. Runtime domains are guarded.',
                'local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable',
                '',
            ]
            body = emit_function(fn)
            body[0] = 'return ' + body[0]
            text = '\n'.join(header + body) + '\n'
            (functions_dir / filename).write_text(text, encoding='utf-8')
            exported.append({'path': fn['path'], 'file': filename,
                             'sha256': hashlib.sha256((functions_dir / filename).read_bytes()).hexdigest(),
                             'capture_cells_required': fn.get('upvalue_count', 0)})
        for child in fn['children']:
            visit(child)
    visit(ir['root_function'])
    assert len(exported) == ir['summary']['emittable_function_bodies']
    drafts += len(exported)
    records.append({'file': entry['file'], 'name': entry['name'], 'status': 'exported',
                    'input_sha256': ir['input_sha256'], 'summary': ir['summary'], 'drafts': exported})
report = {'selected_scripts': len(records), 'parsed_scripts': sum(r['status'] == 'exported' for r in records),
          'function_drafts': drafts, 'whole_script_outputs': sum(r['status'] == 'exported' for r in records),
          'scope': 'Static guarded drafts; whole outputs can contain unresolved stubs; no game execution',
          'records': records}
(out / 'manifest.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
assert drafts == comparison['totals']['after_eligible']
print(json.dumps({k: v for k, v in report.items() if k != 'records'}))
