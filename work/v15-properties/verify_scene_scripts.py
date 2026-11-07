from pathlib import Path
import json,hashlib,sys
r=Path.home()/'Documents/Opem Amalur';sys.path.insert(0,str(r/'work/v15-properties'));from native_type_catalog import index_batch,member_bytes
selected=json.loads((r/'outputs/scene-v15/scene-native-types.json').read_text())['types'];ids=sorted({x['metadata']['script_id'] for x in selected if x['metadata']['script_id'] not in (0,1,0xffffffff)})
source=json.loads((r/'outputs/scene-v07/standalone-name-index.json').read_text(encoding='utf-8-sig'));by_file={x['file']:x for x in source};rows=[]
for archive in ['initial_0.pak','patch_0.pak']:
 p=r/'work/scene-inputs-v09'/archive/'134230570_klua.batch';data=p.read_bytes();batch=index_batch(data)
 for key in ids:
  original=by_file.get(f'{key}.lua_bxml');member=batch['members'].get(key)
  if original is None or member is None:raise ValueError(f'Missing scene script {key}')
  raw=member_bytes(data,member);digest=hashlib.sha256(raw).hexdigest()
  rows.append(dict(script_id=key,name=original['name'],archive=archive,batch='134230570_klua.batch',member=member,sha256=digest,recovered_input_sha256=original['sha256'],exact_match=digest==original['sha256']))
report=dict(script_ids=ids,scripts=len(ids),variants_checked=len(rows),exact_matches=sum(x['exact_match'] for x in rows),records=rows,scope='Runtime batch source-byte identity; no event execution or gameplay parity claim')
(r/'outputs/scene-v15/scene-script-source-verification.json').write_text(json.dumps(report,indent=2));print(json.dumps({k:v for k,v in report.items() if k!='records'}))
changed=r/'work/v15-properties/changed-script-inputs';changed.mkdir(exist_ok=True)
for row in rows:
 if row['exact_match']:continue
 data=(r/'work/scene-inputs-v09'/row['archive']/row['batch']).read_bytes();raw=member_bytes(data,row['member']);dest=changed/f"{row['script_id']}.lua_bxml"
 if dest.exists() and dest.read_bytes()!=raw:raise ValueError('Preserve differing changed script variant')
 dest.write_bytes(raw);row['isolated_input']=str(dest)
scene_path=r/'outputs/scene-v15/scene-native-interactions.json';scene=json.loads(scene_path.read_text());direct={x['native_script_id'] for x in scene['objects'] if x['native_script_id'] not in (0,1,0xffffffff)}
for obj in scene['objects']:
 matches=[x for x in rows if x['script_id']==obj['native_script_id']]
 obj['script_input_variants']=[dict(archive=x['archive'],sha256=x['sha256'],matches_recovered_input=x['exact_match']) for x in matches]
 obj['dependency_version_parity']='Not established solely by direct script input identity'
scene_path.write_text(json.dumps(scene,indent=2))
report['direct_scene_script_ids']=sorted(direct);report['direct_script_variants_checked']=sum(x['script_id'] in direct for x in rows);report['direct_script_mismatches']=[x for x in rows if x['script_id'] in direct and not x['exact_match']]
report['changed_ancestor_or_dependency_candidates']=sorted({x['script_id'] for x in rows if not x['exact_match'] and x['script_id'] not in direct});report['dependency_parity_established']=False
(r/'outputs/scene-v15/scene-script-source-verification.json').write_text(json.dumps(report,indent=2))
assert all(x['exact_match'] for x in rows if x['script_id']==237033)
print(json.dumps(dict(direct_scene_scripts=len(direct),direct_variants=report['direct_script_variants_checked'],direct_mismatches=len(report['direct_script_mismatches']),changed_ancestor_candidates=report['changed_ancestor_or_dependency_candidates'])))
p=r/'outputs/scene-v15/workbench-interaction-contract.json';contract=json.loads(p.read_text());contract['original_recovered_callback']['runtime_batch_byte_identity_verified']=True;contract['original_recovered_callback']['runtime_batch_evidence']='scene-script-source-verification.json';p.write_text(json.dumps(contract,indent=2))
