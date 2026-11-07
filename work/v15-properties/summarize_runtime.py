from pathlib import Path
import json
r=Path.home()/'Documents/Opem Amalur';p=r/'outputs/scene-v15/rea-runtime-replacement/trace_status.json';e=json.loads(p.read_text())['structuredContent'];n=e['normalized_result'];rows={}
for m in n['messages']:
 x=m.get('payload',{})
 if x.get('event')=='selected_runtime_type':
  if x['id'] in rows and rows[x['id']]!=x:raise ValueError('Selected runtime type changed across snapshots')
  rows[x['id']]=x
assert rows[230417]['parent_source_key']==226948 and rows[230417]['script_source_key']==237033
assert rows[230417]['header'][10]==len(rows[230417]['parts'])==7
out=dict(evidence_id=e['evidence_id'],original_process=n['pid'],source_snapshot_scope='loaded native Type payload after inheritance/finalization; not original compact parsing',type_records=list(rows.values()),workbench_native_confirmed=dict(type_id=230417,parent_type_id=226948,script_id=237033,resolved_component_kinds=[x['kind'] for x in rows[230417]['parts']],flags_word_offset_hex='0x1c',flags_value=rows[230417]['header'][7]),limitations=['No original compact byte-consumption path observed yet.','Array index-to-source-key mapping follows native catalog initialization0xa732d0.','No interaction callback or gameplay input invoked.'])
(r/'outputs/scene-v15/selected-runtime-types.json').write_text(json.dumps(out,indent=2));print(json.dumps(out['workbench_native_confirmed']))
