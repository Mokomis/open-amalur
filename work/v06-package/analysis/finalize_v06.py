"""Windows packaging for native binding evidence and portable Android foundation."""
import hashlib,json,platform,shutil,zipfile
from datetime import datetime,timezone
from pathlib import Path
assert platform.system()=='Windows'
root=Path.home()/'Documents'/'Opem Amalur';out=root/'outputs';ev=out/'engine-bindings-v06'
target=Path(r'C:\Program Files (x86)\Steam\steamapps\common\Kingdoms of Amalur Re-Reckoning\koa.exe')
expected='16a400f6e8fc10dbe446a9e57717de9fbe975ef17c004f4ca405e2e4e09cb314'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert sha(target)==expected
assert read(ev/'rea-session/status.json')['state']=='closed'
integrity=read(ev/'rea-session/input-integrity.json');assert integrity['unchanged'] and integrity['sha256_after']==expected
families=[('primitive VM','final-primitives',364),('integer math callbacks','final-math',319),
          ('real function inputs','final-real-functions-verified',71),('C calls and open results','final-calls',63),
          ('nested Lua calls','native-vm-lua-calls-full',55)]
comparisons=[]
for name,folder,n in families:
 p=ev/folder/'comparison.json';r=read(p)
 assert r['cases']==r['matched']==n and r['native_exit_code']==0 and r['target_unchanged']
 assert r['harness_sha256']=='e2e0f14aa39ae6bad5503ac8d06591faed8c32da276a75bdb224a81ba361c2c3'
 comparisons.append({'family':name,'matched':n,'report':folder+'/comparison.json','sha256':sha(p)})
assert sum(x['matched'] for x in comparisons)==872
bindings=read(ev/'adapter-test-report.json');assert bindings['passed']==7 and bindings['registry_total']==1062 and bindings['registry_matches_native_descriptor_manifest']
handles=read(ev/'handle-marshaling-validation.json');assert handles['passed']==10
guards=read(ev/'runtime-admission-validation.json');assert guards['passed']==82
portable=read(ev/'portable-runtime/validation.json');assert portable['windows_checks_passed']==8 and portable['embedding_api_checks']==20 and not portable['android_execution_verified']
host=root/'work/v06-portable'
for relative,record in portable['artifacts'].items():assert sha(host/relative)==record['sha256']
for relative,digest in portable['sources'].items():assert sha(host/relative)==digest
for name,digest in {'amalur_reconstruct.py':'8617cfc6744f614f6d0da5fb8442bd8677d5bfdf13fc98abbf9c128409d9703e'}.items():assert sha(root/'src'/name)==digest
assert sha(out/'native-script-profile.json')=='310f760c9ba73a3a06d16287ee7585d9a2d572816bc58a71a50fc6cb3ace2594'
stage=root/'work/v06-package';stage.mkdir(exist_ok=True)
portable_stage=stage/'portable';portable_stage.mkdir(exist_ok=True)
for name in ['include','src','tests','runtime','third_party']:
 shutil.copytree(host/name,portable_stage/name,dirs_exist_ok=True)
for name in ['CMakeLists.txt','README.md','build_windows_android.cmd']:
 shutil.copy2(host/name,portable_stage/name)
for folder,files in [('android-arm64',['amalur-script','amalur-runtime-api-test','libamalur_runtime.a','libamalur_lua51.a']),
                     ('windows',['amalur-script.exe','amalur-runtime-api-test.exe','amalur_runtime.lib','amalur_lua51.lib'])]:
 dest=portable_stage/'prebuilt'/folder;dest.mkdir(parents=True,exist_ok=True)
 build=host/('build-android-arm64' if folder=='android-arm64' else 'build-windows')
 for name in files:shutil.copy2(build/name,dest/name)
shutil.copy2(ev/'portable-runtime/validation.json',portable_stage/'validation.json')
shutil.copy2(ev/'portable-runtime/android-elf.txt',portable_stage/'android-elf.txt')
building='''Opem Amalur portable runtime — building and linking

This package is a script-runtime foundation, not a playable game or APK.
The Windows build ran the supplied tests. Android arm64 was cross-compiled
on Windows and its ELF inspected; Android execution is not yet verified.

From this package's portable directory, configure with CMake:
  cmake -S . -B build -DLUA_SOURCE_DIR=./third_party/lua-5.1.5
  cmake --build build --config Release
Use a Visual Studio developer shell on Windows. For Android, choose Ninja
and add the following configure arguments (replace the NDK path):
  -DCMAKE_TOOLCHAIN_FILE=C:/path/to/ndk/build/cmake/android.toolchain.cmake
  -DANDROID_ABI=arm64-v8a -DANDROID_PLATFORM=android-26
  -DCMAKE_BUILD_TYPE=Release

Link your engine target against the CMake target amalur_runtime. It carries
the Lua dependency and public include directories. Include amalur_runtime.h.
Supply the runtime directory containing the five included Lua modules when
creating a realm. Install engine providers through amalur_runtime_set_provider.
The public header documents exact stack/result ownership and protected calls.
Each realm is single-threaded and independent. Original x86 addresses are
reference metadata only and are never called by this portable library.

Prebuilt Android files require arm64 Android API26 or later. To test on an
attached development device, copy prebuilt/android-arm64/amalur-script,
runtime/, and tests/ to a new directory under /data/local/tmp, make the binary
executable, and run:
  ./amalur-script --runtime-dir runtime tests/native_verified_real_functions.lua
Expected: ok=true and one numeric result71. This is a CLI test, not a game UI.
The same command accepts tests/portable_contract.lua for exact handle/nil checks.
No device installation, game launch, saved-game change or root change occurred.

Dependencies: bundled unmodified Lua5.1.5 source (MIT license in third_party).
Android NDK and Windows compiler are not redistributed. The project-specific
build_windows_android.cmd uses this workstation's tool paths; the CMake
commands above are the relocatable build interface.
'''
(portable_stage/'BUILDING.txt').write_text(building,encoding='utf-8')
# Make source available as the Windows project baseline, outside transient work.
source_dest=root/'src/portable';source_dest.mkdir(exist_ok=True)
for name in ['include','src','tests','runtime','third_party']:
 shutil.copytree(portable_stage/name,source_dest/name,dirs_exist_ok=True)
for name in ['CMakeLists.txt','README.md','BUILDING.txt','build_windows_android.cmd']:
 shutil.copy2(portable_stage/name,source_dest/name)
runtime_dest=root/'src/runtime';runtime_dest.mkdir(exist_ok=True)
for p in (host/'runtime').glob('*.lua'):shutil.copy2(p,runtime_dest/p.name)
# Keep static mappings, their proof, and source-level tools together.
for name in ['v06-bindings','v06-handles','v06-compare','v06-runtime']:
 dest=stage/'analysis'/name;dest.mkdir(parents=True,exist_ok=True)
 for p in (root/'work'/name).iterdir():
  if p.is_file() and p.suffix in {'.py','.c','.h','.lua','.json','.txt','.md','.cmd'}:shutil.copy2(p,dest/p.name)
shutil.copy2(root/'work/v06-compare/native_vm_harness.exe',stage/'analysis/v06-compare/native_vm_harness.exe')
for p in (root/'work/v06-bindings').glob('*.json'):shutil.copy2(p,ev/p.name)
for p in (out/'bytecode-reader').glob('v06-*.json'):shutil.copy2(p,ev/p.name)
for name in ['prepare_portable_tests.py','validate_portable_runtime.py','finalize_v06.py','engine_bindings_v06_session.py','native_query.py']:
 shutil.copy2(root/'work'/name,stage/'analysis'/name)
for p in host.glob('*.log'):shutil.copy2(p,ev/'portable-runtime'/p.name)
toolchain={'ndk':{'version':'30.0.16248370','url':'https://dl.google.com/android/repository/android-ndk-r30-windows.zip',
 'official_sha1':'9bf167a1985fa7d4a036186b78f702eab9179408','download_sha256':sha(root/'tools/downloads/android-ndk-r30-windows.zip'),
 'source':'https://developer.android.com/ndk/downloads'},
 'lua':{'version':'5.1.5','url':'https://www.lua.org/ftp/lua-5.1.5.tar.gz','sha256':sha(root/'tools/downloads/lua-5.1.5.tar.gz'),'source':'https://www.lua.org/ftp/'}}
write(ev/'portable-runtime/toolchain.json',toolchain)
validation={'version':'0.6','finalized_utc':datetime.now(timezone.utc).isoformat(),'execution_host':platform.node(),
 'target_sha256':expected,'target_unchanged':True,'rea_session_closed':True,'game_launched':False,'game_patched':False,
 'native_comparisons':comparisons,'native_comparisons_passed':872,'native_real_function_bodies':19,
 'binding_namespaces':bindings['registry_counts'],'binding_entries':1062,'provider_bridge_checks':7,
 'handle_marshaling_checks':10,'math_admission_checks':82,'portable_windows_scenarios':8,'portable_embedding_api_checks':20,
 'android_arm64_compiled':True,'android_execution_verified':False,'playable_build':False,
 'v05_parser_and_reconstructor_unchanged':True,
 'limits':['Native comparisons use synthetic frames and selected input domains, not a running game.',
 'Engine service registration is statically traced; quest/actor/world outcomes have not been replayed against the live engine.',
 'The portable host implements no world, graphics, physics, animation, audio or actual engine providers.',
 'Full module loading, scheduling, yields, metamethod/coercion domains and complete game behavior remain unfinished.',
 'Android library and CLI compile; device execution and APK integration remain pending.']}
write(ev/'validation.json',validation)
project=read(out/'project.json');project['updated']=validation['finalized_utc']
project['objective']='Recover and rebuild Kingdoms of Amalur as a standalone, modifiable implementation that can be compiled for and run on Android.'
project['primary_target']={'platform':'Android','architecture':'arm64-v8a','build_host':'Windows / RobMachineX','original_game_role':'reference evidence and owned asset source'}
project['engine_bindings_v06']={'validation':'engine-bindings-v06/validation.json','registered_entries':1062,'native_comparisons_passed':872,
 'native_real_function_bodies':19,'service_closure_installer':'0x00aa4500','session_closed':True,'target_unchanged':True,
 'in_game_behavior_verified':False,'report':'engine-bindings-and-android-foundation.txt'}
project['portable_runtime']={'source':str(source_dest),'compiled_platforms':['Windows x64','Android arm64 API26'],
 'library':'amalur_runtime','lua_version':'5.1.5','android_execution_verified':False,'playable':False,
 'package':'opem-amalur-portable-runtime-v0.1.zip'}
project['next_script_experiment']='Run the portable host on Android when a device is available; select a small actual script/world slice and implement its engine services and asset path with native-reference validation.'
write(out/'project.json',project)
report=f'''Opem Amalur — engine bindings and Android foundation
Verified on Windows, {validation['finalized_utc']}

Target: a standalone Android implementation with source we can compile and
modify. The original Windows game is the reference, not an Android runtime.

Completed
  - 1,062 exact descriptor name/callback mappings: ACTOR611, QUEST48,
    GAME165, TIME6, WINDOW232.
  - Static service bridge traced: copied callback at service record+0x10
    enters0xaa4500, with optional provider lightuserdata as closure upvalue0;
    0x10a7430/0x109e700 publish a direct native C closure. The VM dispatches
    that callback with its native state. No x86 pointers enter the portable API.
  - 872/872 isolated original-code comparisons:364 primitive VM,319 native
    integer math,71 inputs across19 recovered functions,63 C call/result-list,
    and55 nested Lua call cases. Final harness hash is identical for all five.
  - Portable C library and CLI compiled for Windows x64 and Android arm64.
    Windows passed71 recovered inputs, exact five-value handle/nil transport,
    20 embedding API checks, and8 end-to-end process scenarios.
  - Android ELF64/AArch64, linker64 interpreter and16KiB LOAD alignment verified.
    Native sources are in src/portable on Windows, with portable engine-provider
    boundaries and exact handles. The new runtime math preserves verified
    integer overflow and negative/high-range sqrt behavior.

What this does not establish
There is no playable game or APK yet. Android execution is pending because no
device was attached. The native comparisons use selected code with synthetic
frames; they do not establish in-game or whole-engine equivalence. Actor,
quest, timer, UI and world providers are explicit interfaces, not implemented
game systems. Missing calls report errors. Graphics, geometry/animation import,
physics, audio, world loading and game lifecycle remain ahead.

The next playable milestone is one Android scene loaded from owned game data,
with movement and one recovered gameplay behavior connected to implemented
engine services. First run the portable tests on Android, then establish a
minimal mesh/material/world path and its required provider subset. A reliable
playable ETA depends on those remaining format and engine unknowns; the current
runtime build is an early component, not evidence that a full port is imminent.

Preservation
The installed executable SHA256 remains{expected}.
The game was not launched or patched; saves were not changed. The v0.5 parser,
reconstructor and profile remain unchanged. REA evidence was exported and the
Windows analysis session closed. All native execution and builds ran on Windows.

Deliverables
  opem-amalur-portable-runtime-v0.1.zip — reusable C source, headers, Lua source,
    runtime modules, Windows and Android binaries, tests and build instructions.
  opem-amalur-engine-tools-v0.6.zip — new binding/handle/math tools, native
    comparison harness and portable host sources.
  opem-amalur-engine-evidence-v0.6.zip — static evidence and validation records.

NDK/Lua dependency sources and checksums are recorded in
engine-bindings-v06/portable-runtime/toolchain.json.
'''
(out/'engine-bindings-and-android-foundation.txt').write_text(report,encoding='utf-8')
def archive(path,files):
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for p,name in files:z.write(p,name)
archive(out/'opem-amalur-portable-runtime-v0.1.zip',[(p,p.relative_to(stage).as_posix()) for p in portable_stage.rglob('*') if p.is_file()])
archive(out/'opem-amalur-engine-tools-v0.6.zip',[(p,p.relative_to(stage).as_posix()) for p in stage.rglob('*') if p.is_file()])
archive(out/'opem-amalur-engine-evidence-v0.6.zip',[(p,'engine-bindings-v06/'+p.relative_to(ev).as_posix()) for p in ev.rglob('*') if p.is_file()]+[(out/'engine-bindings-and-android-foundation.txt','engine-bindings-and-android-foundation.txt')])
packages={p.name:{'bytes':p.stat().st_size,'sha256':sha(p)} for p in [out/'opem-amalur-portable-runtime-v0.1.zip',out/'opem-amalur-engine-tools-v0.6.zip',out/'opem-amalur-engine-evidence-v0.6.zip']}
write(out/'v06-package-sha256.json',packages);print(json.dumps(packages,indent=2))
