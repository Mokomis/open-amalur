"""Preserve scene-to-script candidates without dispatching unverified callbacks."""
from pathlib import Path
import hashlib
import json
import re
import struct
import sys

root = Path.home() / 'Documents/Opem Amalur'
out = root / 'outputs/scene-v13'
sys.path.insert(0, str(root / 'work/v07-bxml'))
from amalur_blob import parse_bytes

objects = json.loads((root / 'outputs/scene-v12/scene-objects.json').read_text())
graph = json.loads((root / 'outputs/scene-v12/type-graph.json').read_text())
nodes = {n['type_id']: n for n in graph['nodes']}
index = json.loads((root / 'outputs/scene-v07/standalone-name-index.json').read_text(encoding='utf-8-sig'))
script_sources = {}
for entry in index:
    name = str(entry.get('name', '')).lower()
    script_sources.setdefault(name, []).append(entry)

scripts = []
for item in graph['scripts']:
    matches = script_sources.get(item['name'].lower(), [])
    hashes = {x['sha256'] for x in matches}
    if len(hashes) != 1:
        raise ValueError(f'Ambiguous or absent recovered script: {item}')
    input_sha = next(iter(hashes))
    path = root / 'outputs/initial-corpus-drafts-v05/scripts' / input_sha / 'whole-script.lua'
    raw = path.read_bytes()
    text = raw.decode('utf-8')
    literals = set(re.findall(r'\["([A-Za-z_][A-Za-z0-9_]*)"\]', text))
    scripts.append(dict(id=item['id'], name=item['name'], input_sha256=input_sha,
                        recovered_source_sha256=hashlib.sha256(raw).hexdigest(),
                        recovered_source=str(path),
                        literal_callback_keys=sorted(x for x in literals if x.startswith('on_')),
                        literal_environment_globals=sorted(set(re.findall(
                            r'__getfenv\(1\)\["([^"]+)"\]', text))),
                        callback_analysis='Literal keys only; callback availability and behavior not validated'))

records = []
for obj in objects['objects']:
    chain, seen, key = [], set(), obj['type_id']
    while key not in (0, 1, 0xffffffff):
        if key in seen or key not in nodes:
            raise ValueError('Missing or cyclic candidate ancestry')
        seen.add(key)
        n = nodes[key]
        chain.append(dict(type_id=key, name=n['name'], script_candidate=n['script_candidate'],
                          script_name=n['script_name'], source=n['source']))
        key = n['parent_candidate']
    candidates = [dict(type_id=n['type_id'], script_id=n['script_candidate'],
                       script_name=n['script_name']) for n in chain if n['script_name']]
    records.append(dict(instance_id=obj['instance_id'], name=obj['name'], type_id=obj['type_id'],
                        position_xyz=obj['position_xyz'], candidate_ancestry=chain,
                        script_candidates=candidates, dispatch_enabled=False,
                        blocked_by=['Compact SimType property conversion not recovered',
                                    'Native instance-state binding not implemented',
                                    'Required gameplay/UI services not established']))

parts = json.loads((out / 'component-map.json').read_text())
for part in parts['components']:
    for table in part['tables']:
        # Only the four confirmed blueprint virtual slots; following words can
        # belong to an adjacent vtable or ordinary data.
        table['slots'] = {k: v for k, v in table['slots'].items() if int(k, 0) < 16}
(out / 'component-map.json').write_text(json.dumps(parts, indent=2))
names = {p['kind']: p['tables'][0]['name'] for p in parts['components']}
partsets = []
for filename in ['8129.partset_bxml', '8119.partset_bxml']:
    raw = (root / 'work/scene-inputs-v09/initial_0.pak' / filename).read_bytes()
    carrier = parse_bytes(raw)
    ptr, count = struct.unpack_from('<II', raw, 8)
    end = 8 + carrier['header']['payload_bytes']
    if count > 43 or ptr < 8 or ptr + count * 4 > end:
        raise ValueError('Partset observation bounds')
    values = list(struct.unpack_from('<' + 'I' * count, raw, ptr))
    if any(v not in names for v in values):
        raise ValueError('Partset values outside mapped component kinds')
    partsets.append(dict(file=filename, sha256=hashlib.sha256(raw).hexdigest(),
                         observed_values=values, matching_native_component_names=[names[v] for v in values],
                         status='Array layout observed; component-list role is an inference, native partset consumer untraced'))

manifest = dict(status='research-only; original interactions are not connected',
                source_scene_sha256=objects['source_sha256'], objects=records, scripts=scripts,
                partset_observations=partsets,
                counts=dict(objects=len(records), type_nodes=len(nodes), original_scripts=len(scripts),
                            native_component_kinds=len(parts['components']), enabled_dispatches=0),
                limitations=['Candidate parent/script prefix fields are not native-confirmed.',
                             'No callback inheritance or dispatch semantics are assumed.',
                             'Workbench opens an alchemy UI whose Android backend is not implemented.',
                             'No tablet changes, gameplay input or successful native service stubs.'])
(out / 'interaction-manifest.json').write_text(json.dumps(manifest, indent=2))
print(json.dumps(manifest['counts']))
