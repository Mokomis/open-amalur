"""Verify and package the completed Windows reconstruction checkpoint."""
import hashlib
import json
import platform
import re
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path

assert platform.system()=='Windows'
root=Path.home()/'Documents'/'Opem Amalur';out=root/'outputs'
focus=out/'reconstruction-v04';full=out/'initial-corpus-drafts-v04';evidence=out/'loops-openlists'
expected='16a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
exe=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning\koa.exe')
assert sha(exe)==expected
assert read(evidence/'rea-session/status.json')['state']=='closed'
integrity=read(evidence/'rea-session/input-integrity.json')
assert integrity['unchanged'] and integrity['sha256_before']==integrity['sha256_after']==expected
testlog=(evidence/'tests.txt').read_text(encoding='utf-8-sig')
assert re.search(r'Ran 205 tests in [\d.]+s',testlog) and testlog.rstrip().endswith('OK')
assert 'skipped=' not in testlog
profile=read(out/'native-script-profile.json');assert len(profile['opcodes'])==41
def compile_check(directory,count):
    report=read(directory/'lua51-compile-validation.json')
    assert report['runtime']=='Lua 5.1' and report['files']==report['passed']==len(report['records'])==count
    assert {p.relative_to(directory).as_posix() for p in directory.rglob('*.lua')}=={r['file'] for r in report['records']}
    for r in report['records']:assert r['compiled'] and sha(directory/r['file'])==r['sha256']
compile_check(focus,171);compile_check(full,42508)
syntax=read(focus/'syntax-validation.json')
assert syntax['files_checked']==len(syntax['results'])==171
assert all(r['syntax']=='passed' and sha(focus/r['file'])==r['sha256'] for r in syntax['results'])
manifest=read(full/'manifest.json');inventory=read(out/'initial-corpus-v04/inventory.json')
assert manifest['function_drafts']==39063 and manifest['parsed_scripts']==3445 and manifest['selected_scripts']==3457
t=inventory['totals'];assert t['parsed_functions']==42060 and t['after_supported']==39063 and t['after_unresolved']==2997
assert t['before_supported']==29905 and t['complete_scripts']==2636 and t['parse_errors']==12
records={r['file']:r for r in inventory['records']}
losses=[];drafts=0
for record in inventory['records']:
    assert sha(root/'work/initial-script-corpus-v04'/record['file'])==record['sha256']
    if 'after'in record and record['after']['emittable_function_bodies']<record['before']['emittable_function_bodies']:losses.append(record['file'])
assert not losses
for record in manifest['records']:
    if record['status']!='exported':continue
    directory=full/Path(record['file']).stem
    ir=read(directory/'ir.json')
    assert ir['input_sha256']==record['input_sha256']==records[record['file']]['sha256']
    assert ir['summary']==record['summary']==records[record['file']]['after']
    for draft in record['drafts']:
        assert sha(directory/'functions'/draft['file'])==draft['sha256'];drafts+=1
assert drafts==39063
focused={}
for name,file,folder,count in [('small','1596600.lua_bxml','script-samples',2),('sq02','441939.lua_bxml','script-samples',154),
                               ('third','1701254.lua_bxml','script-samples',5),('ayten','1378937.lua_bxml','capture-corpus',6)]:
    ir=read(focus/(name+'.ir.json'))
    assert sha(root/'work'/folder/file)==ir['input_sha256']
    assert ir['summary']['emittable_function_bodies']==ir['summary']['functions']==count
    assert ir['summary']['unresolved_function_bodies']==0
    focused[name]={'file':file,'sha256':ir['input_sha256'],**ir['summary']}
sources=[root/'src'/n for n in ['amalur_script.py','amalur_reconstruct.py']]
tests=sorted((root/'tests').glob('test_amalur_*.py'))
assert len(tests)==10
validation={'version':'0.4','execution_host':platform.node(),'finalized_utc':datetime.now(timezone.utc).isoformat(),
            'target_sha256':expected,'target_unchanged':True,'rea_session_closed':True,'fresh_native_helpers':9,
            'tests_passed':205,'tests_skipped':0,'parser_tests':37,'reconstruction_tests':52,'runtime_oriented_methods':116,
            'focused_syntax_passed':171,'focused_lua51_compiled':171,'full_lua51_compiled':42508,
            'semantic_opcode_mappings':41,'focused_samples':focused,'full_archive':t,
            'coverage_losses':losses,'supported_body_features':inventory['supported_body_features'],
            'source_and_test_sha256':{p.relative_to(root).as_posix():sha(p) for p in sources+tests},
            'input_and_export_hashes_rechecked':True,'generated_code_executed_with_mocks':True,
            'game_launched':False,'game_patched':False,'native_runtime_equivalence_verified':False,
            'limits':['Initial archive only, not all game archives.','Guarded operand domains; supported parents may contain unresolved children.',
                      'No native Havok runtime differential test.','Large-dispatch environment sync verified on normal completion only.']}
write(focus/'validation.json',validation);write(full/'validation.json',validation);write(evidence/'validation.json',validation)
shutil.copy2(evidence/'tests.txt',focus/'tests.txt')
reused=evidence/'reused-evidence';reused.mkdir(exist_ok=True)
for name in ['vm_a_pseudocode.json','vm_a_pseudocode.c','vm_a_info.json','opcode_metadata_bytes.json']:
    shutil.copy2(out/'bytecode-reader/rea-session'/name,reused/name)
for name in ['integer-semantics.json','loop-v04-handlers.json','open-v04-core.json','open-v04-more.json','loop-v04-len-field.json','loop-v04-table-create.json']:
    shutil.copy2(out/'bytecode-reader'/name,evidence/name)
shutil.copy2(out/'initial-corpus-v04/inventory.json',evidence/'full-archive-inventory.json')
project=read(out/'project.json');project['updated']=validation['finalized_utc']
project['next_script_experiment']='Recover remaining arithmetic/string/table opcodes, cached-state proofs and legacy vararg argument tables; inspect batch wrappers and plan native-runtime differential checks'
project['script_parser'].update(status='native-correlated structural reader; full initial archive checked',package='opem-amalur-script-tools-v0.4.zip',real_samples=3445,functions=42060,tests_passed=37)
project['script_parser']['limitations']=['Exact observed header only','Nonempty debug/prototype sections unsupported','12 batch wrapper entries unsupported','Metadata-string semantic role not established']
project['lua_reconstruction']={'status':'guarded loops, open lists, shared captures and table reconstruction',
    'source':str(root/'src/amalur_reconstruct.py'),'profile':'native-script-profile.json','profile_opcode_mappings':41,
    'focused_function_bodies':167,'focused_supported_bodies':167,'full_initial_archive':t,
    'combined_tests_passed':205,'focused_lua51_compiled':171,'full_lua51_compiled':42508,
    'generated_code_executed_with_mocks':True,'generated_code_executed_in_game':False,'runtime_equivalence_verified':False,
    'drafts_package':'opem-amalur-initial-script-drafts-v0.4.zip','focused_drafts_package':'opem-amalur-focused-drafts-v0.4.zip',
    'limitations':validation['limits']+['Other opcodes, legacy vararg tables, custom Havok/userdata/metamethod domains and high-level source structure remain incomplete']}
project['loops_openlists']={'session_closed':True,'target_unchanged':True,'report':'loops-openlists-findings.md',
                          'evidence_package':'opem-amalur-loops-openlists-evidence.zip','validation':'reconstruction-v04/validation.json'}
write(out/'project.json',project)

def package(filename,paths):
    path=out/filename;seen=set()
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for item in paths:
            for file in sorted(item.rglob('*')) if item.is_dir() else [item]:
                if not file.is_file() or '__pycache__'in file.parts or (file.name.startswith('tests-') and file.name.endswith('.txt')):continue
                relative=file.relative_to(root).as_posix();assert relative not in seen
                assert file.suffix not in ('.exe','.lua_bxml','.pak')
                seen.add(relative);z.write(file,relative)
    with zipfile.ZipFile(path) as z:assert z.testzip() is None
    result={'file':filename,'bytes':path.stat().st_size,'sha256':sha(path),'entries':len(seen)}
    print(json.dumps(result),flush=True);return result
workflow=['export_fragments.py','validate_lua.cjs','validate_lua51.py','validate_corpus_v04.py','inspect_v04_candidates.py',
          'analyze_initial_corpus_v04.py','export_initial_corpus_v04.py','refresh_initial_exports_v04.py','finalize_v04.py']
tool_files=sources+tests+[root/n for n in ['README.md','RECONSTRUCTION.md']]
tool_files += [out/n for n in ['native-script-profile.json','loops-openlists-findings.md','project.json']]
tool_files += [root/'work'/n for n in workflow]
packages=[package('opem-amalur-script-tools-v0.4.zip',tool_files),
          package('opem-amalur-focused-drafts-v0.4.zip',[focus]),
          package('opem-amalur-initial-script-drafts-v0.4.zip',[full]),
          package('opem-amalur-loops-openlists-evidence.zip',[evidence])]
write(out/'v04-package-sha256.json',{'execution_host':platform.node(),'packages':packages})
print('Finalized v0.4: 205 tests; 42,508 full-archive Lua files compiled; 39,063 body drafts.',flush=True)
