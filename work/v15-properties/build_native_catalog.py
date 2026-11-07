"""Read compiled runtime types from existing archives; never enable dispatch."""
from pathlib import Path
import collections,csv,hashlib,json,sys,time
root=Path.home()/'Documents/Opem Amalur'
sys.path[:0]=[str(root/'work/v07-bxml'),str(root/'work/v13-properties'),str(root/'work/v15-properties')]
from compiled_type import CompiledTypeError
from native_type_catalog import index_batch,member_bytes,decode_type
out=root/'outputs/scene-v15';started=time.monotonic()
component_map=json.loads((root/'outputs/scene-v13/component-map.json').read_text())['components']
names={p['kind']:p['tables'][0]['name'] for p in component_map}
symbols=root/'references/ZucchiniZap--AmalurBxmlConverter/bin/Release/net10.0-windows/symbol_tables'
def symbols_for(name):
 return {int(x['id']):x['value'] for x in csv.DictReader((symbols/(name+'.csv')).open(encoding='utf-8-sig'))}
type_names=symbols_for('simtype');script_names=symbols_for('luascript');interaction_names=symbols_for('interaction')
scene=json.loads((root/'outputs/scene-v12/scene-objects.json').read_text());roots={x['type_id'] for x in scene['objects']}
expected={'initial_0.pak':'e5933313691435758fc6dc473c7d07c66397eb3824cda76b83f3e4dc7d3264af','patch_0.pak':'09dff529684d2deef530a418c11b0729fedb6b89f85e61cdd84f04f18942268c'}
capture=(root/'work/v15-properties/native-workbench-230417.bin').read_bytes();variants={};provenance=[]
for archive,digest in expected.items():
 data=(root/'work/scene-inputs-v09'/archive/'134225858_ksmt.batch').read_bytes();index=index_batch(data)
 if index['input_sha256']!=digest:raise ValueError('Compiled batch provenance mismatch')
 member=member_bytes(data,index['members'][230417])
 if member!=capture:raise ValueError('Archive Workbench does not match native capture')
 variants[archive]=(data,index)
 provenance.append(dict(archive=archive,file='134225858_ksmt.batch',sha256=digest,bytes=len(data),members=index['count'],workbench_equals_native_capture=True))
# Keep both variants. The patch profile has the same27350 resource count as the
# captured manager's27352 entries, including its two reserved indices.
data,index=variants['patch_0.pak'];rows=[];failures=[];selected={};counts=collections.Counter();decoded_by_id={}
for key,entry in index['members'].items():
 raw=member_bytes(data,entry)
 try:decoded=decode_type(raw,names)
 except CompiledTypeError as exc:
  failures.append(dict(type_id=key,offset=entry['offset'],bytes=entry['bytes'],error=str(exc)));continue
 kinds=[x['kind'] for x in decoded['components']];counts.update(kinds)
 row=dict(type_id=key,name=type_names.get(key),parent_type_id=decoded['parent_key_u32'],script_id=decoded['script_key_u32'],script_name=script_names.get(decoded['script_key_u32']),type_flags_u32=decoded['header_words_u32'][7],component_kinds=kinds,interaction_reference_keys=[ref for p in decoded['components'] if p['kind']==34 for ref in p['reference_keys_u32']],source=dict(archive='patch_0.pak',batch='134225858_ksmt.batch',offset=entry['offset'],bytes=entry['bytes'],sha256=decoded['input_sha256']))
 rows.append(row);decoded_by_id[key]=row
 if key in roots:selected[key]=decoded
queue=collections.deque(roots);visited=set();missing=[]
while queue:
 key=queue.popleft()
 if key in visited or key in (0,1,0xffffffff):continue
 if len(visited)>=256:raise ValueError('Scene ancestry scope exceeded')
 visited.add(key);row=decoded_by_id.get(key)
 if row is None:missing.append(key);continue
 if key not in selected:selected[key]=decode_type(member_bytes(data,index['members'][key]),names)
 queue.append(row['parent_type_id'])
selected_records=[dict(metadata=decoded_by_id[k],decoded=selected[k]) for k in sorted(selected)]
compact=json.loads((root/'outputs/scene-v12/type-graph.json').read_text());compact_nodes={n['type_id']:n for n in compact['nodes']};comparisons=[]
for key in sorted(selected):
 native=decoded_by_id[key];old=compact_nodes.get(key)
 if old:comparisons.append(dict(type_id=key,compact_bytes=old['source']['bytes'],compiled_bytes=native['source']['bytes'],parent_same=old['parent_candidate']==native['parent_type_id'],compact_script_candidate=old['script_candidate'],compiled_script_key=native['script_id']))
script_index=json.loads((root/'outputs/scene-v07/standalone-name-index.json').read_text(encoding='utf-8-sig'));by_name=collections.defaultdict(list)
for entry in script_index:by_name[str(entry.get('name','')).lower()].append(entry)
objects=[]
for obj in scene['objects']:
 row=decoded_by_id.get(obj['type_id'])
 if row is None:continue
 script=row['script_name'];sources=by_name.get(str(script).lower(),[]);hashes=sorted({x['sha256'] for x in sources})
 objects.append(dict(instance_id=obj['instance_id'],name=obj['name'],position_xyz=obj['position_xyz'],type_id=obj['type_id'],native_parent_type_id=row['parent_type_id'],native_script_id=row['script_id'],script_name=script,recovered_script_input_hashes=hashes,component_kinds=row['component_kinds'],interaction_definitions=[dict(key=ref,name=interaction_names.get(ref)) for ref in row['interaction_reference_keys']],source=row['source'],dispatch_enabled=False,remaining_work='Instance-state services and original UI/gameplay backends; other component fields remain opaque'))
summary=dict(status='native compiled batch located and Workbench byte identity verified',profile='patch compiled Type catalog; base variant retained separately',native_count_correspondence=dict(batch_members=index['count'],captured_manager_entries=27352,reserved_indices=2),structurally_decoded=len(rows),failed=len(failures),failures=failures,selected_scene_objects=len(objects),selected_type_definitions_with_ancestors=len(selected),missing=missing,component_instances_by_kind=dict(sorted(counts.items())),source_variants=provenance,elapsed_seconds=time.monotonic()-started,limitations=['Workbench input matches actual native Type reader and live object. Other types use that native-confirmed structural contract; not per-type runtime behavior tests.','Component payload fields remain opaque except native-confirmed references; this is not full gameplay reconstruction.','The compact SimType source format is preserved and not claimed decoded.','No archive precedence or optional DLC entitlement is inferred from file presence.','No interaction callback or Android feature is enabled by this catalog.'])
(out/'native-type-index.json').write_text(json.dumps(dict(summary=summary,types=rows),indent=2));(out/'scene-native-types.json').write_text(json.dumps(dict(summary=summary,types=selected_records,compact_comparison=comparisons),indent=2));(out/'scene-native-interactions.json').write_text(json.dumps(dict(source_scene_sha256=scene['source_sha256'],objects=objects,object_count=len(objects),native_runtime_verified_type_id=230417,dispatch_enabled=False),indent=2));(out/'native-catalog-summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps({k:v for k,v in summary.items() if k not in ['component_instances_by_kind','source_variants','limitations','failures']},indent=2))
if failures or missing:raise SystemExit('See explicit structural failures or missing scene types')
