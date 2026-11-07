"""Bounded deterministic Windows-only corpus sampling for captured variables."""
import hashlib
import json
import random
import subprocess
import sys
from pathlib import Path

root = Path.home() / 'Documents' / 'Opem Amalur'
game = Path(r'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning')
sys.path.insert(0, str(root / 'src'))
from amalur_script import parse_file

out = root / 'outputs' / 'branch-capture'
out.mkdir(exist_ok=True)
destination = root / 'work' / 'capture-corpus'
destination.mkdir(exist_ok=False)
data = (root / 'outputs' / 'initial-archive-list.txt').read_bytes()
text = data.decode('utf-16' if data.startswith((b'\xff\xfe', b'\xfe\xff')) else 'utf-8-sig')
names = sorted({line.strip() for line in text.splitlines() if line.strip().endswith('.lua_bxml')})
order = names[:]
random.Random(20261029).shuffle(order)
records, found = [], []
for start in range(0, min(384, len(order)), 128):
    selected = order[start:start + 128]
    result = subprocess.run([str(game / 'modding' / 'pakfileunpacker.exe'),
                             str(game / 'data' / 'initial_0.pak'), 'unpack', str(destination), *selected],
                            cwd=str(game / 'modding'), capture_output=True, timeout=120)
    (out / ('capture-extract-' + str(start) + '.log')).write_bytes(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError('Unpacker failed: ' + str(result.returncode))
    for name in selected:
        path = destination / name
        try:
            parsed = parse_file(path)
            captures = []
            def visit(fn, fnpath):
                if fn['upvalue_count']:
                    captures.append({'function': fnpath, 'upvalues': fn['upvalue_count'],
                                     'instructions': len(fn['instructions'])})
                for i, child in enumerate(fn['children']):
                    visit(child, fnpath + '/' + str(i))
            visit(parsed['chunk']['root_function'], '0')
            item = {'file': name, 'bytes': path.stat().st_size, 'sha256': parsed['input_sha256'],
                    'name': parsed['wrapper']['name'] if parsed['wrapper'] else None,
                    'summary': parsed['chunk']['summary'], 'captured_functions': captures}
            if captures:
                found.append(item)
                (out / (path.stem + '.parsed.json')).write_text(json.dumps(parsed, indent=2), encoding='utf-8')
        except (OSError, ValueError) as exc:
            item = {'file': name, 'error': str(exc)}
        records.append(item)
    if found:
        break
report = {'sampling': 'sorted archive names, shuffled with random seed20261029; batches128, stop after first capture-bearing batch, max384',
          'archive_scripts': len(names), 'selected': len(records), 'parsed': sum('error' not in r for r in records),
          'capture_bearing': found, 'records': records}
(out / 'capture-corpus-inventory.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps({k: v for k, v in report.items() if k != 'records'}, indent=2))
