"""Refresh scripts affected by large dispatch or the observed flags3 vararg mode."""
import collections
import hashlib
import json
import sys
from pathlib import Path
root=Path.home()/'Documents'/'Opem Amalur'
sys.path.insert(0,str(root/'src'))
from amalur_script import parse_file
from amalur_reconstruct import reconstruct,emit_function
profile=json.loads((root/'outputs/native-script-profile.json').read_text())
out=root/'outputs/initial-corpus-drafts-v04'
manifest=json.loads((out/'manifest.json').read_text())
inventory_path=root/'outputs/initial-corpus-v04/inventory.json'
inventory=json.loads(inventory_path.read_text())
inventory_records={r['file']:r for r in inventory['records']}
def visit(fn):
    yield fn
    for child in fn['children']:yield from visit(child)
changed=[]
for record in manifest['records']:
    if record['status']!='exported':continue
    directory=out/Path(record['file']).stem
    old=json.loads((directory/'ir.json').read_text())
    affected=(record['file']=='13158.lua_bxml' or any(f['body_emittable'] and (sum(bool(r['reachable']) for r in f['instructions'])>1000 or any(r.get('kind') in {'forprep','forloop','integer_division'} for r in f['instructions'])) for f in visit(old['root_function'])))
    if not affected:continue
    parsed=parse_file(root/'work/initial-script-corpus-v04'/record['file'])
    assert parsed['input_sha256']==record['input_sha256']
    ir,lua=reconstruct(parsed,profile)
    (directory/'whole-script.lua').write_text(lua,encoding='utf-8')
    (directory/'ir.json').write_text(json.dumps(ir,indent=2),encoding='utf-8')
    drafts=[]
    for fn in visit(ir['root_function']):
        if not fn['body_emittable']:continue
        filename='function_'+fn['path'].replace('/','_')+'.lua'
        header=['-- Opem Amalur guarded function draft, not original source or a game-ready replacement.',
                '-- Input SHA-256: '+ir['input_sha256'],'-- Function path: '+fn['path'],
                '-- Original environment required; captured bodies return factories accepting shared cells.',
                '-- Nested children may remain explicit error stubs. Runtime domains are guarded.',
                'local __getfenv, __unresolved, __type, __getmetatable = getfenv, error, type, getmetatable','']
        body=emit_function(fn);body[0]='return '+body[0]
        destination=directory/'functions'/filename
        destination.write_text('\n'.join(header+body)+'\n',encoding='utf-8')
        drafts.append({'path':fn['path'],'file':filename,'sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),
                       'capture_cells_required':fn.get('upvalue_count',0)})
    record.update(summary=ir['summary'],drafts=drafts)
    inventory_records[record['file']]['after']=ir['summary']
    changed.append({'file':record['file'],'summary':ir['summary']})
    print('refreshed',record['file'],flush=True)
manifest['function_drafts']=sum(len(r.get('drafts',[])) for r in manifest['records'])
manifest['draft_hash_encoding']='SHA-256 of actual file bytes, including Windows line endings'
(out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
t=inventory['totals']
t['after_supported']=sum(r['after']['emittable_function_bodies'] for r in inventory['records'] if 'after'in r)
t['after_unresolved']=sum(r['after']['unresolved_function_bodies'] for r in inventory['records'] if 'after'in r)
t['complete_scripts']=sum(r['after']['unresolved_function_bodies']==0 for r in inventory['records'] if 'after'in r)
features=collections.Counter();unknowns=collections.Counter()
for record in manifest['records']:
    if record['status']!='exported':continue
    ir=json.loads((out/Path(record['file']).stem/'ir.json').read_text())
    for fn in visit(ir['root_function']):
        if fn['body_emittable']:
            kinds={r.get('kind') for r in fn['instructions'] if r['reachable']}
            features.update(kinds&{'forprep','tforloop','vararg','setlist','integer_division'})
            if any('open_read_start'in r or ('open_top_effect'in r and r['open_top_effect'] is not None) for r in fn['instructions']):features['open_lists']+=1
        else:unknowns.update(set(u['reason'] for u in fn['unknowns']))
inventory['supported_body_features']=dict(features)
inventory['unknown_reasons']=dict(unknowns.most_common())
inventory['export_refresh']={'reason':'large-function tail dispatcher, observed vararg flags3, and canonical integer zero','scripts':changed}
inventory_path.write_text(json.dumps(inventory,indent=2),encoding='utf-8')
print(json.dumps({'totals':t,'features':dict(features),'refreshed_scripts':len(changed)},indent=2))
