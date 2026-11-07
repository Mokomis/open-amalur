"""Read existing recovered alchemy drafts and bind their native batch identities.

Windows-only artifact processing. Never launches game, device or disassembler.
"""
import hashlib
import json
import platform
import shutil
import sys
from pathlib import Path

assert platform.system() == 'Windows', 'Run artifact processing on Windows'
root = Path.home() / 'Documents' / 'Opem Amalur'
out = root / 'outputs' / 'scene-v16-alchemy' / 'source-audit'
out.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(root / 'work/v15-properties'))
from native_type_catalog import index_batch, member_bytes

index = json.loads((root / 'outputs/scene-v07/standalone-name-index.json').read_text(encoding='utf-8-sig'))
manifest = json.loads((root / 'outputs/initial-corpus-drafts-v05/manifest.json').read_text(encoding='utf-8-sig'))
named = [r for r in index if any(s in str(r.get('name', '')).casefold() for s in ['alchemy', 'reagent', 'recipe'])]
batch_data = {}
for archive in ['initial_0.pak', 'patch_0.pak']:
    path = root / 'work/scene-inputs-v09' / archive / '134230570_klua.batch'
    if path.exists():
        data = path.read_bytes()
        batch_data[archive] = (data, index_batch(data))

rows = []
for row in named:
    result = dict(row)
    try:
        rid = int(Path(row['file']).name.split('.')[0])
    except (KeyError, ValueError):
        rid = None
    result['resource_id'] = rid
    result['runtime_variants'] = []
    for archive, (data, batch) in batch_data.items():
        member = batch['members'].get(rid)
        if member:
            raw = member_bytes(data, member)
            digest = hashlib.sha256(raw).hexdigest()
            result['runtime_variants'].append(dict(archive=archive, sha256=digest, bytes=len(raw), matches_recovered_input=digest == row['sha256']))
    frozen = root / 'outputs/initial-corpus-drafts-v05' / manifest['unique_scripts'][row['sha256']]['directory']
    destination = out / (str(rid) + '-' + row['name'])
    destination.mkdir(exist_ok=True)
    for filename in ['whole-script.lua', 'ir.json', 'summary.json']:
        path = frozen / filename
        if path.exists():
            shutil.copy2(path, destination / filename)
    result['local_source_directory'] = str(destination.relative_to(root))
    if (frozen / 'ir.json').exists():
        ir = json.loads((frozen / 'ir.json').read_text(encoding='utf-8-sig'))
        result['recovery_summary'] = ir.get('summary')
    rows.append(result)

(out / 'source-index.json').write_text(json.dumps(rows, indent=2), encoding='utf-8')
print(json.dumps(rows, indent=2))
