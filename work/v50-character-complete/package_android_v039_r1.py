"""Private first-room character-creation checkpoint; preserve all parent outputs."""
from pathlib import Path
import hashlib,json,subprocess,time,zipfile
P=Path(__file__).resolve().parents[2]
V=P/'work/v50-character-complete';ST=P/'work/v50-apk-r1';OUT=P/'outputs/scene-v50-r1'
ASSETS=P/'work/v48-opening/integration/probe-preview-closed-container'
LIB=P/'work/v19-host/build-android-arm64/libopem_amalur_scene.so'
APK=OUT/'open-amalur-v0.39-r1-character-creation-arm64.apk'
OUT.mkdir(exist_ok=True);ST.mkdir(exist_ok=True)
if APK.exists():raise SystemExit('Preserve existing signed checkpoint')
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def run(argv,label):
 r=subprocess.run([str(x)for x in argv],capture_output=True,timeout=300)
 (OUT/(label+'.log')).write_bytes(r.stdout+r.stderr)
 if r.returncode:raise RuntimeError(label+' failed: '+str(r.returncode))
 return r.stdout.decode(errors='replace')
receipt_path=P/'work/v48-opening/integration/final-renderer-build.json'
receipt=json.loads(receipt_path.read_text())
assert receipt['inputs_stable_during_build'] and all(receipt[k]['exit']==0 for k in ['windows','android'])
assert sha(LIB)==receipt['android_library_sha256']
for n,h in receipt['sources'].items():assert sha(P/'work/v19-host'/n)==h,n
for n,h in receipt['recipes'].items():assert sha(P/n)==h,n
started=time.monotonic();bt=P/'tools/android/sdk/android-15';java=P/'tools/jdk-21.0.13+9/bin/java.exe'
manifest=(P/'work/v47-apk/AndroidManifest.xml').read_text(encoding='utf8')
assert 'versionCode="40"' in manifest and 'versionName="0.38.0"' in manifest
manifest=manifest.replace('versionCode="40"','versionCode="42"').replace('versionName="0.38.0"','versionName="0.39.1"')
(ST/'AndroidManifest.xml').write_text(manifest,encoding='utf8')
unsigned=ST/'unsigned.apk'
run([bt/'aapt2.exe','link','-o',unsigned,'--manifest',ST/'AndroidManifest.xml','-I',P/'tools/android/sdk/android-35/android.jar','--min-sdk-version','26','--target-sdk-version','35'],'manifest-link')
files={'assets/'+f.relative_to(ASSETS).as_posix():f for f in ASSETS.rglob('*') if f.is_file() and f.suffix!='.json'}
files['lib/arm64-v8a/libopem_amalur_scene.so']=LIB
for n in ['Cinzel-OFL.txt','Alegreya-OFL.txt']:files['assets/licenses/'+n]=P/'work/v21-ui/fonts'/n
assert 'assets/scene-profile.bin' in files
assert 'assets/creator-bank/textures/1576506.oacube' in files
assert len([n for n in files if n.startswith('assets/creator-bank/models/')])==189
assert len([n for n in files if n.startswith('assets/creator-bank/clips/')])==28
assert len([n for n in files if n.startswith('assets/opening-runtime/creation/')])==8
records=[]
with zipfile.ZipFile(unsigned,'a',allowZip64=True)as z:
 for i,(name,f)in enumerate(sorted(files.items())):
  records.append({'path':name,'bytes':f.stat().st_size,'sha256':sha(f)})
  z.write(f,name,compress_type=zipfile.ZIP_DEFLATED,compresslevel=1)
  if i%100==0:print('PACK',i,'/',len(files),flush=True)
aligned=ST/'aligned.apk';run([bt/'zipalign.exe','-f','-P','16','4',unsigned,aligned],'align')
key=P/'tools/android/opem-scene-debug.keystore';assert key.exists()
run([java,'-jar',bt/'lib/apksigner.jar','sign','--ks',key,'--ks-key-alias','opem-scene-debug','--ks-pass','pass:android','--key-pass','pass:android','--v1-signing-enabled','false','--v2-signing-enabled','true','--v3-signing-enabled','true','--out',APK,aligned],'sign')
cert=run([java,'-jar',bt/'lib/apksigner.jar','verify','--verbose','--print-certs',APK],'signature-verify')
signer=next(x.split(':',1)[1].strip()for x in cert.splitlines()if 'certificate SHA-256 digest:'in x)
prior=json.loads((P/'outputs/scene-v47/android-apk-manifest.json').read_text());assert signer==prior['signer_sha256']
run([bt/'zipalign.exe','-c','-P','16','4',APK],'alignment-verify')
badging=run([bt/'aapt2.exe','dump','badging',APK],'badging');assert "versionCode='42'"in badging and "versionName='0.39.1'"in badging
with zipfile.ZipFile(APK)as z:
 assert len(z.namelist())==len(set(z.namelist())) and z.testzip()is None
 assert z.getinfo('resources.arsc').compress_type==zipfile.ZIP_STORED
 for row in records:
  with z.open(row['path'])as f:assert hashlib.file_digest(f,'sha256').hexdigest()==row['sha256'],row['path']
result={'apk':str(APK),'bytes':APK.stat().st_size,'sha256':sha(APK),'package':'org.opemamalur.scene','version_name':'0.39.1','version_code':42,'signer_sha256':signer,'source_receipt':str(receipt_path),'source_receipt_sha256':sha(receipt_path),'native_library_sha256':sha(LIB),'assets':len(files)-1,'asset_root':str(ASSETS),'package_seconds':time.monotonic()-started,'device_executed':False,'private_key_copied':False,'payload_hashes_verified':True,'scope':'First-room creator and source-backed finalized profile; old Gorhart save/settings remain separate. Tutorial item/door services and full opening campaign unfinished.','files':records}
(OUT/'android-apk-manifest.json').write_text(json.dumps(result,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in result.items()if k!='files'},indent=2),flush=True)
