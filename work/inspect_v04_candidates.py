import collections
import json
import sys
from pathlib import Path
root=Path.home()/'Documents'/'Opem Amalur'
sys.path.insert(0,str(root/'src'))
from amalur_script import parse_file
from amalur_reconstruct import reconstruct,emit_function
profile=json.loads((root/'outputs/native-script-profile.json').read_text())
out=root/'outputs/reconstruction-v04'
out.mkdir(exist_ok=True)
def visit(fn):
    yield fn
    for child in fn['children']:yield from visit(child)
for name,source in [('small','script-samples/1596600.lua_bxml'),('sq02','script-samples/441939.lua_bxml'),('third','script-samples/1701254.lua_bxml'),('ayten','capture-corpus/1378937.lua_bxml')]:
    parsed=parse_file(root/'work'/source)
    ir,lua=reconstruct(parsed,profile)
    (out/(name+'.ir.json')).write_text(json.dumps(ir,indent=2),encoding='utf-8')
    (out/(name+'.lua')).write_text(lua,encoding='utf-8')
    print(name,json.dumps(ir['summary']))
report=json.loads((root/'outputs/loops-openlists/corpus-comparison.json').read_text())
counts=collections.Counter(); reasons=collections.Counter(); candidates=[]
for record in report['records']:
    if 'parse_error' in record:continue
    parsed=parse_file(root/'work/capture-corpus'/record['file'])
    ir,lua=reconstruct(parsed,profile)
    for fn in visit(ir['root_function']):
        if not fn['body_emittable']:
            reasons.update(set(u['reason'] for u in fn['unknowns']))
            continue
        kinds={r.get('kind') for r in fn['instructions'] if r['reachable']}
        features=sorted(kinds&{'forprep','forloop','tforloop','vararg'})
        if any('open_read_start' in r or ('open_top_effect' in r and r['open_top_effect'] is not None) for r in fn['instructions']):features.append('open_lists')
        counts.update(features)
        if features:
            candidates.append({'file':record['file'],'name':record['name'],'input_sha256':ir['input_sha256'],
                               'path':fn['path'],'features':features,'instruction_count':len(fn['instructions']),'function':fn})
candidates.sort(key=lambda r:(r['instruction_count'],r['file'],r['path']))
chosen=[]
for feature in ['forprep','tforloop','open_lists','vararg']:
    chosen.extend([c for c in candidates if feature in c['features']][:4])
result={'counts':dict(counts),'remaining_reasons':dict(reasons.most_common()),'candidates':chosen}
(root/'outputs/loops-openlists/candidates.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({'counts':dict(counts),'remaining_reasons':dict(reasons.most_common(10)),
                  'candidates':[{k:v for k,v in c.items() if k!='function'} for c in chosen]},indent=2))
