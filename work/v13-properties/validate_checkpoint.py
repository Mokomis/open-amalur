from pathlib import Path
import hashlib,io,json,sys,unittest
r=Path.home()/'Documents/Opem Amalur';sys.path[:0]=[str(r/'work/v07-bxml'),str(r/'work/v13-properties')]
from compiled_type import decode_compiled_type,CompiledTypeError
import test_compiled_type
stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(test_compiled_type));print(stream.getvalue())
if not result.wasSuccessful():raise SystemExit('Contract checks failed')
o=r/'outputs/scene-v13';graph=json.loads((r/'outputs/scene-v12/type-graph.json').read_text());component_map=json.loads((o/'component-map.json').read_text());names={p['kind']:p['tables'][0]['name'] for p in component_map['components']};rejections=[]
for node in graph['nodes']:
 source=node['source'];batch=r/'work/scene-inputs-v09'/source['archive']/source['batch'];raw=batch.read_bytes()[source['offset']:source['offset']+source['bytes']]
 if len(raw)!=source['bytes'] or hashlib.sha256(raw).hexdigest()!=source['sha256']:raise ValueError('Original member provenance mismatch')
 try:decode_compiled_type(raw,names)
 except CompiledTypeError as exc:rejections.append(dict(type_id=node['type_id'],bytes=len(raw),sha256=source['sha256'],reason=str(exc)))
 else:raise ValueError('Compact source unexpectedly accepted as compiled Type')
manifest=json.loads((o/'interaction-manifest.json').read_text());assert manifest['counts']==dict(objects=21,type_nodes=33,original_scripts=11,native_component_kinds=43,enabled_dispatches=0)
report=dict(status='passed',contract_test_cases=result.testsRun,synthetic_fixture=True,real_compact_type_sources_hash_verified=len(rejections),compact_inputs_correctly_refused=rejections,manifest_counts=manifest['counts'],runtime_validation=False,android_build_or_install=False,scope='Parser contract and rejection safety; no successful real compiled Type fixture or gameplay claim')
(o/'decoder-validation.json').write_text(json.dumps(report,indent=2));(o/'decoder-tests.txt').write_text(stream.getvalue());print(json.dumps({k:v for k,v in report.items() if k!='compact_inputs_correctly_refused'}))
