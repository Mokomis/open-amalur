"""Extract and analyze the complete known initial archive on Windows."""
import collections
import hashlib
import importlib.util
import json
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

assert platform.system()=='Windows'
root=Path.home()/'Documents'/'Opem Amalur'
game=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning')
sys.path.insert(0,str(root/'src'))
from amalur_script import parse_file
from amalur_reconstruct import reconstruct
spec=importlib.util.spec_from_file_location('baseline_v03',root/'work/baseline-v03/amalur_reconstruct.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
old_profile=json.loads((root/'work/baseline-v03/native-script-profile.json').read_text())
profile=json.loads((root/'outputs/native-script-profile.json').read_text())
out=root/'outputs/initial-corpus-v04';out.mkdir(exist_ok=False)
dest=root/'work/initial-script-corpus-v04';dest.mkdir(exist_ok=False)
raw=(root/'outputs/initial-archive-list.txt').read_bytes()
text=raw.decode('utf-16' if raw.startswith((b'\xff\xfe',b'\xfe\xff')) else 'utf-8-sig')
names=sorted({line.strip() for line in text.splitlines() if line.strip().endswith('.lua_bxml')})
assert len(names)==3457
assert all(Path(name).name==name for name in names)
missing=[]
for name in names:
    known=root/'work/capture-corpus'/name
    if known.exists():shutil.copy2(known,dest/name)
    else:missing.append(name)
for start in range(0,len(missing),128):
    result=subprocess.run([str(game/'modding/pakfileunpacker.exe'),str(game/'data/initial_0.pak'),
                           'unpack',str(dest),*missing[start:start+128]],cwd=game/'modding',
                          capture_output=True,timeout=120)
    (out/('extract-'+str(start)+'.log')).write_bytes(result.stdout+result.stderr)
    assert result.returncode==0, ('unpacker failed',result.returncode,start)
    print('extracted',min(start+128,len(missing)),'of',len(missing),'new scripts',flush=True)

records=[];totals=collections.Counter();unknown=collections.Counter();features=collections.Counter()
started=time.monotonic()
def functions(fn):
    yield fn
    for child in fn['children']:yield from functions(child)
for index,name in enumerate(names):
    record={'file':name,'sha256':hashlib.sha256((dest/name).read_bytes()).hexdigest()}
    try:
        parsed=parse_file(dest/name)
        record.update(name=parsed['wrapper']['name'] if parsed['wrapper'] else None,
                      functions=parsed['chunk']['summary']['functions'])
        totals['parsed_scripts']+=1;totals['parsed_functions']+=record['functions']
        for label,runner,selected in [('before',old.reconstruct,old_profile),('after',reconstruct,profile)]:
            try:
                ir,source=runner(parsed,selected)
                record[label]=ir['summary'];totals[label+'_scripts']+=1
                totals[label+'_supported']+=ir['summary']['emittable_function_bodies']
                totals[label+'_unresolved']+=ir['summary']['unresolved_function_bodies']
                if label=='after':
                    totals['complete_scripts']+=not ir['summary']['unresolved_function_bodies']
                    for fn in functions(ir['root_function']):
                        if fn['body_emittable']:
                            kinds={r.get('kind') for r in fn['instructions'] if r['reachable']}
                            features.update(kinds&{'forprep','tforloop','vararg','setlist','integer_division'})
                            if any('open_read_start' in r or ('open_top_effect' in r and r['open_top_effect'] is not None) for r in fn['instructions']):features['open_lists']+=1
                        else:unknown.update(set(u['reason'] for u in fn['unknowns']))
            except (ValueError,KeyError) as exc:
                record[label+'_error']=str(exc);totals[label+'_errors']+=1
    except (ValueError,OSError) as exc:
        record['parse_error']=str(exc);totals['parse_errors']+=1
    records.append(record)
    if (index+1)%256==0:print('analyzed',index+1,'of',len(names),flush=True)
report={'archive':'initial_0.pak','scope':'All .lua_bxml names in retained archive inventory; not all game archives',
        'scripts':len(names),'totals':dict(totals),'supported_body_features':dict(features),
        'unknown_reasons':dict(unknown.most_common()),'analysis_seconds':time.monotonic()-started,
        'records':records}
(out/'inventory.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='records'},indent=2))
