"""Export reviewable function drafts from an existing reconstruction IR on Windows."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from amalur_reconstruct import emit_function

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('ir', type=Path)
parser.add_argument('destination', type=Path)
args = parser.parse_args()
data = json.loads(args.ir.read_text(encoding='utf-8'))
args.destination.mkdir(parents=True, exist_ok=False)
manifest = []

def visit(fn):
    if fn['body_emittable']:
        name = 'function_' + fn['path'].replace('/', '_') + '.lua'
        header = [
            '-- Opem Amalur standalone function draft; NOT an executable game replacement.',
            '-- Original input SHA-256: ' + data['input_sha256'],
            '-- Function path: ' + fn['path'],
            '-- Requires its original environment; child bodies may contain explicit unresolved stubs.',
            '-- Register names are generated. Static reconstruction, not runtime-equivalence proof.',
            '-- Captured functions return a factory accepting zero-indexed shared {value=...} cells.',
            'local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable',
            '',
        ]
        body = emit_function(fn)
        body[0] = 'return ' + body[0]
        (args.destination / name).write_text('\n'.join(header + body) + '\n', encoding='utf-8')
        manifest.append({'function_path': fn['path'], 'file': name,
                         'capture_factory': bool(fn.get('upvalue_count')),
                         'external_upvalue_cells_required': fn.get('upvalue_count', 0),
                         'body_emittable': True, 'standalone_environment_unresolved': True})
    for child in fn['children']:
        visit(child)

visit(data['root_function'])
(args.destination / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
print(json.dumps({'source_ir': str(args.ir), 'function_drafts': len(manifest)}))
