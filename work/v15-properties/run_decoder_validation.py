from pathlib import Path
import io,json,sys,unittest,hashlib
r=Path.home()/'Documents/Opem Amalur';sys.path[:0]=[str(r/'work/v07-bxml'),str(r/'work/v13-properties'),str(r/'work/v15-properties')]
modules=['test_compiled_type','test_real_workbench','test_native_type_catalog'];suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(x) for x in modules);stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
o=r/'outputs/scene-v15';(o/'decoder-tests.txt').write_text(stream.getvalue());print(stream.getvalue())
if not result.wasSuccessful():raise SystemExit('Decoder validation failed')
summary=json.loads((o/'native-catalog-summary.json').read_text());assert summary['failed']==0 and summary['structurally_decoded']==27350 and not summary['missing']
proof=json.loads((o/'native-workbench-decoded.json').read_text());assert proof['capture_sha256']=='3aaa675201631ed6a3c27f15db2ed41cb0c317963f914acd2afd17822f55cbf7'
query=json.loads((r/'outputs/bytecode-reader/v15-interaction-resolver.json').read_text());expected=next(x['raw_hex'] for x in query['ranges'] if x['address']=='0x1001070')
trace=json.loads((o/'rea-runtime-early/trace_status.json').read_text())['structuredContent'];ready=next(m['payload'] for m in trace['normalized_result']['messages'] if m.get('payload',{}).get('event')=='trace_ready');assert ready['reader_bytes']==expected
report=dict(status='passed',unit_test_cases=result.testsRun,real_workbench_bytes=408,real_workbench_matches_both_archive_members=True,real_workbench_reader_memory_matches_pinned_executable=True,structurally_decoded_patch_types=27350,scene_objects=summary['selected_scene_objects'],scene_type_definitions=summary['selected_type_definitions_with_ancestors'],unresolved_compact_source_conversion=True,android_build=False,android_behavior_tested=False,limitations='Structural data validation and native Workbench observations; no gameplay or full component semantic parity')
(o/'decoder-validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
