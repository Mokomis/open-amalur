"""Compare v0.2 and current reconstruction on the bounded Windows corpus."""
import collections
import importlib.util
import json
import sys
import time
from pathlib import Path

root = Path.home() / 'Documents' / 'Opem Amalur'
sys.path.insert(0, str(root / 'src'))
from amalur_script import parse_file
from amalur_reconstruct import reconstruct

spec = importlib.util.spec_from_file_location('baseline_reconstruct', root / 'work' / 'baseline-v02' / 'amalur_reconstruct.py')
baseline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(baseline)
old_profile = json.loads((root / 'work' / 'baseline-v02' / 'native-script-profile.json').read_text())
new_profile = json.loads((root / 'outputs' / 'native-script-profile.json').read_text())
out = root / 'outputs' / 'branch-capture'
inventory = json.loads((out / 'capture-corpus-inventory.json').read_text())
records, captures, losses = [], [], []
totals = collections.Counter()
started = time.monotonic()

def functions(fn, path='0'):
    yield path, fn
    for i, child in enumerate(fn['children']):
        yield from functions(child, path + '/' + str(i))

for item in inventory['records']:
    if time.monotonic() - started > 180:
        raise RuntimeError('Corpus validation budget exceeded')
    filename = item['file']
    try:
        parsed = parse_file(root / 'work' / 'capture-corpus' / filename)
        captured = [{'path': path, 'upvalues': fn['upvalue_count'], 'instructions': len(fn['instructions'])}
                    for path, fn in functions(parsed['chunk']['root_function']) if fn['upvalue_count']]
        entry = {'file': filename, 'name': parsed['wrapper']['name'], 'sha256': parsed['input_sha256'],
                 'metadata_strings': parsed['wrapper']['metadata_string_count'],
                 'functions': parsed['chunk']['summary']['functions'], 'captured_functions': captured}
        totals['parsed'] += 1
        totals['wrapper_metadata_strings'] += bool(entry['metadata_strings'])
        if captured:
            captures.append(entry)
        for label, runner, profile in [('before', baseline.reconstruct, old_profile), ('after', reconstruct, new_profile)]:
            try:
                ir, _ = runner(parsed, profile)
                entry[label] = ir['summary']
                totals[label + '_eligible'] += ir['summary']['emittable_function_bodies']
                totals[label + '_unresolved'] += ir['summary']['unresolved_function_bodies']
            except (ValueError, KeyError) as exc:
                entry[label + '_error'] = str(exc)
                totals[label + '_errors'] += 1
        if 'before' in entry and 'after' in entry and entry['after']['emittable_function_bodies'] < entry['before']['emittable_function_bodies']:
            losses.append(entry)
    except (ValueError, OSError) as exc:
        entry = {'file': filename, 'parse_error': str(exc)}
        totals['parse_errors'] += 1
    records.append(entry)

for entry in sorted(captures, key=lambda x: x['functions'])[:3]:
    parsed = parse_file(root / 'work' / 'capture-corpus' / entry['file'])
    (out / (Path(entry['file']).stem + '.parsed.json')).write_text(json.dumps(parsed, indent=2), encoding='utf-8')
    ir, source = reconstruct(parsed, new_profile)
    (out / (Path(entry['file']).stem + '.ir.json')).write_text(json.dumps(ir, indent=2), encoding='utf-8')
    (out / (Path(entry['file']).stem + '.lua')).write_text(source, encoding='utf-8')

report = {'selected': len(records), 'totals': dict(totals), 'capture_bearing': captures,
          'coverage_losses': losses, 'records': records, 'elapsed_seconds': time.monotonic() - started}
(out / 'corpus-comparison.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps({k: v for k, v in report.items() if k != 'records'}, indent=2))
