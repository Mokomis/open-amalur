"""Windows integrity, provenance and packaging for complete initial-script coverage."""
import hashlib,json,platform,re,shutil,zipfile
from pathlib import Path
from datetime import datetime,timezone
assert platform.system()=='Windows'
root=Path.home()/'Documents'/'Opem Amalur';out=root/'outputs';full=out/'initial-corpus-drafts-v05';ev=out/'remaining-v05'
expected='16a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n',encoding='utf-8')
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
exe=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning\koa.exe')
assert sha(exe)==expected
assert read(ev/'rea-session/status.json')['state']=='closed'
i=read(ev/'rea-session/input-integrity.json');assert i['unchanged'] and i['sha256_before']==i['sha256_after']==expected
for filename,count in [('tests-final-core.txt',277),('tests-parser-final.txt',68),('tests-cache.txt',16)]:
 t=(ev/filename).read_text(encoding='utf-8-sig');assert f'Ran {count} tests in ' in t and t.rstrip().endswith('OK') and 'skipped=' not in t
manifest=read(full/'manifest.json');checks=read(full/'lua51-compile-validation.json')
assert not manifest['errors'] and len(manifest['unique_scripts'])==6151 and len(manifest['bindings'])==9815
assert manifest['unique_totals']['functions']==manifest['unique_totals']['emittable_function_bodies']==68530
assert manifest['unique_totals'].get('unresolved_function_bodies',0)==0
assert checks['files']==checks['passed']==len(checks['checks'])==74681
actual={p.relative_to(full).as_posix() for p in full.rglob('*.lua')};assert actual=={r['file'] for r in checks['checks']}
for r in checks['checks']:assert r['compiled'] and sha(full/r['file'])==r['sha256']
print('All 74,681 compiled file hashes verified.',flush=True)
baseline=read(out/'initial-corpus-v04/inventory.json')
for r in baseline['records']:assert sha(root/'work/initial-script-corpus-v04'/r['file'])==r['sha256']
assert len(baseline['records'])==3457
for h,rec in manifest['unique_scripts'].items():
 ir=read(full/rec['directory']/'ir.json');assert ir['input_sha256']==h and ir['summary']==rec['summary']
 def verify(fn):
  assert fn['body_emittable'] and not fn['unknowns']
  for ch in fn['children']:verify(ch)
 verify(ir['root_function'])
print('Every function IR and all original input hashes verified.',flush=True)
profile=read(out/'native-script-profile.json');sources=[root/'src'/n for n in ['amalur_script.py','amalur_reconstruct.py','cache_flow.py','amalur_uint64.lua']]
alltests=sorted((root/'tests').glob('test_*.py'))
validation={'version':'0.5','execution_host':platform.node(),'finalized_utc':datetime.now(timezone.utc).isoformat(),
 'target_sha256':expected,'target_unchanged':True,'all_3457_extracted_inputs_unchanged':True,'rea_session_closed':True,
 'core_test_methods_passed':277,'parser_bundle_token_test_methods_passed':68,'cache_dataflow_test_methods_passed':16,
 'unique_test_methods_passed':324,'test_accounting':'37 structural tests overlap core and parser suites; 277+68+16-37=324 distinct methods.',
 'semantic_opcode_mappings':len(profile['opcodes']),'original_unresolved_before':2997,'original_unresolved_after':0,
 'standalone_function_instances':42060,'bundle_function_occurrences':51828,'bundle_containers':12,'bundle_member_occurrences':6370,
 'distinct_wrapped_inputs':6151,'distinct_input_function_bodies':68530,'generated_lua_files':74681,'lua51_compiled':74681,
 'source_and_test_sha256':{p.relative_to(root).as_posix():sha(p) for p in sources+alltests},
 'generated_code_executed_with_mocks':True,'game_launched':False,'game_patched':False,'native_runtime_equivalence_verified':False,
 'limits':['Initial_0.pak only, not all archives or native engine.',
           'Generated register-level source with runtime guards, not original source.',
           'Type11 values require shared opaque userdata adapter plus explicit engine bindings; no floating-point ID conversion.',
           'Custom types, metamethods, coercions and runtime paths outside admitted domains remain explicit errors.',
           'Batch storage layout confirmed by complete parsing; native batch loading order not traced.',
           'Large-dispatch environment synchronization checked on normal completion, not errors or yields.']}
write(ev/'validation.json',validation);write(full/'validation.json',validation)
shutil.copy2(root/'README-v05.txt',full/'README.txt')
# Runtime included next to the corpus without changing the validated generated-Lua set.
(full/'runtime').mkdir(exist_ok=True);shutil.copy2(root/'src/amalur_uint64.lua',full/'runtime/amalur_uint64.lua.txt')
reused=ev/'reused-evidence';reused.mkdir(exist_ok=True)
for name in ['vm_a_pseudocode.json','vm_a_pseudocode.c','constant_reader_pseudocode.c','constant_reader.json']:
 p=out/'bytecode-reader/rea-session'/name
 if p.exists():shutil.copy2(p,reused/name)
for p in (out/'bytecode-reader').glob('*.json'):
 if p.stem.startswith(('v05-','remaining-v05-')):shutil.copy2(p,ev/p.name)
for name in ['lua_call_setup.json','table_list_writer.json']:
 p=root/'work/openlist-audit'/name
 if p.exists():shutil.copy2(p,reused/name)
project=read(out/'project.json');project['updated']=validation['finalized_utc']
project['next_script_experiment']='Build native-runtime differential checks and engine-binding contract for guarded drafts, then high-level control-flow recovery and other archives.'
project['script_parser'].update(status='complete observed initial archive including all12 batch wrappers',package='opem-amalur-script-tools-v0.5.zip',real_samples=3457,functions=93888,tests_passed=56)
project['script_parser']['limitations']=['Exact observed header only','Nonempty debug/prototype sections unsupported','Native wrapper metadata roles and batch load order not fully traced']
project['lua_reconstruction']={'status':'Complete guarded body coverage for observed initial archive, including bundle variants',
 'source':str(root/'src/amalur_reconstruct.py'),'profile':'native-script-profile.json','profile_opcode_mappings':len(profile['opcodes']),
 'standalone':manifest['totals_by_group']['standalone'],'bundle_occurrences':manifest['totals_by_group']['bundle'],
 'distinct_wrapped_inputs':6151,'distinct_input_functions':68530,'unresolved_function_bodies':0,
 'original_unresolved_before':2997,'original_unresolved_after':0,'unique_test_methods_passed':324,'full_lua51_compiled':74681,
 'generated_code_executed_with_mocks':True,'generated_code_executed_in_game':False,'runtime_equivalence_verified':False,
 'drafts_package':'opem-amalur-initial-script-drafts-v0.5.zip','limitations':validation['limits']}
project['remaining_functions_v05']={'session_closed':True,'target_unchanged':True,'report':'remaining-functions-findings.txt','evidence_package':'opem-amalur-remaining-functions-evidence-v0.5.zip','validation':'remaining-v05/validation.json'}
write(out/'project.json',project)
report=f'''Opem Amalur v0.5 — remaining functions and wrapper variants

Completed on Windows: {validation['finalized_utc']}

All 2,997 previously unresolved standalone function bodies now have guarded
Lua5.1 source drafts. All 12 formerly unsupported batch wrappers parse fully.
The original standalone set contains 42,060 bodies, all emitted. The wrappers
contain 6,370 member occurrences and 51,828 function occurrences. Deduplicating
only identical wrapped bytes across both sets yields 6,151 script variants and
68,530 function bodies, all emitted with zero structural or lift errors.
All 74,681 generated files (whole scripts plus body drafts) compile with Lua5.1.

Validation: 277 core tests, 68 parser/bundle/token tests, 16 cache-flow tests;
324 distinct methods after accounting for 37 overlapping structural tests.
All original extracted inputs and executable hashes remained unchanged. The
REA session closed cleanly. The game was not launched, patched, or modified.

Recovered details include exact wrapping int32 arithmetic, signed remainder,
integer powers, byte-exact concatenation with native decimal conversion,
typed table fallback, receiver setup, canonical tail calls, cached-value
proof across branches and loops, and flags7 legacy argument-table semantics.
The final legacy count key was traced through native state initialization and
CRT string initialization to the exact literal n. Saved varargs and the arg
table have separate storage, preserving nil counts and mutation behavior.

64-bit type11 IDs retain original hexadecimal bytes in IR. A shared opaque
userdata carrier applies the native low-nibble tag and preserves all remaining
bits. It is deliberately distinct from a Lua number. Engine bindings still
need explicit marshaling; this module is not a bridge into the shipped game.

What this proves: complete guarded source-draft coverage for initial_0.pak's
observed scripts, plus compiler validity and focused synthetic/mock execution.
What remains: native-runtime equivalence, engine API bindings, custom types and
metamethod domains, other archives, high-level source formatting, and the native
engine itself. A fully rebuildable game has not yet been demonstrated.

Windows drafts: {full}
Each manifest binding preserves source file/member identity, resource ID,
container offsets, and hashes. Distinct wrappers are not merged by resource ID.
The tools and runtime contract are in opem-amalur-script-tools-v0.5.zip.
'''
(out/'remaining-functions-findings.txt').write_text(report,encoding='utf-8');shutil.copy2(out/'remaining-functions-findings.txt',ev/'findings.txt')
def package(name,items):
 path=out/name;entries=0
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  seen=set()
  for item in items:
   for p in sorted(item.rglob('*')) if item.is_dir() else [item]:
    if not p.is_file() or '__pycache__' in p.parts:continue
    relative=p.relative_to(root).as_posix()
    if relative in seen:continue
    assert p.suffix not in ('.exe','.lua_bxml','.pak')
    seen.add(relative);z.write(p,relative);entries+=1
 with zipfile.ZipFile(path) as z:assert z.testzip() is None
 record={'file':name,'bytes':path.stat().st_size,'sha256':sha(path),'entries':entries};print(json.dumps(record),flush=True);return record
parser_tests=[root/'work/v05-parser'/n for n in ['amalur_script.py','test_amalur_script.py','test_amalur_bundles.py','test_amalur_real_bundles.py','test_amalur_uint64.py','test_amalur_uint64_encoding.py','amalur_uint64.lua']]
workflows=[root/'work'/n for n in ['export_corpus_v05.py','reevaluate_v05.py','finalize_v05.py']]
packages=[package('opem-amalur-script-tools-v0.5.zip',sources+alltests+parser_tests+workflows+[root/'README-v05.txt',out/'native-script-profile.json',out/'project.json',out/'remaining-functions-findings.txt',root/'work/v05-cache/cache_flow.py',root/'work/v05-cache/test_cache_flow.py',ev/'BATCH_WRAPPERS.md',ev/'UINT64_CONTRACT.md']),
 package('opem-amalur-remaining-functions-evidence-v0.5.zip',[ev]),
 package('opem-amalur-initial-script-drafts-v0.5.zip',[full])]
write(out/'v05-package-sha256.json',{'execution_host':platform.node(),'packages':packages})
print('v0.5 finalized',flush=True)
