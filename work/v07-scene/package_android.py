"""Assemble a project-private NativeActivity scene preview APK on Windows."""
import platform,subprocess,zipfile,json,hashlib,shutil
from pathlib import Path
assert platform.system()=='Windows'
root=Path.home()/'Documents'/'Opem Amalur';out=root/'outputs/scene-v07';stage=root/'work/v07-apk';stage.mkdir(exist_ok=True)
sdk=root/'tools/android/sdk';bt=sdk/'android-15';java=root/'tools/jdk-21.0.13+9/bin/java.exe';keytool=java.with_name('keytool.exe')
logs=[]
def run(args,label):
 result=subprocess.run([str(a) for a in args],capture_output=True,timeout=180)
 (out/(label+'.log')).write_bytes(result.stdout+result.stderr)
 if result.returncode:raise RuntimeError(label+' exit '+str(result.returncode))
 return result.stdout.decode('utf-8',errors='replace')
unsigned=stage/'unsigned.apk';aligned=stage/'aligned.apk';apk=out/'opem-amalur-scene-v0.7-arm64.apk'
run([bt/'aapt2.exe','link','-o',unsigned,'--manifest',root/'work/v07-host/AndroidManifest.xml','-I',sdk/'android-35/android.jar','--min-sdk-version','26','--target-sdk-version','35'],'apk-manifest-link')
module_dir=out/'modules';files={
 'assets/scene.bin':out/'scene.bin',
 'assets/inputdeviceaction_init.bin':root/'work/scene-inputs-v07/initial_0.pak/inputdeviceaction_init.bin',
 'lib/arm64-v8a/libopem_amalur_scene.so':root/'work/v07-host/build-android-arm64/libopem_amalur_scene.so',
 'assets/modules/modules.tsv':module_dir/'modules.tsv'}
for p in (root/'work/v07-portable/runtime').glob('*.lua'):files['assets/runtime/'+p.name]=p
for line in (module_dir/'modules.tsv').read_text().splitlines():
 if line and not line.startswith('#'):
  name,file=line.split('\t');assert Path(file).name==file;files['assets/modules/'+file]=module_dir/file
files['assets/scene-evidence.json']=out/'combined-scene.json'
files['assets/scene-props-evidence.json']=out/'placements.json'
files['assets/scene-static-evidence.json']=out/'shell-candidate.json'
with zipfile.ZipFile(unsigned,'a') as z:
 for name,path in files.items():z.write(path,name,compress_type=zipfile.ZIP_DEFLATED)
run([bt/'zipalign.exe','-f','4',unsigned,aligned],'apk-align')
key=root/'tools/android/opem-scene-debug.keystore'
if not key.exists():run([keytool,'-genkeypair','-keystore',key,'-storepass','android','-keypass','android','-alias','opem-scene-debug','-keyalg','RSA','-keysize','2048','-validity','3650','-dname','CN=Opem Amalur Local Debug,O=Local Development,C=US'],'apk-local-debug-key')
run([java,'-jar',bt/'lib/apksigner.jar','sign','--ks',key,'--ks-key-alias','opem-scene-debug','--ks-pass','pass:android','--key-pass','pass:android','--v1-signing-enabled','false','--v2-signing-enabled','true','--v3-signing-enabled','true','--out',apk,aligned],'apk-sign')
verify=run([java,'-jar',bt/'lib/apksigner.jar','verify','--verbose','--print-certs',apk],'apk-signature-verify')
run([bt/'zipalign.exe','-c','4',apk],'apk-alignment-verify')
run([bt/'aapt2.exe','dump','badging',apk],'apk-badging')
ndk=root/'tools/android/android-ndk-r30/toolchains/llvm/prebuilt/windows-x86_64/bin'
run([ndk/'llvm-readelf.exe','-h','-l','-d','-s',files['lib/arm64-v8a/libopem_amalur_scene.so']],'android-scene-elf')
manifest={'apk':str(apk),'bytes':apk.stat().st_size,'sha256':hashlib.sha256(apk.read_bytes()).hexdigest(),'package':'org.opemamalur.scene','abi':'arm64-v8a','min_sdk':26,'target_sdk':35,'native_activity':True,'device_executed':False,'purpose':'Partial real-scene geometry inspection and recovered-script bootstrap diagnostic; not a playable game','files':[{'apk_path':n,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for n,p in files.items()]}
(out/'android-apk-manifest.json').write_text(json.dumps(manifest,indent=2));print(json.dumps({k:v for k,v in manifest.items() if k!='files'},indent=2));print(verify.split('Signer')[0])
