"""Validate built host on Windows; inspect Android build without claiming execution."""
import hashlib, json, platform, re, subprocess
from pathlib import Path
assert platform.system() == 'Windows'
root=Path.home()/'Documents'/'Opem Amalur'
here=root/'work/v06-portable'; runtime=here/'runtime'
out=root/'outputs/engine-bindings-v06/portable-runtime'
out.mkdir(parents=True,exist_ok=True)
exe=here/'build-windows/amalur-script.exe'
api=here/'build-windows/amalur-runtime-api-test.exe'
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
records=[]
def run(name, command, expect_ok, phase=None, fragment=None):
    record={'name':name,'command':list(map(str,command)),'timeout_seconds':10}
    try:
        result=subprocess.run(command,capture_output=True,text=True,timeout=10)
        record.update(exit_code=result.returncode,stdout=result.stdout,stderr=result.stderr,timed_out=False)
        parsed=json.loads(result.stdout)
        record['parsed']=parsed
        assert (result.returncode==0)==expect_ok,record
        assert parsed['ok']==expect_ok,record
        if phase: assert parsed.get('phase')==phase,record
        if fragment: assert fragment in parsed.get('error',''),record
        record['passed']=True
    except subprocess.TimeoutExpired as e:
        record.update(timed_out=True,stdout=(e.stdout or b'').decode(errors='replace'),stderr=(e.stderr or b'').decode(errors='replace'),passed=False)
        records.append(record)
        (out/'validation-partial.json').write_text(json.dumps(records,indent=2))
        raise
    except BaseException:
        record['passed']=False;records.append(record)
        (out/'validation-partial.json').write_text(json.dumps(records,indent=2))
        raise
    records.append(record)
    return parsed
def cli(name,file,ok=True,options=(),phase=None,fragment=None):
    return run(name,[str(exe),'--runtime-dir',str(runtime),*options,str(here/'tests'/file)],ok,phase,fragment)
real=cli('native-verified real functions','native_verified_real_functions.lua')
assert real['result_count']==1 and real['results']==[{'type':'number','value':71}]
contract=cli('nil and type11 transport','portable_contract.lua')
assert contract['result_count']==5 and contract['results']==[
    {'type':'nil'},{'type':'amalur-type11','hex':'ffffffff0000039b'},
    {'type':'number','value':7},{'type':'boolean','value':False},{'type':'nil'}]
api_result=run('embedding API and recovery',[str(api),str(runtime)],True)
assert api_result['checks']>=17
for name in ['budget_cannot_be_swallowed.lua','budget_xpcall_cannot_be_swallowed.lua','budget_xpcall_handler_loop.lua']:
    cli(name,name,False,['--budget','1000'],'evaluate','instruction budget exhausted')
cli('allocator memory cap','memory_limit.lua',False,['--memory-limit','1048576'],'evaluate','memory')
cli('initialization memory cap','portable_contract.lua',False,['--memory-limit','32768'],'initialize','memory')
android=here/'build-android-arm64/amalur-script'
readelf=root/'tools/android/android-ndk-r30/toolchains/llvm/prebuilt/windows-x86_64/bin/llvm-readelf.exe'
elf=subprocess.run([str(readelf),'-h','-l',str(android)],capture_output=True,text=True,timeout=10,check=True).stdout
(out/'android-elf.txt').write_text(elf,encoding='utf-8')
assert 'AArch64' in elf and '/system/bin/linker64' in elf
loads=[line for line in elf.splitlines() if line.strip().startswith('LOAD ')]
assert loads and all(line.split()[-1]=='0x4000' for line in loads)
artifacts=[exe,api,android,here/'build-android-arm64/libamalur_runtime.a',here/'build-android-arm64/libamalur_lua51.a']
report={'scope':'Windows execution of portable host; Android arm64 cross-compilation and ELF inspection only.',
        'execution_host':platform.node(),'windows_checks':records,'windows_checks_passed':len(records),
        'recovered_function_input_cases':71,'recovered_function_bodies':19,
        'embedding_api_checks':api_result['checks'],'android_execution_verified':False,
        'android_runtime_blocker':'No attached Android device was observed; no emulator was started.',
        'android_architecture':'arm64-v8a','android_min_api':26,'android_load_segment_alignment_bytes':16384,
        'artifacts':{str(p.relative_to(here)):{'bytes':p.stat().st_size,'sha256':sha(p)} for p in artifacts},
        'sources':{str(p.relative_to(here)):sha(p) for d in ['include','src','runtime','tests'] for p in sorted((here/d).glob('*')) if p.is_file()}}
(out/'validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ['sources','windows_checks','artifacts']},indent=2))
