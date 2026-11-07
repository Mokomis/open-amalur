"""Assemble a project-private NativeActivity scene preview APK on Windows."""
import platform,subprocess,zipfile,json,hashlib,shutil,sys,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'v08-scene'))
from package_readiness import inspect_inputs
assert platform.system()=='Windows'
root=Path.home()/'Documents'/'Opem Amalur';base=root/'outputs/scene-v08';out=root/'outputs/scene-v11';stage=root/'work/v11-apk';stage.mkdir(exist_ok=True)
sdk=root/'tools/android/sdk';bt=sdk/'android-15';java=root/'tools/jdk-21.0.13+9/bin/java.exe';keytool=java.with_name('keytool.exe')
logs=[]
def file_sha(path):
 digest=hashlib.sha256()
 with path.open('rb') as stream:
  for chunk in iter(lambda:stream.read(1024*1024),b''):digest.update(chunk)
 return digest.hexdigest()
parser=argparse.ArgumentParser()
parser.add_argument('--bootstrap-report',type=Path,default=base/'scene-final-windows.json')
args=parser.parse_args()
module_pairs,readiness=inspect_inputs(root,args.bootstrap_report)
(out/'android-bootstrap-readiness.json').write_text(json.dumps(readiness,indent=2))
def run(args,label):
 result=subprocess.run([str(a) for a in args],capture_output=True,timeout=180)
 (out/(label+'.log')).write_bytes(result.stdout+result.stderr)
 if result.returncode:raise RuntimeError(label+' exit '+str(result.returncode))
 return result.stdout.decode('utf-8',errors='replace')
run([sys.executable,root/'work/v11-host/verify_android_package_inputs.py'],'apk-input-preflight')
unsigned=stage/'unsigned.apk';aligned=stage/'aligned.apk';apk=out/'opem-amalur-scene-v0.11-arm64.apk'
run([bt/'aapt2.exe','link','-o',unsigned,'--manifest',root/'work/v11-host/AndroidManifest.xml','-I',sdk/'android-35/android.jar','--min-sdk-version','26','--target-sdk-version','35'],'apk-manifest-link')
module_dir=base/'modules';files={
 'assets/compiled_enums.bin':base/'assets/compiled_enums.bin',
 'assets/scene.bin':root/'outputs/scene-v11/scene-normals.bin',
 'assets/inputdeviceaction_init.bin':root/'work/scene-inputs-v07/initial_0.pak/inputdeviceaction_init.bin',
 'lib/arm64-v8a/libopem_amalur_scene.so':root/'work/v11-host/build-android-arm64/libopem_amalur_scene.so',
 'assets/modules/modules.tsv':module_dir/'modules.tsv'}
for p in (root/'work/v08-portable/runtime').glob('*.lua'):files['assets/runtime/'+p.name]=p
for name,file in module_pairs.items():files['assets/modules/'+file]=module_dir/file
files['assets/collision.bin']=root/'outputs/scene-v10/collision-confirmed.bin'
collision_receipt=json.loads((out/'collision-source.json').read_text())
if file_sha(files['assets/collision.bin'])!=collision_receipt['output_sha256'] or not collision_receipt['native_layout_corroborated']:raise RuntimeError('Collision provenance mismatch')
files['assets/collision-evidence.json']=out/'collision-source.json'
files['assets/scene_materials.bin']=out/'scene_materials.bin'
scene_hash=file_sha(files['assets/scene.bin'])
cache=(root/'work/v11-host/build-android-arm64/CMakeCache.txt').read_text()
if 'AMALUR_SCENE_SHA256:STRING='+scene_hash not in cache:raise RuntimeError('Compiled scene identity mismatches packaged scene')
if scene_hash.encode()+b'\0' not in files['lib/arm64-v8a/libopem_amalur_scene.so'].read_bytes():raise RuntimeError('Scene identity missing from native library')
files['assets/scene-evidence.json']=out/'render-scene.json'
files['assets/source-geometry-evidence.json']=root/'outputs/scene-v07/combined-scene.json'
files['assets/scene-props-evidence.json']=root/'outputs/scene-v07/placements.json'
files['assets/scene-static-evidence.json']=root/'outputs/scene-v07/shell-candidate.json'
for macro in json.loads((base/'asset-macros.json').read_text()):files['assets/'+macro['file']]=base/'assets'/macro['file']
file_records=[{'apk_path':n,'bytes':p.stat().st_size,'sha256':file_sha(p)} for n,p in files.items()]
for record in file_records:
 source=files[record['apk_path']]
 expected=readiness['input_hashes'].get(str(source.relative_to(root)))
 if expected is not None and record['sha256']!=expected:raise RuntimeError('Input changed after readiness check: '+str(source))
preflight=json.loads((out/'android-package-input-preflight.json').read_text())
library_record=next(record for record in file_records if record['apk_path']=='lib/arm64-v8a/libopem_amalur_scene.so')
if library_record['sha256']!=preflight['shared_library_sha256']:raise RuntimeError('Android library changed after preflight')
with zipfile.ZipFile(unsigned,'a') as z:
 for name,path in files.items():z.write(path,name,compress_type=zipfile.ZIP_DEFLATED)
run([bt/'zipalign.exe','-f','4',unsigned,aligned],'apk-align')
key=root/'tools/android/opem-scene-debug.keystore'
if not key.exists():raise RuntimeError('Existing rollback-compatible signing key required')
run([java,'-jar',bt/'lib/apksigner.jar','sign','--ks',key,'--ks-key-alias','opem-scene-debug','--ks-pass','pass:android','--key-pass','pass:android','--v1-signing-enabled','false','--v2-signing-enabled','true','--v3-signing-enabled','true','--out',apk,aligned],'apk-sign')
verify=run([java,'-jar',bt/'lib/apksigner.jar','verify','--verbose','--print-certs',apk],'apk-signature-verify')
run([bt/'zipalign.exe','-c','4',apk],'apk-alignment-verify')
run([bt/'aapt2.exe','dump','badging',apk],'apk-badging')
ndk=root/'tools/android/android-ndk-r30/toolchains/llvm/prebuilt/windows-x86_64/bin'
run([ndk/'llvm-readelf.exe','-h','-l','-d','-s',files['lib/arm64-v8a/libopem_amalur_scene.so']],'android-scene-elf')
with zipfile.ZipFile(apk) as z:
 names=z.namelist()
 for record in file_records:
  name=record['apk_path']
  if names.count(name)!=1 or z.getinfo(name).file_size!=record['bytes']:raise RuntimeError('Packaged entry missing/duplicated/resized: '+name)
  digest=hashlib.sha256()
  with z.open(name) as stream:
   for chunk in iter(lambda:stream.read(1024*1024),b''):digest.update(chunk)
  if digest.hexdigest()!=record['sha256']:raise RuntimeError('Packaged bytes changed since preflight: '+name)
manifest={'apk':str(apk),'bytes':apk.stat().st_size,'sha256':file_sha(apk),'package':'org.opemamalur.scene','abi':'arm64-v8a','min_sdk':26,'target_sdk':35,'native_activity':True,'device_executed':False,'bootstrap_readiness':readiness,'payload_hashes_verified_from_signed_apk':True,'purpose':'Partial scene exploration: approximate collision, first-person movement and selected recovered texture preview; not complete gameplay','files':file_records}
(out/'android-apk-manifest.json').write_text(json.dumps(manifest,indent=2))
summary={k:v for k,v in manifest.items() if k not in ('files','bootstrap_readiness')}
summary.update({k:readiness[k] for k in ('registered_modules','recovered_function_bodies','asset_macro_count','bootstrap_report_sha256')})
print(json.dumps(summary,indent=2));print(verify.split('Signer')[0])
